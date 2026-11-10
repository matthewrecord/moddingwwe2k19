# Character-slot expansion proxy (`dinput8.dll`)

Stage 1 of the 509-cap work (`notes/characters/expand_509_scope_2026-11-10.md`). A stand-in `dinput8.dll` next to
`WWE2K19_x64.exe` patches the game **in memory** at load; the .exe is never modified. Every site's original bytes are
checked first; on any mismatch nothing is applied. Log: `wwe2k19_slots.log` next to the exe.
Remove: rename/delete `dinput8.dll` in the game folder.

Build: `apt-get install gcc-mingw-w64-x86-64`, then
`x86_64-w64-mingw32-gcc -O2 -shared -masm=intel -o dinput8.dll dinput8_slots.c dinput8.def -static-libgcc`
(`-DSLOT_CAP=520` for later stages).

## Stages
| Stage | What | Expected in game |
| --- | --- | --- |
| test0 (now) | Relocates the 3 static 509-entry tables (main movesets, 40-byte per-slot table, index->id) to 1024-entry buffers; detours the pofo getter's main path (idx >= 509 -> overflow array). No bound raised. | Identical to vanilla: boots, roster, a match with movesets intact. Log says `applied` and `30 s check: still in place`. |
| test1 | Raise loader/consumer/getter caps to N; one test row (dat/mvs/pro) at index 509, cloned wrestler, fresh id. | Boot; clone in select screen?; can wrestle. |
