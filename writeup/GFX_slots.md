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

## Redirect (Matthew 07:57): groundwork only, CCT does the installing
- Not asking us to install characters or graphics. Goal: **open empty slots that CCT can then fill** (characters and
  graphics). Character side: **64 overflow slots** (the DLL's current limit) is the target.
- Design problem to solve for characters: CCT injects pofo/moveset live at `pofoStartAddress + slotNumber*484`
  (data.xml: superstars 0x142840600). For slotNumber >= 509 that address is past the 509-entry array (0x14287C854 =
  the MyWWE team table at 0x14287C860), while our overflow pofos live in the DLL's own buffer. So adding rows to
  CCT's data.xml alone would corrupt the team table. Options: (a) DLL-side bridge (CCT writes somewhere safe, DLL
  copies into the overflow slot; needs a CCT list with its own start address, like its `caws` list has); (b) a drop
  folder the DLL/installer reads (CCT export .pofo/.moveset -> `slots\`); (c) patch CCT's address math. Needs CCT's
  config/binary in hand (laptop link) to choose. File side (models by id, Chunk0.def) already matches CCT's layout.
- GFX capacity, what is known: 229 video sets per screen already on disk without a menu entry + ~15 hidden by the
  index collision. Ids in video names go beyond 999 (1001-1085, 1501, 2100, 2999 exist), so the id space is not the
  limit. Other lists in the same menu file hold 1566 entries, and the music list runs at 515 in game. The exe's
  per-list cap for lists 1/42/43/44 is NOT measured yet (exe not in the repo; needs the laptop).
- Note: `tools/bootstrap_repo.sh` (named in the project instructions) does not exist in the repo.

## 08:30 List loader read in the exe: no fixed list size (CORRECTS the "index collisions" item above)
- Loader/manager object (global 0x1425e35e0; ctor 0x1401cfa10 / 0x140c1f4a0; `/ENEX/LSD` base, `/ENEX%d/LSD` per patch
  level). Per package it keeps, for each of 0x2E (46) list ids, a pointer to the entries **inside the loaded file**
  (base: obj+0x1A0+8*id, count u16 obj+0x310+2*id; patches: 0x340-byte blocks at [obj+0x370], ptr +0x170, count
  +0x2E0). Parser 0x140c1f7b0: count = first u16 of the .lsd; **the second u16 ("running end") is skipped, never
  stored**; entries = 40 bytes; only special case: list id 2 (BGM) drops an entry whose value is 0xFE.
- Count getter 0x140c1fca0 = base count + every patch's count (u16 sum). Entry getter 0x140c1fd60(list, i): i < base
  count -> base[i], else walk the patches subtracting counts. Find-by-value 0x140c1fb70 / 0x140c1fe30 scan base then
  patches. So the lists are **plain concatenation by own counts**: nothing is overwritten, the stale running totals
  in Matthew's files are harmless, and all 357 list-1 entries are reachable. (The earlier music finding "base append
  overwritten by p10" was explained later by the MEMU record + unlock fields, consistent with this.)
- **Structural ceiling per list: 65,535 entries in total (u16), no fixed buffer.** Not yet measured: limits in the
  Create an Entrance menu screen code itself (music list id 2 runs at 515 entries in game; list 1 at 357).
- Entry value = id*100 + variant; VMUM table (assetconv_p30, 1147 rows, ids 0-999 + a few 2000s) fields 9-14 hold the
  same id*100 values per row (per-screen video refs; which field = which screen open), field 15 flag bytes.
  Field 15 is NOT the menu gate: of Matthew's 9 "Selectable" slots 3 have flags 0 and 1 has no row.
  Of the 229 wall sets without a menu entry, 194 have VMUM flags 0.
- Id space: wall video sets cover 418-ish distinct ids; see numbers in the chat summary / rerun tron_coverage.
- CCT route for characters, leading candidate: CCT's addresses are plain config in `data.xml` (pofoStartAddress +
  slotNumber*484, movesetStartAddress + slotNumber*3464, same for universe1-3). A second CCT profile ("CCT - Extra
  Slots") whose data.xml lists only the 64 new slots and points at a fixed-address buffer the DLL allocates would let
  CCT inject into overflow slots unpatched; the DLL then copies changes into its overflow arrays and writes them back
  to `slots\*.pofo/.moveset` so they survive a restart. To verify next in CCT's code (it is the staged
  Custom_Character_Tools.exe): what it reads before writing, universe copies, file copies by slotId.
