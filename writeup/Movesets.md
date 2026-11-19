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
