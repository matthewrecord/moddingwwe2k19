# Backport test 9: JeVon Evans (2K26), 2026-11-19

First 2K26 port. Source: `D:\Pictures\WWE 2K19\A - Resources\2K26 Extracted\Characters\1235_JeVon_Evans` (default model + attire).
Config `jevon` in `tools/backport/build_port.py` (male template, `weights='source'`, `hide='geom'`, `eye_straighten_deg=0.5`).
Delivered: `Downloads\jevon_v1_ch50602.pac` and `_moddingwwe2k19_builds\backport\test9_jevon\` (EMD 00050602; Matthew injects it himself).

## 2K26 format changes handled
- `.mcd` = `MCD!` wrapper with chunks; the MDL file starts at `MDL!MDL!`+4 (base model has a `CTG!` chunk first). `open_model` searches for it.
- MDL version 0x2f: LOD0 has the 2K25 layout; LOD1+ records carry an extra field (not decoded). `mdlfmt.lods()` reads LOD0 only for >= 0x2f.
- `HPL!` is embedded in the attire `.mcd` (`HPL!HPL!` then `LOD!` blocks). A mesh appears several times per LOD (unioned in `hpl.parse`).
- **The 2K26 attire HPL indices do NOT fit the character's own M_Body**: sorted lists up to 11613 that spread over the whole body,
  including the hands and feet, so they most likely index the game's generic body. Using them hid both arms (v1 first render).
  → new `hide='geom'`: a body vertex is hidden when its normal ray (stored NORMAL stream; computed normals point inward on 2K26)
  hits a cover mesh within 8 cm; a triangle is hidden when all 3 vertices are. Jevon: 6,921 verts; upper 3,730 / lower tris hidden.
- Textures: same `_color`/`_nrm`/`_rai` names and DXT1/DXT5 as 2K24; unused `_flow`, `head_flush`, `CAS/headhair_mask`.
- 2 attire vertices without source weights (`M_R_A_Acce`/atlas) → now take the nearest weighted vertex (`attire_unweighted_fixed`).

## Slots
necklace = atlas (U_Acce chain, Pierce, R_A_Acce); l/r_wrist; bottoms = Tights; shoes; r_elbowpad slot = Tops; l/r_kneepad.
Hair 0x2715 = M_Hair (dreads, 8,852 v, tint 28/21/17); 0x2716 = M_Combinations (beard). S_Hair (scalp shell) left out; the head texture already carries the hairline.

## Gates (all pass)
preview: misaligned none, unweighted none, eye masks ok · facecheck: matches source at rest · morphgrid: clean ·
bodypose: no wings or spikes · eyemorphs: lids close like the donor · eyegaze: drift 0.00, vergence 0.2° (was 1.7° before straightening), poke ≤ 0 ·
jaw (new `jawtest.py`): no spikes. Renders: `notes/builds/renders/jevon/`.

## Open
Awaiting in-game check. Watch: the shirt/tights hide edges (geom hide), dreads clipping the shoulders (rigid hair), the chain.
