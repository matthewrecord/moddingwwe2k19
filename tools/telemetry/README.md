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
