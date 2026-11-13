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
- 03:15 Matthew: the modded game's Dynamite '22 lights normally. Compared everything slot 17 uses in both games via
  each chunk0.def (624 paths): differences = crowd 10 (AEW crowd shirts), bgeffect, **`pac\evt\evt_light.pac`**
  (modded b2d8b93f, the Genesis entrance pack's... / clean 641e5be5), 33 entrance light files (evt\light, absent in the
  clean game: entrance lighting only), the four tables (expected), misc05_save_p30, attire file. Test 5: the modded
  game's evt_light.pac copied into the clean game (backup in `_arena_work\backup_ctl17\pac\evt\`).
- 03:35 Matthew: the modded game's slot 17 (same Dynamite '22) is static too = **the mod's own ceiling light/
  spotlight (CL20/SP20) are static.** His good-lighting Dynamite (modded slot 3) uses MattFick's **AEW Ceiling
  Light** mod: CeilingLighting 73, Spotlight 91, Floor 3 (its readme lists floors per AEW arena: 1 Grand Slam,
  3 Dynamite, 4 Rampage, 5 Double or Nothing, 7 Road Rager, 8 All Out, 17 Revolution, 19 Full Gear, 20 Fyter Fest,
  21 Winter is Coming, 22 Battle of the Belts). Done: control test and evt_light reverted (slot 17 stock again);
  AEW Ceiling Light files installed in the clean game (13 new files, ids unused by the pack, def lines added);
  slot 158 row: CeilingLighting 73, Spotlight 91, Floor 3 (misc04 fe272943). Build script updated. **For the batch:
  every AEW arena gets 73/91 + its floor from that list.**
- 08:10 Matthew: **lighting fixed by the AEW Ceiling Light settings.** Next three, installed 08:10:
  - **Ramp walk-through:** misc01 Stage 2 -> 1 ("Fix Floating on Air Issue.txt": 1 = shorter inclined stage, AEW/NXT;
    the modded slot-3 Dynamite also uses 1). misc01 2cd64408.
  - **Transitions:** from the modded game's Dynamite (slot 3, = AEW Dynamite GFX Easy Install): transition payload
    rewrapped into slot 158's container (357b09be); transition_replay copied as `pac\mov\transition_replay\000158.pac`
    (new; def line added).
  - **Match card foreground:** decoded with texture2ddecoder (BC7). Slot 158's layout draws its 1024x256 foreground
    as a strip about 6.7:1 on screen (measured from the screenshot); the mod's image has its content in the bottom
    half of 2048x1024. `tools/arena/card_fg_fit.py`: crop the mod image to 6.7:1 from the bottom (keeps 'UP NEXT' and
    the colour splash), resize to 1024x256, BC7 via etcpak, ZLIB. Card 22e4f4d4 (previous dfa1abd4 kept in
    `_arena_work\cardfix\ltag_158_before_cardfix.pac`).
