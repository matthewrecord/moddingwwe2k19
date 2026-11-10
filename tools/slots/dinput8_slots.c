/* WWE 2K19 character-slot expansion proxy (dinput8.dll). Drop next to WWE2K19_x64.exe; delete/rename to remove.
 * The .exe on disk is never modified: patches are applied in memory from DllMain, before the game's own code runs.
 * Every patch first checks the exact original bytes; if ANY site differs (other exe build), NOTHING is applied.
 * Log: wwe2k19_slots.log next to the exe.
 *
 * Stage "test0" (this build, SLOT_CAP = 509): behaviour must be identical to vanilla. It proves the mechanism:
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
#define SLOT_CAP   509           /* raised bound checks (test0: unchanged) */
#endif

static FILE *g_log; static HMODULE g_real; static uintptr_t g_img;
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
    /* index->id init loop: 0x1f*16 + tail 13 ints; cover MAX_SLOTS (63*16 + 13 = 1021 <= 1024+0x1000/4) */
    uint8_t movecx[5] = {0xB9, 0x3F, 0, 0, 0}; put(0x14190fc8a, movecx, 5);
    /* pofo getter main path -> stub (mov rax, imm64; jmp rax; 2 x int3) */
    uint8_t j[14] = {0x48, 0xB8}; uint64_t s = (uint64_t)stub_pofo_main; memcpy(j + 2, &s, 8);
    j[10] = 0xFF; j[11] = 0xE0; j[12] = 0xCC; j[13] = 0xCC; put(0x140965760, j, 14);
    L("applied: %d relocs, getter detour -> %p, overflow pofo %p, SLOT_CAP %d", NRELOC, (void *)s, (void *)g_ovf_pofo, SLOT_CAP);
    return 1;
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
        if (g_img == 0x140000000ULL) { if (apply()) CreateThread(0, 0, later_check, 0, 0, 0); }
        else L("unexpected image base: NOTHING applied");
    }
    return TRUE;
}
