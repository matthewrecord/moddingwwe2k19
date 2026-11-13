# Backport tool: newer WWE 2K mods (2K24 `.mdl` / 2K25 `.mcd`) into WWE 2K19

Status (2026-11-13): Keith Lee (2K24, big body, source weights) is built and passes all gates. Validated in game on **Flash Morgan Webster (2K25)** and **Mark Briscoe (2K24)**. The first female, **Toni Storm (2K25)**, is built and passes every bench gate; awaiting an in-game test. Both are
from-scratch ports with no porter involved. Findings are in `writeup/Backport.md`; per-build notes are in
`notes/builds/backport_test5_fmw_scratch.md` and `backport_test6_briscoe.md`.

## Templates (container + donor + reference), picked by `cfg['template']`
| | male | female |
|---|---|---|
| Container | Fletcher port `ch50602.pac` | Willow port `ch50602.pac` |
| Donor (head morphs, body weights) | Andrade ch68702 | stock ch75602 |
| Reference 2K24 original (texture match, mouth-part offsets) | Kyle Fletcher | Willow (969_Doudrop) |
| Main objects | 1 upper, 2 lower; eyes 3/4; overlay 5; mouth 6/7/8 | 1 upper, 2 hands (abs(x) > 66), 3 lower; eyes 4/5; overlay 6; mouth 7/8/9; obj 10 (lip ring) collapsed |
| Hair slots | 0x2715 hair, 0x2716 hair2 | 0x2715 hair only (several meshes and textures -> rai atlas) |
| Eyelashes | none | 0x4e22: the source's `M_transB_eyelash`, with morphs and skin taken from the built head |
| Hide blocks | objects 1, 2 | objects 1, 3 |
| Attire slots | necklace, l/r_wrist, bottoms, shoes; r_elbowpad, l/r_kneepad | brassiere, l/r_wrist, nets, shoes; outfit, l/r_kneepad |

`hidetable.build_blocks` writes any block layout (it round-trips both containers byte for byte).

## What the builder does (`build_port.py`)
1. **Container:** scorpionxxx's Kyle Fletcher port `ch50602.pac` (male, Andrade ch68702 palette; his 0x50/0xCA/0x2580
   blocks; EMD 50602). Every model in it is rewritten.
2. **Head:** the source's own `M_Head` mesh. Andrade's head (3,936 vertices, 119 morphs) is fitted onto it
   (`facefit.fit_welded`, cached as `<work>/fit_W.npy`). Morphs and skin are then carried from the fitted surface to
   each source vertex. Lip handling:
   - lip classes by surface distance from clear upper/lower seeds (`lip_class_topo`);
   - the transfer may not borrow from the opposite lip;
   - morph offsets are smoothed on the welded mesh in the lip zone, blocking only upper/lower edges across the central
     75% of the mouth (corners stay joined);
   - bridge triangles behind the lips are dropped;
   - vertices left unweighted take the nearest weighted vertex's skin;
   - neck-seam vertices take the body's weights.
3. **Body weights:** `cfg['weights']='source'` uses the mod's own BI/BW, remapped to 2K19 palette slots by bone name
   (a missing bone hands its weight to its nearest ancestor that exists; for Keith, 99% of the weight is on shared names).
   The default is still the donor's nearest-point weights, which fail for big bodies (Keith v1: shoulder wings, knee spike).
   **Recommended for every new character.** Big builds also take `prop_from` (the 0x50 proportion block of a similar
   stock wrestler, e.g. ch23802 Big Boss Man), as scorpion does; the skeleton itself is identical in his big-man ports.
   Body: `M_Body` split upper/lower (triangle centroid y < -108 or |x| > 26 = upper). Weights come from the body-only
   Andrade donor, welded by position and outlier-smoothed. Triangles are ordered hidden-first so each hide range is one span.
4. **Eyes:** the source's own `M_EYE`, rigid on J_Eye_L/R. Eye overlay and mouth parts (teeth, tongue, mouth piece) are
   his Fletcher objects, shifted by the source-minus-Kyle part centroids.
5. **Hair:** slot 0x2715 = hair (or one hidden triangle if bald); 0x2716 = beard/second hair. Rigid to the head, as in
   stock. Textures come from `<stem>_rai` with a tint.
6. **Attire:** 8 slots (0x5601: 0 necklace, 1 l_wrist, 2 r_wrist, 3 bottoms, 4 shoes; 0x5602: 0 r_elbowpad,
   1 l_kneepad, 2 r_kneepad).
   - Each slot takes one mesh, one side of a mesh ('L'/'R'), or a **2x2 atlas** of up to 4 meshes (1024 px tiles,
     UVs inset 8 px).
   - Unused slots get one hidden triangle.
   - Attire points nearest the head take head weights (hats, bandanas).
