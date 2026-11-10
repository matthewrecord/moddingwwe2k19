# Handoff 009: slot bank installed (589 slots, 200 in menu) (2026-11-10)

## Decision (Matthew, 2026-11-10 12:29-12:37)
Do not rely on a build script for routine work. Create the slots ONCE; Matthew fills/swaps songs with Sound Editor and
assigns with Data Editor (community workflow). ~150 slots needed now -> 200 in the menu; ready-made drop-ins to grow the
menu in 100s, in `A - Resources`. Names: placeholders "Custom NNN" now; Claude renames to wrestler names later
(Wrestleminus is too shaky). Background: Matthew has >100 wrestlers whose music is built into their graphics (needs help
later), plus ~12 using soundtrack songs.

## Design
- ALL free ids get a slot now (audio, VMUM row, strings, MEMU record, Data Editor + Sound Editor names); only the menu
  entry (BGM.lsd in `pac/menu/cae_item_p30.pac`) is limited to the first 200. Growing the menu = swapping that one small
  file, which Sound Editor never touches, so songs already injected into patch_30.pck are safe. (Pre-built patch_30.pck
  increments would have erased injected songs; rejected.)
- Free ids now also exclude ids the Data Editor list names (e.g. 179000 Mark Henry): 589 free.
- Placeholder audio: 413-byte Wwise Vorbis clip (0.05 s, mono 48 kHz) from comm_menu0_m.pck stream 79095899,
  `_moddingwwe2k19_builds/placeholder_silent_413b.wem`. Prefetch size clamped to file size (formula gave 4152 > 413).
- Size: patch_30.pck 26.9 MB with the bank (original 30.4 MB; our tight repack, same as every in-game-tested build).
  AKPK offsets are u32 (block size 1) -> ~4 GB ceiling; game_mode_m.pck is 2.48 GB and loads. 589 full songs at ~4-5 MB
  would approach 3 GB: if Matthew ever fills most slots, consider a second package (patch_40 route, untested).
- Why music is split over music_0..3/misc/show/patch_NN: not established. Likely packaging/patching convenience (DLC as
  patch levels so updates do not rewrite large files); no evidence of a per-file limit at these sizes.

## Installed on the laptop (game closed; uninstall of v14 then install)
Build `_moddingwwe2k19_builds/slotbank_v16` (`--fill "Custom %03d,<placeholder>,200" --menu-steps 300,400,500,600`),
installed with `--tools`. Michael Cole's string 3150 restored by the v14 uninstall. All 7 targets MODDED, backups
present (`.orig_musicslot`).
Drop-ins: `D:\Pictures\WWE 2K19\A - Resources\Extra Music Slots (moddingwwe2k19)\` : README.txt, slots.csv,
cae_item_p30 - menu 200/300/400/500/589 slots.pac, ORIGINAL. MD5 menu 200 62f61519…, 300 f1a1c37a…, 400 5897d261…,
500 c94ba34d…, 589 dd10fbdf…, original 8b77395c….
Caveat: `install.py uninstall` restores the original patch_30.pck, which would also remove songs injected later with
Sound Editor. Do not uninstall once Matthew has filled slots without exporting his songs first.

## Pending checks (Matthew)
1. Boot; CAE > Entrance Music lists Custom 001-200 (silent).
2. **Key test:** Sound Editor -> patch_30.pck -> replace "THEME Custom 001" with a real song -> plays fully in game.
   (Our placeholder prefetch is 413 bytes; whether Sound Editor updates the bank's prefetch field is unknown.)
3. Data Editor dropdown shows "Custom 001" etc.; a wrestler assigned 109000 plays it.
4. CCT dropdown (side check).

## Next
Renaming tool path (strings 13000+id/3000+id + Data Editor + Sound Editor names) for wrestler names; music-in-graphics
help; write-up (Music_map.md, Status.md).

## Result 12:56 (Matthew, screenshots)
Sound Editor sees all 599 streams of patch_30.pck (10 DLC + 589 slots, 413 bytes each) and, with its database set to
**WWE 2K19** (it was on "WWE 2K23"), shows the names: DLC themes and "THEME Custom 001..589", IDs match slots.csv.
Check 3 (Sound Editor names) passed. Still pending: 1 (CAE menu), 2 (Sound Editor replace plays in game), 3 (Data Editor).

## Result 13:03 (Matthew): IT WORKS
A real song injected with Sound Editor into "THEME Custom 001" plays in game. The routine is validated: slots created
once by us; Matthew fills them with Sound Editor (no prefetch fix needed) and assigns with Data Editor.
Remaining optional: Data Editor dropdown names, CCT dropdown, rename slots to wrestler names, music-in-graphics help,
write-up (Music_map.md, Status.md).

## 13:05-13:10 rename to game ids (Matthew: names must match across menu, Data Editor, Sound Editor)
Slots renamed "Custom <id>" (Custom 109 = Data Editor 109000 = Sound Editor "THEME Custom 109") with new
`tools/build/rename.py --pattern "Custom %03d"`. Changed: string_win.pac 4677ddb2 -> 049d9cb2, Data Editor list
bd8d7036 -> 2d4b8bf1, Sound Editor custom_data.xml 37369033 -> 1128d3da (backups `.bak_rename_20261110-180646`).
patch_30.pck untouched (MD5 e9812399… before and after; it now holds Matthew's injected song, so it no longer matches
the build output). slots.csv (Resources + build folder) and README updated. Menu drop-ins need no change (names come
from strings). Note: install.py status will now report str/de/se/pck as OTHER; expected. Use rename.py for future
wrestler names.
