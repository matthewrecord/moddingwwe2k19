/* WWE 2K19 character-slot expansion proxy (dinput8.dll). Drop next to WWE2K19_x64.exe; delete/rename to remove.
 * The .exe on disk is never modified: patches are applied in memory from DllMain, before the game's own code runs.
 * Every patch first checks the exact original bytes; if ANY site differs (other exe build), NOTHING is applied.
 * Log: wwe2k19_slots.log next to the exe.
 *
 * Stage "test1": SLOT_CAP 510 + slots\\ injection (see README). Stage "test0" (SLOT_CAP = 509): behaviour must be identical to vanilla. It proves the mechanism:
 *  - relocates the static 509-entry tables (main moveset array 0x142671078, 40-byte per-slot table 0x14281f7e0,
 *    index->id table 0x1425bfb60) into bigger buffers allocated near the image, by rewriting their RIP-relative refs;
 *  - detours the main-array path of the pofo getter 0x140965710 to a stub that sends idx >= 509 to an overflow array.
 * No bound check is raised in test0, so no slot >= 509 can be reached yet.
 * Notes: notes/characters/expand_509_scope_2026-11-10.md (step 1f) and tools/slots/README.md.
 * Build: x86_64-w64-mingw32-gcc -O2 -shared -masm=intel -o dinput8.dll dinput8_slots.c dinput8.def -static-libgcc
 */
#include <windows.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define BASE_SLOTS 509
#define MAX_SLOTS  1024          /* capacity of the relocated buffers (ids are < 1024 anyway) */
#ifndef SLOT_CAP
#define SLOT_CAP   510           /* slots 0..SLOT_CAP-1 pass the raised lookup checks (test1: one overflow slot) */
#endif

static FILE *g_log; static HMODULE g_real; static uintptr_t g_img; static DWORD g_t0;
static void L(const char *f, ...) { if (!g_log) return; va_list a; va_start(a, f); vfprintf(g_log, f, a); va_end(a);
    fputc('\n', g_log); fflush(g_log); }

typedef HRESULT (WINAPI *DI8C)(HINSTANCE, DWORD, REFIID, LPVOID *, LPUNKNOWN);
__declspec(dllexport) HRESULT WINAPI DirectInput8Create(HINSTANCE h, DWORD v, REFIID r, LPVOID *o, LPUNKNOWN u) {
    if (!g_real) { char p[MAX_PATH]; GetSystemDirectoryA(p, MAX_PATH); strcat(p, "\\dinput8.dll"); g_real = LoadLibraryA(p); }
    DI8C f = g_real ? (DI8C)GetProcAddress(g_real, "DirectInput8Create") : 0;
    return f ? f(h, v, r, o, u) : E_FAIL;
}

#define VA(x) (g_img + ((uint64_t)(x) - 0x140000000ULL))

/* ---- stub for the pofo getter's main-array path (0x140965760: imul rax,r8,0x1e4 / add rax,[main] / ret) ---- */
uintptr_t g_main_ptr_addr;   /* address of the qword holding the main block pointer (0x1425e69b0) */
uintptr_t g_ovf_pofo;        /* overflow pofo array: slot BASE_SLOTS+k at g_ovf_pofo + k*0x1E4 */
extern char stub_pofo_main[];
__asm__(
    ".globl stub_pofo_main\n"
    "stub_pofo_main:\n"
    "  cmp r8, 509\n"
    "  jge 1f\n"
    "  imul rax, r8, 0x1e4\n"
    "  mov rcx, qword ptr [rip + g_main_ptr_addr]\n"
    "  add rax, qword ptr [rcx]\n"
    "  ret\n"
    "1:\n"
    "  lea rax, [r8 - 509]\n"
    "  imul rax, rax, 0x1e4\n"
    "  add rax, qword ptr [rip + g_ovf_pofo]\n"
    "  ret\n");

/* ---- inline pofo-array indexing (pofo index from the id map, array = some 509-entry pofo array): each site's
   `imul R, X, 0x1e4` (7 bytes) becomes `call stub; nop; nop`. The stub returns X*0x1E4 for X < 509; for X >= 509 it
   returns overflow_entry + k - B, so the site's following `add R, B` (+ constant) lands on the overflow pofo. ---- */
