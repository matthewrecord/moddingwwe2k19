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

  **[Superseded by section 11: this test was wrong for stock files, which store bone indices byte-swapped.]**
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
- **[RETRACTED 2026-11-13, see section 13: reader bug, not his tool]** ~~Exactly 17 vertices collapsed to the origin~~ in the head, eye-overlay, mouth and trans objects of every port
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

## 9. Materials (2026-11-12, late; `jboy.obj_params`)

- Header [9]/[11]: a table of **texture names** (16 bytes each; Fletcher 97). It mixes stock 2K19 slot names
  (`swtbm_*` sweat masks, `wrinkles_n`, `lobbycube`, `cmm_mouth`, `head_b/_f`, `cap`, `glasses`, `socks`, ...) with the
  port's own names (`pad`, `band`, `metal`, `nets` are added freely).
- Object [37] = parameter count, [38] = pointer list. Each parameter is 24 bytes: `name[16], u16 type, u16 size(24),
  value`. Type 10 = float, type 15 = texture (u32 index into the name table).
- **Shader per mesh (his rule, the same on all 4):** `yCS_skin` = head/body (+ stock mouth); `yCS_gear` = opaque
  accessories (kneepads, wrist tape, shoes, pads); `yCS_trans` = alpha cloth (tights/bottoms, combinations, necklace,
  elbow pads, eyelash, nets, brassiere, goatee); `yCS_hair` = hair (+ `_a_hairl*` lookups); `yCS_eye` /
  `yCS_eyeOv` = stock eyes.
- **Parameter values are a template.** yCS_skin has 98 parameters and only 11 vary between the four (skin specular
  set; two value groups, presumably copied from two stock characters, plus one `g_fSpecLevel` 20.0 outlier).
  yCS_trans has 3 that vary (spec on/off), yCS_eye has 1 (`g_fEyeRL` = -1/+1 left/right), and gear/hair/eyeOv have 0.
  Bindings are fixed by shader: Diffuse = `<mat>`, TNmlMap = `<mat>_n`, MetRouMap = `<mat>_mr`. Skin also binds the
  stock textures (sweat masks, wrinkles, vessels, flush, mouth cube), which come from the game's shared texture set,
  not the port.
- Writer implication: materials can be generated from per-shader templates copied from one of his ports. Only
  the texture names and a handful of floats change per character.

## 10. Where this leaves the pipeline (status 2026-11-12 late)

| Step | Status |
|---|---|
| Read 2K22+ MDL (mesh, skeleton, 8 weights) | done |
| Read 2K19 JBOY (bones + palette, vertices, 7 weights, UV, strips, materials) | done |
| Read pacs (his EPK8/zlib, stock HSPC/Oodle) | done |
| Bone/weight rule | done: transfer from his male/female ports as templates (about 90%), name map for the rest |
| Texture rule | done: deterministic except a hand-picked hair tint |
| Material rule | done: per-shader templates |
| Face: graft and fit stock 2K19 eye overlay / mouth / head base | understood, not yet built (the hardest step) |
| Unknown small tables in the pac (3,056 B; ~119 KB `yM_*`; M_Body mask; 2,072 B) | to identify |
| **Writer** (JBOY + texture pack + EPK8) | **next big job**: patch-style writer that reuses one of his ports as the container |
| App (preview, stress poses, fixes, export) | after a first in-game test |

## 11. His templates found: stock ch687 (male) and ch756 (female) (2026-11-12, late; corrects section 6)

- **Section 6 was wrong.** The **stock** JBOYs store each skin bone index **byte-swapped** (u16 512 = bone 2,
  0xFF00 = 255), while his ports store it big-endian. Two different writer tools, so the stock comparison read
  garbage bones. `jboy.fix_order` now detects this per object: if an index exceeds the palette and the swapped value
  doesn't, it swaps.
- I hashed every small Oodle block in all 525 stock pacs on Matthew's PC (`blk.py` -> `blocks.jsonl`) and matched
  them against the port tables:
  - **Male template = `ch68702` (slot 687, Andrade "Cien" Almas).** The ~119 KB `yM_*` muscle table and the 2,072-byte
    block of all three male ports are byte-identical to ch68702's, and the port skin palette is identical to
    ch68702's (432 entries, same order). **His male model files are built on Andrade's file.**
  - **Female template = `ch75602` (slot 756).** Willow's `yM_*` table (118,848 B) and block 5 come from it.
  - The 3,056-byte block (per-character, probably body proportions/collision) is taken from a stock wrestler of
    similar build: Fletcher and O-Khan from ch68702, **Gabe from ch23802 (Big Boss Man), Willow from ch62902 (Nia Jax)**.
