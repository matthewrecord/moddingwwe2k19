# Backport test 5: Flash Morgan Webster from scratch (2K25), 2026-11-13

First character with no scorpionxxx port. Source: `Paired Ports\FlashMorganWebster_2K25.zip`.
Builder: `tools/backport/build_fmw.py` (about 5 s end to end once the head fit is cached).

## 2K25 format (new)
- Models are `.mcd`: `MCD!`, u32 4, u32 size, then the MDL stream. That stream begins `MDL!MDL!` with version **0x29** (2K24 = 0x28).
  Drop the first 16 bytes and the rest is a normal MDL with chunks from 0x24.
- v0x29 differences that `mdlfmt.py` now handles:
  - The mesh header is 48 bytes (bbox at +16; vc and stream count at +40). 2K24 used 46 bytes.
  - A new stream, `PackedTBN` (R32 uint).
  - Padding blocks inside the BONE table. The reader resyncs on bone name index = record number.
- Same 209-bone skeleton names as 2K24, in a different order. The pipeline maps by name, so no change was needed.
- `.hpl` = `MESH`, u32 name length, name (padded to 4), u32 n, n × u32 vertex index. There are 10 copies for M_Body (LODs); `tools/backport/hpl.py`.
- Head boundary loops are the same as Fletcher's 2K24 head (neck 58, mouth 48, eyes 32), so the face fit carried over unchanged.

## Build (v1)
- Container: Fletcher port `ch50602.pac` (Andrade palette, his 0x50/0xCA/0x2580 blocks, EMD 50602).
- Head: Andrade ch68702 obj0 plus its 119 morphs, fitted to the 2K25 M_Head. Similarity init, welded fit, free_radius 0.6.
  Surface distance: mean 0.16 cm, max 1.0 cm.
- Body: M_Body split into upper and lower. Weights come from the body-only Andrade donor, then outlier smoothing.
- Eyes, eye overlay and mouth parts are his Fletcher objects. Each one is shifted by the mean change between Fletcher's
  fitted face and Flash's fitted face (same topology) at its 20 nearest head vertices. Shifts are under 0.4 cm. Morph
  sets are offsets (max 2-5 cm), so only the base set moves.
- Hair 0x2715 = M_Hair (11,441 vertices). Hair 0x2716 = M_Combinations (beard). Both use his rigid J_Head hair skin.
  The tint is a hand pick, dark brown (45,35,30): the 2K25 hair colour sits behind hashed `.mtls` parameters.
- Attire 0x5601:
  - Slot 0 (the necklace) is collapsed to a hidden triangle.
  - Slots 1 and 2 = M_Wrist, split at x = 0.
  - Slot 3 = M_Bottoms; slot 4 = M_Shoes.
  - All three kneepad/elbow-pad slots in 0x5602 are collapsed.
- Hide table:
  - Rule: `.hpl` M_Body (a triangle hidden if any of its vertices is listed) plus body triangles with every vertex within 1 cm of attire.
  - Checked against Fletcher: this rule covers 1,006 of his 1,229 upper-body triangles. Lower body: whole object in both.
  - Flash result: 1,062 upper triangles; lower body fully hidden.
- Textures: body→all_color/_mr/all_n, head, eye, bottoms, shoes, l/r_wrist (both from wrist), and hair/hair2 from the rai maps.
  Everything else (mouth, swtbm, lobbycube, vessel/flush) is Fletcher's.
- Render check: no holes or spikes on the head front, back or side; body and attire are clean (`renders/fmw1_*.png`).
- File: `_moddingwwe2k19_builds\backport\test5_fmw\fmw_v1_ch50602.pac` (slot 50602, not installed).

## v1 result: crashed (2026-11-13)
Offline checks found nothing wrong:
- Every index and palette slot is in range.
- The texture pack has the same 48 names as his.
- The hide table is 8.7 KB, smaller than Fletcher v7's 9.9 KB, which loaded.

Four test files, each putting one group back to Fletcher v2/v7 data that is known to load:
- **A:** Fletcher's hair and beard.
- **B:** Fletcher's attire (which also tests the collapsed 3-vertex objects).
- **C:** Fletcher's texture pack.
- **D:** all of A, B and C, so only Flash's head and body are new.

## Results for A-D: A and D load; B and C crash
**The cause is Flash's hair (0x2715 M_Hair, 11,441 vertices).** Its layout matches his hair (1 vertex set, 4 influences, yCS_hair), so size is the only difference.
The largest hair known to load has 5,853 vertices, so there seems to be a vertex limit on a hair object somewhere between 5,853 and 11,441.

Next tests (built with `tools/backport/fmw_hairfix.py`):
- **E:** the hair split at the median x into 2 objects (5,755 + 5,995) in 0x2715, using `clone_object`. This is the first in-game use of `clone_object`.
  Its `nobj` lookup was fixed for 8-byte hair headers.
