# GFX (entrance video) slots and the 50-character-slot goal (started 2026-11-11 04:20)

Matthew 04:18: raise the extra character slots from 6 to 50; start unlocking as many GFX slots as possible.

## Character slots 6 -> 50: status
- Installed: 6 overflow slots (index 509-514, ids 937-942; `slots\installed.json`).
- Tooling limit: `dinput8_slots.c` `g_slots[64]` (relocated tables hold 1024), `slotinstall.py` id pool = 938-949 then
  free ids from 100 up (381 free on 2026-11-10). **50 fits with no DLL change**; above 64 = one constant.
- Supply: 160 pictures-folder wrestlers install as-is (`_moddingwwe2k19_builds/tools/ready_wrestlers.txt`), but by
  name only 15 are not already in the roster (Alexander Hammerstone, Angelico, Damian Sandow, Derek Drexl, Dominik
  Dijakovic, Edge, Ethan Page - Men of the Year, Hana Kimura, Jinny, Pauline, Rosemary, Sasha Banks, Sheamus,
  Stephanie Vacquer, Subculture). 220 folders are not ready (106 without a .pofo etc.).
- Waiting on Matthew: which 44 wrestlers. Known gaps for overflow slots: no 0xD88 superstar record (managers),
  renders/titantrons writer not done.

## GFX slots: first survey (read-only)
Meaning (handoff 010): a GFX slot = a character id's entrance videos (titantron etc.); "Selectable" = pickable in
Create an Entrance. Matthew got 9 selectable with Wrestleminus.
- Videos: `pac\mov\ss_{wall,mini,ramp,apron}\0NNNVV.pac` (+ `mods\CCT\movies\pac\mov\...`). Sets on disk (base + CCT):
  wall 488, mini 518, ramp 478, apron 481 (list: `_moddingwwe2k19_builds\tron_movie_ids_2026-11-11.txt`).
- Menus: `pac\menu\cae_item[_pNN].pac`, `.lsd` lists, 40-byte entries like BGM.lsd: value = id*100 + variant, unlock
  field, name string, DLC flag. The four lists Matthew's files changed most vs unmodded: **SHDC ids 1, 42, 43, 44**
  (unmodded base counts 158/118/119/129 -> 217 each). Presumably wall/mini/ramp/apron (which is which: to confirm).
- **Coverage (list 1, modded): 357 entries, 326 live values; of 488 wall video sets 259 have a menu entry, 229 have
  none.** Same picture for the other three lists (226-241 without entry). These 229 are the unlock target.
- **Index collisions:** the lists form one combined index (base, p10, p20, p30; header = own count, running end).
  The modded base says 217/221 but p10 still says 7/165 and p30 9/174 (stale vanilla totals +n), so p10/p30 entries
  land on base positions 158-173: ~15 entries per list are overwritten and invisible (list 1: 70200..72900 range).
  Same mechanism that hid our first music slots.
- Plan (same recipe as the music slot bank): consistent running totals across the four pacs, then append entries
  for every video set without one at the end of the last list. Open before a build: per-list capacity in the exe,
  whether a registry record (MEMU-like) or the VMUM field-15 flags (TitantronFix) gate the entries, unlock fields
  (write "none"), name strings for new entries.
- Scripts: `tools/gfx/lsd_survey.py` (list sizes), `lsd_diff.py <list id>` (modded vs unmodded), `tron_coverage.py`.
