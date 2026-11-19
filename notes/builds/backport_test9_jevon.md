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

## v1 in game (2026-11-19): no crash. Slimy/speckled surface, rigid dreads, loose-looking knees → v2
- **Speckle (all 2K26 ports):** the extracted `_nrm` maps are **BC7 data under a DXT5 header**; decoded as DXT5 they are noise,
  which became noisy normals + gloss. `texconv.load` now detects a noisy DXT5 decode and re-decodes as BC7. 2K26 `_nrm` is a pure
  tangent normal (B = z, no gloss/metal), so `load_pair` sets the 2K24-style gloss channel to a constant 124 (median of Kyle's) and metal 0.
- **Dreads:** 2K19 moving hair = a hair model with its own skeleton (J_Head + 295 `Hair_b*` bones) driven by the **0x2580** sim block
  (Roman 432 KB, Seth 564 KB; Andrade/Fletcher only 2 KB). `hair_physics='ch36902'` (Seth Rollins: closest hair volume, nn median 1.0 cm):
  his hair JBOY becomes the 0x2715 template (obj1 `yDefault` = physics proxy, kept), his 0x2580 replaces ours, and each dread vertex
  copies the skin of the nearest Seth hair vertex (260 bones used, J_Head 47%). Can't be simulated on the bench: in-game check needed.
- **Knees:** the kneepads now take the 2K19 body donor's weights (`donor_weights`), not 2K26's helper-bone mix (H_Hip_L_OS1 9% at the knee).
  Tights and shoes stay on source weights (on donor weights they tore behind the knee in the squat).
Delivered `jevon_v2_ch50602.pac`. Gates pass.

## v2 in game: surface and knees fixed; the Seth-rig dreads look wrong; the shirt is entrance-only → v3
- Scanned all `mods/CCT/characters/pac/ch/ch*02.pac` for physics hair (count of `Hair_b` in 0x2715, size of 0x2580; device script `hairscan.py`):
  80 mods have it. Long dark candidates rendered on Jevon's head: Ortiz 453, Sonny Kiss 968, **Hikuleo 397**, Rush 992, Lio Rush 805, Red Velvet 467.
- `hair_from=<pac>`: Hikuleo's (`ch39702`) **whole hair** (JBOY 0x2715 byte-for-byte except vertex positions + his 0x2580 + `hair`/`hair_n`
  textures). It's fitted to Jevon's scalp by a radial correspondence offset (scalp gap median 0.7 cm, max 2.5).
- Bench limitation: Hikuleo's hair skin slots are stored in a layout `pose.skin` doesn't decode (0xFF00/0x0200), so in bodypose
  the hair collapses to a line from the hips to the floor. The donor file is identical and works in game.
- Ring (`jevon_ring`, ch50602): no tank top. Entrance (`jevon_entrance`, ch50604): with it.
Delivered `jevon_v3_ch50602.pac`, `jevon_v3_ch50604.pac`.