extern char st_e8130b[], st_e23c67[], st_e5de59[], st_d2513f[];
__asm__(
    ".globl st_e8130b\n st_e8130b:\n  cmp rax, 509\n  jge 1f\n  imul rax, rax, 0x1e4\n  ret\n"
    "1:\n  sub rax, 509\n  imul rax, rax, 0x1e4\n  add rax, qword ptr [rip + g_ovf_pofo]\n  sub rax, rdi\n  ret\n"   /* then add rax, rdi */
    ".globl st_e23c67\n st_e23c67:\n  cmp rax, 509\n  jge 1f\n  imul rax, rax, 0x1e4\n  ret\n"
    "1:\n  sub rax, 509\n  imul rax, rax, 0x1e4\n  add rax, qword ptr [rip + g_ovf_pofo]\n  sub rax, rdx\n  ret\n"   /* then add rax, rdx */
    ".globl st_e5de59\n st_e5de59:\n  cmp rax, 509\n  jge 1f\n  imul rcx, rax, 0x1e4\n  ret\n"
    "1:\n  lea rcx, [rax - 509]\n  imul rcx, rcx, 0x1e4\n  add rcx, qword ptr [rip + g_ovf_pofo]\n  add rcx, 0x120\n  sub rcx, rdi\n  ret\n"   /* rdi = array + 0x120; then add rcx, rdi */
    ".globl st_d2513f\n st_d2513f:\n  cmp rcx, 509\n  jge 1f\n  imul rax, rcx, 0x1e4\n  ret\n"
    "1:\n  lea rax, [rcx - 509]\n  imul rax, rax, 0x1e4\n  add rax, qword ptr [rip + g_ovf_pofo]\n  sub rax, 0x2247c\n  sub rax, rdi\n  ret\n"   /* then add rax, 0x2247c; add rax, rdi */
);
typedef struct { uint64_t va; const char *orig; void *stub; } Site;
static const Site SITES[] = {
    {0x140e8130b, "4869c0e4010000", st_e8130b}, {0x140e23c67, "4869c0e4010000", st_e23c67},
    {0x140e5de59, "4869c8e4010000", st_e5de59}, {0x140d2513f, "4869c1e4010000", st_d2513f},
};
#define NSITES (int)(sizeof SITES / sizeof SITES[0])
static uint8_t *g_tramp;   /* near-image jump table: call rel32 must reach it */

