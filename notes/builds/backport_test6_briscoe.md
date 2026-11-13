# Backport test 6: Mark Briscoe (2K24), 2026-11-13

First build from the general builder `tools/backport/build_port.py` (config `BRISCOE`). It keeps every Flash v4 fix.
Built in about 20 s, plus a one-time head fit.

## New in the builder
- **Atlas:** jacket, bottoms, leg (tights) and right-leg pad share the bottoms slot (0x5601/3) as a 2x2 atlas
  (1024 px tiles, UVs inset 8 px against bleed). The source has 10 attire meshes and the container has 8 slots.
- **Hide table:** body triangles are ordered hidden-first, so each body object's hide table is one span.
  Upper: 2,733 of 14,424 triangles (jacket). Lower: all.
- **Bald hair slot:** 0x2715 gets one hidden hair-format triangle. The beard (M_Combinations) goes in 0x2716.
- **Missing eye normal map:** the eye uses the source colour with his eye _n/_mr.
- **`preview.py`:** textured render of the built pac from its own texture pack (hide table applied), plus an alignment check.

## Checks (all offline)
- Head fit mean 0.145 cm. Lip split 411 upper / 305 lower. Neck seam: 58 vertices welded.
- Atlas UVs: 0% outside 0-1.
- No misaligned chunks.
- Renders: `renders/mb1_body.png`, `mb1_facemouth.png`, `mb1_talk.png`.
- **Beard:** rigid to the head, as in stock (Andrade's beard object, main JBOY obj 17, has one rigid weight).
  It cannot follow an extreme mouth-open morph; at talking range (35%) it looks fine.

## v1 in game: mouth off, headband broken, liquid skin, eyes maybe too far apart. v2
My miss: the v1 open-mouth preview showed the mouth problem and I put it down to beard behaviour.
New bench step: `morphgrid.py` puts Andrade's stock head and our head side by side for the 12 morphs that move the mouth most
(`renders/morph_grid.png` is v1, `morph_grid2.png` is v2). Every build must pass it.

- **Mouth (curtain + corner tears).** 2K24 heads continue the lips inward and bridge upper and lower behind the opening.
  2K19 heads (Andrade) end at the lip rim. Fixes:
  1. Lip classes by surface (graph) distance from clear upper/lower seeds, not by height.
  2. Lip-split transfer may use any Andrade triangle not on the opposite lip (removes the zone-edge tears).
  3. Morph offsets smoothed on the welded mesh in the lip zone, blocking only upper<->lower edges across the central 75%
     of the mouth. The corners stay joined.
  4. Upper/lower bridge triangles in the central 75% are dropped (1 for Briscoe).
  Result: all 12 morphs track Andrade's shapes.
- **Liquid skin (the real cause).** `texconv.resize` used PIL on RGBA, which resizes premultiplied, so RGB went to 0 wherever
  alpha = 0. 2K24/25 `_nrm` maps have alpha 0, so every resized normal map lost R/G/B: skin `_mr` = (0,0,255), flat normals.
  Flash v3's blue-channel "fix" only worked because it set alpha to 255 first.
  Fix: per-channel resize. Skin `_mr` is now 117/127 (his: 123/130); head 151/97 (his: 154/100).
- **Headband.** Attire weights came from the body-only donor, so the bandana got neck/shoulder weights.
  Fix: attire points whose nearest skin is the head take the head's own weights. Bandana: 861/883 on J_Head.
- **Eyes.** Rest positions equal the source's own. Mark's model is asymmetric: eyeballs at +3.76/-4.00 cm, while J_Eye
  pivots sit at ±3.5. Eye rotation around off-centre pivots can read as slightly wall-eyed. Not changed in v2 (candidate:
  move the J_Eye bones).

## v2 in game: textures and headband fixed; a sliver juts from the mouth corner and grows as the mouth opens. v3
- **Cause:** 92 head vertices on the mouth rim had NO skin weights. The game drags them toward the origin, making a thin spike.
  Andrade's rim vertices are weighted to face bones absent from his container palette, and the lip-split transfer
  could only borrow from those rim triangles.
  Morphs alone never show it; rotating J_Jaw in `pose.py` does (`renders/jaw_hunt.png` v2, `jaw_hunt3.png` v3).
- **Fix:** unweighted head vertices take the nearest weighted vertex's skin.
- **New bench gate:** `preview.py` reports unweighted vertices per object. It must be "none".
- **Flash v4 had the same defect** (140 vertices). Flash is rebuilt with the general builder as `flash_v3`
  (config FLASH, 142 fixed). That also gives Flash the per-channel texture resize, welded lip smoothing and head-attached attire weights.
