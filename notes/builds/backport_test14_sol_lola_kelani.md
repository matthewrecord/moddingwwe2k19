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
