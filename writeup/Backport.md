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

## 4. 2K19 JBOY reader (`tools/backport/jboy.py`, 2026-11-12)

Every JBOY in all 6 port pacs parses (`epk.py` unpacks the pac's zlib blocks). The format is big-endian and every
offset is +8.
- Header words: [6] object count, [8] bone count, [10] bone table, [11] texture-name table, [12] mesh-name table.
  The words at 0x48 give 0x77 morph names (BrowInn_L_Dn, ...), and at 0x50 `count, ptr` gives the **skin palette**
  (`n, ptr, n x u32 bone id`). **Skin indices go through this palette.** Without it the weights look like nonsense
  (J_Head -> J_Chest).
- Bones: 80-byte records `name[16], 3f translation, pad, 3f Euler rotation, pad, i32 parent, ..., 4f world bounding
  sphere`. Main rig: 433 bones (548 for Willow). It uses the **same names, units (cm, -Y up) and rest values as the
  2K24 rig** (J_Hips -108.703, J_Spine1 6.539). It adds 2K19 helper bones named `m0xx_yyyy`. Hair uses a separate
  67-bone rig in its own JBOY (`yCS_hair`).
- Objects: 184-byte records at 0x58: [0] vertex count, [3..22] -1, [23] influences, [26] vertex ptr (28 B:
  u8x4 color, pos f32x3, normal f32x3), [27] skin ptr (per influence `u16 bone, u16 pad, f32 weight`), [28] UV f32x2,
  [29] second 8-byte stream, shader name at +124 (`yCS_skin`, `yCS_gear`, `yCS_trans`, `yCS_hair`, `yCS_eye`,
  `yCS_eyeOv`), [36] material, [39] index buffer (not yet decoded).
- **2K19 allows 7 influences per vertex** (hair: 4). The 2K24 originals use up to 8, so we must trim to the top 7
  and renormalise. This is not the 4 that the handoff expected.
- Each port is split into several JBOYs: main (head/body/skin), hair, gear and trans(parent) objects.

## 5. Feasibility results (2026-11-12): bone map and weight transfer

Method (`tools/backport/bonemap.py`, `check2.py`): each port vertex is paired with the nearest original vertex.
**There is no transform between the two**: the median distance is 0 for 3 pairs. Willow is the exception: 8% of
her vertices moved more than 1 cm, so the porter edited her shape. A vertex pair counts if it is within 0.05 cm,
giving 20k-42k pairs per character. Weight error = half the L1 distance between the two weight distributions
(0 = identical, 1 = disjoint). "Dominant" = same top bone.

| Pair | Naive copy (same bone names, top 7) | Best 1:1 bone rename (learned) | **His weights from another male port (template)** |
|---|---|---|---|
| Gabe Kidd | L1 0.223 (median 0.045), dominant 79.1% | 0.205 (0.030), 81.8% | 0.102 (0.000), 90.2% |
| Kyle Fletcher | 0.273 (0.111), 74.8% | 0.277 (0.106), 77.2% | 0.094 (0.000), 91.0% |
| Great O-Khan | n/a (original has no skeleton) | 0.210 (0.023), 83.9% | 0.137 (0.006), 87.6% |
| Willow (female) | n/a | 0.254 (0.088), 78.1% | 0.404+ from male ports, 59% (needs a female template) |

What this says about scorpionxxx's method:
1. **He did not rename bones; he re-weighted the body from a fixed 2K19 template.** A learned 1:1 rename barely
   beats the naive copy, and purities are low (0.2-0.3 for helper bones such as H_Hip_*_OS1 -> J_Leg_*). Meanwhile
   one male port's weights predict another male port's at median error 0. The most likely method is "transfer
   weights from a stock 2K19 male body (and a female one for women)". The template's source (stock 2K19 body vs. his
   own master file) is not yet identified. Next check: the stock 2K19 bodies in Matthew's game folder.
2. 12-16% of his weight mass is on 2K19-only `m0xx_*` helper bones that no 2K24 file has. A rename can never
   produce these; a template can.