- Weight test with the fix (nearest stock skin vertex, his weights as truth):

| Donor | Gabe | Fletcher | O-Khan | Willow |
|---|---|---|---|---|
| **stock ch68702 (male)** | **87.0%**, median L1 0.027 | **88.1%**, 0.014 | **82.7%**, 0.035 | 58.6% |
| **stock ch75602 (female)** | 67.7% | 67.9% | 67.2% | **84.7%**, 0.014 |
| stock ch73304 (closest by fingerprint) | 76.6% | 77.2% | 73.8% | 53.7% |

  The remaining 12-17% is where the 2K24 body is shaped differently from Andrade's (nearest-vertex distance is 0.4-0.5 cm
  on average) plus any hand fixes. A smoother transfer (barycentric on the donor surface instead of nearest vertex)
  should close part of the gap.
- **Pipeline decision (final):** weight donors = stock ch68702 (men) and ch75602 (women), both already in Matthew's
  game folder. Also copy from the same donor: its `yM_*` table, block 5, palette and skeleton, and (per character)
  a 3,056-byte block from a stock wrestler of similar build. Writing a port = **start from the donor's own pac and
  replace its geometry and textures**, which is exactly what he did.
- Stock ch13604 still reads badly (24%), so there is a third index layout somewhere. It doesn't matter for the
  pipeline, but don't use ch13604 as a donor.

## 12. Facial animation = 119 morph targets (2026-11-13 ~01:30)

- **JBOY layout per object** (fully mapped for Fletcher; every byte accounted for except alignment padding): vertices
  (vc x 28) -> **morph targets** (if object [25] > 1: ([25]-1) x vc x 28, same vertex layout, positions are
  **offsets** from the base) -> skin (vc x ninf x 8) -> UV (vc x 8) -> UV2 (vc x 8) -> an extra vc x 4 buffer
  (zeros so far) -> strip header (12 B) -> strip indices -> parameter pointer list -> parameter records (24 B each).
  Global tables (bones, texture names, mesh names, morph names, palette) sit at the end. Morph count comes from header
  0x48 (= 119, names BrowInn_L_Dn ...). `jboy.morphs()` reads them.
- **Objects with face morphs** ([25] = 120): head, eye overlay, mouth bag, plus stock objects 24/25. In the port, the
  head's morphs are 28 MB (8,509 verts x 119). **Every head vertex has 119 morph offsets, including the 3,408
  that came from 2K24** (2,465 of them move). So he **generated facial animation for the new head**. That's the
  real reason ports take time, and why the head object merges a stock head with the 2K24 one.
- Where his morphs come from (tests on Fletcher; relative error = mean |predicted - his| / mean |his| over moving
  vertices; 0 would be a perfect source):
  - No vertex in the port carries an **exact** copy of any stock vertex's 119 morph values (8 stock pacs checked
    exactly). He regenerated them; nothing was copied.
  - Nearest-vertex copy from each of the **333 stock heads** with 119 morphs (scan on Matthew's PC,
    `face_scan.py`): best is relative error 0.48 (ch42502 for Fletcher, ch73002 for Gabe, ch62302 for Willow). Donor
    ch687 gives 0.65.
  - Smooth weighting (inverse distance over 6 neighbours) from the best local head: 0.49. **Even a best-fit linear map
    per morph leaves 0.37.**
  - Conclusion: his face shapes come from a source that is **not** any superstar head. Prime suspect: the **CAW
    (create-a-wrestler) base head**, which is designed to be reshaped, or a head from a newer game with matching
    shapes. Next test: CAW head assets (pac/caa, pac/edit, chcommon).
- **Practical route for the tool, whatever his source:** transfer the 119 morph offsets from a 2K19 head onto the
  2K24 head with a surface-based transfer (fit the stock head to the 2K24 face, then carry offsets across). That's
  standard practice and it gives plausible expressions. Exact reproduction of his files isn't needed; reviewing the
  expressions in the app's preview poses is. **This is the step most likely to be labelled "needs a human touch-up".**
