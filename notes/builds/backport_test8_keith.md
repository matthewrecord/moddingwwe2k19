# Backport test 8: Keith Lee (2K24 mod on the Noam Dar slot 710), 2026-11-13
- **New problem class: big body on Andrade's skeleton.**
  - Scorpion's big-man ports (Gabe) keep the identical skeleton and take the 0x50 proportion block from a similar stock
    wrestler. Here: `prop_from='ch23802'` (Big Boss Man).
  - Donor nearest-point weights fail. Keith's thick upper arm's nearest Andrade point is the chest, so lowered arms leave
    shoulder "wings"; there is also a knee spike (`renders/keith_pose_v1v2.png`, top row).
  - Big Boss Man as the weight donor was worse (unweighted vertices).
- **Fix: `weights='source'`.** Keith's own 2K24 weights, remapped by bone name; 99% of the weight is on bones with the same
  name in 2K19, and volume helpers fall back to their parents. Result: clean in every pose (bottom row).
- **New gate:** `bodypose.py` (hierarchical posing, `pose.pose_fk`).
- **`.hpl` is empty** (the modder left it blank), so skin is hidden by attire proximity only. The builder tolerates an empty hpl.
- **Assignments:**
  - jacket (sleeveless hooded vest, cloth-simmed in 2K24, rigid here) -> necklace slot;
  - underwear -> bottoms; shoes;
  - L elbow pad -> elbowpad slot; knee pads;
  - beard -> 0x2716; no hair mesh.
- **Gates:** all pass (alignment, weights, eye masks; gaze drift 0, vergence -1.1°; mouth morph grid `keith_morphs.png`;
  textured preview `kl2_check.png`).
- **Note:** Mark rebuilt today would differ from v4 only by a 0.05 cm eyeball straightening (one eye just over 2°).

## v3 (2026-11-13)
- Pinholes: source head had 2 tiny 3-edge holes near the right ear. New permanent builder rule `cap_small_holes` (≤8-edge loops, head and body).
- Ring vs entrance split: configs `keith_ring` (no sweatshirt, EMD 00050602) and `keith_entrance` (sweatshirt, EMD 00050604); new `cfg emd` writes the slot name at header 0x80C.
- Gates: misaligned none, unweighted none, eye masks ok, bodypose clean. Render: renders/keith_v3_check.png
- Install like the old 2K20 Keith (ch92502/ch92504): ring = attire 02, entrance = attire 04.
