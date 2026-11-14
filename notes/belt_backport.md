# Belt backport (2K23 -> 2K19): first look, 2026-11-14

Input: IWGP US Title 2K23 mod (Belt_128_Default/Ladder/Cutscene.mdl + 5 DDS, 2048px; normals BC7). Not committed.

- `tools/backport/mdl.py` (branch claude/backport-tool) parses all three MDL! v0x25 files: one mesh `base`, 29,339 vertices each.
- 2K19 stock belts: `pac/edit/belt/belt_NNNNN.pac` (81 files, 0.25-1.6 MB). Container HSPC -> one Oodle block (`oodl.py`)
  -> directory (`model`, `tex`, `ycl_00000`, `ywa`, `corr_ywa`, `lod`, `shape`, `bones`, `_skin_bone_palette`, `tex_name`, `subobj`)
  with nested `ZLIB0` sub-blocks + 3-4 DDS (1024px: belt, belt_n, belt_Mask1, belt_mr; DXT1/DXT5/BC7).
- belt_00019's model is skinned to the **full body rig** (J_Hips, J_Chest, ... bone records with 32-byte names), meshes M_Belt (+M_Head/M_Body refs).
  This is NOT the character JBOY layout `jboy.py` reads: header, bone and object records differ. A belt reader/writer is new work.
- Reusable from the character pipeline: MDL reader, bone-name weight remap (`weights='source'`), texconv, Oodle/zlib, pac writer patterns.
- Next: decode the belt model layout (diff 2-3 stock belts), then the builder: replace a stock belt's M_Belt, drop tris to the stock budget, textures to 1024.