- **CAW head lead (2026-11-13 ~01:45):** `pac/edit/head/head_00000.pac` (male) and `head_10000.pac` (female) are
  HSPC + Oodle like the other stock pacs, but the payload is a **different model format**: a big-endian tagged tree of
  records `u32 size, u32 count, name[32]` (`model` -> 15 `subobj`, `tex_name`, `shape` (30 entries), `bones`,
  `skin_bone_palette`, ...). `pac/edit/face_type/*` hold face texture sets (eye_ov, head_Mask, head_mr/_n,
  mouth*, wrinkles_n). There is no JBOY reader for this yet. Decoding the `shape` node would test whether his face
  morphs come from the CAW head. That's not on the critical path, because the tool can transfer shapes from any
  2K19 head.

## 13. Correction + pointer table (2026-11-13 ~02:15)

- **Reader bug fixed.** Object field [26] points to a **table of pointers to vertex sets**: 1 entry (4 bytes) for plain
  objects, 120 entries (480 bytes; base + 119 morphs) for face objects. Each set is vc x 28 bytes = **pos f32x3,
  normal f32x3, colour u8x4** (colour is last, not first). My first reader skipped 4 bytes instead of reading the table.
  That was harmless for plain objects but shifted face objects by 480 bytes (= 17 vertices + 4). So:
  - **Retracted:** "17 vertices collapsed to the origin in every port". That was the pointer table read as vertices.
  - Re-run with the fixed reader: male template ch68702 -> Fletcher **91.1%** dominant (median L1 0.010); female
    ch75602 -> Willow **88.7%** (0.007). As good as his ports match each other, so the templates are
    confirmed. Head composition is unchanged (3,411 verts from 2K24 M_Head, 83% of the rest within 1 cm of the
    ch687 head). The face-morph conclusion stands: nearest-vertex copy from stock heads gives relative error
    0.53-0.69 and at most 6% exact. (The PC-side 333-head scan ran with the old reader; it was consistent on both
    sides but should be re-run before relying on its ranking.)
- **POF0 pointer table.** After the last region of every JBOY sits `POF0`, u32 byte count, then the encoded offsets
  of **every pointer in the file** (relative to +8). Each byte's top bits give the width: 0x40 = 6-bit, 0x80 = 14-bit,
  0xC0 = 30-bit step in 4-byte units (`pof0.py` decode/encode). Fletcher: 1,002 pointers. The header size words ([1]
  and [3]) count up to the start of POF0. **The writer must regenerate POF0**; the game probably relocates pointers
  with it at load time.
- **Writer status (`jwrite.py`):** region-split relocating writer. A rebuild with a region grown by 64 bytes parses
  back identically (all vertices, weights, UVs, strips, parameters, bones and palette). Remaining: use POF0 as the
  pointer list (it also covers the per-morph pointers), regenerate POF0 and the size words, then byte-identical
  identity rebuild.

## 14. JBOY writer: byte-exact round trip (2026-11-13 ~02:45)

`tools/backport/jwrite.py` (+ `jlayout.py` region map, `pof0.py`):
- Split the file at every region start (header, object table, per object: vertex-set pointer table, each vertex set
  (base + morphs), skin, UV, tangent, strip header, strips, parameter list, each parameter record; then bones, texture
  names, mesh names, morph names, palette header, palette). A chunk runs from its start to the next region's start, so
  trailing padding travels with its chunk.
- **Every pointer in all 62 models points at a region start** (checked against POF0, which lists every pointer).
  So any chunk can be replaced by bytes of a different length: the writer lays chunks out again (keeping 16- or
  4-byte alignment), re-points all POF0 pointers, rewrites the header size words ([1] = [3] = POF0 offset - 8)
  and regenerates POF0.
