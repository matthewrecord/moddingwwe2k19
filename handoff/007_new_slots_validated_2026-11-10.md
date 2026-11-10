# Handoff 007: new music slots VALIDATED in game (2026-11-10)

Read `STATE.md` first. The full blow-by-blow is `handoff/006_overnight_debug_2026-11-10.md`; this file is the summary.

## Result

Brand-new music slots work in WWE 2K19. Build `multi_v14_nounlock` added 8 test slots (IDs 109, 150, 200, 500, 650,
807, 850, 999, all using the Alex Shelley `.wem`, labels "TEST <id>"). In Create an Entrance > Entrance Music,
**all 8 appear, each plays its own audio, and they save and reload** (Matthew, 2026-11-10 12:07 ET, screenshot).
CCT has NOT been tested yet; that is the remaining part of the project's validation goal.

## The recipe (all five layers are required; each fails silently on its own)

`tools/build/musicslot.py` (repeat `--id/--name` for several slots in one build) writes:

1. **Audio**: stream + Event/Play/RanSeq/Sound chain in the DLC bank 1755985664 inside `sound/patch_30.pck`.
2. **Music table row**: `mods/TitantronFix/pac/audio/assetconv_p30.pac` (VMUM). Empty row for the ID gets key
   `id*100000`, unique f0/f1, and is moved into the sorted tail (the game binary-searches field 4).
3. **Names**: strings 13000+id (name) and 3000+id (upper-case menu label) in
   `mods/SuperString/pac/string/win/string_win.pac` (file index 0 = English).
4. **Menu entry**: BGM.lsd (SHDC file id 2) in `pac/menu/cae_item_p30.pac`, appended at the END of the p30 list
   (lists form one combined index base/p10/p20/p30; a base append is overwritten by p10).
5. **Unlock fields = none (the gate found today)**: BGM entry u16 fields at +4, +6, +8, +0xA, +0xC are
   unlock-requirement IDs (-1 = none). The menu builder (0x140179a80) calls 0x140c1eb50 / 0x140c1ec80, which check each
   via 0x1404c9460 / 0x1404bef50 and hide the entry if the unlockable is not owned. We used to write `0xFFFF0000|id`
   there (copying vanilla), i.e. "requires unlockable #id", so IDs matching an unowned unlockable were hidden
   (109/150/200/650/850) and others shown (500/807/999). Now `NO_UNLOCK = True` writes `0xFFFFFFFF`.

Plus a MEMU music-info record in `pac/root/misc05_save_p30.pac` (SHDC file 6), `DLC_STYLE = False` (v9's DLC flags
coincided with a hang; not needed).

Install with `tools/build/install.py install|uninstall|status --build <dir> --game "<install>"` (MD5 gates,
`.orig_musicslot` backups). Build from the originals: copy the five `.orig_musicslot` backups into a temp tree and
pass that as `--game` (see handoff 006 for the exact commands).

## Current state of Matthew's laptop

- Game: `D:\SteamLibrary\steamapps\common\WWE 2K19` (laptop VM path `$HOME/mnt/common/WWE 2K19`).
  **Installed: `multi_v14_nounlock`** (8 TEST slots). Note ID 150's string slot was Michael Cole's; the uninstall restores it.
- Builds: `D:\Pictures\WWE 2K19\_moddingwwe2k19_builds\` (`$HOME/mnt/WWE 2K19/_moddingwwe2k19_builds`).
- Telemetry DLL disabled (renamed `dinput8.dll.telemetry_disabled`, plus an older `dinput8.dll.v5_disabled`). Matthew
  turned Windows Defender off for testing: **remind him to turn it back on.**
- Laptop repo clone `~/repo` is on branch `claude/dlcstyle`, not main; `git pull` there does not get main. Use
  `git fetch origin main` + `git show origin/main:<file>` (as handoff 006 does), or fix the checkout.

## Tools added this session

- `tools/telemetry/dinput8_trace.c`: proxy `dinput8.dll` (mingw cross-build). Memory scanner + in-process hardware
  watchpoints + lock-free logging to `wwe2k19_trace_<tick>.log` in the game folder. v5c (watch long-lived strings)
  is what found the gate. Lessons: watch long-lived data (string table), not short-lived buffers (freed and reused);
  never suspend threads while holding a lock the VEH needs; the game ignores synthetic input (Matthew drives menus);
  a stuck WWE process blocks new launches (reboot).

## Next steps (triage order)

1. **CCT**: confirm CCT lists and assigns the new slots (project validation goal). Decompile/inspect if it does not.
2. **Productise**: real song names, several different `.wem` files per build, choose free IDs automatically (skip
   real rows such as 700), clean uninstall of the TEST build, then install Matthew's real songs.
3. Write-up: fold the five-layer recipe and the unlock gate into `writeup/Music_map.md` and `writeup/Status.md`.
4. Optional: identify what unlockable #109 etc. are (not needed for the fix).

## Working-style notes from Matthew (binding)

- After every test run, say plainly what went right and what went wrong, and why another run is needed.
- Don't ask him to repeat a run without explaining what changed; repeated asks with little explanation read as
  spinning wheels.
