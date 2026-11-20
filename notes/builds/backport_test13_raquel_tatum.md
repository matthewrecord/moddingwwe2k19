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
