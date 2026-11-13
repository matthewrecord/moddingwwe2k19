# Model backport tool (newer WWE 2K -> 2K19): feasibility

Thread started 2026-11-12 (handoff 014). Branch `claude/backport-tool`. Model files are never committed: they stay
on Matthew's drive (`D:\Pictures\WWE 2K19\A - Resources\Paired Ports`) and in the agent workspace.

## 1. Inventory of the first 4 pairs (2026-11-12)

| Character | Source game | Original (mod files) | Original built on slot | Port (2K19) |
|---|---|---|---|---|
| Gabe Kidd | 2K24 | `BaseModel/baseModel.mdl` + `159_Default_Attire/159_Attire.mdl` (+ .mtls, .hpl, .ctg), 23 DDS | 159 | `ch50602.pac`, `ch50604.pac` (2 attires) |
| Great O-Khan | 2K23 | base + `275_Attire` (+ .ycl cloth), 26 DDS | 275 (Dolph Ziggler 2019 folder) | `ch50602.pac`, `ch50604.pac` |
| Kyle Fletcher (JakeyAttires & BANbantam) | 2K24 | base + `1070_Attire` (+ .ycl, .hpl), 26 DDS | 1070 | `ch50602.pac` |
| Willow Nightingale | 2K24 | base + `969_Attire` (+ .ycl), 30 DDS | 969 (Doudrop folder) | `ch50602.pac` |

The port file names say who made the original mod: "MrH" (Gabe Kidd), "JKxBNB" (Kyle Fletcher), "DB" (Willow). The
ports have the `chXXXXX.pac` names Matthew installed them under, so the slot numbers are his, not the porter's.

**The originals are community 2K22+ mod files, not raw game archives.** These are the loose files used by the 2K22+
mod scene (CakeView / MDL Blender scripts):
- `.mdl` magic `MDL!`: geometry + skeleton. Each character is split into `baseModel.mdl` (head/body, about 6 MB) and
  `<slot>_Attire.mdl` (attire, 1.5-29 MB).
- `.mtls` magic `MTLs`: material list (`name:skinned`, then `MTL!` records with shader name + texture slots such
  as `colorMap`, `g_comboMap`, `flowMap`).
- `.hpl` magic `HPL!`/`LOD!`/`MESH`: per-mesh vertex index lists (HPL = hide/mask lists; the MDL Blender scripts
  expose them as `HPL_Entrance` / `HPL_Ring` vertex groups). Several are 44-byte stubs.
- `.ctg` magic `CTG!`/`SOBJ`/`TOBJ`: per-mesh (M_Head, M_Body) index tables, probably the head/body seam or topology groups.
- `.ycl`: cloth simulation (2K24 "YCL", no magic). It's absent from 2K19 and will be dropped.
- Textures: modern PBR set per material (`_color`, `_nrm`, hair `_flow`/`_rai`), DDS, up to 4096 px.

**The ports are standard 2K19 character pacs:** `EPK8` (EMD virtual name `000506xx` at 0x80C) holding zlib
blocks. Uncompressed contents for each port:

| Block | Gabe 50602 | O-Khan 50602 | Fletcher | Willow | Meaning (first guess) |
|---|---|---|---|---|---|
| JBOY (main model) | 61.1 MB | 79.2 MB | 34.5 MB | 33.9 MB | full character YOBJ (big-endian) |
| texture pack | 111.6 MB | 154.7 MB | 135.4 MB | 215.0 MB | first string `_a_hairl0_n` ... |
| 3,056 B table | yes | yes | yes | yes | bone/face table, same size in all four |
| ~119.5 KB table | yes | yes | yes | 118.8 KB | contains `yM_Trape...` (body-morph names) |
| small table | 3.2 KB | 0.6 KB | 1.9 KB | 5.8 KB | contains `M_Body` (HPL-like mask) |
| 2,072 B / 137 KB | yes | yes | yes | 137 KB | ? |
| extra JBOYs | 8.16 MB, 0.67 MB | 0.60, 1.04 MB | 2 x 8.16 MB, 0.87, 0.22 MB | 8.16, 3.83, 1.33, 0.40 MB | the 8,159,928-byte JBOY recurs in 3 characters: a shared stock 2K19 object the porter reuses (probably the face/head rig) |

Ports are 1.5-3x the size of the originals' meshes. He did not decimate to a tight budget, and 4K texture data
survives.

## 2. Format readers: existing tools (checked 2026-11-12)

- **2K22+ MDL:** no open-source reader found. The known tools are HanleysFramer's MDL Blender IO scripts (2K22/2K23,
  PWMods Patreon), CakeView + MDL Blender Plugin v1.2.5 (2K24, Patreon), and the "YCL Reformatter".
- **2K19 YOBJ/JBOY:** the Xentax/Tekken57 3ds Max importer, X-Rey (paid), Grix reShape and Skeleton Tools, and
  Discovery's Blender YOBJ/JBOY plugin (Patreon). `coreynguyen/rumblerosesxx` has an open MaxScript for the
  Rumble Roses XX YOBJ (older variant, a possible reference).
- Decision: write our own Python readers (`tools/backport/`). This needs no installs on Matthew's PC, and the app
  will need them anyway.

## 3. 2K22+ MDL format: decoded, reader works (`tools/backport/mdl.py`, 2026-11-12)

All 8 original `.mdl` files parse, and the index chunk is consumed byte-exactly. Layout (little-endian):
- Header: `MDL!`, u32 0x28, u32 1, 6 floats bbox (min/max). Then chunks `tag, u32 size, data`: `TEXT`, `BONE`,
  `AtPt` (attach points, optional), `MTL!`, `MBfD` (mesh buffers), `LODs` (index buffers), `END!`.
- `TEXT`: u32 n, n u32 offsets, NUL strings. Every name in the file is a TEXT index.
- `BONE`: 8 bytes, u32 count, then 33-byte records `u32 flag, i16 name index, i16 parent, 3f translation, 3f rotation
  (Euler, radians, local), u8`. Bone 0 is a dummy (`vector`). Units are cm and **up is -Y** (hips at Y = -108.7).
  **Skeletons differ per file:** Gabe 209 bones, Fletcher attire 337 (own hair chain), Fletcher base 199. The names
  are shared (J_Root, J_Hips, ..., H_* helpers, *_Jig_* jiggle, *_RBF_* correctives) but the order is not.
  O-Khan's and Willow's files have **0 bones**: their weights index the game's built-in rig.
- `MBfD`: u32 mesh count; per mesh `u32 name, u32 flags, u16, u32, 6f bbox, u32 vertex count, u16 stream count, u16`,
  then per stream `12-byte hash, u16 semantic, u16 format, u16 type, u16` with its packed array right after
  (4-byte aligned; structure-of-arrays). Streams: POSITION f32x3, NORMAL/TANGENT snorm8x4, BINORMAL (sign) snorm8,
  COLOR unorm8x4, TEXCOORD f32x2 (one or two sets). Then skin: `u16, u16 influences (= 8)`, 8 x u16 bone
  indices per vertex, 8 x u8 weights per vertex (sum 255), then a u32 vertex-id list and a trailer ending `ENDM`.
- `LODs`: u32 LOD count (2), u32 mesh count; per mesh `u16, u32 index count, u16 indices, trailer ... ENDM`.
- Sizes: attires 18.9k-41.8k vertices, bases 23.5k-24.9k vertices / about 42k triangles. Up to **8 weights per
  vertex**. 2K19's limit still has to be measured from the JBOY (the expectation is 4).