3. The bone-name overlap is large: 57-59 of the bones the originals use carry the identical name in 2K19. So the
   deterministic name map works as a fallback for parts the template does not cover (attire far from the body,
   hair has its own rig).
4. Recovered maps: `tools/backport/bonemap_recovered.csv`.

**Feasibility verdict: yes, and simpler than planned.** The pipeline does not need a learned weight model for the
body. It needs: (a) readers (both done), (b) a male and a female 2K19 skin template and a nearest-surface weight
transfer from them (reproduces his weights at about 90% dominant agreement), (c) a name map for the rest, trimmed to 7 influences,
(d) a writer (JBOY index buffers, materials and textures not yet decoded). The small learned model is optional:
use it only if the template residual (about 10%) turns out to matter in stress poses.

## 6. Where his weight template comes from (2026-11-12, late)

- **The stock character pacs use a different container from his ports:** HSPC -> blocks compressed with Oodle Kraken
  (`OODL`, u32 0, u32 flags, `KRKN`, u32 raw size + 0x14, u32 stream size, stream). They decompress with the pip
  package `pyooz` (`tools/backport/oodl.py`). Inside is the same JBOY format: stock ch10002 has 421 bones, 23
  objects and 19,648 skin vertices. His ports use EPK8 + zlib.
- Fingerprinted all **525 stock character models** in `pac/ch` on Matthew's PC (weight mass per bone over skin
  objects; `sig.py`, results in the game folder at `_moddingwwe2k19_builds\backport\stock_sigs.jsonl`). The two closest
  were `ch38402` (slot 384) and `ch73304`, both 0.99 cosine. Every other stock model scored at most 0.91.
- Exact test (`tmpl.py`: nearest stock skin vertex -> compare to his weights):

| Donor | Gabe | Fletcher | O-Khan | Willow |
|---|---|---|---|---|
| stock ch73304 | 72.3% (L1 0.283) | 72.7% (0.274) | 69.5% (0.313) | 49.6% |
| stock ch38402 | 60.6% | 58.9% | 59.9% | 45.1% |
| stock ch10002 | 57.1% | 60.5% | 56.6% | 35.8% |
| **another of his male ports** | **90.2%** | **91.0%** | **87.6%** | 59% |

  **None of the stock bodies is his template.** Stock ch73304 is the nearest, but it's well below his ports
  reproducing each other. His donor was his own master body (probably a re-weighted stock body he kept and reused),
  and it isn't in the game folder.
- **Decision: use his ports as the template.** A male donor built from his three male ports (where they agree) and
  Willow as the female donor. This reproduces his body weighting at about 90% dominant-bone agreement without
  learning anything. More of the ~60 pairs will tighten the template, especially the female one (only 1 so far).
- Side note: stock `ch13604` gives 2-4% agreement (bone indices don't line up). Some stock models must use per-object
  palettes or a different palette layout. Check this before using any stock model as a donor.

## 7. Triangles, and what his ports are built from (2026-11-12, late)

**Index buffers decoded.** Object field [39] points to `u8 primitive (6), ..., u32 index count, u32 ptr`, then BE u16
indices. Type 6 = **triangle strip** with repeated indices as joins (`jboy.strip_to_tris`). All 110 objects in the 6
ports decode, with indices in range and every vertex used. Where the port vertices come from the original, 80-99% of
the decoded triangles match the original triangles exactly. The rest are most likely seam duplicates (same
position, different index), so they don't indicate a decoding error.

**Composition of a port, measured.** Every vertex was traced to the 2K24 original or to stock 2K19 objects
(ch73304, ch38402, ch14704):
- Body, attire, hair, gear, trans: **straight from the 2K24 original** (vertex match 94-100%; hair keeps its exact
  vertex count, e.g. Fletcher M_Hair 3456 = port hair 3456).
- **Stock 2K19 parts re-fitted to the new head** (same vertex count as the stock object, each vertex moved 1-3 cm):
  eye overlay `yCS_eyeOv` (194 verts), mouth interior (1,974 verts = stock object 14), a 341-vertex part (stock
  object 15). Willow also has the stock 2,014-vertex part (stock ch14704 object 4, female).
- **Head object = the 2K24 M_Head merged with a stock 2K19 head.** Fletcher object 0 has 8,509 verts: 3,398 are
  2K24 M_Head, and of the other 5,101, 90% sit within 1 cm of stock object 0 (3,936 verts) or object 24. The mouth
  bag is likewise 2K24 M_MouthBag + stock object 2. Probable reason: 2K19 facial animation (the 119 morph names at
  header 0x48: BrowInn_L_Dn ...) and the mouth/eye shaders are tied to 2K19 head topology, so he kept the 2K19 face
  parts that animate and fitted them inside the new head. **This is the "neck/head" step of the pipeline, and it's
  the part most likely to need a human touch-up.** Next check: whether the stock head part is visible or hidden
  (material/shader flags), and how the morph targets attach.
- **Exactly 17 vertices collapsed to the origin** in the head, eye-overlay, mouth and trans objects of every port
  (male and female; 5-15 degenerate triangles each). The count never varies, so it's an artifact of his JBOY-writing
  tool (or a deliberate hide), not hand work. The pipeline should reproduce it until we know why.

Implication for the tool: the deterministic pipeline gains a fixed step, "graft the stock 2K19 face parts (eye
overlay, mouth interior, 341-vertex part, head base) and fit them to the new head". This is a repeatable fit to the
2K24 head, which always has the same topology (base meshes have 42,275-42,598 triangles on all 4 characters).

