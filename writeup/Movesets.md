# 2K26 -> 2K19 moveset translation (started 2026-11-19)

Goal: an offline tool that takes a 2K26 wrestler's moveset and writes a 2K19 `.moveset`, mapping moves that don't
exist in 2K19 to the closest equivalent and slots by role, with a report of every substitution.

## Plan (feasibility probe)
1. **2K19 layout** — DONE (below).
2. **2K26 moveset data:** locate in the `.cak` archives (AuroraForge CAK Foundry) and decode for 2-3 known wrestlers (Jevon first).
3. **Mapping:** move names -> 2K19 ids (exact, normalised, then family/position/impact table); slot roles 2K26 -> 2K19.
4. **One wrestler end to end**, then generalise into `tools/movesets/translate.py`.

## 1. 2K19 `.moveset` layout (solved)
- 3464 bytes. The field order and every padding block come from the Data Editor 2k19 (Java; the jar is embedded in
  `Data Editor.exe` after the PE stub). `DataEditorPopulateMovesetData_2k19` reads sequentially with a running offset;
  the padding arrays' lengths are in `DataEditor.<clinit>`. Simulated with javap bytecode (no decompiler needed):
  `tools/movesets/layout_2k19.json` (726 fields, 368 move slots; the trailing 700 bytes after 0xACC are not read by that routine).
- Move ids are **big-endian u16**; 5094 names in `MovesID.data` (Modded list; Original has 5054).
- Validation: 97% of move slots valid across the 303 template movesets; AJ Styles and Aleister Black decode to their real moves.
- `tools/movesets/moveset19.py` reads/writes slots by name.

## 2. 2K26 side: archives readable from the shell (2026-11-19)
- AuroraForge NT100 ships its full source (GPL-3.0). Its `cak-reader.js` runs under node on the PC; payload
  decoding is ported to Python (`tools/cak26/`). All 15 archives indexed (410,627 files); 218/218 test files decode.
- Game tables are FlatBuffers `.jsfb` with a 4-char file id. **Per-wrestler movesets are in `bakedfile02`, the small
  unnamed archive:** `Char` (6.15 MB, file 204) = CharMoveSetDataTable (AuroraForge documents the 2K25 layout: one record
  per wrestler id, ~354 move slots, each slot -> a string-db name id). Also there: `CMov` (3.76 MB, file 179, likely the move
  catalog), `MoveData/AttackData.jsfb` (`CAtt`), `GhostWriter/Common/MoveSlotPresets.jsfb`, `CAM/MoveData.jsfb`.

## 3. 2K26 CharMoveSetDataTable decoded; move ids carry over from 2K19 (2026-11-19)
- `Char` table (bakedfile02 file 204): root f0 -> vector of **789 wrestler records** (f0 = u16 wrestler id = the
  `Characters/<id>_Name` folder id, f1 -> wrapper); wrapper f0 -> vector of **358 slot tables**; slot table f0 = **u16 move id**
  (f4 -> optional small sub-table, 4 of 358 slots use it).
- **2K26 move ids are 2K19 move ids, byte-swapped** (the Data Editor stores them big-endian). 4,124 of the 5,615 distinct ids used
  across the 2K26 roster exist in the 2K19 move list; Jevon: 217 of 265 filled slots map directly (Superkick, Blue Thunder Bomb,
  Springboard Cutter, Sit-Out Powerbomb, ...).
- **Slot roles** learned by voting: 117 wrestlers exist in both games (2K19 template movesets x 2K26 roster); each filled 2K26 slot
  votes for the 2K19 slot holding the same move. 294/358 slots get a role (`tools/movesets/slot_roles_2k26.json`: slot ->
  [2K19 field, votes, wrestlers with that slot filled]). E.g. 33/34 signatures, 40/41 finishers, 38/45 ringside sig/fin,
  18-21 front strong grapples, 28-31 rear strong grapples, 0-7 strikes.
- Game data stays out of git: decoded tables live in `D:\Pictures\WWE 2K19\A - Resources\2K26 Extracted\`.

## 4. First translation: Jevon Evans (2026-11-19)
- Move catalog `CMov` (bakedfile02 file 179): 8,161 named moves (record f0 = name, f1 = u16 id). Jevon's 2K26 finisher id
  0xB2DC = "OG Cutter 1"; his other moves with no 2K19 id now have names (Trouble In Paradise, Ripcord Spanish Fly, ...).
- `tools/movesets/translate.py`: base = the 2K19 template sharing the most moves (Jevon: Kofi Kingston '12); 2K26 slots
  written to learned roles in confidence order; moves without a 2K19 id -> `overrides.json` (curated) else closest 2K19 name
  (token match, move-type word weighted), all flagged in the report. Jevon: 233 slots set, 22 not placed.
- `decode26.py` rebuilds `char_movesets.json` / `move_catalog26.json` from the two decoded tables.
- Output `jevon_evans_v1.moveset` + `.report.md`. Note: the base template's non-move data (entrance etc.) comes along; Matthew injects.
- **v2 (Jevon):** overrides for Crossface 2 - escape -> Crossface, Springboard Enziguiri -> Handspring Enzuigiri, Gamenigiri 2 ->
  Gamengiri; 2K26-only taunts -> generic 2K19 taunts (Puma -> Crowd Approval 1, Jackrabbit -> Bring It On 1/2, LFG -> Arms Spread 1),
  replacing Kofi's personal taunts from the base. Displaced moves (valid move, role taken) get a second pass into a FREE slot of the
  same kind only (taunt/move, strike/grapple/running, springboard/diving, top/middle rope, standing/downed, front/rear, corner/apron/
  ringside/ground/seated/kneeling must all match), since 2K19 animations are tied to the slot's category. Result: 241 set; 14 not placed
  = 5 duplicates + 9 variants with no free compatible slot (2K19 has fewer corner-springboard / middle-rope / corner-running slots).