/* ---- buffers near the image (RIP-relative disp32 needs +-2 GB) ---- */
static void *alloc_near(size_t n) {
    uintptr_t a = (g_img + 0x3700000 + 0xFFFF) & ~(uintptr_t)0xFFFF;
    for (; a < g_img + 0x7F000000ULL; a += 0x10000) {
        void *p = VirtualAlloc((void *)a, n, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
        if (p) return p;
    }
    return 0;
}

typedef struct { uint64_t va; const char *orig; int n; uint8_t neu[16]; const char *what; } Patch;
typedef struct { uint64_t va; int len; int dispoff; uint64_t oldbase; int which; const char *orig; } Reloc;

static int hexb(const char *s, uint8_t *o) { int n = 0; while (s[0] && s[1]) { unsigned v; sscanf(s, "%2x", &v); o[n++] = (uint8_t)v; s += 2; } return n; }
static int same(uint64_t va, const char *hex) { uint8_t b[32]; int n = hexb(hex, b); return memcmp((void *)VA(va), b, n) == 0; }
static void put(uint64_t va, const void *src, int n) {
    DWORD old; void *p = (void *)VA(va); VirtualProtect(p, n, PAGE_EXECUTE_READWRITE, &old);
    memcpy(p, src, n); VirtualProtect(p, n, old, &old); FlushInstructionCache(GetCurrentProcess(), p, n);
}

/* relocated tables: 0 moveset main (0xD88 x), 1 per-slot 40-byte table, 2 index->id ints */
static const uint64_t TBL_OLD[3] = {0x142671078ULL, 0x14281f7e0ULL, 0x1425bfb60ULL};
static const size_t   TBL_STRIDE[3] = {0xD88, 40, 4};
static uint8_t *TBL_NEW[3];

static const Reloc RELOCS[] = {
    {0x140963101, 7, 3, 0x142671078ULL, 0, "488d0570dfd001"},
    {0x1409635ac, 7, 3, 0x142671078ULL, 0, "488d0dc5dad001"},
    {0x1409636ce, 7, 3, 0x142671078ULL, 0, "4c8d25a3d9d001"},
    {0x14096580e, 7, 3, 0x142671078ULL, 0, "488d0d63b8d001"},
    {0x140962fe4, 7, 3, 0x142671078ULL, 0, "488d0539e4d001"},   /* target +0x3AC inside element 0 */
    {0x14096529c, 7, 3, 0x142671078ULL, 0, "488d0581c1d001"},   /* target +0x3AC */
    {0x140965906, 7, 3, 0x14281f7e0ULL, 1, "488d05d39eeb01"},
    {0x1404c98f6, 7, 3, 0x1425bfb60ULL, 2, "488d0d63620f02"},
    {0x14190fc83, 7, 3, 0x1425bfb60ULL, 2, "488d05d6feca00"},
};
#define NRELOC (int)(sizeof RELOCS / sizeof RELOCS[0])

static int apply(void) {
    int ok = 1;
    for (int i = 0; i < NRELOC; i++) if (!same(RELOCS[i].va, RELOCS[i].orig)) { L("MISMATCH reloc %llx", RELOCS[i].va); ok = 0; }
    if (!same(0x140965760, "4969c0e40100004803054212c801c3")) { L("MISMATCH pofo getter 140965760"); ok = 0; }
    if (!same(0x14190fc8a, "b91f000000")) { L("MISMATCH idx->id init 14190fc8a"); ok = 0; }
    if (!same(0x1409656bb, "3dfc010000")) { L("MISMATCH 1409656bb"); ok = 0; }
    if (!same(0x1409657ef, "4181f9fd010000")) { L("MISMATCH 1409657ef"); ok = 0; }
    if (!same(0x1404c98e9, "4181fafd010000")) { L("MISMATCH 1404c98e9"); ok = 0; }
    if (!same(0x14190fe1d, "4589948160fb5b02")) { L("MISMATCH 14190fe1d"); ok = 0; }
    if (!same(0x14190fe36, "41898c8160fb5b02")) { L("MISMATCH 14190fe36"); ok = 0; }
    for (int i = 0; i < NSITES; i++) if (!same(SITES[i].va, SITES[i].orig)) { L("MISMATCH site %llx", SITES[i].va); ok = 0; }
    if (!same(0x1409658f9, "3dfd010000")) { L("MISMATCH 1409658f9"); ok = 0; }
    if (!ok) { L("exe build differs: NOTHING applied"); return 0; }

    for (int t = 0; t < 3; t++) {
        size_t n = TBL_STRIDE[t] * MAX_SLOTS + 0x1000;
        TBL_NEW[t] = alloc_near(n);
        if (!TBL_NEW[t]) { L("alloc_near failed (table %d): NOTHING applied", t); return 0; }
        memcpy(TBL_NEW[t], (void *)VA(TBL_OLD[t]), TBL_STRIDE[t] * BASE_SLOTS);   /* carry any static contents */
        if (t == 2) for (int k = BASE_SLOTS; k < MAX_SLOTS; k++) ((int32_t *)TBL_NEW[t])[k] = 0x400;
        L("table %d: %llx -> %p (%zu bytes)", t, TBL_OLD[t], TBL_NEW[t], n);
    }
    g_ovf_pofo = (uintptr_t)alloc_near(0x1E4 * (MAX_SLOTS - BASE_SLOTS));
    g_main_ptr_addr = VA(0x1425e69b0ULL);
    if (!g_ovf_pofo) { L("alloc_near failed (overflow): NOTHING applied"); return 0; }

    for (int i = 0; i < NRELOC; i++) {
        const Reloc *r = &RELOCS[i];
        int32_t d; memcpy(&d, (void *)(VA(r->va) + r->dispoff), 4);
        uint64_t tgt = VA(r->va) + r->len + d;                     /* old absolute target */
        uint64_t neu = (uint64_t)TBL_NEW[r->which] + (tgt - VA(r->oldbase));
        int64_t nd = (int64_t)neu - (int64_t)(VA(r->va) + r->len);
        if (nd > INT32_MAX || nd < INT32_MIN) { L("disp out of range at %llx", r->va); return 0; }
        int32_t d2 = (int32_t)nd; put(r->va + r->dispoff, &d2, 4);
    }
    /* image-base-relative writes of the index->id table in the registration function 0x14190fdf0
       ([r9 + rax*4 + 0x25bfb60], r9 = image base): disp32 at +4 becomes new table - image base */
    { int64_t nd = (int64_t)(uintptr_t)TBL_NEW[2] - (int64_t)g_img;
      if (nd <= 0 || nd > INT32_MAX) { L("idx2id table too far for image-relative disp: NOT applying"); return 0; }
      int32_t d2 = (int32_t)nd; put(0x14190fe1d + 4, &d2, 4); put(0x14190fe36 + 4, &d2, 4); }
    /* index->id init loop: 0x1f*16 + tail 13 ints; cover MAX_SLOTS (63*16 + 13 = 1021 <= 1024+0x1000/4) */
    uint8_t movecx[5] = {0xB9, 0x3F, 0, 0, 0}; put(0x14190fc8a, movecx, 5);
    /* pofo getter main path -> stub (mov rax, imm64; jmp rax; 2 x int3) */
    uint8_t j[14] = {0x48, 0xB8}; uint64_t s = (uint64_t)stub_pofo_main; memcpy(j + 2, &s, 8);
    j[10] = 0xFF; j[11] = 0xE0; j[12] = 0xCC; j[13] = 0xCC; put(0x140965760, j, 14);
    /* inline pofo sites -> call near trampoline (jmp [rip+0] abs64) -> stub */
    g_tramp = alloc_near(0x1000);
    if (!g_tramp) { L("alloc_near failed (tramp)"); return 0; }
    for (int i = 0; i < NSITES; i++) {
        uint8_t *t = g_tramp + 16 * i; t[0] = 0xFF; t[1] = 0x25; memset(t + 2, 0, 4); uint64_t a = (uint64_t)SITES[i].stub; memcpy(t + 6, &a, 8);
        int64_t rel = (int64_t)(uintptr_t)t - (int64_t)(VA(SITES[i].va) + 5);
        if (rel > INT32_MAX || rel < INT32_MIN) { L("tramp out of range"); return 0; }
        uint8_t c[7] = {0xE8}; int32_t r32 = (int32_t)rel; memcpy(c + 1, &r32, 4); c[5] = 0x90; c[6] = 0x90; put(SITES[i].va, c, 7);
    }
    { DWORD old; VirtualProtect(g_tramp, 0x1000, PAGE_EXECUTE_READ, &old); }
    /* lookup bounds: pofo-by-id getter (ja 0x1FC), moveset-by-id getter (jge 0x1FD), index->id reader (jae 0x1FD) */
    { uint32_t v = SLOT_CAP - 1; put(0x1409656bb + 1, &v, 4); v = SLOT_CAP; put(0x1409657ef + 3, &v, 4); put(0x1404c98e9 + 3, &v, 4);
      put(0x1409658f9 + 1, &v, 4); /* 40-byte record getter 0x140965860 (jge 0x1FD): used with the moveset by match setup 0x141331281 */ }
    L("applied: %d inline sites, %d relocs, getter detour -> %p, overflow pofo %p, SLOT_CAP %d", NSITES, NRELOC, (void *)s, (void *)g_ovf_pofo, SLOT_CAP);
    return 1;
}

/* ---- overflow slots: slots\\IIII_DDDD.pofo / .moveset next to the exe (profile index IIII >= 509, character id DDDD).
   After the game has built its id->index map, write pofo/moveset into the overflow/relocated arrays and register
   id <-> index; re-done whenever the map is rebuilt (checked every second). ---- */
typedef struct { int idx, id, src; uint8_t pofo[0x1E4]; uint8_t mov[0xD88]; int done_logged; } Slot;
static Slot g_slots[64]; static int g_nslots;
static int readf(const char *p, void *buf, DWORD n) { HANDLE h = CreateFileA(p, GENERIC_READ, FILE_SHARE_READ, 0, OPEN_EXISTING, 0, 0);
    if (h == INVALID_HANDLE_VALUE) return 0; DWORD got = 0; ReadFile(h, buf, n, &got, 0); DWORD hi = 0, sz = GetFileSize(h, &hi); CloseHandle(h); return got == n && sz == n; }
static void load_slots(void) {
    char dir[MAX_PATH], pat[MAX_PATH]; GetModuleFileNameA(NULL, dir, MAX_PATH); char *s = strrchr(dir, '\\'); if (s) s[1] = 0;
    strcat(dir, "slots\\"); strcpy(pat, dir); strcat(pat, "*.pofo");
    WIN32_FIND_DATAA f; HANDLE h = FindFirstFileA(pat, &f); if (h == INVALID_HANDLE_VALUE) { L("no slots\\*.pofo"); return; }
    do { int idx, id, src = -1; int nf = sscanf(f.cFileName, "%d_%d_%d.pofo", &idx, &id, &src);
        if (nf < 2 || g_nslots >= 64) continue; if (nf == 2) src = -1;
        Slot *t = &g_slots[g_nslots]; char p[MAX_PATH];
        if (idx < BASE_SLOTS || idx >= SLOT_CAP || id < 100 || id >= 1024) { L("slot %s: index/id out of range (cap %d)", f.cFileName, SLOT_CAP); continue; }
        strcpy(p, dir); strcat(p, f.cFileName); if (!readf(p, t->pofo, 0x1E4)) { L("slot %s: bad pofo", f.cFileName); continue; }
        strcpy(strrchr(p, '.'), ".moveset"); if (!readf(p, t->mov, 0xD88)) { L("slot %s: missing/bad .moveset", f.cFileName); continue; }
        t->idx = idx; t->id = id; t->src = src; *(uint16_t *)t->pofo = (uint16_t)id; *(uint16_t *)(t->pofo + 2) = (uint16_t)idx;
        g_nslots++; L("slot loaded: index %d id %d (%s)", idx, id, f.cFileName);
    } while (FindNextFileA(h, &f)); FindClose(h);
}
static DWORD WINAPI slot_thread(LPVOID p) {
    (void)p; volatile int32_t *flag = (int32_t *)VA(0x1425beb50ULL), *map = (int32_t *)VA(0x1425beb60ULL);
    int32_t *i2i = (int32_t *)TBL_NEW[2];
    for (int tick = 0;; tick++) {
        Sleep(1000);
        if (!*flag) continue;
        for (int k = 0; k < g_nslots; k++) {
            Slot *t = &g_slots[k];
            if (map[t->id] == t->idx && i2i[t->idx] == t->id) continue;
            if (map[t->id] != -1 && map[t->id] != t->idx) { if (!t->done_logged) L("id %d already used by index %d: slot %d skipped", t->id, map[t->id], t->idx); t->done_logged = 1; continue; }
            memcpy((void *)(g_ovf_pofo + (size_t)(t->idx - BASE_SLOTS) * 0x1E4), t->pofo, 0x1E4);
            memcpy(TBL_NEW[0] + (size_t)t->idx * 0xD88, t->mov, 0xD88);
            if (t->src >= 0 && map[t->src] >= 0 && map[t->src] < BASE_SLOTS)   /* per-slot 40-byte record: clone the source's */
                memcpy(TBL_NEW[1] + (size_t)t->idx * 40, TBL_NEW[1] + (size_t)map[t->src] * 40, 40);
            i2i[t->idx] = t->id; map[t->id] = t->idx;
            L("[%d s] slot %d registered (id %d, 40-byte record from id %d)", tick + 1, t->idx, t->id, t->src);
        }
    }
    return 0;
}


/* ---- file-activity recorder: hooks the exe's kernel32 imports (IAT; the exe on disk is untouched).
   Keeps the last RING_N file events in memory; written to the log on a crash, on F12, and at exit.
   Failed opens are written immediately (a missing file is the usual reason "something doesn't work"). ---- */
#define RING_N 1024
#define NAMES 8192
typedef struct { DWORD t, tid; char op; HANDLE h; uint64_t a, b; } Ev;
static Ev g_ring[RING_N]; static volatile LONG g_ri;
static struct { HANDLE h; wchar_t n[180]; } g_names[NAMES]; static CRITICAL_SECTION g_ncs;
static void name_set(HANDLE h, const wchar_t *n) {
    EnterCriticalSection(&g_ncs); unsigned k = ((uintptr_t)h >> 2) % NAMES;
    for (unsigned i = 0; i < NAMES; i++, k = (k + 1) % NAMES) if (!g_names[k].h || g_names[k].h == h) {
        g_names[k].h = h; wcsncpy(g_names[k].n, n, 179); g_names[k].n[179] = 0; break; }
    LeaveCriticalSection(&g_ncs); }
static const wchar_t *name_get(HANDLE h) {
    unsigned k = ((uintptr_t)h >> 2) % NAMES;
    for (unsigned i = 0; i < NAMES; i++, k = (k + 1) % NAMES) { if (g_names[k].h == h) return g_names[k].n; if (!g_names[k].h) break; }
    return L"?"; }
static void ev(char op, HANDLE h, uint64_t a, uint64_t b) {
    LONG i = InterlockedIncrement(&g_ri) - 1; Ev *e = &g_ring[i % RING_N];
    e->t = GetTickCount(); e->tid = GetCurrentThreadId(); e->op = op; e->h = h; e->a = a; e->b = b; }
static void dump_ring(const char *why) {
    LONG n = g_ri; LONG from = n > RING_N ? n - RING_N : 0;
    L("---- last %ld file events (%s), oldest first; O=open R=read(size,offset) X=readex S=seek C=close M=map ----", n - from, why);
    for (LONG i = from; i < n; i++) { Ev *e = &g_ring[i % RING_N];
        L("  %8.2f t%-5lu %c %ls  %llx %llx", (e->t - g_t0) / 1000.0, e->tid, e->op, name_get(e->h), (unsigned long long)e->a, (unsigned long long)e->b); }
    L("---- end of file events ----"); }

typedef HANDLE (WINAPI *CFW)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
typedef HANDLE (WINAPI *CFA)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
typedef BOOL (WINAPI *RF)(HANDLE, LPVOID, DWORD, LPDWORD, LPOVERLAPPED);
typedef BOOL (WINAPI *RFX)(HANDLE, LPVOID, DWORD, LPOVERLAPPED, LPOVERLAPPED_COMPLETION_ROUTINE);
typedef DWORD (WINAPI *SFP)(HANDLE, LONG, PLONG, DWORD);
typedef BOOL (WINAPI *CH)(HANDLE);
typedef HANDLE (WINAPI *CFMW)(HANDLE, LPSECURITY_ATTRIBUTES, DWORD, DWORD, DWORD, LPCWSTR);
static CFW o_cfw; static CFA o_cfa; static RF o_rf; static RFX o_rfx; static SFP o_sfp; static CH o_ch; static CFMW o_cfmw;
static HANDLE WINAPI h_cfw(LPCWSTR n, DWORD a, DWORD s, LPSECURITY_ATTRIBUTES sa, DWORD c, DWORD f, HANDLE t) {
    HANDLE h = o_cfw(n, a, s, sa, c, f, t); DWORD err = GetLastError();
    if (h != INVALID_HANDLE_VALUE) { name_set(h, n ? n : L"(null)"); ev('O', h, a, c); }
    else if (n && wcsncmp(n, L"\\\\.\\", 4)) L("[%8.2f] OPEN FAILED (err %lu): %ls", (GetTickCount() - g_t0) / 1000.0, err, n);
    SetLastError(err); return h; }
static HANDLE WINAPI h_cfa(LPCSTR n, DWORD a, DWORD s, LPSECURITY_ATTRIBUTES sa, DWORD c, DWORD f, HANDLE t) {
    HANDLE h = o_cfa(n, a, s, sa, c, f, t); DWORD err = GetLastError(); wchar_t w[180] = L"(null)";
    if (n) MultiByteToWideChar(CP_ACP, 0, n, -1, w, 179);
    if (h != INVALID_HANDLE_VALUE) { name_set(h, w); ev('O', h, a, c); }
    else if (n) L("[%8.2f] OPEN FAILED (err %lu): %s", (GetTickCount() - g_t0) / 1000.0, err, n);
    SetLastError(err); return h; }
static BOOL WINAPI h_rf(HANDLE h, LPVOID b, DWORD n, LPDWORD got, LPOVERLAPPED o) {
    ev('R', h, n, o ? ((uint64_t)o->OffsetHigh << 32 | o->Offset) : (uint64_t)-1); return o_rf(h, b, n, got, o); }
static BOOL WINAPI h_rfx(HANDLE h, LPVOID b, DWORD n, LPOVERLAPPED o, LPOVERLAPPED_COMPLETION_ROUTINE cr) {
    ev('X', h, n, o ? ((uint64_t)o->OffsetHigh << 32 | o->Offset) : (uint64_t)-1); return o_rfx(h, b, n, o, cr); }
static DWORD WINAPI h_sfp(HANDLE h, LONG lo, PLONG hi, DWORD m) { ev('S', h, (uint64_t)(hi ? (uint64_t)*hi << 32 : 0) | (DWORD)lo, m); return o_sfp(h, lo, hi, m); }
static BOOL WINAPI h_ch(HANDLE h) { ev('C', h, 0, 0); return o_ch(h); }
static HANDLE WINAPI h_cfmw(HANDLE f, LPSECURITY_ATTRIBUTES sa, DWORD p, DWORD hi, DWORD lo, LPCWSTR n) {
    HANDLE m = o_cfmw(f, sa, p, hi, lo, n); ev('M', f, (uint64_t)hi << 32 | lo, (uintptr_t)m); return m; }

static int hook_iat(const char *fn, void *hook, void **orig) {
    IMAGE_DOS_HEADER *d = (IMAGE_DOS_HEADER *)g_img; IMAGE_NT_HEADERS64 *nt = (IMAGE_NT_HEADERS64 *)(g_img + d->e_lfanew);
    IMAGE_DATA_DIRECTORY dd = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    for (IMAGE_IMPORT_DESCRIPTOR *im = (void *)(g_img + dd.VirtualAddress); im->Name; im++) {
        if (_stricmp((char *)(g_img + im->Name), "KERNEL32.dll")) continue;
        IMAGE_THUNK_DATA64 *nm = (void *)(g_img + im->OriginalFirstThunk), *ad = (void *)(g_img + im->FirstThunk);
        for (; nm->u1.AddressOfData; nm++, ad++) {
            if (nm->u1.Ordinal & IMAGE_ORDINAL_FLAG64) continue;
            if (strcmp((char *)((IMAGE_IMPORT_BY_NAME *)(g_img + nm->u1.AddressOfData))->Name, fn)) continue;
            if ((void *)ad->u1.Function == hook) return 1;
            if (!*orig) *orig = (void *)ad->u1.Function;
            DWORD old; VirtualProtect(&ad->u1.Function, 8, PAGE_READWRITE, &old); ad->u1.Function = (uintptr_t)hook; VirtualProtect(&ad->u1.Function, 8, old, &old);
            return 2;
        }
    }
    return 0;
}
static int hook_all(void) {
    int r = 0;
    r += hook_iat("CreateFileW", h_cfw, (void **)&o_cfw) == 2; r += hook_iat("CreateFileA", h_cfa, (void **)&o_cfa) == 2;
    r += hook_iat("ReadFile", h_rf, (void **)&o_rf) == 2; r += hook_iat("ReadFileEx", h_rfx, (void **)&o_rfx) == 2;
    r += hook_iat("SetFilePointer", h_sfp, (void **)&o_sfp) == 2; r += hook_iat("CloseHandle", h_ch, (void **)&o_ch) == 2;
    r += hook_iat("CreateFileMappingW", h_cfmw, (void **)&o_cfmw) == 2;
    return r; }

/* ---- hang snapshot (F12): ask the game's own dbghelp.dll (loaded by name at run time) to write a minidump of the
   process: every thread's registers and stack. Read with tools/exe/crashdump.py --all. (test1d's own thread
   suspension was blocked by Windows security, so this build uses the standard dump API instead.) ---- */
typedef BOOL (WINAPI *MDWD)(HANDLE, DWORD, HANDLE, int, void *, void *, void *);
static void dump_threads(void) {
    static MDWD f; if (!f) { HMODULE d = LoadLibraryA("dbghelp.dll"); if (d) f = (MDWD)GetProcAddress(d, "MiniDumpWriteDump"); }
    if (!f) { L("no MiniDumpWriteDump"); return; }
    char p[MAX_PATH]; GetModuleFileNameA(NULL, p, MAX_PATH); char *s = strrchr(p, '\\'); if (s) s[1] = 0;
    sprintf(p + strlen(p), "slots_snapshot_%lu.dmp", (unsigned long)((GetTickCount() - g_t0) / 1000));
    HANDLE h = CreateFileA(p, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, 0, 0);
    if (h == INVALID_HANDLE_VALUE) { L("snapshot: cannot create %s", p); return; }
    BOOL ok = f(GetCurrentProcess(), GetCurrentProcessId(), h, 0x0 /* MiniDumpNormal: all thread stacks */, 0, 0, 0);
    CloseHandle(h); L("snapshot %s: %s", p, ok ? "written" : "FAILED");
}
static DWORD WINAPI rec_thread(LPVOID p) {
    (void)p; int down = 0;
    for (int i = 0;; i++) {
        Sleep(100);
        if (i % 20 == 0) { int r = hook_all(); if (r) L("[%8.2f] file hooks (re)installed: %d", (GetTickCount() - g_t0) / 1000.0, r); }
        int k = (GetAsyncKeyState(VK_F12) & 0x8000) != 0;
        if (k && !down) { L("[%8.2f] F12", (GetTickCount() - g_t0) / 1000.0); dump_threads(); dump_ring("F12 pressed"); }
        down = k;
    }
    return 0;
}

/* ---- crash logger: vectored handler logs fatal-type exceptions raised in the exe or this DLL (first chance,
   so also ones the game later handles; capped at 20 entries). Registers, faulting address as exe offset, and
   exe return addresses found on the stack. ---- */
static volatile LONG g_nexc;
static LONG CALLBACK veh(PEXCEPTION_POINTERS e) {
    DWORD c = e->ExceptionRecord->ExceptionCode;
    if (c != EXCEPTION_ACCESS_VIOLATION && c != EXCEPTION_ILLEGAL_INSTRUCTION && c != EXCEPTION_INT_DIVIDE_BY_ZERO &&
        c != EXCEPTION_STACK_OVERFLOW && c != EXCEPTION_PRIV_INSTRUCTION && c != 0xC0000409) return EXCEPTION_CONTINUE_SEARCH;
    if (InterlockedIncrement(&g_nexc) > 20) return EXCEPTION_CONTINUE_SEARCH;
    CONTEXT *x = e->ContextRecord; uintptr_t ip = (uintptr_t)e->ExceptionRecord->ExceptionAddress;
    HMODULE me = 0; GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)veh, &me);
    MEMORY_BASIC_INFORMATION mb; VirtualQuery((void *)ip, &mb, sizeof mb);
    int in_exe = ip >= g_img && ip < g_img + 0x3700000, in_me = mb.AllocationBase == (void *)me;
    L("EXCEPTION %08lx at %p (%s) info %llx %llx thread %lu", c, (void *)ip, in_exe ? "exe" : in_me ? "slots dll" : "other module",
      (unsigned long long)e->ExceptionRecord->ExceptionInformation[0], (unsigned long long)e->ExceptionRecord->ExceptionInformation[1], GetCurrentThreadId());
    L("  rax %llx rbx %llx rcx %llx rdx %llx rsi %llx rdi %llx rbp %llx rsp %llx", x->Rax, x->Rbx, x->Rcx, x->Rdx, x->Rsi, x->Rdi, x->Rbp, x->Rsp);
    L("  r8 %llx r9 %llx r10 %llx r11 %llx r12 %llx r13 %llx r14 %llx r15 %llx", x->R8, x->R9, x->R10, x->R11, x->R12, x->R13, x->R14, x->R15);
    char line[512]; int n = sprintf(line, "  stack exe addrs:"); uint64_t *sp = (uint64_t *)x->Rsp;
    for (int i = 0, k = 0; i < 512 && k < 24; i++) {
        uint64_t v; if (IsBadReadPtr(sp + i, 8)) break; v = sp[i];
        if (v >= g_img + 0x1000 && v < g_img + 0x1e06000) { n += sprintf(line + n, " %llx", (unsigned long long)v); k++; }
    }
    L("%s", line);
    if (g_nexc <= 3) dump_ring("exception");
    return EXCEPTION_CONTINUE_SEARCH;
}

