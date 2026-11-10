# Handoff 006: overnight autonomous debugging (2026-11-10, Matthew asleep)

Matthew granted blanket permission (00:21-00:24) to use his computer in game and run debugging without asking.
Granted apps (computer use): Steam, steamwebhelper, WWE2K19_x64.exe, File Explorer (click tier), x64dbg
(`D:\Pictures\WWE 2K19\_tools\x64dbg\release\x64\x64dbg.exe`, official 2026.05.27 snapshot), clipboard, system keys.

## State at start
- Installed: slot109 **v9** (DLC-style flags; untested). Build dirs in `D:\Pictures\WWE 2K19\_moddingwwe2k19_builds\`.
  Undo with tools/build/install.py uninstall --build <v9 dir>.
- Open question: the Create-an-Entrance music menu rejects value 109000 (v7 proof). Gate is in code.

## Plan
1. Attach x64dbg to the game, open Entrance Music, set a hardware read breakpoint on our appended BGM entry's value
   (109000 = 0x1A9C8) in the loaded list memory -> the first reader that rejects it is the gate function.
2. Read the gate; implement what it needs in data if possible; build, install, verify in game myself.
Progress lines are appended below as they happen.

## Log
- 05:30Z x64dbg attached to WWE2K19_x64.exe (PID 18212). `findallmem` for our BGM entry bytes (C8A90100 6D00FFFF)
  found 3 copies in memory: 0x515C42C, 0x244A69CC, 0x3FE3E4AC (file buffer / loaded list / working copy, not yet
  identified). Hardware read breakpoints set on all three. Software TLS breakpoints cleared (`bc`), game resumed.
- 05:38Z Game is stuck at Create an Entrance > Superstar > (first wrestler) > "Easy Creation": no response to keys or
  clicks since ~05:19Z (i.e. before the debugger was attached). Installed build is v9 (DLC-style flags, never tested
  by Matthew). Suspect: v9 hangs CAE loading, or the game is waiting on something else. Checking main thread state.

- 2026-11-10 ~06:00Z: x64dbg window found empty (no debuggee: registers all zero), so it is NOT attached and did not cause the hang. Game is still frozen on Create an Entrance > Superstar > Easy Creation (renders, ignores input). Paused overnight GUI debugging here: screen-driven x64dbg is too slow to be productive.
  Next agent: (1) close the game, `install.py uninstall`, install v8 (no DLC flags) to rule out v9 as the hang cause; (2) prefer scripted debugging (x64dbg script file or a small Python/ptrace-style tracer via `dbgcmd`) over clicking: attach, `bphws` on the three BGM entry copies, open Entrance Music, dump the call stack to a log file, then read the log.
- 2026-11-10 09:50Z: game closed by Matthew. v9 uninstalled, v8 installed (status: all 5 MODDED, backups present). Game path from the laptop VM: $HOME/mnt/common/WWE 2K19; builds: $HOME/mnt/WWE 2K19/_moddingwwe2k19_builds. Next: launch, check whether the Easy Creation hang recurs (if not, v9's DLC flags caused it), then scripted x64dbg trace of the 109000 reject.