7. **Hide table:** `.hpl` (`hpl.py`). A body triangle is hidden if any of its vertices is listed, or if all its vertices
   are within 1 cm of the meshes listed in `cover`.
8. **Textures:**
   - The 2K24 rules: `<mat>` = colour; `_n` = (255-R, 255-G, 255, 255); `_mr` = (A or 0 for skin, B, 255-B, 255).
   - 4096 maps are cut to 2048.
   - Skin `_nrm` blue is matched to Kyle's distribution.
   - **Resizing is per channel**: PIL premultiplies RGBA, which zeroes RGB where alpha = 0, and 2K24/25 normal maps have alpha 0.
9. **Eye pivots (default on, `eye_pivots`):** J_Eye_L/R are moved to the eyeball sphere centres in every model that
   carries them. Bone position = chained local t/r from the root (extrinsic xyz Euler; `bone_world`). The record field at
   +64 is a bounding sphere, not the bone position. The +64 centre is moved by the same delta.
10. **Eyes (lessons from Toni):**
    - Only the eye *colour* comes from the source. `eye_n` and `eye_mr` stay the container's: the 2K19 eye shader uses
      the `eye_n` alpha as an iris mask (iris depth, `g_fEyePa`) and `eye_mr` as a cornea/sclera gloss mask. 2K24/25 eye
      maps are flat there, which gives "dead", unfocused eyes.
    - Eyeballs whose forward axis is more than 2° off straight ahead are turned forward about their centre (iterated;
      Flash was 5.4° wall-eyed). The forward axis runs from the eyeball centre to the cornea-cap centroid.
    - The eyelid split transfer exists (`lid_split`) but is off by default: the plain transfer already matches the donor's lid motion within 0.01 cm.
11. **Optional `undereye_lighten`:** blends the band below the eyes in the head texture toward the cheek colour (2K25/24
    makeup reads heavier under 2K19 lighting).
12. **Writing:** `jbuild` keeps every chunk at its original address mod 16 (the hair crash). `epkwrite` writes EPK8 + ZLIB +
   the EOP5 footer.

