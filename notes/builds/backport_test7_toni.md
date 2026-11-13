# Backport test 7: Toni Storm, Revolution '25 (2K25, BANbantam), 2026-11-13
The first female port. The mod has 3 variants (standard, facepaint, B&W); v1 is the standard one.

## New: templates
The builder now takes a container/donor/reference template (see the README).
The female template (Willow port + ch75602 + Willow 2K24 original) differs from the male one in:
- separate hands;
- the eye/overlay/mouth object indices;
- a lip-ring object to collapse (with its morph sets);
- one hair slot;
- an eyelash model with blink morphs;
- hide blocks for objects 1 and 3.

The hide-table writer is now general (`build_blocks`, byte round-trip on both containers). Briscoe and Flash rebuild
byte-identical with the template builder.

## Toni v1 assignments
- Hair: 2× M_Hair + M_Hair2, 17,531 vertices in slot 0x2715 with a 2-tile rai atlas (hair, hair2). Tint (232,214,178).
  S_Hair and M_Lambert1 (120-vertex cards) are skipped.
- Eyelashes: her own M_transB_eyelash. Morphs and skin come from the built head (max distance 0.99 cm). Colour from eyelash_color.
- Attire:
  - outfit -> 0x5602/0;
  - tights -> nets (0x5601/3);
  - shoes -> 0x5601/4;
  - tape split L/R -> l_wrist/r_wrist;
  - belt + rose + nails share a 2x2 atlas in the brassiere slot (0x5601/0);
  - the rose takes head weights (274 vertices).
- Gates:
  - Alignment and weights: no misaligned chunks, no unweighted vertices.
  - Expressions (`renders/ts1_morphs.png`, vs donor ch75602) and source vs build face (`ts1_srcvs.png`): pass.
  - Blink and jaw (`ts1_blink_jaw.png`): pass.
  - Textured body (`ts1_check.png`): pass.
- Preview fixes: hide blocks are parsed generally (the female layout had hidden the hands in the preview), and trans
  objects use an alpha test.

## v1 in game: "extremely impressive, almost perfect". Too-dark under the eyes; cross-eyed again. v2
- **Cross-eyed.** The eyeballs sat 0.5 cm inside, 1.0 cm below and 0.5 cm behind the J_Eye pivots, so turning the eyes
  slid them 0.3-0.35 cm in their sockets.
  - Fix: J_Eye bones moved to the eyeball sphere centres (`move_bones`, true bone positions via `bone_world`).
  - New gate `eyegaze.py` (requested by Matthew). v1: drift 0.35 cm. v2: drift 0.00 (`renders/toni_gaze_cmp.png`).
  - Control build `toni_v2b_nopivot`, in case the game keeps a separate eye rest pose.
- **Dark under the eyes.** It is not the eye overlay (`renders/ts_ov.png`: the overlay sits inside the openings, and the
  same texture is used in both containers). It is the source's own smoky makeup. `undereye_lighten=0.45` blends the
  under-eye band toward the cheek colour (`renders/ts_undereye.png`).
- `pose.py` now rotates about true bone positions (it previously used the +64 bounding-sphere field).