static DWORD WINAPI later_check(LPVOID p) {
    (void)p; Sleep(30000);
    uint8_t b[2]; memcpy(b, (void *)VA(0x140965760), 2);
    L("30 s check: getter patch %s", (b[0] == 0x48 && b[1] == 0xB8) ? "still in place" : "GONE (overwritten?)");
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD why, LPVOID r) {
    (void)r;
    if (why == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(h);
        g_img = (uintptr_t)GetModuleHandleA(NULL);
        char p[MAX_PATH]; GetModuleFileNameA(NULL, p, MAX_PATH); char *s = strrchr(p, '\\'); if (s) strcpy(s + 1, "wwe2k19_slots.log");
        g_log = fopen(p, "w");
        L("wwe2k19 slots proxy, build " __DATE__ " " __TIME__ ", image %p", (void *)g_img);
        g_t0 = GetTickCount(); InitializeCriticalSection(&g_ncs);
        AddVectoredExceptionHandler(1, veh);
        L("file hooks installed: %d of 7", hook_all()); CreateThread(0, 0, rec_thread, 0, 0, 0);
        if (g_img == 0x140000000ULL) { if (apply()) { CreateThread(0, 0, later_check, 0, 0, 0); load_slots(); if (g_nslots) CreateThread(0, 0, slot_thread, 0, 0, 0); } }
        else L("unexpected image base: NOTHING applied");
    }
    if (why == DLL_PROCESS_DETACH && g_log) dump_ring("game exit");
    return TRUE;
}
