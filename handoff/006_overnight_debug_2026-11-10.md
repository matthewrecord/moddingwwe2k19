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
