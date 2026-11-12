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

## 00:30 Assignment v4 (Matthew-approved slots; pairings are Claude's draft unless Matthew changes them)
Named unwanted slots (27): 123, 132, 119, 159, 124, 135, 96, 128, 158, 4, 143, 5, 127, 133, 138, 112, 118, 139, 117,
149, 130, 107, 53, 134, 125 (D-Generation X), 140 (Payback '13), 160 (Payback '14).
| Arena | Slot | Was |
| --- | --- | --- |
| AEW All Out '21 | 118 | Bad Blood '04 |
| AEW Double or Nothing '19 | 119 | Vengeance '01 |
| AEW Dark '21 | 117 | Armageddon '02 |
| AEW Rampage '21 | 139 | Armageddon '99 |
| AEW Road Rager '21 | 149 | Armageddon '03 |
| AEW Grand Slam | 159 | Vengeance '11 |
| AEW Revolution | 112 | Backlash '03 |
| AEW Full Gear | 133 | Backlash '00 |
| AEW Dynamite '22 | 158 | Over the Limit '11 |
| AEW Dynamite '20 | 107 | No Way Out '01 |
| AEW x NJPW Forbidden Door | 4 | Payback '17 |
| All In | 123 | WrestleMania 13 |
| ROH Death Before Dishonor | 138 | Backlash '01 |
| ROH '05 | 134 | King of the Ring '99 |
| NXT 2.0 | 127 | Unforgiven '98 |
| NXT White & Gold | 128 | Over the Edge '98 |
| Raw (arena + Raw 18 videos) | 96 | Great Balls of Fire |
| Smackdown 21 | 53 | No Mercy '16 |
| Tokyo Dome | 5 | Battleground '13 |
| WrestleMania 27 | 125 | D-Generation X |
| WrestleMania 31 | 140 | Payback '13 |
| WrestleMania 35 | 130 | Rock Bottom '98 |
| WrestleMania 38 | 132 | WrestleMania 15 |
| Royal Rumble Retro | 124 | In Your House '97 (Revenge of the Taker) |
| Royal Rumble 2020 | 135 | Fully Loaded '99 |
| Summerslam 09 | 143 | Night of Champions '09 |
Spare: 160 (Payback '14).
**Reserve list (Matthew agrees with the reasoning; use when more slots are needed, in this order):** Battleground
'15 (141); two of Survivor Series '11/'12/'13 (153, 154, 145; keep one, which one to ask); Hell in a Cell '10/'11
(152, 144); TLC '13 (146); Elimination Chamber '13 (147); Extreme Rules '11 (156); St. Valentine's Day Massacre
(131); Judgment Day '04 (120). Keep: Capitol Punishment '11 (41), Money in the Bank '11 (148), Raw '11 (150),
Smackdown '08 (157).

## 00:50 Groundwork for the installer (read-only work on the clean install)
- **misc04_arena.pac decoded** (`tools/arena/misc04_arena.py`): SHDC file 920 is a small archive (u32 count, 16-byte
  header, 32-byte entries: 16-char name, type, size, offset) of **one JSON text per arena slot**, `arenaInfoNNNNN`
  (181 in the pack install): Stadium, Advertisement, CornerPost, LED_CornerPost, Rope, Apron, LED_Apron, Turnbuckle,
  Barricade, Fence, CeilingLighting, Spotlight, Stairs, CommentarySeat, RingMat, FloorMattress, Crowd,
  CrowdSeatsPlace/Model, IBL, Titantron, Minitron, Wall_L/R, Header, Floor, MiscObjects, LightingType, *_CM.
  Rows can be rewritten one arena at a time.
- **misc01_start.pac rows** (124 bytes): name string id, slot, select number, a1, a2, b1, b2 ... In Matthew's modded
  game All Out/Double or Nothing (118/119) carry a2 = 3 (the creator's note: "everything the same as 003"), most
  ported arenas a2 = 249; so a2 looks like "which slot's presentation set to use". Select number 24 is common there
  for working arenas, so **it does not mean "not selectable"** (earlier statement about slots 4 and 5 withdrawn;
  what makes an arena appear in the list is still to be determined).
- **Re-slotting method (community tutorial in Resources, "HOW TO CHANGE THE SLOT OF WWE 2K19 GRAPHICS PACK MOD"):**
  graphics/videos/stage are moved by putting the mod's inner file into the *target slot's own* container, which
  already carries the right internal name. So the internal name for any slot can be read from the clean install's
  per-arena files (`mods\WWE 2K19 Unpacked Arena Graphics`, installed with the pack); no hash rule has to be
  guessed. WrestleMINUS source (cloned for reference): file-name hash = bytes 11..8 of MD5 of the name; CAK names
  FNV-1a 64 of the lower-case name.
- **Part-number clashes with arenas that stay** (pack's misc04 vs the downloads): 21 part numbers, e.g. stadium 29
  (Dynamite/Revolution/Raw; used by 8 kept slots), stadium 31 and apron 79 and commentary 32 (WrestleMania 35 vs
  WrestleMania 33 slots), apron 75 (Dynamite vs slot 3), apron 74 + commentary 28 (Smackdown 21 vs slot 0), apron
  78 + commentary 31 (Royal Rumble 2020 vs slot 13), corner post 2 (Death Before Dishonor, 25 kept slots), Tokyo
  Dome's stadiums 40/41, ring mat 6, turnbuckle 4, corner post 3. Some of these are intended reuse of a stock part
  (same file), others are replacements: each has to be compared by content; replacements get a free number (free
  numbers exist in every category) and the arena's JSON row points at it. Usage table:
  `notes/arena_pack_part_use_2026-11-12.json`.
- Next: installer (`arena install`), first test = AEW Dynamite '22 into slot 158 on the clean install, then
  Matthew launches and checks.

## 01:20 Installer pieces built; first test build (Dynamite '22 -> slot 158)
- `tools/arena/epk.py`: EPK8/EPAC read, rename, payload, single-entry build, rewrap (keep the target slot's
  container and internal name, swap the payload). Format per WrestleMINUS: directory at 0x800, data at 0x4000,
  entry offset in 0x800 units, size in 0x100 units, header word 8 = data size, tail block kept. Round-trip checked
  byte-identical on 27 pack/mod files.
- `tools/arena/tables.py`: row editors for misc01_start (124-byte rows, all WrestleMINUS fields), misc04_arena (JSON per
  slot, archive rebuilt with NUL + 16-byte alignment like the original), initposition (WPAR rows slot,i2,i3,i4),
  prm_ar_lg_color (NIBJ table, 10 colour columns x 1000 slots, column-major from 0x170).
- Findings: stock slots use HSPC files found by path; pack/mod slots use EPK8/EPAC with internal names (MD<slot>,
  M000<slot>, part codes AP/BR/CL/CP/RM/SP/ST/TB + 2 digits, CC/CO/CB for *_CM). Every Dynamite '22 part differs
  from the pack's file with the same number, and 6 of those numbers are used by arenas that stay.
- Test build `tools/arena/build_dyn22_158.py`: stage + 3 videos rewrapped into slot 158's containers; parts
  renumbered apron 75->7, barricade 22->6, ceiling light 20->4, corner post 7->17, ring mat 2->7, spotlight 20->2,
  stadium 29->1, turnbuckle 15->13 (CM files kept at 2, no clash); rope 3 not installed (no known part code; uses
  the game's rope 3); 4 menu graphics (mod's slot-3 Dynamite '22 set) renamed to slot 158's names; name string
  48158 "AEW DYNAMITE '22"; the creator's misc01/misc04/initposition/light values on row 158 only (other rows checked
  unchanged). bgeffect.pac (global) not installed.
- 01:30 **Test build installed on the clean game** (`...\common\WWE 2K19`): 24 files (5 new, 19 replaced) + 5 lines
  appended to chunk0.def (CRLF kept). Originals backed up to `_arena_work\backup_dyn22_158\` (same relative paths,
  incl. chunk0.def); build copy + manifest in `_arena_work\out\`. Uninstall = copy the backup tree back and delete
  the 5 new files. **Matthew to check:** arena select shows "AEW DYNAMITE '22" in the Over the Limit '11 spot; a
  match loads; stage, ring (apron, ring mat, turnbuckles, posts), barricade, lighting colour and the three screens
  look right; menu graphics (locator/nameplate/match result/copyright); another arena (e.g. Raw, slot 1, uses
  stadium 29) still looks normal.
- 01:55 Matthew's test: **arena works; locator, nameplate, match result right; arena-select logo still Over the
  Limit; match card not Dynamite.** Cause: those two live in other files (`texture\ppv_logo\158 - ...pac`,
  `pac\menu\win\Assets\wwe19_anime\match_up\ltag_158_overlimit_2011_win.pac`). Sources: `AEW Dynamite GFX\Easy
  Install` (made for slot 3). Match-card pacs are an SHDC variant (header 0x40, dir at w2+w3, table 16-aligned after
  w6 bytes of 20-byte dir entries; reader/writer `tools/arena/shdc2.py`); files: 1 = background movie (BIKi), 3 =
  foreground image (DDS), 4 = unknown, last = text layout (atb0). Slot 158's card has 8 files, the Dynamite (205 Live)
  card 7. Built per the community tutorial: slot 158's card with files 1, 3, 4 from the mod, its own layout kept;
  ppv logo renamed to 158's name. Installed 01:55 (backups in `_arena_work\backup_dyn22_158`). Risk named in the
  tutorial: foreground image in a different size format (158's is about 0.25 MB, the mod's 2 MB) can show too big or
  small; text positions are slot 158's.
- 02:05 Matthew's test 2 (screenshots): match card works, foreground slightly squished (the size-format issue the
  tutorial warns about); **arena lighting dark and static until the entrance starts**. Cause found: in Matthew's
  modded game this exact stage file (md5 6bceeda2) runs at slot 17 with different settings than the creator's txt:
  misc01 Stage 2, Ref 4, Bar 6, Live 0, Filter 000000FFFFFF; light row = slot 17 stock colours; initposition 9,9,9;
  misc04 Crowd 10. **v2 tables** use those values (now identical to the modded slot-17 rows except the renumbered
  part ids) and are installed (misc01 9330973a, misc04 e09d6feb, initposition 9694f195, light 8193d58d). Rule for the
  batch: **take settings from the working modded game where the arena exists there; creator txt only otherwise.**
- 02:20 Match card squish: decoded with pyooz (Oodle Kraken, pip `pyooz`). Card files: 0 ?, 1 background movie
  (KB2i/BIKi), 2 small layout (ATB0), 3 foreground image (BC7 DDS: slot 158 1024x256, mod 2048x1024), 4 font pack
  (FTPK), 5/6 1024x1024 images, last = main layout (ATB0, references textures by name, e.g. "10024_fr", hence not
  swappable). The layouts differ in the foreground quad: slot 158 size 908 + scale 0.5 x 1.0, 205 Live (= the
  mod's) 454 + 0.5 x 0.5. Fix: those values in 158's layout set to the 205 Live ones (text positions stay 158's),
  layout stored ZLIB. Installed 02:20 (md5 660eae54, same as the container build); previous version kept as
  `_arena_work\cardfix\ltag_158_before_cardfix.pac`.
- 02:35 Matthew's test 3: lighting still static before the entrance; card fix made it worse (foreground misplaced).
  Changes (on the laptop, with the repo's yukes.py):
  - **Per-arena prop file:** every slot has `pac\prop\0NNN.pac` (128 of them; 0158 = 0.3 MB, 0017 = 1 MB). The mod
    "replaces WWE Main Event", i.e. it was built on slot 17's prop file (light rigs/props, hypothesis). Slot 158 now
    carries 0017's payload in its own container (backup in `_arena_work\backup_dyn22_158\pac\prop\0158.pac`).
    **To add to the installer if confirmed:** copy the prop file of the slot the mod was built for.
  - **Match card:** layout patch reverted; slot 158's card now holds the mod's whole card (the 205 Live layout with its
    own texture names, self-consistent), as the pack itself clones cards (158's own layout references slot 13's
    names). md5 a014fc30.
- 02:45 Test 4: lighting unchanged by the prop file; whole-card swap = no card at all. **Both reverted**: card back
  to the first build (dfa1abd4, slightly squished but correct), prop 0158 back to stock (a229c42b). Lessons: a card
  cannot be moved whole (its layout's texture names are tied to the slot), the prop file is not the lighting. Open
  question to Matthew before more guessing: does the same arena at slot 17 in the modded game show the same static
  idle lighting (i.e. is this the mod's own behaviour)?
- 02:55 **Control test installed on the clean game:** Dynamite '22 exactly as its creator ships it, into slot 17
  (Main Event), files under their own names + misc04 row 17 = the modded game's row 17 (misc01, initposition, light
  rows for 17 were already identical to the modded game). Temporary: this overwrites stock parts other arenas use
  (stadium 29 = Raw etc.); backups in `_arena_work\backup_ctl17` (misc04 e09d6feb). Question it answers: is the idle
  lighting right when the arena sits in its own slot?
- 03:05 Control result: **idle lighting static in slot 17 too** (mod in its own slot, modded-game settings). So not
  slot-related. Only other file the mod ships: `pac\bg\bgeffect.pac` (global; the modded game has the mod's copy,
  fcf3ecc9; clean has 38ff566d). Its only difference: VTGN = three 64x64 textures (mod BC-DX10, clean DXT5);
  EFFC/VTGL identical. Unlikely to be lighting. Open: does the modded game's Main Event (same Dynamite files) light
  correctly before the entrance? Asked Matthew.
