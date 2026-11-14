# Title belt backport (2K22+ mod -> WWE 2K19)

Branch `claude/belt-backport` (built on `claude/backport-tool`). First case: IWGP United States Championship
(2K23 mod: `Belt_128_Default/Ladder/Cutscene.mdl` + 5 DDS at 2048 px). Mod files are not committed.

## 1. Where 2K19 keeps title belts (2026-11-14)
- **`pac/prop/20xx.pac` = main belt, `pac/prop/50xx.pac` = cutscene belt** (the pair of prop ids a title record points to).
  Identified from the Havok scene path in each pac: 2001 HV (Heavyweight), 2002 IC, **2003 US**, 2004 WWE Title,
  2005 HC, 2006 WM, 2007 TG, 2008 CR, 2009 World HV, 2010 World TG, 2011 Universal, 2012 SD Women's, 2013 Raw Tag,
  2014 SD Tag, 2015 CWC, 2016 UK, 2017 NXT, 2018 NXT Women's, 2019 NXT Tag. 50xx follow the same numbering.
- `pac/edit/belt/belt_NNNNN.pac` are **Create-a-Championship** parts: a different "edit" model format (tree of
  `name[32], u32 size, u32 count` nodes; `subobj` holds JBOY-style object records whose pointers are
  **self-relative**, i.e. target = pointer address + value). Decoded far enough to read a mesh; not needed for title ports.

## 2. Title belt prop format
- HSPC -> one SHDC -> 5-9 Oodle blocks, file table of 16-byte entries `(id, off, size, 0)`:
  id 0 main JBOY, 4 nameplate JBOY (US/IC/etc only), 10 texture pack (`belt`, `belt_n`, `belt_p`), 30 nameplate
  texture, 200 800-byte table, 1000/1010 font data, 2000 Havok, 4000 `mask` (strap silhouette atlas, not in the material).
- Main JBOY: one `yPBR` object, 4 influences, standard character JBOY layout (`jboy.py`, `jbuild.Model` round-trip
  byte-exact on 2003, 5003 and the nameplate). Skin entries = **u8 palette slot, u8 0, u16 0, f32 weight; unused slot 0xFF**.
- Main belt rig: `root`, `bone01..06` (+x), `bone07..12` (-x), `bone13`, `bone14`; flat, 131 cm wide, y = thickness, z = height.
  Cutscene rig: `root`, `L_bone01..12`, `R_bone01..12`; z = thickness, y = height.
- Material: `g_texBaseColor`=belt (DXT1), `g_texNormal`=belt_n (ATI2/BC5), `g_texMtlRgh`=belt_p (DXT1: R metal,
  G roughness, stock range metal ~25 / leather ~50, B 255). 1024 px, 11 mips.

## 3. The 2K23 mod vs 2K19
- **Same rigs, same names.** Default.mdl = root + bone01..14 (BI indexes the TEXT name list directly);
  Cutscene.mdl = root + L_/R_bone01..12. Per-bone vertex-cluster centroids agree with stock 2003/5003 to ~1 cm
  (main) and ~3 cm (cutscene: mod sits ~3 cm higher, 1 cm deeper -> shifted by (0,-3,+1)). Max 4 influences in the mod.
- The 2K23 Ladder.mdl (root only) has no 2K19 counterpart; dropped.
- Normal map: 2K23 tangent-space R matches 2K19, **G is inverted** (correlation of normal channels with metal-mask edges:
  stock R -0.41/G +0.46, mod R -0.79/G -0.81).
- 2K23 UVs tile outside 0..1 (14,500 of 39,320 triangles); none straddles a tile edge, so triangles are moved back into
  0..1 (no texture-wrap assumption).

## 4. Builder: `tools/backport/belt_port.py` (+ `beltview.py` preview, `ddsread.py`)
`python3 -I belt_port.py --mod <mod dir> --stock <pac/prop> --main 2003 --cut 5003 --out <dir>`
Replaces the main object of each stock pac (29,339 vertices, 39,320 triangles; winding checked against vertex normals),
weights remapped by bone name (top 4, renormalised), texture pack rebuilt at 2048 px with full mips, nameplate JBOY
collapsed (vertices at origin), everything else byte-kept. Replaced blocks are written as ZLIB (game also uses ZLIB in
HSPC/edit pacs). Gate: `beltview.py` renders flat + chain-bent pose next to stock.

## 5. Builds
| Build | Slot | Files | Status |
|---|---|---|---|
| iwgp_us_v1 | US Championship (2003 + 5003) | `_moddingwwe2k19_builds\belt\iwgp_us_v1\` | delivered 2026-11-14, awaiting in-game check |

Open risks for v1: (1) ZLIB instead of Oodle blocks in a prop pac (expected fine); (2) 29k vertices vs ~3.5k stock;
(3) roughness/metal look; (4) nameplate collapse.
