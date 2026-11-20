# Backport test 13: Raquel Rodriguez (2K26 927) and Tatum Paxley (2K26 1216), 2026-11-20

Both use the female template, source weights, geom hide, lid_fit, Paige ch43402 physics hair and
`hair_body_blend` (-180..-160, d 12→3, smooth 100). Ring is `_ch50602`, entrance `_ch50604`.

## Raquel (`raquel_ring` / `raquel_entrance`)
| Slot | Contents |
|---|---|
| 0x5602,0 | M_Outfit (full-body suit) |
| 0x5601,2 | R wrist |
| 0x5601,4 | boots |
| 0x5601,0 atlas | L_A_Acce (arm sleeve); the entrance adds M_Glasses (sunglasses) |

- Hair: Paige fit med 1.2 / p90 2.8 cm; tint 38/26/20 (dark brown).
- `eye_recess` 0.15: 0.05 left 1-2 poke verts, 0.1 left 1.
- h_acce/h_acce1/h_other textures have no mesh in the attire model, so they're unused.

## Tatum (`tatum_ring` / `tatum_entrance`)
| Slot | Contents |
|---|---|
| 0x5602,0 | brassiere |
| 0x5601,3 | underwear |
| 0x5601,1 | socks |
| 0x5601,4 | shoes |
| 0x5602,1/2 | kneepads (donor weights) |
| 0x5601,0 atlas | U_Acce (chokers) |

- The entrance adds the hoodie M_Jacket (hood down) in 0x5601,2 and swaps to M_Hair_Entrance, which is shaped to sit
  over the jacket. M_HoodUp and M_Hair_CS_Hoodup are not used.
- Hair: Paige fit med 1.4 / p90 3.6 cm; tint 25/22/22.
- Her 2K26 textures came out at 1024 (lower mip priority), so the pac is smaller (10 MB).

## Gates (all four pass)
- preview clean.
- eyegaze: drift 0, vergence -0.3 / -0.7°, poke ≤ 0.
- lidcheck: matches the donor.
- morphgrid, jaw, bodypose, hairswing: clean.

| Build | hairclip (arms down / shrug / fwd / lean) | hairstretch, head turn 45° (p99.9 / max) |
|---|---|---|
| Raquel | 10 / 11 / 15 / 2 (≤1.4 cm) | 1.9 / 2.7 |
| Tatum ring | 1 / 2 / 8 / 3 | 2.1 / 3.9 |
| Tatum entrance | 47 / 62 / 37 / 0 (≤1.4 cm; hair on the hoodie) | 2.4 / 4.2 |

Renders: `notes/builds/renders/raquel`, `notes/builds/renders/tatum`.