## Porting a new character
1. Unzip the mod into `/home/claude/pairs/<NAME>/` (it should contain `BaseModel/` and `<n>_Default_Attire/`).
2. Inventory its meshes and textures (snippet in `notes/builds/backport_test6_briscoe.md`, or `mdlfmt.MDL(path).meshes`).
3. Add a config dict at the bottom of `build_port.py` (copy `BRISCOE` or `FLASH`) and register it in `CONFIGS`:
   `base`, `attire_model`, `tex_base`, `tex_attire`, `hpl`, `cover` (attire meshes that hide skin), `hair`, `tint`, and
   `attire` slot assignments.
   - Use 'atlas' when there are more pieces than slots.
   - A female character: `template='female'` (ch75602 donor / Willow port container; see TONI).
   - Big or unusual bodies: `weights='source'` (the mod's own skin weights, remapped by bone name) and `prop_from='<stock pac>'` for body proportions (see KEITH). Recommended for every new character.
   - Separate ring and entrance attires: two configs on the same base, each with `emd='000506NN'` (slot name written into the header); the ring config drops the jacket from `attire` and `cover` (see KEITH_RING / KEITH_ENT). Install as attire 02 and 04.
4. Build: `python3 -I tools/backport/build_port.py <config> /home/claude/out/<name>_v1_ch50602.pac`. This takes about
   20 s, plus a few minutes once for the head fit.
5. **Bench gates (all must pass before handing a build to Matthew):**
   - `python3 -I tools/backport/preview.py <pac> <outprefix>` prints `misaligned: none` and `unweighted vertices: none`,
     and writes textured front/back/left/face/mouth renders. Look at every one.
   - Source vs build textured face (see `facecheck.py`, or the snippet in the Briscoe notes): at rest they must match.
   - `python3 -I tools/backport/morphgrid.py <pac> <out.png>`: the 12 mouth morphs, stock Andrade vs ours. There must be
     no curtains, tears or spikes.
   - **Body pose test**: `bodypose.py <pac> <out.png>` (arms down, elbows bent, arms forward, squat; hierarchical
     `pose.pose_fk`). There must be no skin left behind (shoulder "wings"), no smeared sleeves and no knee spikes.
   - `preview.py` also prints **`eye masks: ok`**. FLAT means dead eyes (see "Eyes" below).
   - **Eye/brow morphs**: `eyemorphs.py <pac> <out.png> <donor>` (add `--lashes` to draw lashes). The lids must close
     like the donor's. Never judge lid closure with the lashes drawn: opaque lashes in the flat renderer look like half-closed lids.
   - **Eye gaze test**: `python3 -I tools/backport/eyegaze.py <pac> <out.png>` aims both eyes together (left/right
     25°, up/down 15°, as the game does) and renders each. Gates: **drift ≈ 0** (the eyeball turns in place: J_Eye pivot
     on the eyeball centre), **vergence ≈ 0** (the lines of sight stay parallel), **poke ≤ ~0** (no eyeball pushed through
     the lids beyond rest).
   - Female: lash blink check (head + lash under the strongest eyelid morph; lashes must close with the lid).
   - Jaw test with `pose.py` (rotate J_Jaw 15° plus morph 114 at 0.6, front and side): no spikes.
6. Commit the notes and renders, then deliver to
   `D:\SteamLibrary\steamapps\common\WWE 2K19 - modded\_moddingwwe2k19_builds\backport\<testN_name>\`.
   Matthew installs it in slot ch50602, backing up first.

## Inputs the tools expect (not in git)
- Stock 2K19 pacs staged from the game: `/mnt/user-data/uploads/WWE 2K19 - modded/pac/ch/ch68702.pac` (Andrade donor).
- The Fletcher port pac and the Kyle Fletcher 2K24 original (texture and mouth-part reference) unpacked under
  `/home/claude/pairs/` (from `D:\Pictures\WWE 2K19\A - Resources\Paired Ports`).
- Python packages: numpy, scipy, pillow, matplotlib, etcpak, pyooz (`ooz`), libarchive-c.

## Module map
| Module | Purpose |
|---|---|
| `mdlfmt` | 2K22-2K25 MDL reader (v0x28 and v0x29) |
| `hpl` | `.hpl` hide lists |
| `jboy` | 2K19 JBOY reader |
| `jbuild` | object-level JBOY writer |
| `jlayout` | JBOY region layout |
| `pof0` | pointer table |
| `epkwrite` | pac container |
| `oodl` | stock pac reader |
| `epk` | pac container (read side) |
| `texconv` | texture conversion and pack |
| `facefit` | head fitting |
| `facexfer` | closest-point / barycentric transfer |
| `loops` | boundary loops |
| `regen_full` | mesh/weight helpers |
| `build_fmw` | shared helpers and the Flash v4 builder |
| `build_port` | general builder + configs |
| `render` | flat renderer |
| `preview` | textured pac preview + gates |
| `facecheck` | textured source-vs-build faces |
| `pose` | offline skinning/morph posing |
| `morphgrid` | mouth morph comparison |
| `eyemorphs` | eye/brow morph comparison (gate) |
| `eyegaze` | eye gaze stress test (gate) |
| `lidcheck` | lid closure % per eye-closing morph |
| `bodypose` | body pose stress test (gate) |
| `eyepatch` | straighten eyes + move eye pivots on an EXISTING pac (any port) |
| `hidetable` | block 0xCE hide table read/build |
| `jcheck` | compare a written object against port conventions |
| `jwrite` | relocating JBOY writer (v2, superseded by jbuild) |
| `texrule`, `texcmp`, `texpack` | texture rule derivation / comparison / pack parse (research) |
| `sig`, `tmpl`, `check2`, `bonemap`, `pairs` | weight-template and bone-map research (how the donor-weight approach was chosen) |
| `mdl`, `mdl1`, `mdl2`, `mdlpeek`, `face_scan` | early MDL format reverse-engineering (superseded by `mdlfmt`) |
| `build_fletcher`, `build_fmw`, `build_fmw_v2`, `fmw_hairfix`, `regen`, `regen_full`, `build_port_pre_templates` | earlier builders kept for history; `build_fmw` still supplies shared helpers |

## Patching an existing pac (no rebuild)
`python3 -I eyepatch.py IN.pac OUT.pac` turns each eyeball about its own centre until it faces straight ahead and moves J_Eye_L/R to the eyeball centres in every JBOY. Use it on older ports with wall-eyed/cross-eyed or "dead" stares, then run `eyegaze.py` (vergence and drift must be ≈ 0) and `preview.py`. Works on pacs with uncompressed blocks (older ports store some raw).

## Builder rules added per character (each one permanent)
Flash: alignment mod 16, per-channel texture resize. Briscoe: topological lip split, head-nearest attire weights, unweighted-vertex fix. Toni: female template, eye straightening, eye pivots, keep container eye masks, undereye lighten. Keith: source weights, proportions block, `cap_small_holes` (pinholes of light), `emd` ring/entrance split. Old Keith: `eyepatch.py`.

## Open items
- Beards are rigid (stock behaviour). An extreme open mouth shows the chin moving behind the beard.
- The atlas halves resolution for the pieces it packs.
- Older builds (Flash, Briscoe) use donor weights; a rebuild with `weights='source'` may improve them (untested in game).
- Keith v3 and the old-Keith eye patch await in-game confirmation.
- Next: a simple app for Matthew (preview, flagged problems, simple fixes, export).
