# In-game telemetry (proxy dinput8.dll)

`dinput8_trace.c` builds a stand-in `dinput8.dll`. Copied next to `WWE2K19_x64.exe`, it loads with the game (no
debugger), forwards `DirectInput8Create` to the real System32 DLL, and writes `wwe2k19_trace.log` next to the exe.
Remove it by deleting `dinput8.dll` from the game folder (the exe is never modified).

Build (cloud container): `apt-get install mingw-w64`, then
`x86_64-w64-mingw32-gcc -O2 -shared -o dinput8.dll dinput8_trace.c dinput8.def -static-libgcc`.

v1: scans memory every 1-2 s for the test BGM entries (`id*1000`, `0xFFFF0000|id`), logs every copy that appears or
disappears with context, then arms in-process hardware watchpoints (DR0-DR3 set on every thread, vectored exception
handler) on the raw 109 entry (value and label), the raw 500 and raw 807 values, and logs each new reading/writing
instruction with candidate return addresses (offsets from the exe base).

## filetrace (2026-11-14): `dinput8_filetrace.c`
Same proxy approach, for load hangs. Hooks the exe's imports CreateFileA/W, ReadFile, ReadFileEx, CloseHandle; logs opens/reads
of `.pac/.def/.arc` and anything with `prop`/`belt` in the path (create `TRACE_ALL` next to the exe for every file), first-chance
exceptions (first 200), and when there's no file I/O for 8 s samples every thread's RIP 5x with exe-relative return addresses.
Log `wwe2k19_filetrace_<tick>.log` next to the exe.
Build: `apt-get install gcc-mingw-w64-x86-64`; `x86_64-w64-mingw32-gcc -O2 -shared -o dinput8.dll dinput8_filetrace.c dinput8.def -static-libgcc`.
