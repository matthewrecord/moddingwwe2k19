/* WWE 2K19 telemetry proxy (dinput8.dll). Drop next to WWE2K19_x64.exe; delete to remove.
 * - Forwards DirectInput8Create to the real System32 dinput8.dll (the game imports only that).
 * - Watcher thread scans process memory every 2 s for the test BGM entries (u32 id*1000, u32 0xFFFF0000|id) and logs
 *   every copy that appears or disappears, with 160 bytes of context.
 * - Once raw copies exist, sets in-process hardware watchpoints (DR0-DR3, no debugger) on chosen entries in every
 *   thread; a vectored handler logs each new (watchpoint, RIP) with candidate return addresses from the stack.
 * Log: wwe2k19_trace.log next to the exe. Build: x86_64-w64-mingw32-gcc -O2 -shared -o dinput8.dll dinput8_trace.c
 *        dinput8.def -lpsapi -static-libgcc
 */
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

static const int IDS[] = {109, 650, 200, 150, 850, 807, 500, 999};
#define NIDS 8
static FILE *g_log; static CRITICAL_SECTION g_cs; static DWORD g_t0; static HMODULE g_real;
static uintptr_t g_base, g_end; static DWORD g_watcher_tid;
static volatile uintptr_t g_watch[4]; static volatile int g_watch_type[4]; /* 1=write 3=rw */
static const char *g_watch_name[4];

#define RING 8192
static char g_ring[RING][384]; static volatile LONG g_rw, g_rr;
static void ring_put(const char *line) {
    LONG k = InterlockedIncrement(&g_rw) - 1; if (k - g_rr >= RING) return;
    char *d = g_ring[k % RING]; strncpy(d, line, 383); d[383] = 0; }
static void tlog(const char *fmt, ...);
static void ring_flush(void) { while (g_rr < g_rw) { char *d = g_ring[g_rr % RING]; if (d[0]) { tlog("%s", d); d[0] = 0; } g_rr++; } }
static void tlog(const char *fmt, ...) {
    va_list ap; EnterCriticalSection(&g_cs);
    if (g_log) { fprintf(g_log, "[%7.2f t%5lu] ", (GetTickCount() - g_t0) / 1000.0, GetCurrentThreadId());
        va_start(ap, fmt); vfprintf(g_log, fmt, ap); va_end(ap); fputc('\n', g_log); fflush(g_log); }
    LeaveCriticalSection(&g_cs);
}
static void loghex(uintptr_t a, size_t n) {
    unsigned char buf[256]; SIZE_T got = 0; if (n > sizeof buf) n = sizeof buf;
    if (!ReadProcessMemory(GetCurrentProcess(), (void *)a, buf, n, &got)) { tlog("   <unreadable %p>", (void *)a); return; }
    for (size_t i = 0; i < got; i += 40) {
        char line[200]; int p = sprintf(line, "   %p:", (void *)(a + i));
        for (size_t j = i; j < i + 40 && j < got; j += 4) p += sprintf(line + p, " %08x", *(uint32_t *)(buf + j));
        tlog("%s", line);
    }
}

/* ---------- forwarding ---------- */
typedef HRESULT (WINAPI *DI8C)(HINSTANCE, DWORD, REFIID, LPVOID *, LPUNKNOWN);
__declspec(dllexport) HRESULT WINAPI DirectInput8Create(HINSTANCE h, DWORD v, REFIID r, LPVOID *o, LPUNKNOWN u) {
    if (!g_real) { char p[MAX_PATH]; GetSystemDirectoryA(p, MAX_PATH); strcat(p, "\\dinput8.dll"); g_real = LoadLibraryA(p); }
    DI8C f = g_real ? (DI8C)GetProcAddress(g_real, "DirectInput8Create") : 0;
    return f ? f(h, v, r, o, u) : E_FAIL;
}

