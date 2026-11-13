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

## Result + cause found (2026-11-13 00:21 local)
- **A crashed** (Matthew), while his own Willow runs fine. A contained his data unchanged, so the fault was in **our pac writer**.
- **Cause:** the EPK8 size field (header +8, EMD +0x818 = total - 0x4800) must cover all data. His files are laid out
  as data -> zero-pad to 2,048 -> a **2,048-byte footer** (`EOP5/plugin version 1.26`, a tag, a build-machine IP
  string; identical in all 6 ports). Our writer padded to 2,048 without the footer, so the size field ended 475 bytes
  before the end of the last ZLIB block, and the game read a truncated block. Test 1 crashed for the same reason.
- Fix: `epkwrite` appends his footer and has `build_raw()` (reuses original compressed blocks); unchanged files keep
  their original compressed bytes, and changed files are compressed with zlib level 1 (`78 01`, like his). **Container
  rebuild is byte-identical on all 7 pacs** (his 6 ports + Matthew's installed Willow).
- Files A/B/C in test2 are obsolete (built with the bug). Replacements in `test3_willow_fixed\`:
  `B2_ch86502.pac` (his geometry, our weights on shoes + kneepads) and `C2_ch86502.pac` (our shoes + kneepads).
  Not installed.
