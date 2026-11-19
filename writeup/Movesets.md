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
