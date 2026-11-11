# Character-slot expansion proxy (`dinput8.dll`)

Stage 1 of the 509-cap work (`notes/characters/expand_509_scope_2026-11-10.md`). A stand-in `dinput8.dll` next to
`WWE2K19_x64.exe` patches the game **in memory** at load; the .exe is never modified. Every site's original bytes are
checked first; on any mismatch nothing is applied. Log: `wwe2k19_slots.log` next to the exe.
Remove: rename/delete `dinput8.dll` in the game folder.

Build: `apt-get install gcc-mingw-w64-x86-64`, then
`x86_64-w64-mingw32-gcc -O2 -shared -masm=intel -o dinput8.dll dinput8_slots.c -static-libgcc`
(`-DSLOT_CAP=520` for later stages).

## Stages
| Stage | What | Expected in game |
| --- | --- | --- |
| test0 (now) | Relocates the 3 static 509-entry tables (main movesets, 40-byte per-slot table, index->id) to 1024-entry buffers; detours the pofo getter's main path (idx >= 509 -> overflow array). No bound raised. | Identical to vanilla: boots, roster, a match with movesets intact. Log says `applied` and `30 s check: still in place`. |
| test1 | Raise loader/consumer/getter caps to N; one test row (dat/mvs/pro) at index 509, cloned wrestler, fresh id. | Boot; clone in select screen?; can wrestle. |
| test1 (now) | SLOT_CAP 510; lookup bounds raised in the pofo-by-id getter 0x1409656bb, moveset-by-id getter 0x1409657ef, index->id reader 0x1404c98e9. Thread: once the game's id map exists, copies `slots\IIII_DDDD.pofo/.moveset` into the overflow pofo / relocated moveset entry and registers id<->index (re-done if the map is rebuilt). The profile tables are NOT used for overflow slots. | Test Wrestler (index 509, id 937, Alex Shelley clone) in the select screen; can wrestle. |

`tools/build/charslot.py` makes the slot files plus the name string (SuperString English table) and the Chunk0.def
lines / CCT asset copies (models ch<id>xx, trons and renders 0<id>00) for a new id from a CCT export in the pictures folder.

## Diagnostics (from test1c, always on)
- **Crash log**: a vectored exception handler writes access violations / illegal instructions / stack overflows /
  fast-fail (0xC0000409) to `wwe2k19_slots.log`: exception address (exe/dll/other), registers, exe return addresses on
  the stack (max 20 entries). The game also writes its own minidumps to `CrashDump\` (`tools/exe/crashdump.py`).
- **File-activity recorder**: hooks the exe's kernel32 imports (CreateFileW/A, ReadFile, ReadFileEx, SetFilePointer,
  CloseHandle, CreateFileMappingW) by IAT patch (re-checked every 2 s in case the Steam stub rewrites the IAT).
  Keeps the last 1024 events in memory; writes them to the log on a crash (first 3 exceptions), on **F12**, and at
  game exit. Failed opens (file not found etc.) are logged immediately. Not seen: file I/O done through the C
  runtime (fopen) or by other DLLs (e.g. Wwise, Bink) with their own imports.

## Multi-slot (test2, 2026-11-10 19:20)
The proxy loads every `slots\IIII_DDDD_SSSS.pofo/.moveset`, sets the lookup cap to (highest index + 1, min 510) and
traces all overflow slots. Install wrestlers with `tools/build/slotinstall.py` (see its docstring): spec file of
pictures-folder names -> next free slot (510 = index 509, ...) and id (937-999), models renamed internally,
Chunk0.def sorted insert, name string 39370 + (id - 937). Renders/Titantrons: not yet.

## test3 (2026-11-10 21:30): memory reads for Universe work
- `slots_mem.request` in the game folder: lines `<hex VA> <hex len> [deref]` -> `slots_mem_<sec>_<n>.bin` (raw bytes,
  ReadProcessMemory, so bad addresses only log). `deref` reads a pointer at VA first.
- `slots_fulldump.request` -> `slots_full_<sec>.dmp` (MiniDumpWithFullMemory; several GB).

## test4 (2026-11-10 23:15): Universe auto-capture
`universe_capture.ini` next to the exe: line 1 SAVEDATA path, line 2 archive folder, line 3 optional command.
At game start and whenever the save's write time changes (checked every 5 s, stable 5 s), the DLL decodes the save in
memory and writes the UNVSBODY0001 chunk (~30 KB) to `<archive>\unvs_<date_time>.bin`; then runs the command
hidden. Read-only on the save. `tools/universe/tracker.py --archive <folder>` turns captures into history.

## test6 (2026-11-10 23:40): find + hardware watchpoints
- `slots_find.request` (one line of text) -> `FIND hit <addr>` lines for every occurrence in committed memory (max 64).
- `slots_watch.request`: up to 4 lines `<hex addr> <1|2|4|8> <w|rw> <name>` -> DR0-DR3 on all threads (re-applied
  every 2 s); each new instruction that hits is logged once as `WATCH <name> rip=... stack: <exe return addresses>`.