## 8. Texture conversion: his recipe recovered (2026-11-12, late; Fletcher, `texrule.py`)

**Port texture pack** (block 1 of the pac): `u32 count`, then 32-byte entries `name[16], "dds\0", u32 size, u32 offset,
u32 0` (the first entry's name starts at +0x10), then plain DDS files (`texpack.py`). Fletcher: 48 textures, 129 MB.
Every texture in it is **DXT5, one mip level (mips stripped)**.

**Per material, 2K19 wants 3 maps: `<mat>` (color), `<mat>_mr`, `<mat>_n`.** 2K24 ships `_color` (DXT1) and `_nrm`
(BC7: RG = normal XY, B = roughness-like, A = metal-like). His conversion, checked pixel by pixel against his output
after resizing (mean absolute error, 0-255 scale):

| 2K19 map | Rule | Error vs his file |
|---|---|---|
| `<mat>` | = `_color` | 0.0-2.3 |
| `<mat>_n` | R = 255 - nrm.R, G = 255 - nrm.G (**both normal channels inverted**), B = A = 255 | 1.0-2.9 |
| `<mat>_mr` | R = nrm.A, G = nrm.B, B = 255 - nrm.B, A = 255 | 0.4-2.9 |
| skin `_mr` (head, body) | same, but **R = 0** | G/B r = 0.98-0.997 |

- Sizes: 4096 maps are halved to 2048. There are exceptions: the body stays 4096x2048, and Fletcher's `shoes_mr`
  stays 4096, which looks like an oversight. 512 and smaller are kept.
- Renames: `body` -> `all` (`all_color`, `all_color_mr`, `all_n`), `tights` -> `bottoms`. Other attire names are
  kept. The 2K19 material names expected by the shader/object table will settle the rename list.
- **Hair is a separate recipe:** `hair` = a **hand-picked flat tint** (Fletcher about RGB 210/173/119, small
  variation) with **alpha = rai.G** (opacity, r = 0.95). `hair_n` = flat normal (123, 0, 140) + the same alpha.
  `hair_mr` = constant (0, 174, 0). `_a_hairl0_n` / `_a_hairl1_n` are 128x128 2K19 hair lookups, not derived
  from the original: copy them from a stock model. **The hair tint is a human choice.** The app should offer a
  colour picker that defaults to the average of the 2K24 hair's colour.
- Eyes and eyelashes (`eye`, `eye_mr`, `eye_n`, `eye_ov`, `eyelash*`) still need checking against stock 2K19.

**Implication:** texture conversion is fully deterministic apart from the hair tint. Encoding needs a DXT5 encoder
(Python options: `texture2ddecoder` decodes only; for encoding, use `etcpak`/`quicktex` or a small numpy encoder).
