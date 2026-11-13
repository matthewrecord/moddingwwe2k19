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

## Next (triage order)
1. Find the template: compare port weights against stock 2K19 male and female bodies in the game folder (pick a few
   ch pacs). If a stock body matches, the weight step is fully deterministic.
2. Decode the remaining JBOY parts needed for writing: index buffers (object field [39]), materials/texture table,
   morph names (header 0x48). Also the texture pack block (`*_a_hairl0_n` names) and the small tables (3,056 B,
   about 119 KB `yM_*`, M_Body mask).
3. Texture rule: diff his texture pack against the original PBR DDS set (color/nrm/flow/rai -> 2K19 maps).
4. Then the prototype pipeline on one pair (Fletcher), round-tripping through our own writer, before any app work.
Model files stay in the workspace (`/home/claude/pairs`, `/home/claude/ext`; re-stage from Matthew's
Paired Ports folder if the environment was reset). Never commit them.
