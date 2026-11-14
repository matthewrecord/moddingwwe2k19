/* File + hang tracer for WWE2K19 (proxy dinput8.dll). v1 2026-11-14, for the belt-prop load freeze.
 * - Patches the exe's import table: CreateFileA/W, ReadFile, ReadFileEx, CloseHandle (kernel32). Logs every open (path, handle, result)
 *   and, per handle, the first read and a summary at close (count, bytes, offsets seen). Paths containing a filter
 *   substring ("prop", "belt", ".pac" by default; all if TRACE_ALL file exists next to the exe) are logged in full.
 * - Vectored exception handler: logs the first 200 exceptions (code, RIP as exe offset).
 * - Watchdog thread: if no file activity for 8 s, samples every thread's RIP 5 times (1 s apart) and logs exe offsets
 *   plus a short stack scan of return addresses, so a hang shows where the game is looping/waiting.
 * Log: wwe2k19_filetrace_<tick>.log next to the exe. Remove by deleting dinput8.dll.
 * Build: x86_64-w64-mingw32-gcc -O2 -shared -o dinput8.dll dinput8_filetrace.c dinput8.def -static-libgcc */
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>

static FILE *g_log; static CRITICAL_SECTION g_cs; static DWORD g_t0; static HMODULE g_real; static uintptr_t g_base, g_end;
static volatile LONG g_lastio, g_lastpac; static char g_dir[MAX_PATH]; static int g_all; static volatile LONG g_nexc;
typedef HRESULT (WINAPI *DI8C)(HINSTANCE, DWORD, REFIID, LPVOID *, LPUNKNOWN);
static void tlog(const char *fmt, ...) {
    va_list ap; EnterCriticalSection(&g_cs);
    if (g_log) { fprintf(g_log, "[%8.3f t%5lu] ", (GetTickCount() - g_t0) / 1000.0, GetCurrentThreadId());
        va_start(ap, fmt); vfprintf(g_log, fmt, ap); va_end(ap); fputc('\n', g_log); fflush(g_log); }
    LeaveCriticalSection(&g_cs);
}
__declspec(dllexport) HRESULT WINAPI DirectInput8Create(HINSTANCE h, DWORD v, REFIID r, LPVOID *o, LPUNKNOWN u) {
    if (!g_real) { char p[MAX_PATH]; GetSystemDirectoryA(p, MAX_PATH); strcat(p, "\\dinput8.dll"); g_real = LoadLibraryA(p); }
    DI8C f = g_real ? (DI8C)GetProcAddress(g_real, "DirectInput8Create") : 0; return f ? f(h, v, r, o, u) : E_FAIL;
}

/* ---- per-handle bookkeeping */
#define NH 4096
typedef struct { HANDLE h; char path[200]; int show; LONGLONG bytes; long reads; LONGLONG minoff, maxoff; } HREC;
static HREC g_h[NH];
static HREC *hfind(HANDLE h) { for (int i = 0; i < NH; i++) if (g_h[i].h == h) return &g_h[i]; return 0; }
static int interesting(const char *p) {
    if (g_all) return 1; char l[260]; int i; for (i = 0; p[i] && i < 259; i++) l[i] = (char)tolower((unsigned char)p[i]); l[i] = 0;
    return strstr(l, "prop") || strstr(l, "belt") || strstr(l, ".pac") || strstr(l, ".def") || strstr(l, ".arc");
}
static void hadd(HANDLE h, const char *p) {
    if (h == INVALID_HANDLE_VALUE || !h) return; EnterCriticalSection(&g_cs);
    HREC *r = hfind(h); if (!r) r = hfind(0);
    if (r) { r->h = h; strncpy(r->path, p, 199); r->path[199] = 0; r->show = interesting(p); r->bytes = 0; r->reads = 0; r->minoff = -1; r->maxoff = 0; }
    LeaveCriticalSection(&g_cs);
}