- 10:40 Matthew: **ramp, transitions, match card, lighting all confirmed working.** New issue: arena names show
  "53E2 -EMPTY STRING TO BE FILLED" etc. and Dynamite '22 has no name. Cause: the clean game has TWO SuperString
  files in chunk0.def: `mods\SuperString\pac\string\win\string_win.pac` (the pack's, edited by us, correct: 26,676
  strings incl. 48158 "AEW DYNAMITE '22", every other string unchanged) and a stray older
  `mods\SuperString\string_win.pac` (2024-07-30, b4d256ff) whose arena strings are placeholders. After our edit the
  game reads the stray one (why it switched is not known). Fix 10:40: stray file replaced by a copy of the good one
  (original kept in `_arena_work\backup_strings\`). For the batch: string edits go to both, or remove the stray line.
- 13:40 **Dynamite '22 in slot 158 declared a success by Matthew.** Per his request, each finished arena is saved back
  to its Resources folder: `AEW Dynamite 22\Installed - slot 158 (Over the Limit 11) 2026-11-12\` = the 23 files as
  installed (pac + mods tree), files_md5.txt, README.txt with every change and the four settings rows. Rule for the
  batch: same "Installed - slot N (...) <date>" folder per arena.

### Dynamite '22 (158): AEW Crowd Shirts (2026-11-12)
- The shirts mod (iTwistedSpartan) replaces stock crowd 10 (md5 1f5a1c34, same as the modded game). Crowd 10 is shared by 10 pack slots, so it went in as a **new crowd id 15** instead: `pac\arena\crowd\arcrowd00015.pac` plus a `.def` copied from 00010, and a chunk0.def line.
- misc04 row 158: Crowd 10 → 15 (misc04 md5 fe272943 → 0427cfe4). Backups are in `_arena_work\backup_crowd`. The saved Resources package and README are updated.
- Needs an in-game check: if crowd 15 doesn't load (empty or stock crowd), fall back to an EPAC wrapper, or overwrite crowd 10 globally.
- **Result:** the game ignored crowd 15, and the stock crowd showed. The game seems to load only crowd ids 0–14. Crowd id 3 is assigned to no arena slot in misc04, so the shirts now sit in `arcrowd00003.pac`. Stock 3 is backed up in `backup_crowd`. Row 158 has Crowd 3 (misc04 md5 d061d9e2). Waiting on an in-game check.
- The crowd 3 attempt also showed the stock crowd. Cause: the HSPC header u32 at 0x10 is a per-file ID (crowd 3 = ce8ed822, 4 = e48ed822, 10 = 0d8fd822), and the shirts file still carried crowd 10's ID. Patched it to crowd 3's ID (md5 711d22e1). Waiting on an in-game check. **Rule: re-slotting an HSPC crowd file also needs the target's header ID at 0x10.**
- **Solved (confirmed in game):** a crowd file carries its id in 5 places: the HSPC header @0x10, two 8-byte name hashes in the directory @0x800/@0x814, and the id @+0x10 of each of the 2 inner SHDC packs. Copying all 5 from stock crowd 3 made the shirts load as crowd 3. Tool: `tools/arena/crowd_reslot.py`. Final state: arcrowd00003 = shirts (d2ff4855) with the stock crowd 3 .def; crowd 10 is stock again; row 158 Crowd 3; misc04 d061d9e2. Crowd 3 was free because no arena slot used it. Crowd ids above 14 don't load, so any later crowd mod has to replace one of ids 0–14.

## Batch 1, part A (2026-11-12): AEW All Out 118, Double or Nothing 119, Dark 117
- Installer `tools/arena/install_native.py` (plan JSON). Files go to the clean game's existing container per slot (mov, Unpacked Arena Graphics names); new paths get a def line. Backups in `_arena_work\backup_batch1`; plan in `_arena_work\cardfix\plan_b1.json`.
- Settings: misc04 = the modded game's rows 118/119. Stadium 29 → 1 and ring mat 2 → 7 (the payloads match the parts already installed for Dynamite '22). Crowd → 3 (shirts). Dark uses the All Out row with its own parts: stadium 47, apron 135, turnbuckle 17, barricade 26, ring mat 17, floor 3. misc01/initpos/light are copied from the proven slot 158 row.
- AEW floor mattress (Dynamite 20 pack, HSPC, made for id 15, which no slot used) is installed at id 15. Slot 158 now uses 15 as well.
- **Rope 3 open:** the AEW rope (fce1740e) replaces stock rope 3, which 15 kept arenas use. All 11 rope ids are taken, and new HSPC ids can't be made (the header ids look like build stamps; the directory hashes are not FNV of the name). The stock rope 3 stays for now.
- Names: 241866 AEW ALL OUT, 241837 AEW DOUBLE OR NOTHING, 241849 AEW DARK (both string files).
- Match cards are not done yet: these mods ship no slot card. Their art is in the AEW Matchup Screens (Create-a-Show) packs.
- **Match cards 117/118/119** (2026-11-12): each slot's card keeps its own container, layout and fonts. File 1 (background movie) = the arena's own transition movie (BIKi, 3840x2160, ZLIB-wrapped). File 3 (foreground) = the arena pack's Create-a-Show foreground (`ltag_30001_90s0X`, DXT5 2048x1024): the bottom strip is cropped to 6.7:1, resized to 1024x256 and BC7-encoded. These cards use the same layout as 158, so the same fit applies. Card md5s: 118 83f9a5bd, 119 900f5bcb, 117 d573ba2d. The Create-a-Show background stills (with the show logos) can't be used, because the card background has to be a Bink movie.
- **Rope:** the AEW rope is re-stamped to rope id 7 (stamps from stock 7, md5 1be3c4cd). Rope 7's only other user is misc04 row 81, which has no misc01 row, graphics or card, so it isn't a selectable arena. Rows 117/118/119/158 use Rope 7 (misc04 689ae6ab).
- Matthew's test (15:27): arenas and cards good. Changes:
  - Dark ppv logo moved to the Unpacked Arena Graphics folder; its def line was rewritten to that path.
  - Dark Stage 0/1 → 3 (flat), because of floating on air (misc01 79cd9103).
  - The Double or Nothing apron 137 and ring mat 18 now go on 117/118/158 too (misc04 9cc67af3).
  - Crowd was already 3 (shirts) on all four AEW rows.
  - Open: the cards draw the wrestler names over the Create-a-Show strip; asked whether to remove them.
- **Hiding card names (test 1):** the ATB0 layout (card file 7, identical in 117/118/119) has 17 nodes. Each node has 12 property tracks (ids 0–9, 0x11, 0x12), and the 16-byte keyframes start at 0xf60, (node*12 + i)*16. Property 0 = position, 1 = scale. Nodes 7, 9, 11 and 14 (text, y 790–805, scale 0.65–0.7) are set to scale 0. The layout is stored ZLIB-wrapped. The cards with names are kept as `_arena_work\cards\withnames_*.pac`. The node↔name pairing from the name table is not certain yet.
- Dark logo fix: the pack names this file `117- Armageddon '02.pac` (no space before the dash; 28, 37, 141 and 151 are irregular too), so the installer missed it and Armageddon won the duplicate name 781E9B35. That file now carries the Dark logo. The extra `117 - AEW Dark.pac` (same content, same name) stays, because deletion isn't permitted. The installer now matches `N\s*-`. Crowd shirts and mats confirmed by Matthew.

## Batch 1, part B (2026-11-12): WrestleMania 35 → 130, Raw → 96, ROH Death Before Dishonor → 138
Backups are in `_arena_work\backup_batch1b`. Plans: `plan_b1b.json`, `plan_raw96.json` (+ `plan_raw96t.json`, tables only), `plan_dbd.json`. The AEW set (117/118/119/158) is saved back to Resources as "Installed - slot N 2026-11-12" folders.
- **New technique: HSPC → EPAC.** When a mod part is an HSPC replacing a stock id that kept arenas use, its payload goes into a named EPAC at a free id (`build_single(b'EPAC', b'SGSN', b'ST48', payload)`), the same way as the Dynamite '22 parts.
- **WM35 (130)**, from the modded game (ground truth):
  - stadium 31 → 48 (ST48), apron 79 → 42 (AP42) and corner post 7 → 23 (CP23), all converted;
  - ceiling light 69 and commentary 76 are new ids; the misc04/misc01 rows are the modded game's 130 rows;
  - menu graphics come from the Resources folder; name "WRESTLEMANIA 35".
  - Card: the mod's card (`130 - Wrestlemania 35.pac`, a 9-file WM layout) supplies movie file 1 (KB2j, raw OODL entry), and its 2048x256 strip is resized to 1024x256 into slot 130's own card. Names are kept (WWE style).
- **Raw (96)**:
  - Raw Arena mod: entrance 1 re-stamped as entrance 96 (HSPC header/hash stamps from stock 96; the mod file has no inner SHDC). Its stadium 29 payload = the installed stadium 1. IBL 0 is re-stamped as IBL 34 (only unwanted slots used it).
  - Raw '18 videos go in at 000096. misc04 = clean Raw row 1 with Stadium 1 and IBL 34; misc01 = the creator's row 1 (F4 = 1); light = the creator's row 1; initpos = row 1.
  - Graphics: the pack's slot-1 Raw set, renamed. Card: the Raw 2018 card's movie + its foreground fitted. Name "RAW".
  - Note: row 96 has no CrowdSeatsPlace/Model keys, so the installer filters on the keys present.
- **DBD (138)**:
  - Creator settings from misc04 PNGs: stadium 22, rope 3, apron 173, turnbuckle 46, barricade 41, fence 29, stairs 1, crowd 8, IBL 30, CM 2.
  - Changes: the corner post (HSPC id 2, used by 25 kept slots) → EPAC CP24. The corner post CM differs from the Dynamite one → renamed CC00003 (CM 3). Ring mat = ROH '05 RM16; floor mattress 13, because 15 is now AEW. misc01 Stage 0, Bar 7; initpos 1,1,1.
  - Graphics: DBD locator, match result and nameplate; copyright from the ROH set (17 - ROH). The ppv logo is the mod's `BAKLASH01.PAC` (internal name A8E18B96 = slot 138).
  - Card: slot 138's own generic movie (the creator ships only still BG/FG PNGs; no Bink encoder). The FG PNG is padded to 6.7:1 → 1024x256; names are hidden (layout_noname). Name "ROH DEATH BEFORE DISHONOR".
- Test (18:13): WM35/Raw/DBD look good, and WM33 is unaffected. The Raw card had white names on the white strip. Fix: copied the text settings from the real Raw 2018 layout (ltag_001 file 5) into the 96 layout, range 0x1200–0x1a10, skipping the foreground scale at 0x16b0/4. That covers the text nodes' x 960 → 1174, scale 0.65/0.7 → 0.9 and colour ffffffff → 000000ff (black, RGBA). **ATB0 colour is the u32 at keyframe +0x20 after position (e.g. 0x1280).** Card md5 e0c6ac25.
- Raw card names were too big and overlapped the logo (18:34). Set x 1182 (centre of the free area right of the logo) and all text scales to 0.6; the colour stays black. No line wrap was found in the ATB0 text nodes. Card md5 2e7e8280.
- Raw card text scale lowered again to 0.45 (all text nodes). Card md5 ff2ba738.
- The stock Raw card fits long names with a condensed font (its own FTPK, file 4) and Raw text settings. The 96 card now uses the Raw FTPK (file 4) + the Raw text settings (x 1174, scale 0.9, black). The scale-0.45 version is replaced. Card md5 cb529e4c. Lesson: **the card font is file 4 (FTPK); copy it together with the text settings.**

## Batch 2 (2026-11-12): AEW re-slots
Rampage 116→139, Road Rager 120→149, Grand Slam (New, made for slot 3, + ppv logo from the 163 version + Dynamite '22 locator/nameplate/result/copyright) →159, Revolution 10→112, Full Gear 14→133, Dynamite '20 3→107. Forbidden Door (→4) is **on hold**: its entrance needs the "2K15-2K18 Arena Port" + Titavius' "AEW Dynamite – LA Forum '22" entrance pieces, and neither is in Resources.
- Tools:
  - `reslot_stage.py` (S→T). Rewrap into T's container; re-stamp HSPC→HSPC. EPK over an HSPC path is allowed. HSPC videos with no T container become new EPK8s named `M%06d `, with tags per folder: ar_apron MVGA, ar_mini MVGM, ar_ramp MVGR, ar_wall MVGW, transition MOVT, transition_replay MVTS, bg_apron MVBA.
  - `stage_b2.py` builds the staged folders `_arena_work\in\b2_T`. The device can't delete, so stale staged files are skipped with the plan's `exclude` regex. bg_* videos are excluded: the modded game's ones are stock videos of the source slot.
- Sources: the modded game for slots 3/10/14 (entrance + mov; `_arena_work\in\src_mN`), plus each Resources folder (GFX). Parts at free ids, as shipped: BR25/TB16 (Rampage), BR29/TB20 (Road Rager), ST74 (Grand Slam), BR66/TB51 (Revolution), BR55/TB67 (Full Gear). Dynamite '20 barricade 22 (HSPC) → EPAC BR30; its turnbuckle 15 = TB16 payload. Stadium 29 = installed stadium 1.
- misc04: the All Out row with the AEW standards (apron 137 + ring mat 18 from Double or Nothing, rope 7, crowd 3, floor mattress 15, ceiling light 73/91) plus own barricade/turnbuckle/floor (4/7/1/17/19/3). IBL: Grand Slam 88, Revolution/Full Gear 50, others 1. Grand Slam: stadium 74, stairs 1. misc01 from 158, initpos 9,9,9, light from 158. Names "AEW RAMPAGE", "AEW ROAD RAGER", "AEW GRAND SLAM", "AEW REVOLUTION", "AEW FULL GEAR", "AEW DYNAMITE '20".
- Cards (`cards_b2.py`):
  - Rampage/Road Rager: movie = own transition; foreground = the arena pack's Create-a-Show foreground. Road Rager's foreground is DDS #0, not #1: pick the DDS with alpha.
  - Grand Slam/Revolution/Full Gear: Create-a-Show foregrounds from AEW Matchup Screens (steel02/hardcore02/80s02; ZLIB-wrapped DXT5 2048x1024). Movies: Dynamite GFX card movie, Revolution card movie, Full Gear card movie.
  - These five have names hidden. Foreground fit `fit2`: crop from the alpha top (or the 6.7:1 bottom strip), pad to 6.7:1.
  - Dynamite '20: Dynamite GFX card movie + foreground fitted, names kept (like Dynamite '22).

## Plan changes (2026-11-12, 23:09)
- **Forbidden Door dropped** (Matthew). The LA Forum mod it needs is gone.
- **SummerSlam '22 added**, now in the Resources arena folder. Planned slot: **160** (the spare slot). Batch 3 order: WM27 → 125, WM31 → 140, WM38 → 132, RR Retro → 124, RR2020 → 135, SummerSlam 09 → 143, SmackDown 21 → 53, ROH '05 → 134, SummerSlam '22 → 160. Batch 4 is unchanged.
- Batch 2 (six arenas) is waiting on Matthew's in-game test. WM35/Raw/DBD still need saving back to Resources after the Raw card font fix is confirmed.

## Batch 2 test (23:31): fixes to do once the laptop is linked again
1. Matthew did not want the Double or Nothing *apron* everywhere. Go back to each arena's own apron: All Out 136, Dark 135, Dynamite '22 7, Rampage 134, Road Rager 138, Revolution 184, Full Gear 97, Dynamite '20 75 (HSPC → EPAC at a free id), Grand Slam = Dynamite apron. Keep ring mat 18 (AEW logo) until he says otherwise.
2. The Rampage nameplate has a baked "AEW RAMPAGE" header that collides with the MITB-winner banner. Swap it for a header-less nameplate (stock or another AEW one).
3. Hide the names on the Dynamite '20 card (layout_noname).
4. The Rampage/Road Rager card background is the short transition, so it loops fast. Bink can't be re-encoded here, so use the longer ar_mini/ar_wall loop video as the card movie instead.
5. **Grand Slam (159) does not load** (red bar, then nothing). Prime suspect: IBL 88, copied from the modded row and probably missing in the clean game. Then stadium ST74 (its readme needs Titavius' AEW apron/barricade/CM parts) and the slot-3 entrance rewrapped into 159. Check that the files exist, try IBL 50, then bisect.

## Batch 2 fixes (2026-11-13, laptop session)
Backups: `_arena_work\backup_b2fix`. Plan `plan_b2fix.json`. New checker `partcheck.py <slots>` (every part id a misc04 row names must exist in pac\arena).
- **Grand Slam (159) load failure: cause found.** `partcheck` showed IBL 88 missing in the clean game (clean has IBL 0–75). The modded game's `aribl00088.pac` is a named EPAC (IA88), so it was copied as is (md5 e3c6948a) and added to chunk0.def. Stadium ST74 is identical to the modded game's (7535674f); every other part of row 159 exists. Waiting on Matthew's test.
- **Own apron per AEW arena (ring mat 18 kept):** All Out 136, Dark 135, Dynamite '22 7, Rampage 134 (EPK8, as shipped), Road Rager 138 (EPK8), Revolution 184 (EPK8), Full Gear = mod HSPC 97 → EPK8 AP00121 at id 121, Dynamite '20 = mod HSPC 75 → EPK8 AP00122 at id 122, Grand Slam = Dynamite apron 7, Double or Nothing 137 (unchanged). misc04 b48ce50e. Note: the modded game's rows 116/117/120 point at ported stock aprons (38/12/20) and are not these AEW mods, so the mods' shipped aprons were used.
- EPK8 header word 8 = data size in bytes, same as stock (checked on ar_wall EPK8s); build_single matches.
- **Rampage nameplate (139):** a nameplate pac = EPK8 > SHDC (shdc2 layout): 0 header, 1 ATB0 layout, 2/3 FTPK fonts, 4 BIKi movie (1920x624, the plate art). All AEW nameplates share files 0–3; the movie is the only difference. Rampage's movie (182254f9, 7.9 MB) has the orange "AEW RAMPAGE" header; All Out/Dark/DoN/Full Gear/Road Rager share a plain AEW plate (4ed579a7). File 4 of 139 replaced with the plain plate, 139's container name kept (3E97F685). md5 02804425. Backup `backup_b2fix\nameplate139.pac`.
- **Cards** (`cards_b2fix.py`, backups in `backup_b2fix`): Dynamite '20 (107) now uses layout_noname (md5 625e1098). Rampage/Road Rager movie = the arena's ar_mini loop (139: 7.4 s 1558x778; 149: 5.0 s) instead of the 1.3 s transition (139 dcfb0f9c, 149 86f165a9). ar_wall was 11.5 s for 139 but square 1024x1024; mini is wider.
- Scripts that live only on the laptop are now copied into `tools/arena/laptop/`.
- **All five batch 2 fixes are installed; waiting on Matthew's test.**

## Saved to Resources (2026-11-13)
- WM35 (130) and ROH DBD (138): "Installed - slot N 2026-11-13" folders with files, files_md5.txt and README (all four table rows + name). Tool `save_res.py <slot> <folder> <title> <install logs>` (laptop; repo copy in tools/arena/laptop). Raw (96) waits for the font check. The AEW saves from 2026-11-12 still show apron 137: re-save them after the apron change is confirmed.

## Batch 3 survey (2026-11-13), `part_survey.py` (FREE / SAME / CLASH against the clean game, with the misc04 rows using the id)
| Arena → slot | source slot | settings source | part clashes |
| --- | --- | --- | --- |
| WM27 → 125 | 402 | modded row 402 (installed there) | apron 136 = All Out's id → new id. IBL 88 SAME (shared with Grand Slam) |
| WM31 → 140 | 105 | creator PNGs (day/evening/night entrances; modded 105 is not WM31) | apron 42 = WM35's AP42 → new id |
| WM38 → 132 | 19/61 mixed | modded row 61 | none (IBL 88 SAME) |
| RR Retro → 124 | 14 | creator PNGs (14 is Full Gear in the modded game) | none |
| RR2020 → 135 | 13 | ships its own misc04/misc01/initpos (row 13); modded row 13 | apron 78, commentary 31 (HSPC, stock users 13/22) → EPK8 at free ids |
| SS09 → 143 | 30 | creator PNGs, initpos 08 08 01 | apron 35 (HSPC, stock user 43) → EPK8 |
| SD21 → 53 | 0 | modded row 0 (installed there) + its light file | apron 74, commentary 28, ceiling light 3, IBL 0, LED corner post 1 (all HSPC stock) → EPK8 |
| ROH '05 → 134 | 312 | readme row: 47,-1,23,-1,3,20,-1,17,25,9,14,24,0,-1,16,-1,14,-1,-1,2,-1,-1,-1,-1,-1,16,0,-1,0,0,0,0,0 | files are named "arXXX - ROH'05.pac" (turnbuckle "0017"): rename. Its ids stadium 47/turnbuckle 17 (Dark), barricade 25 (Rampage), ring mat 16 (DBD/Rampage), corner post 23 (WM35) all clash → new ids |
| SS22 → 160 | 44 | creator PNGs | corner post 37 differs from WM31's CP37 → new id; IBL 89, spotlight 51 identical to WM's (shared) |
Shared identical files across mods: IBL 88, 89, 92, spotlight 51.

## Batch 3 installs (2026-11-13)
Tools: `b3plan.py spec_T.json` (stages parts, remaps clashing ids to named EPK8 `XX%05d`, writes plan_b3_T.json from the modded game's rows or explicit values) → `install_native.py` (now also takes `m01_full` and `light`). Cards: `cardb3.py` (container side; movie file 1 ZLIB-wrapped, foreground fit2 + BC7 into file 3; names kept, WWE style). Backups `_arena_work\backup_b3_T`.
- **New: Oodle works in the container.** `pip install pyooz`; an OODL entry = 'OODL', 0, '0\0\x06.KRKN', u32 raw size @0x10, u32 comp size @0x14, stream @0x18 → `ooz.decompress(b[0x18:], raw)`.
- **Id register (new ids given out):** apron 121 Full Gear, 122 Dynamite '20, 123 WM27; planned 124 WM31, 126 RR2020, 127 SS09, 128 SD21; commentary 38 RR2020, 59 SD21; ceiling light 22 SD21; IBL 76 SD21; LED corner post 29 SD21; ROH '05 stadium 49, turnbuckle 21, barricade 31, corner post 25; SS22 corner post 39.
- **WM27 → 125 installed.** Modded row 402 (stadium 58, corner post 30, barricade 65, ceiling 54, spot 50, commentary 7, IBL 88, crowd 9, fence 5), apron 136 → AP00123. misc01/light = modded 402, initpos 8,8,1 (already). Card: mod movie (BIKi 1920x1080) + mod foreground fitted (card 0ea9037e). No ar_mini/apron video in the mod (slot 125 has none either). Name "WRESTLEMANIA 27".
- **WM38 → 132 installed.** Modded row 61 (stadium 77, apron 185, LED corner post 32, ceiling 92, spot 51, commentary 75, IBL 88, crowd 4, floor mattress 13). Files named 61 and 19 both staged (reslot_stage twice). misc01/light = modded 61, initpos 8,8,1. Card: mod movie + "Live Tonight" foreground. Name "WRESTLEMANIA 38".
- Cards built for 124 (RR Retro: mod movie + OODL foreground decoded), 143 (SS09 mini loop + mod FG PNG), 160 (SS22 mini loop + FG PNG). Slot 140 has no match card file, so WM31 gets none.
- **RR2020 → 135 installed.** Modded row 13 (Titavius' own tables: stadium 18, LED corner post 23, crowd 4), apron 78 → AP00126, commentary 31 → CS00038. misc01/light = modded 13, initpos 16,16,10. Videos ar_apron/mini/wall at 135; bg_* excluded. No card art in the mod: the slot keeps its stock card. Name "ROYAL RUMBLE 2020".
- **SmackDown 21 → 53 installed.** Modded row 0: apron 74 → 128, commentary 28 → 59, LED corner post 1 → 29 (EPK8s). Its ceiling light 3 / IBL 0 were also staged as 22 / 76, but row 0 uses ceiling 0 / IBL 1, so they are unused. Clean row 53 has no CrowdSeats keys: `b3plan.py` now drops keys the target row lacks. misc01/light = modded 0, initpos 1,1,1. No card. Name "SMACKDOWN".
- **ROH '05 → 134 installed.** Files renamed (" - ROH'05", turnbuckle "0017") into `_arena_work\in\src_roh05`. Readme row with stadium 47→49, turnbuckle 17→21, barricade 25→31, corner post 23→25, apron 20→129; ring mat 16 is the identical file DBD already uses. Only a ppv logo and an entrance ship; the misc01 row, videos and card stay stock King of the Ring '99. Name "RING OF HONOR '05".
- WM31: Matthew asked about installing all three times of day. That needs one slot per entrance (the other parts are shared). Waiting on his slot picks.
- **Creator screenshots (WrestleMINUS):** misc01 small fields (I2/I3, F2 "5A", B3 "FFFF") are shown in **hex**. Light colours are shown **ARGB** (`FF091DFF` = blue); our tables store RGBA, so convert c[2:]+c[:2]. The A1/A2/B1/B2 fields were left at the target's values (ambiguous display).
- **RR Retro → 124 installed.** Screenshot row (stadium 22 in the shot, but the mod ships a new **stadium 53**, so 53 is used: flag if it looks wrong), apron 152, corner post 2, barricade 20, fence 5, commentary 46, floor mattress 5, crowd 9, IBL 48. misc01 from PART2 (Stage 0, D 1/2/1/0/1, I3 0x30, Live 8, J 2), initpos 8,8,1, light from the shot. Card: mod movie + "Live Tonight" FG. Name "ROYAL RUMBLE".
- **SummerSlam '09 → 143 installed.** Row: stadium 22, adv 1, corner post 5, apron 35 → 127, turnbuckle 5, barricade 5, commentary 23, floor mattress 3, crowd 7, seats -2/-2, IBL 45. misc01 Stage 1, Ref 5, F3 4, F4 1, I3 0x1D, J 1; initpos 08 08 01 (creator note); light yellow/red. Only a nameplate ships (rest of the GFX stay stock NOC '09). Card: mini loop + FG. Name "SUMMERSLAM '09".
- **SummerSlam '22 → 160 installed.** Row: stadium 72, adv 1, corner post 37 → 39, apron 199, turnbuckle 0, barricade -1, fence -1, ceiling 75, spot 51, commentary 89, floor mattress 13, crowd 4, IBL 89, header 65. misc01 D1 1, D2 2, H 5/4/1/3, I2 0xA, I3 0x2A, J 2; initpos 8,8,1; light blue/orange. GFX: locator + nameplate (texture `WWEL91.pac` not slot-named, not installed). Card: mini loop (2.4 s, the only loop shipped) + FG. Name "SUMMERSLAM '22".
- **Batch 3 status:** 8 of 9 installed (125, 132, 135, 53, 134, 124, 143, 160); untested in game. WM31 Night 140, Day 141, Evening 153 installed.
- **WM31 ×3 installed** (Matthew 00:58: use the reserve list → Battleground '15 141 and Survivor Series '11 153; two of 153/154/145 remain for the keep-one choice). Night → 140, Day → 141, Evening → 153. Each slot has its own entrance (src dirs `in\src_wm31_<V>`); the mod's DAY and EVENING entrance files are identical (70c411a3), so those two differ only by IBL. Shared parts: stadium 7, apron 42 → AP00124, corner post 37, commentary 77, ceiling 48, spot 48, barricade 20, crowd 9; IBL Night 5 / Day 92 / Evening 89. The screenshot lists stock apron 29 / corner post 7 / commentary 17, but the mod ships 42/37/77, so the shipped parts are used (flag if they look wrong). misc01 Stage 1, F4 2, I3 0x1D, J 1; initpos 8,8,1; light red FD0400. Card for 141/153: WM31 mini loop + bottom panel of the matchup FG (cropped from y 560, top band dropped); 140 has no card file. Names "WRESTLEMANIA 31", "... DAY", "... EVENING". `b3plan.py` now takes `m01_set` (overrides on the target's own row).
- **Batch 3 complete (all installed, untested):** 125, 132, 135, 53, 134, 124, 143, 160, 140, 141, 153.
- **WM31 reverted (Matthew 01:57: "looks quite bad").** Slots 140/141/153 restored from `backup_b3_153`, `_141`, `_140` in reverse order (entrances, videos, GFX, cards, all four tables, strings). Rows are back to stock (140: stadium 22, apron 105, IBL 32), and the other batch 3 rows are intact. The WM31-only new files (apron 124, ceiling 48, commentary 77, corner post 37, spot 48, stadium 7) stay on disk unused, because the device can't delete; their chunk0.def lines are harmless. 141/153 are back on the reserve list.
- **WM31 note (Matthew 14:19):** the WM31 already in the game is slot **105** ("WRESTLEMANIA 31": stadium 11, apron 29, corner post 7, commentary 17, IBL 7), and it was never touched in this session. The creator's screenshot shows exactly this row: the mod was built for slot 105 on its stock parts. In the old modded game, 105 used the mod's Day/Evening entrance (70c411a3); in the clean game, 105's entrance is 18cc0a5a (dated with the 2026-11-12 04:41 Genesis rebuild, 46 entrances share that stamp). Offered to put 70c411a3 back into 105 if it doesn't match.

## 2026-11-13 evening: "everything broken" = chunk0.def rebuilt over _arena_work
- Symptom (Matthew): Grand Slam (159) shows its card/nameplate but loads stock Vengeance '11 (stock apron/stage). The live misc04 row 159 was correct (apron 7).
- Cause: at 17:52 chunk0.def was regenerated (and Chunk0.arc is 0 bytes): the rebuild walked the whole game folder and listed 778 files under `_arena_work\`, including every backup copy of misc04/misc01/initposition/light. The game then read an old backup table instead of `pac\root\misc04_arena.pac`.
- Fix: def saved as `chunk0.def.bak_1752_regen`; `_arena_work` **moved out of the game folder** to `D:\SteamLibrary\steamapps\common\WWE2K19_arena_work` (so no rebuild can index it again); its 778 lines removed from chunk0.def (24,958 → 24,180 lines). Tools repointed (G = `../../WWE 2K19/`, backups under `../WWE2K19_arena_work/`; old plans' `_arena_work/` backup paths are mapped automatically). Resources mount is now `~/mnt/A - Resources`.
- **Lesson: never keep work files or backups inside the game folder; a def rebuild indexes everything under it.**
- The 17:52 rebuild was Matthew's normal chunk rebuild for character-port tests. Rebuilds are safe now that no work files live in the game folder; all installed arena files sit at normal `pac\...` paths and get re-indexed correctly.

## 2026-11-13 night: Matthew's AEW feedback (after the def fix)
1. **Grand Slam transition:** Dynamite '22's (158) transition + transition_replay re-slotted to 159 (`reslot_stage.py` → `fxinst.py`): transition/000159 c6e19f6f (HSPC re-stamp), transition_replay/000159 new EPK8 M000159 31d60eb4 (+ def line). Backups `WWE2K19_arena_work\backup_aewfx`.
2/3. **Card movie speed** by editing the Bink header fps (u32 0x1C num / 0x20 den; frames at 0x08), no re-encode (`cards_speed.py slot=num/den`, `binkinfo.py`). Rampage 139 mini loop 29.97→50.8 fps (7.44→4.39 s), Road Rager 149 29.97→47.3 (5.00→3.17 s): halfway between the old transition and the mini loop. Dark 117 30→20 (1.37→2.05 s), All Out 118 60→40 (1.50→2.25 s), Double or Nothing 119 60→40 (1.90→2.85 s). Card md5s 139 2eefe50f, 149 ef5490e4, 117 be8008e0, 118 fc62a2d0, 119 d94c56ac. Needs in-game check that the game honours the header fps.
4. **Crowd:** all 10 AEW rows (107/112/117/118/119/133/139/149/158/159) have Crowd 3 = AEW shirts (d2ff4855). WWE shirts seen earlier were most likely from the stale backup tables the rebuilt def pointed at.
5. **Watermark:** the per-slot copyright graphics of the AEW slots already show the AEW logo (decoded 118, 159). The WWE logo Matthew sees is another element; asked for a screenshot.
- **"W LIVE" bug (bottom right, in match):** a shared animation, `pac\menu\win\Assets\wwe19_anime\gameplay\ltag_wwelive_win.pac` (+ `_block`, `_scratch` variants), not a per-slot graphic. The per-arena switch is **misc01 byte 117 ("Live")**: values in the clean game are 0 (137 rows, modern WWE), 1 (14, WWF-era: 121, 56, 63, 44 ...), 7 (17, WCW/ECW: 36, 37, 40, 50, 58, 62 ...), 8 (45, Attitude era/PPVs). In the old modded game Matthew's AEW arenas (3, 10, 14, 163) had **Live 7**, the WCW/ECW value. Set Live 7 on all 10 AEW rows (misc01 dccef0a6, backup in `backup_aewfx`). Expected: no WWE bug. An actual AEW bug would mean replacing one of the shared variants, which changes every arena using that value.

## Batch 4 (2026-11-13 night): NXT 2.0 → 127, NXT White & Gold → 128, Tokyo Dome → 5, All In → 123
- Ground truth: the old modded game's rows 164 (NXT 2.0), 316 (Tokyo Dome), 142 (All In); every shipped part there is byte-identical to Resources.
- **NXT 2.0 → 127**: Resources "Switched to Slot 164": entrance/videos/ppv logo from 164, locator/result/nameplate/copyright/replay from the slot-2 set. Parts as shipped (apron 195, cornerpost 35, commentary 82, stadium 55 all FREE; IBL 88 SAME). Row = modded 164, misc01 = modded 164, initpos 2,1,1, light = modded 164. Card: the mod's KB2j movie + "Live Tonight" banner fitted into 127's strip (card 9d214269). Name "NXT 2.0".
- **White & Gold → 128**: rar extracted in the container (libarchive), files in `in\src_wg`. Re-skins of NXT 2.0's ids: apron 195→196, cornerpost 35→40, commentary 82→83 (EPK8). Entrance + GFX from NXT 2.0 (re-slotted 164/2→128), then W&G videos, replay, ppv logo over them. Row = modded 164 + Rope 0 (creator), light gold/yellow from the creator's jpg (ARGB→RGBA). Card: W&G movie + "NXT Tonight" banner (517a6a79).
- **Tokyo Dome → 5**: row = modded 316 with HSPC clashes remapped to EPK8: stadium 41→54 (40→56 staged, unused), apron 35→200, cornerpost 3→41, ringmat 6→19, turnbuckle 4→22. Videos: ar_mini (Resources) + ar_wall (modded game). misc01/light = modded 316, initpos 7,7,7. Rope 3 and ceiling 20 differ between the two games (modded rope 3 = the AEW rope); the clean stock ones are used. **No locator/result/nameplate:** slot 5 has none in the clean game and its menu hash names are unknown (MD5 bytes 8–11 of an unknown string; brute force of locator/ppv names failed), so the NJPW set (internally slot 316) is parked in `in\_unused_tokyo_gfx`. No card (slot 5 has none).
- **All In → 123**: entrance 142 → 123, apron 175 (FREE, so no clash with WM27's apron 123), ringmat 33, turnbuckle 30 (files renamed from "- ALL IN"). Videos ar_mini/ar_wall from the modded game's 142 (the port's screens). Row = modded 142 (Live 7). Stadium 22 differs between games; clean's used. Card: 123's own movie + ALL IN foreground (b7ef5af8).
- **b3plan hazard found:** output names come from the folder name, so `arropecm00002`/`arturnbucklecm00004` (corner-mat parts) would have been written over stock rope 2 / turnbuckle 4. Moved out of the All In source; scan of every EPK8/EPAC part in the game: no earlier damage. Also the NXT folder's stray `stadium\arentrance00164.pac` became "stadium 164": moved out.
- New tools: `cardb4.py` (container; template-aware strip fit from a card file or PNG), `cardinfo.py`.
- **Installed 23:40** (`install_native.py plan_b4_T.json`, backups `WWE2K19_arena_work\backup_b4_T`, logs `cardfix\b4_T.log`). partcheck 127/128/5/123 ok; chunk0.def has no `_arena_work` lines; AEW rows unchanged (Live 7 kept). Rows: 127 apron 195/stadium 55/cp 35; 128 apron 196/stadium 55/cp 40; 5 apron 200/stadium 54/cp 41; 123 apron 175/stadium 22/Live 7. Waiting on Matthew's test.
- Id register additions: apron 175, 195, 196, 200; cornerpost 35, 40, 41; commentary 82, 83; stadium 54, 55, 56 (unused); ringmat 19, 33; turnbuckle 22, 30.
- **Batch 4 fixes (Matthew's first look):** backups `WWE2K19_arena_work\backup_b4fix`.
  - Card names removed on 127/128/123: their layout (file 7) is byte-identical to the AEW cards', so `cards\layout_noname.zlib` went in as is (127 1aa2b059, 128 e2695294, 123 f41d68d1).
  - **Arena-select image = the slot's ppv_logo.** All In: its `MITB13.PAC` is the ppv logo made for slot 142 (internal 05A187CF) → payload into `123 - Wrestlemania 13.pac` (67ee7089). Tokyo Dome: the pack's own `316 - Japan Dome (Tokyo Dome).pac` → payload into `5 - Battleground '13.pac` (2f81d651).
  - White & Gold screens were a held still: Bink frame sizes after frame 0 have a median of ~200 bytes (127's are 5–24 KB). Replaced 128's ar_wall/mini/ramp/apron with the stock NXT (slot 2) animated black-and-gold videos, re-slotted (wall 12c4859c, mini be9afa64, ramp cf7b3b5f, apron 54acb6b4); the creator's transition is kept. **Check for static videos: median Bink frame size.**