/* ---------- hardware watchpoints ---------- */
static void apply_dr(HANDLE th) {
    CONTEXT c; memset(&c, 0, sizeof c); c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
    if (!GetThreadContext(th, &c)) return;
    DWORD64 dr7 = 0; uintptr_t *slots[4] = {(uintptr_t *)&c.Dr0, (uintptr_t *)&c.Dr1, (uintptr_t *)&c.Dr2, (uintptr_t *)&c.Dr3};
    for (int i = 0; i < 4; i++) {
        *slots[i] = g_watch[i];
        if (g_watch[i]) dr7 |= (1ull << (i * 2)) | ((DWORD64)(g_watch_type[i] & 3) << (16 + i * 4)) | (3ull << (18 + i * 4));
    }
    c.Dr7 = dr7; SetThreadContext(th, &c);
}
static void apply_all(void) {
    DWORD me = GetCurrentThreadId(), pid = GetCurrentProcessId();
    HANDLE s = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0); THREADENTRY32 te; te.dwSize = sizeof te;
    if (s == INVALID_HANDLE_VALUE) return;
    for (BOOL ok = Thread32First(s, &te); ok; ok = Thread32Next(s, &te)) {
        if (te.th32OwnerProcessID != pid || te.th32ThreadID == me) continue;
        HANDLE th = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_SET_CONTEXT, FALSE, te.th32ThreadID);
        if (!th) continue;
        if (SuspendThread(th) != (DWORD)-1) { apply_dr(th); ResumeThread(th); }
        CloseHandle(th);
    }
    CloseHandle(s);
}
#define MAXSEEN 4000
static struct { int dr; uintptr_t rip; } g_seen[MAXSEEN]; static volatile LONG g_nseen, g_hits;
static char *hx(char *o, unsigned long long v) { char t[17]; int n = 0; do { t[n++] = "0123456789abcdef"[v & 15]; v >>= 4; } while (v); while (n) *o++ = t[--n]; return o; }
static char *sa(char *o, const char *s) { while (*s) *o++ = *s++; return o; }
static LONG CALLBACK veh(PEXCEPTION_POINTERS ep) {
    if (ep->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP) return EXCEPTION_CONTINUE_SEARCH;
    CONTEXT *c = ep->ContextRecord; DWORD64 st = c->Dr6;
    if (!(st & 0xF)) return EXCEPTION_CONTINUE_SEARCH;
    InterlockedIncrement(&g_hits);
    for (int i = 0; i < 4; i++) if (st & (1 << i)) {
        uintptr_t rip = c->Rip; int dup = 0; LONG n = g_nseen;
        for (LONG k = 0; k < n && k < MAXSEEN; k++) if (g_seen[k].dr == i && g_seen[k].rip == rip) { dup = 1; break; }
        if (!dup && n < MAXSEEN) {
            LONG k = InterlockedIncrement(&g_nseen) - 1; if (k < MAXSEEN) { g_seen[k].dr = i; g_seen[k].rip = rip; }
            char line[384], *o = line, *lim = line + 330; uintptr_t *sp = (uintptr_t *)c->Rsp;
            o = sa(o, "t"); o = hx(o, GetCurrentThreadId()); o = sa(o, " HIT "); o = sa(o, g_watch_name[i]);
            o = sa(o, " rip=+"); o = hx(o, rip - g_base); o = sa(o, " rip_abs="); o = hx(o, rip);
            o = sa(o, " rcx="); o = hx(o, c->Rcx); o = sa(o, " rdx="); o = hx(o, c->Rdx); o = sa(o, " r8="); o = hx(o, c->R8);
            o = sa(o, " rax="); o = hx(o, c->Rax); o = sa(o, " stack:");
            for (int j = 0; j < 64 && o < lim; j++) { uintptr_t v = sp[j];   /* stack page is committed */
                if (v > g_base && v < g_end) { o = sa(o, " +"); o = hx(o, v - g_base); } }
            *o = 0;
            ring_put(line);
        }
    }
    c->Dr6 = 0;
    return EXCEPTION_CONTINUE_EXECUTION;
}