- POF0 encoding detail: 1-byte steps below 63 (units of 4 bytes). **His tool switches to 4-byte steps from 0x3000;
  the stock (Yuke's) tool from 0x4000.** `Writer(j, style='porter'|'stock')`.
- **Result: all 26 of his JBOYs and all 36 stock JBOYs tested rebuild byte-identical.** A rebuild with a region
  grown by 64 bytes parses back identically. The writer is therefore safe for any geometry/texture swap that keeps
  the object structure.
- Next: helpers that build each chunk from arrays (vertex sets incl. morph offsets, skin with palette + 7-weight trim,
  UV, tangent, strips via a stripifier or "list as strip", parameter records), then the texture pack writer, then
  pac packing (EPK8 + zlib as in his ports).

## 15. Pac writer (his EPK8 layout) (2026-11-13 ~03:00)

`tools/backport/epkwrite.py`. Layout measured on his 6 ports:
- 0x0 `EPK8`, u32 0x1C, **u32 size = total length - 0x4800**, u32 7 ... (the rest of the first 0x4000 bytes is
  copied from a template).
- 0x800 `EMD `, `04 00 01 00`, 0, **virtual name** (8 ASCII digits, e.g. `00050602`; it must match the slot, see
  notes/characters step 1j), u32 at 0x818 = size / 256.
- 0x4000 `PACH`, u32 count, then per file `u32 id, u32 offset, u32 size`. Offsets are relative to the end of the
  table, and **data starts right after the table (no alignment)**. Each file is a `ZLIB` block (`ZLIB`, u32 0x1230,
  u32 compressed, u32 raw, stream), 4-byte aligned. The file is padded to 2,048 bytes.
- File ids in his ports: 0x0 main JBOY, 0xA texture pack, 0x50 the 3,056-byte block, 0xCA yM_* table, 0xCE M_Body
  table, 0x2580 block 5, 0x2715 / 0x2716 / 0x5601 / 0x5602 ... further JBOYs (hair, gear, trans).
- His deflate output can't be reproduced byte for byte (`78 01` streams from a non-zlib encoder; no zlib
  level/memLevel/strategy matches), and it doesn't need to be. **All 6 ports repack with identical decompressed
  contents and identical header/EMD**. They're 18-20% smaller because we compress at level 6 instead of his fastest
  setting.
- Combined with section 14, the tool can now unpack -> edit -> repack a complete character pac.

**Next engineering step:** object-level JBOY builder: add/remove objects, so the donor (ch68702) can receive the
2K24 attire objects. That means new object records, new chunks and new POF0 entries; the writer already relocates
everything else. Then the geometry/skin/morph generators.

## 16. Object-level builder (2026-11-13 ~03:20; `tools/backport/jbuild.py`)

- `Model(j)`: chunk/pointer model where pointers are (location chunk, offset) -> target chunk; rebuilds byte-identical.
- `clone_object(k)`: appends a copy of object k (all its chunks, its 184-byte record with [30] = new index, all
  its pointers) and bumps header [6]. Tested: clone == source, every other object unchanged.
- `set_object(m, k, pos, nrm, col, uv, tan, slots, weights, strip)`: writes new vertex set, skin (palette **slot**
  indices, BE, `u16 slot, u16 0, f32 w`), UV, tangent, strip, and updates record fields [0] / [23] / [40] (+ bounding
  sphere [42..45]). Tested by re-encoding his kneepad object from decoded arrays: positions, normals, UVs, bones,
  weights and triangles (with winding) read back identical.
- `tris_to_strip`: naive triangle-list -> strip with degenerate joins (3.7x longer than his strips). A proper
  stripifier is optional polish.
- Vertex set = pos f32x3, normal f32x3, colour u8x4. Field 29 stream = 3 floats per vertex (tangent; to be confirmed
  by checking orthogonality with the normals).

**Plan for the first real build:** "re-port" Fletcher: take his port as the container, regenerate the non-face
objects (attire, hair, body) from the 2K24 files with our rules (geometry, template weights, textures), and compare
to his port object by object. That tests the generators against ground truth before the donor-based build (Andrade
ch68702 + new objects).

## 17. Per-vertex rules for regenerating objects (2026-11-13 ~03:45)

Measured on Fletcher and Gabe (vertices matched by position + normal):
- **Positions:** copied unchanged (same space, cm, -Y up).
- **Normals: negated** (2K19 normal = -(2K24 snorm8 normal), dot product -0.999 on every object).
- **UVs: copied unchanged** (no V flip): 94.5-100% exact; the rest are seam duplicates.
- **Field-29 stream (12 bytes/vertex):** all zero on skin/gear/trans/eye objects. **On hair it encodes vertex-index
  parity**: even vertices (0,1,0), odd (1,0,1), on every port (Fletcher, Gabe, Willow). Reproduce as is.
