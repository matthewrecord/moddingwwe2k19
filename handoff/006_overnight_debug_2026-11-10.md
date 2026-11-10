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
- 2026-11-10 09:54Z: blocked. Computer-use app approval expired after 30 min idle and needs Matthew to re-approve, so the game can't be launched unattended. v8 is still installed and untested. Resume: re-request access (Steam, steamwebhelper, Wwe2k19_x64, X64dbg, Explorer), then run the v8 hang check and the scripted trace.
- 2026-11-10 12:50Z: STATIC LEAD. WWE2K19_x64.exe file offset 0x1fc1956 holds a u16 ID list: 200-203, 210-213, 220-223, 230-233, 240-243, 250-253, 300-302, 800-809 (preceded by small struct-like values from 0x1fc18dc). The DLC used 800-806, so 807-809 look like reserved music slots, and an exe-side whitelist would explain why 109000 is rejected while 100000 shows. xref.py finds no direct RIP-relative reference (likely an indexed table); still to trace.
  Built and INSTALLED v10 = slot807_v10: same as v8 (DLC_STYLE False) but music ID 807. A DLC-flag variant is at slot807_v10_dlcflags (not installed). Test: CAE > Entrance Music, look for "Alex Shelley (Custom 807)".
- 2026-11-10 12:43 ET: **BREAKTHROUGH.** Matthew confirms "Alex Shelley (Custom 807)" APPEARS in CAE Entrance Music with v10. The gate is the exe's hard-coded ID list (u16 at file offset 0x1fc1956): only listed IDs show in the menu. Usable new IDs: 807, 808, 809 (unused by the DLC). Still to confirm: it plays the Alex Shelley audio, and it survives save/reload. Next: patch the exe list (or find its consumer) to allow more than 3 new slots.
- 2026-11-10 07:44 ET: Matthew confirms ID 807 PLAYS the Alex Shelley theme. Persistence across save/reload: Matthew testing. Slot pipeline validated end to end in game (CCT still later). v10 = known-good recipe: musicslot.py with DLC_STYLE=False and an ID from the exe list.
- 2026-11-10 08:00 ET: exe list context (file offsets): u16 list at 0x1fc1952 = 0-terminated {200-203,210-213,220-223,230-233,240-243,250-253,300-302,800-809}, followed by a second 0-terminated list 9000-9020 at 0x1fc19a2. No direct RIP-relative xref found (accessed indirectly; consumer still unknown). The list is NOT a simple whitelist (vanilla ID 100 is not on it but shows), so working model: menu shows IDs from base data OR this list.
  Cross-check against the vanilla VMUM keys: listed IDs with NO existing music row = 200-203, 211, 213, 221-223, 230, 231, 240, 242, 243, 250-253, 300-302, 807-809 (25 IDs). If the model holds, these are 25 free slots needing no exe patch. Next test: build one of them (e.g. 200) to confirm. Not swapped yet: Matthew is testing 807 save persistence.
- 2026-11-10 08:30 ET: FOUND the list's consumer: 0x140f62bf0 (file 0xf6231f/0xf62337). It reads `movzx r15d, word [imagebase + idx*2 + 0x1fc2b50]` (idx = low byte of a packed u16, <0x26) and `word [imagebase + idx*2 + 0x1fc2ba0]` (idx = bits 8-13, <0x16). So the list maps a compact index to a music ID (likely show/match music); it is NOT a menu whitelist. CORRECTION: the 807 success is not yet explained by the list. Hypotheses: (a) the CAE menu filters by ID range (>=800 shows, or 100-1xx hides); (b) something about row/ID 109 specifically.
  Discriminating test builds (DLC_STYLE False, not installed): slot850_v11 (ID 850, NOT on the list) and slot200_v11 (ID 200, on the list). If 850 shows, the list is irrelevant and any ID >=8xx likely works.
  NOTE: the laptop clone ~/repo is on branch claude/dlcstyle, not main; `git pull` there does not pick up main. Built via a temp copy with DLC_STYLE=False.
- 2026-11-10 08:45 ET: multi-slot build multi_v12 (built from the .orig_musicslot originals; input MD5s verified). 8 slots, all the Alex Shelley wem, menu labels "TEST <id>": 807 (positive control), 109 (negative control), 850 (>=800, off list), 200 (on list, <800), 150 (1xx, not 109), 500, 650 (mid, off list), 999 (top). (700 is a real song, so it was replaced by 650.) Read-out: which TEST labels appear in CAE Entrance Music. Install: uninstall slot807_v10, then install multi_v12 (game must be closed).