- **F:** half the hair in 0x2715 and half in 0x2716, with no beard. Only known-safe layouts.
- **G:** Fletcher's hair with Flash's beard, to confirm the beard is fine on its own.

## E/F/G all crashed. The real cause was misaligned chunks in the writer
- Every crashing build (v1, B, C, E, F, G) has a hair model whose `bones` region is not 16-byte aligned (relative to base +8).
  Every build that loaded (A, D, all Fletcher v4-v7) has it aligned. The "hair vertex limit" theory is withdrawn.
- Bug: `jbuild.build` tested alignment with `a%16==0` on file addresses. The right test is `(a-8)%16==0`, i.e. keep each
  chunk at its original address mod 16. Big models stayed aligned by luck; hair index lists (u16, odd lengths) did not.
- Fix: pad each chunk back to its original address mod 16 (clones inherit their source's alignment).
  The writer is still byte-identical on 62/62 models.
- New check: every bones/texnames/palhdr/objtable region must sit at (addr-8)%16==0. All v2 files pass.
- Delivered: `fmw_v2_full` (Flash complete, hair in one piece) and `fmw_v2_hairsplit_backup` (hair split in two, in case of a real size limit).

## v2 loads. Matthew's review lists 5 cosmetic issues. v3 (2026-11-13)
Diagnosis, using the new textured face check (`facecheck.py`, `renders/face_cmp.png`):
- **Ears/narrow "PS1" head.** The fitted Andrade mesh did not follow Flash's ears, so the ear texture was painted flat onto the skull.
  The lips were smeared too (the mouth offset).
  - **Fix: use Flash's own M_Head mesh.** Andrade's 119 morphs and skin weights are carried over by closest-point
    barycentric lookup on the fitted Andrade surface W. Each morph keeps 80-100% of Andrade's maximum displacement (median 99%).
  - Head vertices that sit on the neck seam take the body's weights.
- **Eyes set back, cross-eyed look.** His eyeballs' UVs don't match Flash's eye texture (no pupils).
  Fix: Flash's M_EYE, split by side and rigid on J_Eye_L/R.
- **Mouth parts.** Flash's teeth, tongue and mouth bag sit about 1.2 cm lower and 0.4-1.2 cm further back than Kyle's, but the old shift moved them only about 0.1 cm.
  Fix: shift by the Flash-minus-Kyle part centroids (eye overlay uses per-side eye centres).
- **Shiny "liquid" torso and neck/torso tone break.** 2K25 `_nrm` has alpha 0 (2K24: 255) and its blue channel runs about +23 higher.
  Blue correlates positively with 2K24 (0.65 body, 0.86 head), so it isn't inverted. Normals were checked and are fine.
  Fix: match Flash's blue channel to Kyle's distribution (body to body, head to head) before applying the 2K24 rule.
- **Light through body seams.** Smoothing ran per object and per duplicate vertex.
  Fix: weights computed once on the welded full M_Body and shared by the upper and lower pieces.
- Not changed: bone positions (the J_Jaw pivot is about 1.2 cm above Flash's mouth). Possible next step if the mouth moves oddly.

## v3 in game: big improvement. Remaining: hovering hands, puffy/sleepy eyes, mouth opening over the moustache. v4
- New `tools/backport/pose.py`: offline posing (linear-blend skinning about bone world positions plus morph weights),
  rendered with textures through `facecheck.tex_tris`.
- **Mouth.** The head has no J_Jaw weights (Andrade's either): 2K19 opens the mouth with morphs (114 and 45 are the biggest
  downward ones). In v3 the open-mouth morph put the opening above the upper lip, because some of Flash's upper-lip vertices
  borrowed from Andrade's lower lip (`renders/fmw_mouth_v3.png`).
  - **Fix: lip-split transfer.** Flash vertices near the mouth are classed upper or lower by the lip line, taken from Flash's
    mouth boundary loop. Andrade's side is classed by his own morph 114: lower lip = moves more than half the max.
    Each class borrows only from its own side. Result: `renders/fmw_mouth_v4.png`.
  - Andrade's mouth loop is not at his lip line (it gave 499 upper vs 156 lower), so his classes must come from the morph.
- **Eyes.** The eye overlay floated 0.29 cm off Flash's eyeballs (his port: 0.17). It is now re-anchored per side using his
  overlay-to-eyeball offset: 0.22 cm.
- **Hands.** Not solved:
  - Flash's hand mesh occupies the same space as Andrade's.
  - Finger bone weights match Andrade's.
  - Fletcher's 0x50 proportion block is byte-identical to Andrade's.
  So the hover comes from somewhere else. Next: check whether Andrade's own model or scorpion's ports hover too.
