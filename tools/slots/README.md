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

## test7 (2026-11-11 00:00): Universe team-seeder probe
Hooks 0x140FFF130 (type-4 data handler that fills a new Universe's teams from wunistable.pac): logs `SEED call`
with buffer/size/caller and writes `seed_<n>_buf.bin` (the data handed in) and `seed_<n>_blob.bin` (current
Universe blob) next to the exe. Purpose: find the roster-choice flag (default vs MyWWE superstars) at seeding time.

## test9 (2026-11-11 02:00): live team import
`universe_teams.ini` line 1 = roster mode meaning "import MyWWE superstars" (2), line 2 = `live` (or a path to an
LBTS file, test8 behaviour). With `live`, the seeder hook swaps the seeder's return address for a post stub that,
after the default seeding, copies the live MyWWE team table (0x14287C860, rows 0-99 x 0x1B8) over the new
Universe's team records (blob + 0x31BF54). Always current; names inline; no string edits needed.

## test10 (2026-11-11 02:50): memory poke
`slots_poke.request`: lines `<hex VA> <old hex> <new hex>`; writes only when memory equals `old`. First use: clear
stale superstar manager links in the live superstar records (base 0x142e6f9b0 + k*0x1EA9C8, k=0..2; 0xD88 per index;
manager u16 at +0x58; 1024 = none), then the game saves them on the next edit-save. md5 92e6b9d5...

## test11 (2026-11-11 03:15): persistent pokes
`slots_poke_always.txt` (same line format as slots_poke.request) is re-applied every 5 s and never deleted; lines whose
old bytes don't match are silently skipped. Used for the manager table the game rebuilds each launch (0x143700360).

## test12 (2026-11-11 03:55): manager sync (save -> panel table)
Every 5 s after 30 s: reads the 3 manager slots of each MyWWE record (0x142e6f9b0 + idx*0xD88 + 0x58) and copies them
into the panel table rebuilt from profile_pro.pac (0x143700000 + idx*0xD88 + 0x3B8): all records once, then only records
whose saved managers changed. Skips if the panel table header isn't 08 00 88 04 or values look invalid.
md5 aa5b46ef... (includes test11's slots_poke_always.txt; unused).
