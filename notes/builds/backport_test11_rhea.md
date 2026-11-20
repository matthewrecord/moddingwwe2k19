# Backport test 11: Rhea Ripley (2K26), 2026-11-20

Source: 2K26 `1163_Rhea_Ripley`, the Deluxe Edition attire. It's her current look; 2K26 also has 816 (2019), 1119 (WM36),
1158 (Mattel) and 1490 (Borderlands). Extracted headless (`tools/cak26`) to `2K26 Extracted\Characters\1163_Rhea_Ripley`.
Config `rhea` in `tools/backport/build_port.py`:
- female template (Willow port container, ch75602 donor), `weights='source'`, `hide='geom'`;
- kneepads on donor weights.

## Slots
| Slot | Contents |
|---|---|
| 0x5601,0 atlas | U_Acce (choker), Pierce, Pierce1, R_Elbowpad |
| 0x5601,1/2 | L/R wrist |
| 0x5601,3 | tights (fishnet painted over skin, opaque) |
| 0x5601,4 | shoes (the green soles are in the source) |
| 0x5602,0 | tops |
| 0x5602,1/2 | kneepads |

Hair 0x2715 = M_Hair (10,534 v, black, tint 20/18/18).

## New in this build
- **Physics hair from a stock female:** `hair_physics='ch43402'` (Paige). Her rig and 0x2580 are used, and each Rhea hair
  vertex copies the skin of the nearest Paige hair vertex.
  - Chosen by scanning all 253 stock `ch*02` pacs for `Hair_b` rigs (device `hairscan2.py`, Oodle). Fit to Rhea's hair:
    nn median 1.1 cm, p90 2.3, max 6.3. Runners-up: Sarah Logan ch73702 (1.2/4.3), Roman ch36802 (1.8/4.5).
  - hairswing: the sheet stays whole and the crown stays put.
- **`lid_fit`:** without it, Rhea's right lid closed short: 36% of the gap left vs the donor's 16% on morph 38, and 17% vs
  -7% on morph 30. Her eye openings are bigger than the donor's, so the same lid travel doesn't close them.
  - Fix: scale each eye-closing morph's travel around that eye (falloff 1.6× eye half-width) until the remaining gap
    matches the donor. All 8 strongest closers now match within 1%.
  - `lid_split` was tried again and made things worse (51-76% left open), so it stays off.
- **`eye_recess` 0.05 cm:** eyegaze poked 7 vertices at right 25°; after the recess, poke ≤ 0 everywhere.

## Gates (all pass)
- preview: misaligned none, unweighted none, eye masks ok.
- eyegaze: drift 0.00, vergence 0.1°, poke ≤ 0.
- lidcheck: matches the donor.
- morphgrid: clean.
- jaw: clean.
- bodypose: no wings or spikes. Skin specks in bodypose are body triangles that the hide table hides; bodypose doesn't
  apply the hide table.
- hairswing: intact.

Preview notes:
- Magenta around the hair in the left and face previews is Paige's yDefault physics proxy (no texture; the same kind of
  object Jevon's stock rig carries).
- facecheck draws one eye dark (a painter-order artifact in that renderer); the game-texture preview shows both eyes fine.

Renders: `notes/builds/renders/rhea/`.

## Watch in game
- Hair motion: Paige's rig on a one-sided hairstyle.
- The fishnet tights read at distance.
- The elbow-pad atlas tile.
- Blinks on both eyes.
