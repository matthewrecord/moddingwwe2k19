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

## Next (triage order)
1. **Writer**, starting from the donor pac (ch68702): first a byte-identical JBOY round trip (parse every section
   and pointer, rebuild), then swap geometry, skin, UV, strips, materials and texture pack. Then EPK8/zlib packing like
   his ports, or HSPC/Oodle like stock. Test by rebuilding one of his ports from its parsed parts.
2. Face graft: fit the stock eye overlay / mouth / 341-vertex part / head base to the 2K24 head (study how he
   moved them: 1-3 cm per vertex).
3. Identify block 2 (3,056 B) and the M_Body table (block 4); check eyes/eyelash textures.
4. First in-game test (needs Matthew): install a rebuilt Fletcher in a test slot.
