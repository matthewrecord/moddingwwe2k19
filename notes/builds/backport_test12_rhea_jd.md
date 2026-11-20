# Backport test 12: Rhea Ripley, Judgment Day look (2K26 816), 2026-11-20

Matthew on v1 (1163 Deluxe): it looks good, but it's the wrong model. He wants the modern Judgment Day Rhea, and the
hair clips through the body.

In 2K26 that look is ID 816. The folder is named `816_Rhea_Ripley_2019`, but the attire is the black studded set with
the gold R, fishnet tights with tattoos, the mullet and the black make-up, and her SS videos are tagged 2025.
- Ring `rhea_v2_ch50602.pac`: config `rhea_ring`.
- Entrance `rhea_v2_ch50604.pac`: config `rhea_entrance`, the same plus the studded vest M_Jacket in 0x5602,1.

## Slots
| Slot | Contents |
|---|---|
| 0x5601,0 atlas | U_Acce (choker), Pierce, L/R_A_Acce (armbands) |
| 0x5601,1/2 | wrists |
| 0x5601,3 | tights |
| 0x5601,4 | boots |
| 0x5602,0 | M_Brassiere (M_Brassiere_withBelt is the same mesh; skipped) |

Hair: M_Hair 10,932 v on Paige ch43402's rig (nn median 1.0 cm, p90 2.3). lid_fit and eye_recess as in v1.

## Hair clipping fix: `hair_body_blend`
- **Cause:** hair resting on the shoulders and chest was skinned only to the head and Paige's physics chains, so the
  shoulders moved under it.
- **Fix:** blend those vertices' skin toward the nearest body/attire vertex's bones. The blend factor runs over
  y -180 → -160 and over distance to the body 12 → 3 cm, then gets 100 smoothing passes along the hair mesh.
  The needed body bones (8: chest, spines, clavicles, shoulders, neck) are appended to the hair palette; twist/helper
  bones fold into the nearest ancestor the hair skeleton has.
- **New gates:**
  - `hairclip.py`: hair vertices crossing the body under poses.
  - `hairstretch.py`: hair edge stretch on head turns.

| Setting | arms down | +shrug | arms fwd | lean | stretch, head turn 45° (p99.9 / max) |
|---|---|---|---|---|---|
| none | 41 (2.0 cm) | 142 | 51 | 103 | 1.0 / 1.0 (rigid) |
| -160..-150, d 8 | 41 | 129 | 42 | 4 | 2.7 / 4.0 |
| -170..-160, d 12 | 5 (0.6 cm) | 11 | 4 | 1 | 2.5 / 3.2 |
| **-180..-160, d 12, smooth 100 (used)** | **5 (0.6 cm)** | **16** | **6** | **1** | **2.35 / 4.3** |

- **Trade-off:** hair resting on the shoulders now stays on the shoulders when the head turns, so a few triangles
  between scalp and shoulder stretch (about 2× at 45°). In game the physics chains also act on these vertices, so watch
  big head turns.
- Entrance: the vest adds collar contact. arms fwd 76 verts, max 1.6 cm.

## Gates (both slots pass)
- preview clean.
- eyegaze: drift 0, vergence -0.4°, poke ≤ 0.
- lidcheck: matches the donor.
- morphgrid, jaw, bodypose, hairswing: clean.
- Magenta in the previews is Paige's untextured yDefault physics proxy. v1's in-game screenshot shows it isn't drawn.

Renders: `notes/builds/renders/rhea_v2/`.
