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
