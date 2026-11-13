# Backport test 2: Willow crash diagnosis, files A/B/C (built 2026-11-13 ~00:40 local). NOT installed.

Folder: `WWE 2K19 - modded\_moddingwwe2k19_builds\backport\test2_willow_diag\`. All three files are named for slot 865
(EMD 00086502). Install = back up `mods\Genesis\characters\pac\ch\ch86502.pac`, copy one file over it, test, restore.

| File | What changed vs his Willow | If it crashes, the cause is... |
|---|---|---|
| A_ch86502.pac | nothing: his data passed through our JBOY writer + pac writer (decompressed content byte-identical) | our container (zlib level / layout) |
| B_ch86502.pac | his geometry, strips, colours; only the **weights** of shoes + kneepads replaced by ours (template ch756, 0xFFFF empty slots) | weights / skin layout |
| C_ch86502.pac | test 1 again with fixes: vertex colour 245/0/0/255 like his, 0xFFFF empty slots, slot order | geometry/strips (if A and B pass) |

Ruled out offline: pointer relocation (only the header size words are offset-like outside POF0), container alignment
(his offsets are 4-aligned too), bounding spheres (his are a fixed template value), hidden per-vertex references in
other pac blocks. Checker `tools/backport/jcheck.py` passes on all regenerated objects.
Suggested order when Matthew is up for it: A, then B, then C (stop at the first crash).