- **Vertex colour:** white (255,255,255,255) on hair, even where the 2K24 hair has colour.
- **Attire weights:** the ch687 template (nearest donor skin vertex) beats renamed 2K24 weights on almost every
  piece:

| Object | Renamed 2K24 weights (dominant / median L1) | ch687 template |
|---|---|---|
| Fletcher tights (trans, 3,978 v) | 66% / 0.307 | **85% / 0.136** |
| Fletcher shoes (gear, 2,545 v) | 97% / 0.029 | 94% / **0.017** |
| Fletcher elbow pads (gear, 575 v x2) | 43% / 0.670 | **85-87% / 0.111** |
| Fletcher wrists (gear, 252 v x2) | **98% / 0.077** | 95% / 0.096 |
| Gabe kneepads etc. (gear) | 46-54% | **85-90%** |
| Gabe shoes / combinations | 93-100% | 94-100% |
| Loose items >1 cm off the body (necklace, Gabe trans 3.8 cm) | 57-64% | 58-71% |

  Rule: **template for everything, 7 influences**. Loose items (necklace, pads standing off the body) are where both
  methods disagree with him, so the app should flag them for a check in stress poses.

## 18. First generated objects + first in-game test build (2026-11-13 ~04:15; `tools/backport/regen.py`)

- `regen.py`: for each object of a port, find its 2K24 source mesh(es) by vertex match, then rebuild it from the MDL:
  positions, negated normals, UVs, white colour, zero (or hair-parity) field-29 stream, template weights (nearest donor
  skin vertex, top 7, renormalised, mapped to palette slots), strips from the LOD0 triangles.
- **Fletcher (male, ch687 template):** all 8 attire objects regenerated (necklace, wrists x2, tights, shoes, elbow pad,
  kneepads x2). Agreement with his weights: 85-95% dominant on 7 objects, 58% on the necklace. Vertex counts are
  slightly above his (+8 to +33: he deleted a few vertices).
- **Willow (female, ch756 template):** only shoes and kneepads regenerate cleanly; her other attire objects were
  reshaped by him (2K24 coverage 0-57%), which matches the 8% moved vertices and the months he spent on her.
- Installed copies found by main-JBOY size: **only Willow is installed** (slots 238 and 865, identical in CCT and
  Genesis). Fletcher, Gabe and O-Khan aren't installed.
- **Test 1 built (not installed):** Willow slot 865 with our shoes + kneepads. See `notes/builds/backport_test1_willow.md`.
  This is the first build that needs Matthew (in-game check).

## 19. Face-shape transfer experiments (2026-11-13 ~00:30 local; `tools/backport/facexfer.py`)

Truth = his 119 morph offsets on the 3,411 2K24 head vertices of Fletcher. Relative error = mean |pred - his| / mean |his|.

| Method | Rel. error |
|---|---|
| Nearest vertex, stock head ch73304 (unfitted) | 0.53 |
| **Barycentric closest point on the stock head surface, ch73304 (unfitted)** | **0.516** |
| Same, donor ch38402 / ch68702 | 0.60 / 0.68 |
| Donor = the stock part he grafted into the same head object (barycentric) | 0.41 overall, but it doesn't reach the forehead: brow/squint shapes come out near zero |
| Gaussian smoothing of that donor (r 0.5-8 cm) | 0.53 -> 0.86 (worse) |
| Closest-point non-rigid fit of the stock head onto the 2K24 head, then transfer | 0.57-0.67 (fit slides features) |
| Landmark warp (eyes, mouth bag, teeth, tongue, head extents; thin-plate RBF) +/- light fit | 0.60-0.70 |

Per expression (in-object donor): mouth/jaw shapes reproduce well (Mouth_Up 0.25, Mouth_L/R 0.26-0.27, Jaw_Chew 0.28);
brows/squints fail because they need a full-face donor. His head object interleaves 2K24 and stock-like vertices (no
stock ordering), so he rebuilt it in a 3D package. His exact correspondence can't be recovered from the file.

**Conclusion:** none of the 333 superstar heads and no standard fitting reproduces his shapes better than about 50%. His
source is something else (create-a-wrestler head is the remaining candidate). For the tool, matching his numbers isn't
the goal; expressions that look right are. **Working method: barycentric transfer from the best-matching stock head
(chosen per character by surface distance), reviewed in the app.** The CAW head probe is next (bounded).