/* ---- hooks */
typedef HANDLE (WINAPI *CFW)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
typedef HANDLE (WINAPI *CFA)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
typedef BOOL (WINAPI *RF)(HANDLE, LPVOID, DWORD, LPDWORD, LPOVERLAPPED);
typedef BOOL (WINAPI *CH)(HANDLE);
typedef BOOL (WINAPI *RFX)(HANDLE, LPVOID, DWORD, LPOVERLAPPED, LPOVERLAPPED_COMPLETION_ROUTINE);
static CFW oCFW; static CFA oCFA; static RF oRF; static CH oCH; static RFX oRFX;
static HANDLE WINAPI hCFW(LPCWSTR n, DWORD a, DWORD s, LPSECURITY_ATTRIBUTES sa, DWORD c, DWORD f, HANDLE t) {
    HANDLE h = oCFW(n, a, s, sa, c, f, t); DWORD e = GetLastError(); char p[260] = "";
    if (n) WideCharToMultiByte(CP_UTF8, 0, n, -1, p, 259, 0, 0);
    InterlockedExchange(&g_lastio, (LONG)GetTickCount());
    if (strstr(p, ".pac")) InterlockedExchange(&g_lastpac, (LONG)GetTickCount());
    if (interesting(p)) tlog("OPEN %s -> %p%s err=%lu flags=%lx", p, h, h == INVALID_HANDLE_VALUE ? " FAIL" : "", e, f);
    hadd(h, p); SetLastError(e); return h;
}
static HANDLE WINAPI hCFA(LPCSTR n, DWORD a, DWORD s, LPSECURITY_ATTRIBUTES sa, DWORD c, DWORD f, HANDLE t) {
    HANDLE h = oCFA(n, a, s, sa, c, f, t); DWORD e = GetLastError();
    InterlockedExchange(&g_lastio, (LONG)GetTickCount());
    if (n && strstr(n, ".pac")) InterlockedExchange(&g_lastpac, (LONG)GetTickCount());
    if (n && interesting(n)) tlog("OPENA %s -> %p%s err=%lu", n, h, h == INVALID_HANDLE_VALUE ? " FAIL" : "", e);
    hadd(h, n ? n : ""); SetLastError(e); return h;
}
static BOOL WINAPI hRF(HANDLE h, LPVOID b, DWORD n, LPDWORD got, LPOVERLAPPED ov) {
    LONGLONG off = -1;
    if (ov) off = ((LONGLONG)ov->OffsetHigh << 32) | ov->Offset;
    else { LARGE_INTEGER z = {0}, cur; if (SetFilePointerEx(h, z, &cur, FILE_CURRENT)) off = cur.QuadPart; }
    BOOL r = oRF(h, b, n, got, ov); DWORD e = GetLastError();
    InterlockedExchange(&g_lastio, (LONG)GetTickCount());
    EnterCriticalSection(&g_cs); HREC *q = hfind(h);
    if (q) { q->reads++; q->bytes += n; if (q->minoff < 0 || off < q->minoff) q->minoff = off; if (off + n > q->maxoff) q->maxoff = off + n;
        if (q->show && (q->reads <= 3 || strstr(q->path, "prop"))) tlog("READ %s off=%lld n=%lu ok=%d err=%lu%s", q->path, off, n, r, e, ov ? " (overlapped)" : ""); }
    LeaveCriticalSection(&g_cs); SetLastError(e); return r;
}
static BOOL WINAPI hRFX(HANDLE h, LPVOID b, DWORD n, LPOVERLAPPED ov, LPOVERLAPPED_COMPLETION_ROUTINE cr) {
    LONGLONG off = ov ? (((LONGLONG)ov->OffsetHigh << 32) | ov->Offset) : -1;
    BOOL r = oRFX(h, b, n, ov, cr); DWORD e = GetLastError();
    InterlockedExchange(&g_lastio, (LONG)GetTickCount());
    EnterCriticalSection(&g_cs); HREC *q = hfind(h);
    if (q) { q->reads++; q->bytes += n; if (q->minoff < 0 || off < q->minoff) q->minoff = off; if (off + n > q->maxoff) q->maxoff = off + n;
        if (q->show && (q->reads <= 3 || strstr(q->path, "prop"))) tlog("READEX %s off=%lld n=%lu ok=%d err=%lu", q->path, off, n, r, e); }
    else tlog("READEX unknown handle %p off=%lld n=%lu", h, off, n);
    LeaveCriticalSection(&g_cs); SetLastError(e); return r;
}
static BOOL WINAPI hCH(HANDLE h) {
    EnterCriticalSection(&g_cs); HREC *q = hfind(h);
    if (q) { if (q->show) tlog("CLOSE %s reads=%ld bytes=%lld span=[%lld,%lld)", q->path, q->reads, q->bytes, q->minoff, q->maxoff); q->h = 0; }
    LeaveCriticalSection(&g_cs); return oCH(h);
}
static void patch_iat(HMODULE m) {
    BYTE *b = (BYTE *)m; IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(b + ((IMAGE_DOS_HEADER *)b)->e_lfanew);
    IMAGE_DATA_DIRECTORY d = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT]; if (!d.VirtualAddress) return;
    for (IMAGE_IMPORT_DESCRIPTOR *im = (IMAGE_IMPORT_DESCRIPTOR *)(b + d.VirtualAddress); im->Name; im++) {
        IMAGE_THUNK_DATA *ot = (IMAGE_THUNK_DATA *)(b + (im->OriginalFirstThunk ? im->OriginalFirstThunk : im->FirstThunk));
        IMAGE_THUNK_DATA *ft = (IMAGE_THUNK_DATA *)(b + im->FirstThunk);
        for (; ot->u1.AddressOfData; ot++, ft++) {
            if (IMAGE_SNAP_BY_ORDINAL(ot->u1.Ordinal)) continue;
            const char *fn = (const char *)((IMAGE_IMPORT_BY_NAME *)(b + ot->u1.AddressOfData))->Name; void *nf = 0; void **save = 0;
            if (!strcmp(fn, "CreateFileW")) { nf = hCFW; save = (void **)&oCFW; }
            else if (!strcmp(fn, "CreateFileA")) { nf = hCFA; save = (void **)&oCFA; }
            else if (!strcmp(fn, "ReadFile")) { nf = hRF; save = (void **)&oRF; }
            else if (!strcmp(fn, "ReadFileEx")) { nf = hRFX; save = (void **)&oRFX; }
            else if (!strcmp(fn, "CloseHandle")) { nf = hCH; save = (void **)&oCH; }
            if (!nf) continue;
            DWORD op; if (!*save) *save = (void *)ft->u1.Function;
            VirtualProtect(&ft->u1.Function, 8, PAGE_READWRITE, &op); ft->u1.Function = (ULONG_PTR)nf; VirtualProtect(&ft->u1.Function, 8, op, &op);
            tlog("hooked %s!%s", (char *)(b + im->Name), fn);
        }
    }
}

