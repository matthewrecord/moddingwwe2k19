# Backport test 10: Psycho Clown (2K26), 2026-11-19

Source: `2K26 Extracted\Characters\1505_Psycho_Clown` (default). Config `psycho_clown` (male template, source weights, geom hide).
Delivered: `Downloads\psycho_clown_v1_ch50602.pac` (+ `_moddingwwe2k19_builds\backport\test10_psycho_clown\`).

## Mask approach
Existing 2K19 masked ports (Mistico `ch34202` in mods/CCT; Pentagon `ch50702`, Fenix `ch33102`) carry the mask as an extra
gear object in the main model. Our builder writes the template's fixed objects, so the mask (M_Mask, 4,739 v, incl. the wig)
goes on the **head-locked hair slot 0x2715** with its real colour texture + alpha cutout (`texconv.hair_color`; used when a stem has no `_rai`).
- 2K19 face animation = head morphs (+ face bones); a head-locked mask doesn't follow them, so skin would poke through
  (119 morphs, up to 2.9 cm, measured by the new gate `maskpoke.py`).
- `mask='M_Mask'`: head vertices covered by the mask (ray within 4 cm; 3,093 of 4,037) are recessed by 0.3 cm (feathered to 0 over 1 cm toward the
  openings; none within 1.5 cm of the eyeballs), and every morph's outward push is clamped to the head-mask gap. After that: 0 morphs poke, J_Jaw ±22°: 0.
- M_Mask_FaceOnly (alternate face-plate variant) and the S_* meshes (cloth-sim proxies, no UVs) are not used.

## Other new handling
- `alpha_cut=['jacket']`: the 2K19 gear shader is opaque, so jacket triangles in fully transparent texture areas (the fringe gaps) are dropped (2,735).
- Attire source weights: the 2K26 bone `vector` (no ancestor in 2K19) used to fall back to J_Head, which left the armbands hanging in the air as "wings" in bodypose.
  Now unmapped bones are dropped and renormalised; vertices left with no weight take the nearest weighted vertex's skin (286).

## Slots
armbands atlas (L/R_A_Acce) · bottoms · shoes · r_elbowpad slot = jacket · l_kneepad slot = tops · hair 0x2715 = mask+wig.

## Gates (all pass)
preview clean · bodypose: no wings · morphgrid: clean in visible areas (notches only on skin under the mask) · eyegaze: drift 0,
vergence -0.3°, poke 1-2 verts (identical without the mask step, so it comes from the source model) · maskpoke: 0 · jaw: clean.

## Watch in game
Wig/mask alpha edges, the mask's mouth area during promos, fringe gaps on the jacket.

## v1 in game: no crash; speckled surface (BC7 normal fix, see test 9 v2); jacket is entrance-only → v2
- `psycho_clown_ring` (`psycho_clown_v2_ch50602.pac`): no jacket; the shirt is the top layer.
- `psycho_clown_entrance` (`psycho_clown_v2_ch50604.pac`): with the jacket.
Gates pass for both (maskpoke 0).
