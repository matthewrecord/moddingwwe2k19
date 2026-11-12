# Arena inventory and re-install plan (survey 2026-11-11 22:30)

Source: `D:\Pictures\WWE 2K19\A - Resources\Back - Arenas and Arena GFX` (1,598 files, about 9.9 GB, 49 entries).
Method: full file listing + the internal name in every .pac header (1,188 pacs) + the readme/notes. Nothing was
opened beyond headers; nothing compared with the creators' original downloads (not available).

## What an arena consists of (from the files and the creators' notes)
- **Parts** in `pac\arena\<part>\ar<part>NNNNN.pac`: entrance (stage), stadium, apron, ringmat, turnbuckle, barricade,
  cornerpost, ceilinglight, spotlight, commentaryst, floor, ibl, rope, fence, ledapron, ledcornerpost ... Part ids
  are their own number space, shared between arenas (e.g. stadium 29 is used by Dynamite 20/22, Revolution, Raw).
- **Screen videos** per arena slot: `pac\mov\ar_wall|ar_mini|ar_ramp|ar_apron\000NNN.pac`, `bg_*`, `transition`,
  `transition_replay`.
- **Menu graphics** per slot in `pac\menu\win\Assets\...`: locator, match_result, nameplate, copyright, ppv_logo,
  replay, match_up (ltag).