/* ---------- memory scanner ---------- */
#define MAXCOPIES 2048
static struct { uintptr_t a; int id; int alive; int first; } g_cp[MAXCOPIES]; static int g_ncp;
static int find_copy(uintptr_t a) { for (int i = 0; i < g_ncp; i++) if (g_cp[i].a == a) return i; return -1; }
static void scan(int pass) {
    static unsigned char buf[1 << 20]; uintptr_t a = 0x10000; MEMORY_BASIC_INFORMATION mi;
    for (int i = 0; i < g_ncp; i++) g_cp[i].alive &= ~2;
    while (a < 0x7FFFFFFF0000ull && VirtualQuery((void *)a, &mi, sizeof mi)) {
        uintptr_t rb = (uintptr_t)mi.BaseAddress, re = rb + mi.RegionSize;
        int ok = mi.State == MEM_COMMIT && !(mi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) && (mi.Type == MEM_PRIVATE || mi.Type == MEM_MAPPED) &&
                 (mi.Protect & (PAGE_READWRITE | PAGE_READONLY | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE));
        if (ok) for (uintptr_t p = rb; p < re; p += sizeof buf - 8) {
            SIZE_T n = re - p < sizeof buf ? re - p : sizeof buf, got = 0;
            if (!ReadProcessMemory(GetCurrentProcess(), (void *)p, buf, n, &got) || got < 8) break;
            for (SIZE_T k = 0; k + 9 <= got; k++) {
                if (buf[k] != 'T' || memcmp(buf + k, "TEST ", 5)) continue;
                int sid = -1; if (!memcmp(buf + k + 5, "500", 4)) sid = 500; else if (!memcmp(buf + k + 5, "109", 4)) sid = 109;
                if (sid < 0) continue;
                uintptr_t ea = p + k; int f = find_copy(ea);
                if (f < 0 && g_ncp < MAXCOPIES) { f = g_ncp++; g_cp[f].a = ea; g_cp[f].id = 100000 + sid; g_cp[f].alive = 0; g_cp[f].first = pass;
                    tlog("NEW string 'TEST %d' at %p (pass %d, region %p type %lx)", sid, (void *)ea, pass, (void *)rb, mi.Type); }
                if (f >= 0) g_cp[f].alive |= 3;
            }
            for (SIZE_T k = 4; k + 4 <= got; k += 4) {
                uint32_t hi = *(uint32_t *)(buf + k);
                if ((hi >> 16) != 0xFFFF) continue;
                int id = hi & 0xFFFF;
                for (int q = 0; q < NIDS; q++) if (IDS[q] == id && *(uint32_t *)(buf + k - 4) == (uint32_t)id * 1000) {
                    uintptr_t ea = p + k - 4;
                    int f = find_copy(ea);
                    if (f < 0 && g_ncp < MAXCOPIES) { f = g_ncp++; g_cp[f].a = ea; g_cp[f].id = id; g_cp[f].alive = 0; g_cp[f].first = pass;
                        tlog("NEW copy id=%d at %p (pass %d, region %p+%llx type %lx prot %lx)", id, (void *)ea, pass,
                             (void *)rb, (unsigned long long)mi.RegionSize, mi.Type, mi.Protect);
                        { uint32_t prev = 0, nxt = 0; SIZE_T g2;
                          ReadProcessMemory(GetCurrentProcess(), (void *)(ea - 36), &prev, 4, &g2);
                          ReadProcessMemory(GetCurrentProcess(), (void *)(ea + 44), &nxt, 4, &g2);
                          int pn = 0, nn = 0; for (int z = 0; z < NIDS; z++) { if (prev == (0xFFFF0000u | IDS[z])) pn = 1; if (nxt == (0xFFFF0000u | IDS[z])) nn = 1; }
                          if (id != 109 && !pn) tlog("   PARTIAL? id=%d has no test entry before it", id); }
                        loghex(ea - 80, 200); }
                    if (f >= 0) g_cp[f].alive |= 3;
                }
            }
        }
        a = re;
    }
    for (int i = 0; i < g_ncp; i++) if ((g_cp[i].alive & 1) && !(g_cp[i].alive & 2)) {
        tlog("GONE copy id=%d at %p (pass %d)", g_cp[i].id, (void *)g_cp[i].a, pass); g_cp[i].alive = 0; }
}
static DWORD WINAPI watcher(LPVOID _) {
    g_watcher_tid = GetCurrentThreadId(); SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_BELOW_NORMAL);
    int armed = 0;
    for (int pass = 1; pass <= 20000; pass++) {          /* ~60 min */
        Sleep(1000); ring_flush();
        scan(pass);
        {   /* watch the two OLDEST alive copies of each label string (string table is long-lived) */
            uintptr_t want[4] = {0, 0, 0, 0}; int n5 = 0, n1 = 0;
            for (int i = 0; i < g_ncp; i++) if (g_cp[i].alive & 1) {
                if (g_cp[i].id == 100500 && n5 < 2) want[n5++] = g_cp[i].a;
                else if (g_cp[i].id == 100109 && n1 < 2) want[2 + n1++] = g_cp[i].a; }
            if (memcmp((void *)want, (void *)g_watch, sizeof want)) {
                static const char *nm[4] = {"str500#1", "str500#2", "str109#1", "str109#2"};
                for (int k = 0; k < 4; k++) { g_watch[k] = want[k]; g_watch_type[k] = 3; g_watch_name[k] = nm[k]; }
                armed = 1; tlog("ARMED s500a=%p s500b=%p s109a=%p s109b=%p", (void *)want[0], (void *)want[1], (void *)want[2], (void *)want[3]);
            }
        }
        ring_flush();
        { static uintptr_t last[4]; static int lastpass;
          if (armed && (memcmp(last, (void *)g_watch, sizeof last) || pass - lastpass >= 20)) {
              apply_all(); memcpy(last, (void *)g_watch, sizeof last); lastpass = pass; } }
        if (pass % 10 == 0) tlog("heartbeat pass %d copies %d hits %ld unique %ld", pass, g_ncp, g_hits, g_nseen);
    }
    tlog("watcher done");
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD why, LPVOID r) {
    if (why == DLL_PROCESS_ATTACH) {
        InitializeCriticalSection(&g_cs); g_t0 = GetTickCount();
        char p[MAX_PATH]; GetModuleFileNameA(NULL, p, MAX_PATH); char *s = strrchr(p, '\\'); if (s) s[1] = 0;
        strcat(p, "wwe2k19_trace.log"); g_log = fopen(p, "w");
        g_base = (uintptr_t)GetModuleHandleA(NULL);
        IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(g_base + ((IMAGE_DOS_HEADER *)g_base)->e_lfanew);
        g_end = g_base + nt->OptionalHeader.SizeOfImage;
        tlog("telemetry v5 loaded; exe base %p size %lx", (void *)g_base, nt->OptionalHeader.SizeOfImage);
        AddVectoredExceptionHandler(1, veh);
        CreateThread(NULL, 0, watcher, NULL, 0, NULL);
    } else if (why == DLL_THREAD_ATTACH) {
        /* new threads get watchpoints at the next 1-2 s sweep */
    }
    return TRUE;
}