## Unconfirmed
Hair colours are guesses (2K26 hair colour comes from CAS data I haven't decoded).

## v2 (same day), after Matthew's in-game test
**Feedback:**
- Tatum: big problems on the legs (spikes near the backs of her knees and on the socks).
- Tatum: the hair comes apart from itself, and the middle clips while the ends don't.
- Raquel: skin and outfit warp ("fluidity") at the upper thighs and hips.

### Causes
1. **Hips and legs moving with the head.** The body's source weights handed the 2K26 rootless cloth bone `vector` to
   J_Head: up to 0.30 J_Head weight on hip and leg vertices, in Raquel, Tatum and Rhea alike.
   - Fix: drop `vector` on the body too, and fill weightless vertices from the nearest weighted body vertex.
2. **2K26 helper bones the 2K19 skeleton lacks** (H_Quad_Jig, H_Knee_Lower, H_Leg_Vol_S/B, `vector`). The old fallback
   gave their weight to the nearest existing ancestor, which put a thigh jiggle bone on J_Hips. That tore the tops of
   Tatum's socks.
   - Fix (`donor_for_missing`, on by default): on hips and legs (y below -125, ramped), blend in the 2K19 donor's skin
     in proportion to the weight share on missing bones.
   - Tatum's socks (mostly cloth-simulated in 2K26) take donor weights outright.
3. **Hair tearing.** Each hair vertex copied its nearest Paige chain, so triangles spanned two chains that move
   independently.
   - Fix: `hair_body_blend(post_smooth=60)` Laplacian-smooths the final hair skin along the strands.
   - The hair-to-body blend now maps the donor's rootless m### helpers to the nearest J_ bone instead of J_Head.

### New gates
- `legstress.py`: hip/leg poses (bend over 90, split 45, knee 120, kick back), counting attire crossing into the body
  and edge stretch.
- `hairtear.py`: random independent chain swings, measuring hair edge stretch.
- `pose.pose_fk` now moves the donor's rootless m### helper bones with the nearest J_ bone, as the game does. Before,
  they stayed at bind pose, so donor-weighted parts looked frozen in the tests.

| Metric | v1 → v2 |
|---|---|
| hairtear, Tatum | p99.9 6.7 → 1.3 (Paige's own hair: 1.1) |
| hairtear, Raquel | 5.8 → 1.3 |
| legstress, Tatum, bend over 90 | stretch max 94 → 16 (the rest is donor m-bone approximation); cross 215 → 113 |
| legstress, Raquel | cross 328/409/120/702 → 32/5/2/516; stretch unchanged (≤2.2 p99.9) |
| hairclip, Raquel | ≤1.6 cm |
| hairclip, Tatum ring | ≤1.2 cm (lean: 2 verts, 2.9 cm) |
| hairclip, Tatum entrance (hoodie) | 81-127 verts ≤1.8 cm |
| eyes, lids | unchanged, pass |

Rhea v2 also has the J_Head-on-legs problem (built before this fix); rebuild it if Matthew sees it.

## v3 (Raquel, Tatum) + Rhea v4, after the second in-game test
**Feedback:**
- Tatum: the hair stayed completely static through her entrance, then clipped through her mid-section in the ring.
- Raquel: you can see through her skin at the sides of her hips.
- Rhea: you can see through her mid-section during her entrance.

### Causes and fixes
- **See-through = hidden body showing through a gap.** The hide table removes body under cover gear. Where the gear's
  skin differs from the body's, the gear drifts off and leaves a hole.
  - `tight_follow` (default 1.5 cm): gear within 1.5-3 cm of the skin on hips and legs takes the skin of the body under
    it, as a barycentric mix of the closest body triangle. Nearest-vertex copy left steps; smoothing those brought the
    crossings back.
  - legstress cross: Raquel 32/0/0/516 (v2 32/5/2/516); Rhea 66/1/0/1026 (v3 72/9/5/1029).
- **Cut-outs and see-through panels in cover gear:** `opaque_cover` drops cover triangles with ≥10% transparent texels
  (24 samples each) from the hide test. Raquel's hip lace panels are dropped, though that freed no body vertices.
- **Rhea's open vest:** removed from the entrance cover list. It swings open, so the body under it must stay drawn.
- **Tatum's entrance hair (static):** the whole M_Hair_Entrance sits within reach of the hoodie, so the body blend held
  all of it.
  - New `a_max` caps the body share. Entrance uses 0.7, so 30% physics always remains.
  - Static twist test: 59 verts up to 8.7 cm; at 0.5 it was 49 verts up to 11.4 cm.
- **Tatum's ring hair (mid-section clip):** the long back hair is now held further down the back (dfull 6, dzero 18 cm).
  Remapping the pelvis bones to J_Spine2 for hair was tried and was worse (lean back 6.8 cm), so it's reverted.
- `hairclip` gained "lean back" and "twist" poses.

### Gates
- All six pass: preview, eyes, lids, morph, jaw, bodypose.
- hairtear 1.18-1.27.
- Rhea's tights show crotch-seam stretch (p99.9 ~6 at knee 120); the body itself has the same seam.

## Raquel v4, Tatum v4, Rhea v5 (third in-game test)
**Feedback:**
- Raquel: black shows through the hip lace where skin should be.
- Tatum: see-through spots on her leg.

**Causes and fixes:**
- **Raquel's lace:** `opaque_cover` dropped the lace triangles (456, 31-55% transparent texels, outer hips/thighs) from
  the hide test. But the body triangles under the lace are bigger than the lace holes, and rays from their corners still
  hit the opaque lace border, so the skin stayed hidden.
  - Fix: body vertices within 3 cm (`seethrough_reach`) of a dropped see-through cover triangle are un-hidden. That frees
    306 vertices on Raquel, 96 on Tatum's ring version, 617 on her entrance and 61 on Rhea.
  - preview now shows skin through Raquel's lace.
- **Tatum's legs:** her socks and kneepads were on donor weights (`donor_weights`), so they didn't take `tight_follow`
  and drifted off the hidden skin. `donor_weights` is now empty, so they follow the body under them.
  - legstress cross: 103/27/85/1087 → 34/0/0/578.

## Raquel v5, Tatum v5 (fourth test: v4 looked identical to v3)
Matthew: no visible difference at all between v3 and v4. That was right: v4 changed only the hide table, and neither
problem was a hiding problem.
- **Raquel's black lace:** M_Outfit has two materials in 2K26, `outfit` and `outfit_ALPHA`, and the lace holes are
  alpha 0. `mats()` forced colour alpha to 255 on every gear texture, so the holes rendered as their RGB, near-black
  (21,20,21). Un-hiding the skin under it changed nothing visible.
  - Fix: new `keep_alpha=[stems]` keeps the colour alpha (Raquel: `outfit`, 4.3% transparent texels) in the 0x5602,0
    yCS_trans slot.
  - **Untested:** it isn't confirmed that yCS_trans alpha-tests in game; no stock texture I found shows it. If the lace
    is still black in game, that shader ignores alpha, and the lace needs a mesh cut (`alpha_cut` at texel level) or
    the hair-shader slot.
- **Tatum's "see-through" sock:** the socks texture is all alpha 255. The dark brown vertical stripes (51% of texels,
  ~(66,36,30)) are sheer fabric in 2K26, made by the shader. In 2K19 they render as solid dark bands that read like
  holes.
  - Fix: new `sheer={stem:(rgb,tol,mix)}` paints 60% of the body's median skin colour into those texels.
- **Lesson:** check textures and material splits (`_ALPHA` materials, sheer shader params) before hide or weights when
  something "shows through".

## Replication attempt (after v5): not reproduced
Matthew: possibly fixed in the ring attire, definitely not in the entrance attire, and no more in-game tests until I can
reproduce both glitches offline.

**New tool:** `gamerender.py`, a per-pixel rasteriser that uses the pac's own textures.
- It applies the hide table, alpha-tests yCS_trans/yCS_hair (`--trans-opaque` to turn that off), and culls back faces.
- 2K19 stores normals negated, stock bodies included, so back-facing = (-N)·view > 0.

**Findings:**
- Raquel: the lace is real geometry (strings), and the gaps between them show the body in every build (v3 to v5),
  with or without alpha-test.
  - The 0xCE hide table is identical in the ring and entrance pacs, and the body under the lace is not hidden in either.
  - So the offline model predicts skin, while the game shows black in the entrance. The mechanism is not reproduced.
- Tatum v5 entrance: no holes on the thigh sock offline.
- Ruled out:
  - 0xCE differences between ring and entrance (identical).
  - Outfit alpha in the entrance pac (kept, 4.3%).
  - Dark baked body texture under the lace (median skin colour).
  - Vertex colours (constant).
- Still open:
  - The game hides or darkens the body by something the bench doesn't model: an entrance LOD, self-shadow/AO in
    entrance lighting, or a different reading of the hide spans.
  - Whether the entrance pac in the game is the v5 file.
- Proposed next step: a diagnostic pac (body under the lace painted bright green, socks' sheer texels painted bright
  cyan) to tell "body hidden" from "body drawn but dark". Waiting on Matthew.

## Diagnostic result (2026-11-20, in game, entrance pacs)
- **Raquel:** green shows through the lace in the entrance, bright and in every shot. So the body is drawn there, and
  `keep_alpha` (v5) makes the lace panel transparent in game. yCS_trans does alpha-test.
  - The DIAG pac is the v5 entrance with only the body texels recoloured, so v5's entrance shows skin there. The black
    Matthew saw was v3/v4 (alpha forced 255), or v5 not loaded, or skin in deep shadow.
  - `gamerender.py` predicted exactly this image (green diamonds through the lace).
- **Tatum:** cyan stripes render on the sock as painted, and no green shows through the sock anywhere, so there are no
  holes. The green on the bare left thigh is expected (no sock on that leg).
  - So v5's "see-through" look on that leg is the sheer stripes, which v5 tints 60% skin on purpose (how sheer reads).
    It's a look choice, not a hole.
- The bench model (hide spans, alpha-test on yCS_trans, back-face culling with negated normals) matches the game for
  these cases.