- **Four data rows** (one per arena slot): `pac\root\misc04_arena.pac` (slot -> part ids, 24 columns),
  `pac\root\misc01_start.pac` (select number, stage type, filter ...), `pac\prop\propdata\initposition.pac`,
  `pac\misc\parameter\light\prm_ar_lg_color.pac`. Some mods ship whole files (installing one wipes other arenas'
  rows), others ship the values as text/PNG to type in. Matthew's merged tables: `Back - Misc01, Misc 04 and
  InitPosition for modded arenas` (2024-08-21).
- File names on disk are free; the game goes by the name inside the pac: `MD<slot>` (entrance), `AP/BR/TB/RM/ST/CL/FL
  <id>` (parts), `M000<slot>` (videos), an 8-hex hash for menu graphics (one hash per slot and category).

## Inventory (slot = as labelled by folder/file names)
| Arena | Slot | Parts | Videos | Menu GFX | Data rows | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| AEW All Out '21 | 118 | entrance, apron 136, barricade 27, turnbuckle 18 | wall, mini, transition x2 | full set (6) + match_up | none in folder | no stadium/ringmat of its own |
| AEW Dark '21 | 117 | entrance, stadium 47, apron 135, ringmat 17, turnbuckle 17, barricade 26 | wall, mini, transition x2 | full + match_up | none | most complete of the AEW '21 set |
| AEW Double or Nothing '19 | 119 | entrance, apron 137, ringmat 18, turnbuckle 19, barricade 28 | wall, mini, transition x2 (+ loose .bk2) | full + match_up | none | |
| AEW Rampage '21 | 116 | entrance, apron 134, ringmat 16, turnbuckle 16, barricade 25 | wall, mini, transition x2 | full + match_up | none | |
| AEW Road Rager '21 | 120 | entrance, apron 138, turnbuckle 20, barricade 29 | wall, mini, transition x2 | full + match_up | none | |
| AEW Dynamite 20 | 3 | 13 parts | wall, mini | none here (see AEW Dynamite GFX) | whole misc01/misc04/initposition files | whole-file data = overwrites other arenas' rows |
| AEW Dynamite 22 (Titavius) | 17 ("replaces Main Event") | 13 parts | wall, mini, apron | none here | values as .txt (all four rows) | cleanest documented mod |
| AEW Revolution | 10 (Backlash '18) | 6 parts | wall, mini, apron, transition x2 | full + match_up | PNG screenshots | |
| AEW Full Gear | Fastlane slot (14; GFX labelled 7 and 14) | many (70 files) | yes | two sets | PNG + txt | ringmat file 00035 is internally RM36 |
| AEW Grand Slam | "163" | entrance 163, stadium 74, floor 1 | wall, ramp | ppv_logo only | PNG screenshots | **transition file is internally slot 118 (All Out's) and sits in pac\mov, not transition\; no mini/apron video; no locator/nameplate/match_result; stray "109 - NXT TakeOver Philadelphia.pac"** |
| NXT 2.0 | "164" | entrance 164, stadium 55, apron 195, commentary, cornerpost, ibl | all four + transition x2 | set is labelled slot 2 (NXT), ppv_logo 164 | PNG screenshots | **copy of arentrance00164 also in the stadium folder; unpacked work files (0000.oodl ... 0005) left in match_up; menu GFX not re-slotted to 164** |
| All In | 142 | entrance, apron 175, ringmat 33, turnbuckle 30 | **none** | one texture only | txt + PNG | no screen videos, no menu set |
| ROH Death Before Dishonor | 138 | entrance, apron 173, barricade 41, fence 29, turnbuckle 46, cornerposts | **none** | locator, match_result, nameplate | PNG (misc04 only) | no videos, no copyright/ppv_logo/replay |
| Raw Arena / RAW PPV STAGE | 1 | entrance, stadium 29, ibl | wall, mini, ramp, apron | none | whole misc01 + light file | two variants of the same slot (entrance + wall differ) |
| Raw 18 "in for 96 Great Balls of Fire" | 96 | **none** | all four + transition x2 | none | none | videos only |
| Smackdown 21 | 0 | entrance, apron 74, ceilinglight, commentary, ledcornerpost, ibl | all four + bg_wall | none | light file + PNG | |
| Royal Rumble 2020 (Titavius) | 13 | entrance, apron 78, commentary | wall, mini, apron + bg | none | whole misc01/misc04/initposition | whole-file data |
| Royal Rumble Retro | 14 (Fastlane '18) | entrance, stadium 53, apron 152 | wall, mini, transition x2 | full + match_up | PNG | **same slot 14 as Full Gear** |
| Summerslam 09 | 30 | entrance, apron 35 | wall, mini, apron, transition x2 | nameplate + one texture | PNG + note | no locator/match_result |
| Tokyo Dome | 316 (+40, 95) | entrance 316, stadiums 40/41, apron 35, ringmat 6, turnbuckle 4, cornerpost 3 | mini + bg_mini for 5 ids, **no wall** | none (see NJPW Copyright Locator) | whole misc04 | apron 35 collides with Summerslam 09 |
| WrestleMania 27 | 402 (Extreme Rules '14) | 10 parts | wall, transition x2 | full + match_up | PNG | apron 136 collides with All Out '21 |
| WrestleMania 31 | 105 | 8 parts, entrance in 3 variants (day/evening/night) | wall, mini, apron, transition x2 | locator, match_result, nameplate, replay | PNG | **the file in copyright\ is a copy of the match_result file (same size, same internal hash); no ppv_logo** |
| WrestleMania 32 GFX | 115 | none | transition x2 | locator, match_result, nameplate, copyright, replay | readme | graphics only; folder "match result" has a space instead of "_" |
| WrestleMania 34 "moved to slot 134" | files are slot 15 | 11 parts + an old arentrance00130 (2020) | all four + transition x2 | full, all labelled 15 | PNG | **nothing in the folder is slot 134: re-slot not captured here** |
| WrestleMania 35 "moved to slot 130" | 130 | 5 entrance files (33, 45, 46, 130 + a hash-named one), stadiums 31/73 | all four + transition x2 | full for 130 + hash-named originals | whole misc01/misc04 + light | stadium file 00073 is internally ST74 (same id Grand Slam uses) |
| WrestleMania 38 "switched to slot 19" | mixed 19 / 61 | same parts as WM34 (apron 185, stadium 77 ...) entrance 61 | named 61; **wall video named 61 is internally slot 19** | locator + match_result labelled 19, rest labelled 61 | PNG | **half re-slotted: mixture of 19 and 61** |
| Ported Arenas 2K15-2K18 | 104-116 etc. | 333 files | yes | - | whole files + txt | pack, not itemised here |
Graphics-only folders: AEW Dynamite GFX (71 files), AEW PPV GFX (43), AEW Title GFX (8 title intros + id list), AEW
Copyright/Locators (slots 3, 116), NJPW Championship GFX (20 title videos, blue/red), NJPW Copyright Locator (316,
317), ROH Copyright/Locators (17), Matchup Screens (115), WWE Misc GFX (37), Wrestlemania 38 GFX (84), Old WWE 2k GFX
(252), AEW Ceiling Light, AEW Crowd Shirts.

## Collisions between arenas (same part id, different file)
apron 136 (All Out '21 vs WrestleMania 27); apron 35 (Summerslam 09 vs Tokyo Dome); apron 75, barricade 22, ringmat
2, turnbuckle 15 (Dynamite 20 vs Dynamite 22: same slots, pick one); cornerpost 7 (Dynamite 22 vs WrestleMania 35);
cornerpost-cm 2 (Dynamite vs ROH DBD); ledcornerpost 1 (Dynamite 20 vs Smackdown 21); entrance 130 (WM34 folder's
old file vs WM35); entrance 1 + wall video 1 (Raw Arena vs RAW PPV STAGE); slot 14 (Full Gear vs Royal Rumble
Retro). Whichever was installed last wins in the game; the other arena shows the wrong part.

## Installed game for reference
`pac\arena\entrance`: 171 files (vanilla 109), ids 0-164 with gaps, 301+ .

## Plan: overwrite chosen arenas after the clean install
1. **Arena library from the current game (ground truth).** Export every arena slot now in the game into one package:
   read its misc04_arena row to learn which part ids it uses, collect those part files, its videos, its menu GFX,
   and its four data rows; write a manifest (slot, part ids, file hashes). Resources folders fill in only what the
   game lacks.
2. **Decode the four data tables** so rows can be read and written one at a time (never whole-file replacement).
   Field names are in the creators' notes (Dynamite 22 .txt) and WrestleMINUS is open source.
3. **Slot map of the clean install**: after the pack Matthew installs, list which slots/part ids it occupies.
4. **Installer** (`arena install <package> --slot N`): rename the internal ids to the target slot (MD, M000, menu
   hashes: about 40 known slot/hash pairs to derive or look up the rule), give colliding parts a free part id and
   point the misc04 row at it, write the four rows, back up every file touched, regenerate the index, log it.
5. **Test on one arena** (Dynamite 22: fully documented) before doing the rest; then Matthew names arena -> slot
   pairs and they are applied in a batch.
Open: what "the 81 arenas" pack is (asked), menu-hash rule, table formats.

## Update 23:30: fresh downloads read (7 archives in the arenas folder; unpacked in the work container only)
Corrections to the table above come from the creators' own notes and the fresh originals:
- **AEW Grand Slam (MattFick), original**: made for **slot 3**; entrance, stadium 74, floor 1, ceilinglight 73,
  spotlight 91; videos ar_wall, ar_ramp, bg_wall, bg_ramp. **The original has no mini/apron video, no transition and
  no menu graphics**, so those were never "missing". Needs Titavius' AEW apron/barricade/posts/buckles/ropes and the
  AEW Ceiling Light (both in the folder). The slot-118 transition, the stray NXT TakeOver file and the partial move
  to 163 were additions in Matthew's copy. Use the fresh download as the base.
- **WrestleMania 31, original**: the copyright file is a duplicate of the match_result file **in the original too**
  (creator's error), and there is no ppv_logo in the original. Re-download does not fix it. Original part ids:
  apron 29, cornerpost 7, commentary 17; Matthew's copy has them renumbered to 42 / 37 / 77 (avoids the cornerpost 7
  collision), which is the better set.
- **All In**: note says slot 142 "from Abhilash's pack" (the 2K15-2K18 port) with misc01 Bar 7, Live 7. It is a
  re-skin of that pack's slot 142 and takes stage/screens from it. **Complete as designed** if the ported pack is in.
- **ROH Death Before Dishonor**: note says slot 138, misc01 Stage 0 (= no stage, no screens), Bar 7, initposition
  01 01 01. **No videos is by design.** Still lacking: copyright, ppv_logo, replay graphics.
- New material: **ROH '05 V2 (MopeLovesAsians)**: slot 312 (Metropolis Center); entrance, stadium 47, apron 20,
  ringmat 16, turnbuckle 17, barricade 25, cornerpost 23, ppv_logo; misc04 row given in text; no videos. Its part
  ids collide with AEW Dark (stadium 47, turnbuckle 17) and Rampage (ringmat 16, barricade 25): needs renumbering.
  For Death Before Dishonor it can supply an ROH ring mat/stadium and a ppv_logo; the "ROH Copyright, Locators"
  set (slot 17) can be re-slotted for its copyright. **AEW x NJPW Forbidden Door (iTwistedSpartan)**: slot 4
  (Payback); apron 141, ringmat 20, turnbuckle 23, barricade 32, all six videos, six menu graphics, match-up .dds;
  prerequisites 2K15-2K18 port + AEW Dynamite LA Forum '22; includes an entrance *texture* (03E8.pac) to inject
  into that Dynamite stage, not a stage file. **NXT 2.0 original** (slot 2, stadium 3; Matthew's copy = slot 164,
  stadium 55). **NXT White & Gold**: re-skin of NXT 2.0's parts (apron 195, cornerpost 35, commentary 82) + videos
  and two graphics for slot 2; one or the other. **AEW Crowd Shirts**: one crowd file (arcrowd00010).

## 2026-11-12 00:20 Game folders renamed; 81-arena pack slots; replacement plan
- **Folder change (Matthew):** `...\common\WWE 2K19` is now the former unmodded copy with the **Modding Militia
  Arena Essential Pack** ("81 arenas", installed through Genesis 23:41, markers `modding_militia_arena_essential_
  pack.installed`, `unpacked_gfx.installed`; stock exe 41,065,640) = the clean test install. The modded game (ground
  truth, Genesis exe, our builds folder) is now `...\common\WWE 2K19 - modded`. Genesis's game directory setting
  points at `WWE 2K19`, i.e. the clean one.
- **Arena slot table decoded** (`tools/arena/arena_slots.py`): misc01_start.pac, SHDC file 2, 124-byte rows: name
  string id, arena slot, select number, ... 213 rows in the pack install; full list
  `notes/arena_slots_81pack_2026-11-12.tsv`. Select number 24 = not offered in the arena list.
- **Slots of the arenas Matthew does not want** (pack install):
  WrestleMania 13 = 123, WrestleMania 15 = 132, Vengeance '01 = 119, Vengeance '11 = 159, Revenge of the Taker =
  124 (listed as "IN YOUR HOUSE '97"), Fully Loaded '99 = 135, Great Balls of Fire = 96, Over the Edge '98 = 128,
  Over the Limit '11 = 158, Payback = 140 ('13) / 160 ('14) / 4 ('17, not selectable) (which one: to confirm),
  Night of Champions '09 = 143, Battleground '13 = 5 (not selectable; '15 = 141), Unforgiven '98 = 127, Backlash
  '00 = 133, '01 = 138, '03 = 112, Bad Blood '04 = 118, Armageddon '99 = 139, '02 = 117, '03 = 149, Rock Bottom
  '98 = 130. = 20 selectable slots + the Payback choice.
- **Proposed assignment (draft for Matthew):**
  | Downloaded arena | Made for slot | Proposed slot | Re-slot needed |
  | --- | --- | --- | --- |
  | AEW All Out '21 | 118 | 118 (Bad Blood '04) | no |
  | AEW Double or Nothing '19 | 119 | 119 (Vengeance '01) | no |
  | AEW Dark '21 | 117 | 117 (Armageddon '02) | no |
  | ROH Death Before Dishonor | 138 | 138 (Backlash '01) | no |
  | WrestleMania 35 | 130 | 130 (Rock Bottom '98) | no |
  | Raw 18 videos | 96 | 96 (Great Balls of Fire) | no |
  | AEW Rampage '21 | 116 (Survivor Series '02, not on the list) | 139 (Armageddon '99) | yes |
  | AEW Road Rager '21 | 120 (Judgment Day '04, not on the list) | 149 (Armageddon '03) | yes |
  | AEW Grand Slam | 3 (205 Live) | 159 (Vengeance '11) | yes |
  | AEW Revolution | 10 (Backlash '18) | 112 (Backlash '03) | yes |
  | AEW Full Gear | 14 (Fastlane '18) | 133 (Backlash '00) | yes |
  | AEW Dynamite '22 | 17 (Main Event) | 158 (Over the Limit '11) | yes |
  | AEW x NJPW Forbidden Door | 4 (Payback '17) | 140 or 160 (Payback) | yes (4 is not selectable) |
  | NXT 2.0 | 2 (NXT) | 127 (Unforgiven '98) | yes |
  | NXT White & Gold | 2 | 128 (Over the Edge '98) | yes + part renumbering |
  | WrestleMania 34 | 15 (exists in game) | keep vanilla 15, or 123 (WrestleMania 13) | optional |
  | WrestleMania 38 | (re-skin of WM34 parts) | 132 (WrestleMania 15) | yes |
  | Royal Rumble Retro | 14 | 124 (In Your House '97) | yes |
  | Royal Rumble 2020 | 13 (Royal Rumble '18) | 135 (Fully Loaded '99) | yes |
  | Summerslam 09 | 30 | 143 (Night of Champions '09) | yes |
  Not needing a discard slot: All In (re-skin of 142, Money in the Bank '13: overwrites that arena, not on the
  list), ROH '05 (312 Metropolitan Center), Tokyo Dome (316 Japan Dome), WrestleMania 27 (402 Extreme Rules '14),
  WrestleMania 31 (105, already an arena in the pack), Smackdown 21 (0), Raw (1), Dynamite 20 (same slots as
  Dynamite 22: pick one). Left free after this draft: 123 or none, one Payback slot, 5.
- Not yet known: what the pack already puts in each of these slots part-wise (misc04 rows), so part-number
  collisions with the pack are unchecked; "WrestleMania 13 - broken?" not tested.

## 00:25 Rule from Matthew (binding)
**A downloaded arena may only go into a slot Matthew has named as unwanted. The slot a mod was made for is
irrelevant. Nothing else gets replaced** (not Money in the Bank '13 for All In, not the current SmackDown/Raw/NXT/
Main Event/205 Live slots, not 312/316/402/105). Payback = Payback '17 (slot 4). Named slots: 123, 132, 119, 159,
124, 135, 96, 128, 158, 4, 143, 5, 127, 133, 138, 112, 118, 139, 117, 149, 130 = 21. Slots 4 and 5 have select
number 24 (not offered in the arena list) and need their select number set to become usable.
Draft v2: as the table above with Forbidden Door -> 4; Raw Arena + the Raw 18 videos combined in 96; free: 123, 5.
Still without a slot: All In, Smackdown 21, Dynamite 20, ROH '05, Tokyo Dome, WrestleMania 27, WrestleMania 31
(WrestleMania 34 already exists at 15). 21 slots for about 26 arenas: Matthew to name more slots or drop arenas.
- 00:30 More unwanted slots from Matthew: No Way Out '01 = 107, No Mercy '16 = 53, King of the Ring '99 = 134
  (24 named slots). Dynamite 20 + 22 and NXT 2.0 + White & Gold all stay (multiple looks wanted).
  Draft v3 additions: All In -> 123, Smackdown 21 -> 53, Dynamite 20 -> 107, ROH '05 -> 134, Tokyo Dome -> 5.
  Unplaced: WrestleMania 27, WrestleMania 31 (2 slots short).
- WrestleMania 31, pack (slot 105) vs Matthew's download: different files throughout. Stage 10.81 MB vs 10.45 MB;
  wall video 0.92 vs 3.62 MB; mini 1.46 vs 1.19 MB; apron 1.46 vs 0.32 MB; transition 2.05 vs 3.07 MB;
  transition_replay none vs 1.58 MB. Matthew's also has locator/match_result/nameplate/replay graphics. In his copy
  the DAY and EVENING stage files are byte-identical (70c411a3...), NIGHT differs.
