# Backport test 14: Sol Ruca (2K26 1059), Lola Vice (1211), Kelani Jordan (1212), 2026-11-21
Sources: Matthew's extraction at `D:\Pictures\WWE 2K19\A - Resources\2K26 Extracted\Characters\`. Default attire only.
None has separate entrance gear, so ring (ch50602) and entrance (ch50604) are the same model with different slot names.
Matthew picks the slots.

## Configs (build_port.py): `sol_ring|entrance`, `lola_*`, `kelani_*`
- All three: female template, source weights, geom hide, Paige ch43402 physics hair.
- Sol: fishnet tights + top keep alpha. No lace_clear or drop_backing: those were Raquel-specific, and copying them broke Sol (see below).
- Lola: plain.
- Kelani: `eye_recess=0.3`. At 0.05 her eye poked through the lid looking up (+25); at 0.3 it's +4.
- Hair tint isn't in the 2K26 jmtl (binary; it only holds shader floats), so it's set from appearance:
  Sol (205,170,115), Lola (40,28,22), Kelani (22,19,19).

## Tool fixes
- `atlas()`: g×g grid instead of a fixed 2×2 (Sol has 5 small accessories, Kelani 6).
- `mdlfmt.lod0_materials`: the alignment pad before the material count varies (0 or 2 bytes). The reader now keeps the layout whose ranges sum to n.
- `lift_gear` option (float gear off the skin): tried on Sol, didn't help; left in, off.

## Gates (ring builds)
| | preview | eyegaze up-15 poke | legstress kick back cross | hairstretch p99.9 | zfight |
|---|---|---|---|---|---|
| Sol | ok | -31 | 872 | 2.11 | 3.8% FAIL, reviewed |
| Lola | ok | -21 | 399 | 2.08 | 0.55% |
| Kelani | ok | +4 | 564 | 1.00 | 1.7% |
| (Raquel v7, accepted in game) | ok | | 516 | 1.75 | 0.9% |

- Sol's zfight FAIL was reviewed with the ID buffer and depth. The flagged pixels are all on the fishnet tights, as scattered single pixels along
  the strands, where net and skin are nearly tangent. There are no patches in any view, and a hip-to-ankle close-up shows nothing. It's
  likely a gate false positive for fishnet; this is the first in-game test of it.
  A refined gate (only counting 3×3 patches) was rejected because it also passed Raquel v6, the known positive.
- The magenta sheets in previews are the donor physics proxy (yDefault). It's in every physics-hair build, Raquel's included, and the game doesn't draw it.
- Bodypose and morphgrid were viewed for all three: clean.
- Watch in game: Sol's fishnet (flicker over skin?), Lola's and Sol's hair stretch on head turns (a bit above Raquel), and hair colours.

## v2 (in-game feedback on v1: brillo hair, wrong hair look on Lola/Sol, grey roots on Kelani, some hair clipping)
- Cause of the hair look: 2K26 `hair_rai` holds masks, not colour. R = root->tip, G = strand coverage, B = per-strand id; 2K26 tints in its shader.
  We used one flat colour plus G cut out at 128. G is hair-thin lines, so it broke up into speckle.
  Our `_n` (123,0,140) also doesn't match an in-game-proven port: Willow's is (128, 98, strand shade, alpha). The 2K19 colour texture is the real colour; there's no colour parameter.
- Fix: `texconv.hair_rai` + cfg `hair_colors={root,tip,var,thick,gain}`. It bakes root->tip colour with per-strand variation,
  thickens coverage (gaussian 1.2 px × 1.8), and writes the Willow-layout `_n`. Colours are set from references:
  Sol root (110,80,52) / tip (222,192,140); Lola (42,30,24) / (186,146,100), dark roots with blonde lengths per Matthew's reference; Kelani near-black.
- Clipping: hair_body_blend raised to dfull 6 / dzero 18 for all three. Lola's lean-back hairclip goes 3.7 → 2.4 cm.
  The rest is physics swing, which the bench can't simulate.
- Kelani's afro: shoulders rise into its lower edge (hairclip 3.2 cm). Moving the blend zone off didn't help (5.1); left as is.

## v3 (Sol, Lola): hair "a little heavy" in movement
- hair_body_blend dfull 6/18 -> 4.5/15: less of the lower hair pinned to the body, so it swings more. Hair texture unchanged from v2.
- hairclip is unchanged from v2: Lola worst 2.4 cm, Sol 1.8.
- If it still feels heavy, the next step is 3/12 (v1 movement, with v1 clipping 3.7 cm).