/* ---- v3: execution breakpoints (DR0-DR2) on the titantron/belt video path (belt intro investigation 2026-11-14) */
static const uintptr_t BP_OFF[3] = {0x573940, 0x156ec20, 0x49ba20};
static const char *BP_NAME[3] = {"tron_screen_play(obj)", "titantron_play(obj)", "video_name(id)"};
static volatile LONG g_bphits;
static void apply_bp(HANDLE th) {
    CONTEXT c; memset(&c, 0, sizeof c); c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
    if (!GetThreadContext(th, &c)) return;
    c.Dr0 = g_base + BP_OFF[0]; c.Dr1 = g_base + BP_OFF[1]; c.Dr2 = g_base + BP_OFF[2];
    c.Dr7 = 1 | 4 | 16;                /* local enable DR0-DR2, execute (RW=00, LEN=00) */
    SetThreadContext(th, &c);
}
static void apply_bp_all(void) {
    DWORD me = GetCurrentThreadId(), pid = GetCurrentProcessId(); HANDLE s = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    THREADENTRY32 te; te.dwSize = sizeof te; if (s == INVALID_HANDLE_VALUE) return;
    for (BOOL ok = Thread32First(s, &te); ok; ok = Thread32Next(s, &te)) {
        if (te.th32OwnerProcessID != pid || te.th32ThreadID == me) continue;
        HANDLE th = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_SET_CONTEXT, FALSE, te.th32ThreadID); if (!th) continue;
        if (SuspendThread(th) != (DWORD)-1) { apply_bp(th); ResumeThread(th); }
        CloseHandle(th);
    }
    CloseHandle(s);
}
static uint32_t rd32(uintptr_t a) { uint32_t v = 0; SIZE_T g; ReadProcessMemory(GetCurrentProcess(), (void *)a, &v, 4, &g); return v; }
static LONG CALLBACK bpveh(EXCEPTION_POINTERS *x) {
    if (x->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP) return EXCEPTION_CONTINUE_SEARCH;
    CONTEXT *c = x->ContextRecord; DWORD64 st = c->Dr6;
    if (!(st & 7)) return EXCEPTION_CONTINUE_SEARCH;
    c->EFlags |= 0x10000;              /* RF: resume past the execute breakpoint */
    if (InterlockedIncrement(&g_bphits) <= 400) {
        uintptr_t ret = rd32(c->Rsp) | ((uintptr_t)rd32(c->Rsp + 4) << 32); uintptr_t r = ret - g_base; if (ret < g_base || ret >= g_end) r = 0;
        char stk[400] = ""; int n = 0;                       /* exe return addresses on the stack (call chain) */
        for (int k = 0; k < 400 && n < 14; k++) { uintptr_t v = rd32(c->Rsp + 8 * k) | ((uintptr_t)rd32(c->Rsp + 8 * k + 4) << 32);
            if (v > g_base && v < g_end) { char t[24]; sprintf(t, " +%llx", (unsigned long long)(v - g_base)); strcat(stk, t); n++; } }
        if (st & 1) tlog("BP %s obj=%llx [obj+20]=%u [obj+24]=%u [obj+30]=%u vtbl=+%llx | %s", BP_NAME[0], (unsigned long long)c->Rcx,
                         rd32(c->Rcx + 0x20), rd32(c->Rcx + 0x24), rd32(c->Rcx + 0x30),
                         (unsigned long long)((rd32(c->Rcx) | ((uintptr_t)rd32(c->Rcx + 4) << 32)) - g_base), stk);
        if (st & 2) tlog("BP %s obj=%llx [obj+84]=%u | %s", BP_NAME[1], (unsigned long long)c->Rcx, rd32(c->Rcx + 0x84), stk);
        if (st & 4) tlog("BP %s id=%u type=%u ret=+%llx | %s", BP_NAME[2], (unsigned)c->R8, (unsigned)c->R9, (unsigned long long)r, stk);
    }
    c->Dr6 = 0;
    return EXCEPTION_CONTINUE_EXECUTION;
}
/* ---- exceptions and hang sampling */
static LONG CALLBACK veh(EXCEPTION_POINTERS *x) {
    DWORD c = x->ExceptionRecord->ExceptionCode;
    if (c == 0x406D1388 || c == DBG_PRINTEXCEPTION_C || c == 0x4001000A || c == EXCEPTION_SINGLE_STEP) return EXCEPTION_CONTINUE_SEARCH;
    if (InterlockedIncrement(&g_nexc) <= 200) {
        uintptr_t ip = (uintptr_t)x->ExceptionRecord->ExceptionAddress;
        tlog("EXCEPTION %08lx at %p (exe+%llx) p0=%llx p1=%llx", c, (void *)ip, (unsigned long long)(ip >= g_base && ip < g_end ? ip - g_base : 0),
             (unsigned long long)x->ExceptionRecord->ExceptionInformation[0], (unsigned long long)x->ExceptionRecord->ExceptionInformation[1]);
    }
    return EXCEPTION_CONTINUE_SEARCH;
}
static void sample_threads(int round) {
    DWORD me = GetCurrentThreadId(), pid = GetCurrentProcessId(); HANDLE s = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    THREADENTRY32 te; te.dwSize = sizeof te;
    for (BOOL ok = Thread32First(s, &te); ok; ok = Thread32Next(s, &te)) {
        if (te.th32OwnerProcessID != pid || te.th32ThreadID == me) continue;
        HANDLE t = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, 0, te.th32ThreadID); if (!t) continue;
        if (SuspendThread(t) != (DWORD)-1) {
            CONTEXT c; c.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
            if (GetThreadContext(t, &c)) {
                char ret[400] = ""; int nr = 0; uintptr_t *sp = (uintptr_t *)c.Rsp;
                for (int k = 0; k < 256 && nr < 8; k++) { uintptr_t v; SIZE_T g;
                    if (!ReadProcessMemory(GetCurrentProcess(), sp + k, &v, 8, &g)) break;
                    if (v > g_base && v < g_end) { char t2[24]; sprintf(t2, " %llx", (unsigned long long)(v - g_base)); strcat(ret, t2); nr++; } }
                uintptr_t ip = c.Rip;
                if (ip >= g_base && ip < g_end) tlog("HANG r%d thread %lu rip exe+%llx | stack exe+:%s", round, te.th32ThreadID, (unsigned long long)(ip - g_base), ret);
                else { HMODULE mod = 0; char mn[MAX_PATH] = "?";
                    if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)ip, &mod)) GetModuleFileNameA(mod, mn, MAX_PATH);
                    char *bn = strrchr(mn, '\\'); tlog("HANG r%d thread %lu rip %s+%llx | stack exe+:%s", round, te.th32ThreadID, bn ? bn + 1 : mn,
                        (unsigned long long)(ip - (uintptr_t)mod), ret); }
            }
            ResumeThread(t);
        }
        CloseHandle(t);
    }
    CloseHandle(s);
}
static DWORD WINAPI watchdog(LPVOID p) {
    /* v2: sample when no .pac has been OPENED for 15 s while a load was in progress (other I/O such as audio streaming kept
       resetting v1's idle timer during a real hang), and whenever a file DUMP_NOW appears next to the exe (deleted after). */
    (void)p; int dumped = 0, beat = 0; char trig[MAX_PATH]; strcpy(trig, g_dir); strcat(trig, "DUMP_NOW");
    for (;;) {
        Sleep(1000); if (beat % 2 == 0) apply_bp_all(); DWORD now = GetTickCount(), idle = now - (DWORD)g_lastio, pidle = now - (DWORD)g_lastpac;
        if (++beat % 30 == 0) tlog("heartbeat io_idle=%lus pac_idle=%lus exc=%ld", idle / 1000, pidle / 1000, g_nexc);
        if (GetFileAttributesA(trig) != INVALID_FILE_ATTRIBUTES) { DeleteFileA(trig); tlog("=== DUMP_NOW trigger: sampling threads ===");
            for (int r = 0; r < 5; r++) { sample_threads(r); Sleep(1000); } }
        if (pidle > 15000 && pidle < 120000 && dumped < 3 && (dumped == 0 || pidle > 15000u + 20000u * dumped)) {
            tlog("=== no .pac opened for %lus (io_idle %lus): sampling threads (dump %d) ===", pidle / 1000, idle / 1000, dumped + 1);
            for (int r = 0; r < 5; r++) { sample_threads(r); Sleep(1000); } dumped++; }
        if (pidle < 2000) dumped = 0;
    }
    return 0;
}
BOOL WINAPI DllMain(HINSTANCE hi, DWORD r, LPVOID x) {
    (void)hi; (void)x;
    if (r == DLL_PROCESS_ATTACH) {
        InitializeCriticalSection(&g_cs); g_t0 = GetTickCount(); g_lastio = (LONG)g_t0; g_lastpac = (LONG)g_t0;
        char p[MAX_PATH]; GetModuleFileNameA(0, p, MAX_PATH); char *s = strrchr(p, '\\'); if (s) s[1] = 0; strcpy(g_dir, p);
        char q[MAX_PATH]; strcpy(q, p); strcat(q, "TRACE_ALL"); g_all = GetFileAttributesA(q) != INVALID_FILE_ATTRIBUTES;
        { char nm[64]; sprintf(nm, "wwe2k19_filetrace_%lu.log", GetTickCount()); strcat(p, nm); } g_log = fopen(p, "w");
        HMODULE exe = GetModuleHandleA(0); g_base = (uintptr_t)exe;
        IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((BYTE *)exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew); g_end = g_base + nt->OptionalHeader.SizeOfImage;
        tlog("filetrace v3b (belt-video breakpoints + call chains) loaded; exe base %p size %lx all=%d", (void *)g_base, nt->OptionalHeader.SizeOfImage, g_all);
        patch_iat(exe); AddVectoredExceptionHandler(1, bpveh); AddVectoredExceptionHandler(0, veh); CreateThread(0, 0, watchdog, 0, 0, 0);
    }
    return TRUE;
}
