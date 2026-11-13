# Handoff 015: backport tool, feasibility test done (2026-11-12 night)

Branch `claude/backport-tool` (not merged: no game-facing change, nothing installed). Full findings: `writeup/Backport.md`.

## Done
- Inventoried the 4 pairs. The originals are 2K22+ **community mod files** (`.mdl/.mtls/.hpl/.ctg/.ycl` + DDS: Gabe,
  Fletcher, Willow from 2K24, O-Khan from 2K23). The ports are 2K19 EPK8 pacs (zlib -> JBOY + texture pack + tables).
- Wrote both readers from scratch (no community tool is open): `tools/backport/mdl.py` (byte-exact on all 8 files),
  `tools/backport/jboy.py` (all 27 JBOYs in the 6 port pacs; skin palette at header 0x50).
- Bone map and weights: see Backport.md section 5. **Key result: his body weights come from a fixed 2K19 template**
  (male ports predict each other at about 90% dominant-bone agreement, median error 0). A naive name copy gets
  75-79%. 2K19 allows 7 influences.

## Matthew's answers (2026-11-12 22:58)
- Chat logs with scorpionxxx exist but don't describe his process. He has no other files.
- Python is installed on his PC; Blender is not. The app can depend on Python only.
- **No new tools for Matthew, ever.** He owns only 2K19 and won't learn newer formats: our own readers cover that.
- The 2K19 game is at `D:\SteamLibrary\steamapps\common\WWE 2K19` (hundreds of stock chXXXX pacs).

## Later the same night (after Matthew: "keep working, no hand-holding")
- Stock pacs = HSPC + Oodle (pyooz). His ports = EPK8 + zlib. Stock skin indices are byte-swapped.
- **Templates found:** men = stock ch68702 (Andrade "Cien" Almas): same palette, yM table, block 5, weights 83-88%.
  Women = stock ch75602 (84.7%). The 3,056-byte block comes from a similar-build stock wrestler (Gabe <- ch23802 Big
  Boss Man, Willow <- ch62902 Nia Jax).
- Port composition: 2K24 body/attire/hair + grafted stock face parts (eye overlay 194, mouth 1,974, part 341, head
  base merged into the head object) + 17 vertices at the origin.
- Triangles = strips (decoded). Textures: recipe recovered (Backport.md section 8); hair tint is hand-picked.
  Materials: per-shader templates (section 9).
- Tools on Matthew's PC: `$HOME/bp` in the device shell holds sig.py/blk.py/jboy.py (session scratch; recreate from
  tools/backport if gone). Results copy: game folder `_moddingwwe2k19_builds\backport\stock_sigs.jsonl`.

## Status at ~01:45 (2026-11-13)
- JBOY fully mapped (Backport.md section 12): vertices -> morph targets (119 x vc x 28, offsets) -> skin -> UV -> UV2 ->
  vc x 4 buffer -> strip header/indices -> parameter list/records; global tables at the end.
- Face: every head vertex (2K24 ones included) has 119 regenerated morph offsets. They aren't from any of the 333
  superstar heads (best relative error 0.48; linear fit 0.37). CAW head (pac/edit/head) is a new tree format: an
  open lead, off the critical path.

## Next (triage order)
1. **Writer**, starting from the donor pac (ch68702): first a byte-identical JBOY round trip (parse every section
   and pointer, rebuild), then swap geometry, skin, UV, strips, materials and texture pack. Then EPK8/zlib packing like
   his ports, or HSPC/Oodle like stock. Test by rebuilding one of his ports from its parsed parts.
2. Face: surface-based transfer of the 119 morph offsets from a 2K19 head (donor ch687 or best match) onto the
   2K24 head; graft and fit the stock eye overlay / mouth / 341-vertex part / head base to the 2K24 head (study how he
   moved them: 1-3 cm per vertex).
3. Identify block 2 (3,056 B) and the M_Body table (block 4); check eyes/eyelash textures.
4. First in-game test (needs Matthew): install a rebuilt Fletcher in a test slot.

## 2026-11-13 00:00-01:00 local (Matthew: "please go")
- Face experiments (Backport.md sections 19 and the design note): his 119 shapes aren't reproducible from any stock
  head (best relative error 0.52, unfitted barycentric from ch73304), and the CAW head has only 30 sculpt shapes, so his
  source is unknown. Decided design: barycentric transfer from the best-fitting stock head + stock interior parts
  warped by landmarks; expressions reviewed in the app.
- **Test 1 (Willow slot 865, Genesis) is still installed and waiting on Matthew's in-game check** (backup in builds folder).

## Next (triage order, updated)
1. Full Fletcher build on the donor ch68702 (body, head with transferred morphs, interior parts, attire, hair,
   textures with our encoder) -> test pac for a free slot.
2. DXT5 encoder (texture writer) + texture pack writer; stripifier polish.
3. Identify block 2 (3,056 B) / block 4 (M_Body table).
