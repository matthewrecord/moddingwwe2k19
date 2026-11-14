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

- **Legacy titles** use main props in the 26xx-29xx range (e.g. 2043 Attitude Era WWE, 2904 Winged Eagle,
  **2905 Brahma Bull**, 2911 Cena US spinner, 2939 WWE 2013-14). Their cutscene partner is found by an identical
  texture pack: **2905 <-> 5038** (`belt_port.py` pairs are passed explicitly).
- Alignment offset is now computed per target (`auto_shift`: median per-bone cluster offset): 2003 (0,0.6,-0.4)-ish,
  5003/5038 about (0,-3.6,1.0).

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
| iwgp_us_v1 | US Championship (2003 + 5003) | `_moddingwwe2k19_builds\belt\iwgp_us_v1\` | superseded (Matthew wants the Brahma Bull slot) |
| iwgp_brahma_v4 | WWE Championship "Brahma Bull" (2905 + 5038) | plain `WWE 2K19` | **WORKS in game (Matthew, 2026-11-14): flag, banner, gold/silver plates, red strap all correct; loads every time** |
| iwgp_brahma_v1 | WWE Championship "Brahma Bull" (2905 + 5038) | plain `WWE 2K19` | **in game:** loads, wraps the waist correctly, but the plate shows as flat gold with no IWGP detail |
| iwgp_brahma_v2 | same | plain `WWE 2K19` | fix: texture pack DDS offsets 16-byte aligned + pack end padded (v1 had belt_n/belt_p at offsets = 8 mod 16), textures 1024 px / 11 mips exactly like stock | **in game:** same flat gold (stock textures still shown) |
| iwgp_brahma_v3 | same | plain `WWE 2K19` | replaced blocks written as stock-style Oodle blocks (stored Kraken chunks) instead of ZLIB; content identical to v2; awaiting check |

Open risks for v1: (1) ZLIB instead of Oodle blocks in a prop pac (expected fine); (2) 29k vertices vs ~3.5k stock;
(3) roughness/metal look; (4) nameplate collapse.

## 6. In-game result v1 (2026-11-14)
ZLIB blocks, the 29k-vertex mesh and the weights all work: the belt loads and wraps the waist. The plate rendered as flat gold.
Cause found: `texconv.write_pack` doesn't align DDS data; stock props put every DDS on a 16-byte boundary. `belt_port.write_pack16` fixes it.

## 7. v2 result and the ZLIB theory (2026-11-14)
v2 (aligned pack) still showed a plain gold plate: the stock Brahma Bull base colour is pale gold + metal mask, i.e. exactly what the
game draws, so the texture pack is not being taken from our pac while the model is. Theory: the texture path does not accept
ZLIB blocks. v3 writes OODL/KRKN blocks with stored (uncompressed) Kraken chunks (`0xCC 0x06` chunk header, 256 KB), verified with ooz.

## 8. Diagnostics instead of guesses (2026-11-14)
- `belt_diag.py` (checker): **in game the checker shows -> the game uses our texture pack** (v1-v3 'gold' was our own maps).
  But the plate is almost one solid green cell, while the offline render with the stored UVs shows ~7x7 cells: the game
  samples a much smaller texture region than the UVs we wrote. Offline hypotheses (UV = tangent.xy/xz, UV read as f16)
  do not reproduce it (`/tmp` renders, not kept).
- Next: `belt_diag.py --uvgrad` (R = u, G = v, grid every 1/16) installed; the colour read off a screenshot gives the
  sampled UV directly.

## 9. Freeze = size (2026-11-14)
`diag_uvgrad` (29k vertices) froze match loading (Matthew confirmed it is the belt; stock restored). Model block 2.82 MB raw vs
0.30 MB (2905) / 0.52 MB (5038) stock; whole pac 6.2 MB raw vs 3.7-4.1 MB. The earlier 29k builds loading once and this one freezing
fits a memory budget, not bad data (all blocks decode; structure identical). `belt_port.decimate` (meshoptimizer simplify, keeps
original vertices so seams survive) cuts to <= 6000 vertices: 5,484 / 5,508 vertices, model 0.52 MB. `diag_uvgrad_6k` installed.

## 10. Traced run (filetrace DLL), 2026-11-14
- With the tracer installed the 6k UV-gradient build **loaded** (freeze is intermittent). Log: at boot the game opens every
  `pac/prop/*.pac` and reads the first 64 KB (header scan); at match load it reads 2905 then 5038 whole (off 6144, n = SHDC size).
- UV-gradient screenshot matches the offline "as written" render (green plate, red strap, green side plates):
  **UVs are read correctly**. The checker 'solid green' was the plate's real UV region.
- SHDC word 15 rule found: (end of last block - first block offset) rounded up to 4; mine was 20 bytes over. Fixed.
- v3 close-up: smooth cream-gold plate, black strap, no colour detail. Next diag `--matte`: real colour + normal maps,
  belt_p forced metal 0 / roughness 128, to separate "colour map" from "metal shading".

## 11. Freeze trace (2026-11-14)
Traced freeze with `diag_matte` (stored Oodle, 3.3 MB): the hang comes after `pac/root/audience.pac` and **before** the
match opens any wrestler pac or `pac/prop/2905.pac` (in the loading run the order was audience -> ch* wrestlers -> ... -> prop/2905
3 s later). The belt is only touched by the boot header scan (first 64 KB of every prop pac) by then. Working theory:
the match loader budgets memory from the declared prop sizes, and the stored-Oodle pacs (3.3-5.6 MB vs 1.8 MB stock) tip it
over depending on arena/wrestlers: intermittent, at ~1/5 of the bar, never with stock. Test: `diag_matte` rebuilt with
**ZLIB** blocks (1.23 MB, smaller than stock; v1/v2 ZLIB builds always loaded). `belt_port.CODEC` = 'zlib' by default now.
Tracer note: the 8 s idle sampler never fired because unlogged I/O kept resetting it; v2 should trigger on 'no pac opened'.

## 12. Freeze solved (2026-11-14)
`diag_matte_zlib` (ZLIB blocks, 1.23 MB, smaller than stock) **loaded every time** across several matches/arenas (Matthew).
Conclusion: the stored-Oodle pacs (2-3x stock size) caused the intermittent hang at ~1/5 of the loading bar, before the belt is
read. Rule for belt builds: keep the pac at or below the stock size; ZLIB is the default codec.
Look: plate still reads as smooth tan/cream at the bottom edge of the entrance shots; the plate centre (flag, engraving) is out
of frame, so the colour-map question is still open.

## 13. Method reset: control experiment (2026-11-14)
Mistakes so far: several variables changed per build, results judged by eye, no control. Re-read of all three textured runs
(checker, UV gradient, real/matte): the flat face of the plate renders as ONE uniform colour in game, while the UVs written vary
across it. So the game does not render our mesh the way `beltview.py` predicts, and `beltview.py` itself was never validated.
Control: `belt_control.py` = STOCK 2905/5038 pacs with only the `belt` colour texture replaced by the UV gradient
(mesh, belt_n, belt_p, mask, Havok byte-identical; ZLIB texture block; 1.77/1.87 MB). Prediction committed BEFORE the run:
`writeup/img/belt_control_prediction.png` (row 1 = control, row 2 = our 6k mesh for comparison).
- game matches prediction -> renderer model valid; fault is in how our mesh is written -> field-by-field diff vs stock.
- game does not match -> the belt shader uses more than base UV x belt (suspect: stock `mask` block 4000), test that alone.

## 14. ROOT CAUSE of the flat/gold plate: facing convention (2026-11-14)
Control (stock mesh + UV gradient) matched the committed prediction: grid lines sharp on the bull plate -> per-pixel UV sampling works,
`beltview` geometry/UV model is valid. Our mesh showed no grid lines on the plate -> near-constant UVs on the visible faces.
Cause: 2K19 props store normals and winding pointing INTO the belt (2905 front faces at y~-3 with normal +y; 5038 front at
z<0 with normal +z). The 2K23 mesh points outward. `put_object` derives the winding from the normals, so the game culled the plate
front and drew its back faces, whose UVs are near-constant (u .39/.73, v .41-.83) -> flat colour in v1-v3 and every diag.
`beltview` doesn't cull, so offline renders hid it.
Fix: `mod_mesh` negates the normals (winding follows). Check: camera-facing front faces now sample u .09-.44 / v .19-.96 (photo
region, like stock .05-.93 / .15-.99); before: u .39-.73.
Build `iwgp_brahma_v4`: real textures, ZLIB, 5,484 / 5,508 vertices, 1.38 / 1.39 MB (stock 1.80 / 1.90). Installed in PLAIN.
TODO: beltview should back-face cull with the 2K19 convention so this class of bug shows offline.

## 15. Result (2026-11-14)
`iwgp_brahma_v4` confirmed in game by Matthew: the IWGP US title renders correctly on Big Show's entrance (flag, "UNITED STATES"
banner, engraved gold/silver plates, red strap), no freeze. The two fixes that mattered: ZLIB / stock-size pacs, and the 2K19 facing
convention. Not yet checked in game: the cutscene belt (5038, title presentation) close up, and the metal/roughness and normal-map
sign tuning. Tracer DLL removed from the plain install (moved with its logs to `_moddingwwe2k19_builds\telemetry\removed\`).

### Recipe for the next belt (updated 2026-11-14; every step is something that broke in game)
1. **Find the target pair:** `pac/prop/20xx|26xx-29xx` main (the Havok scene name gives the title); cutscene partner = the 50xx pac
   with an identical texture pack.
2. **Stage and back up** both stock pacs + the mod (`*_Default.mdl`, `*_Cutscene.mdl`, `Textures/`). Install the tracer
   (`tools/telemetry` dinput8.dll) and keep it in until the belt is signed off.
3. **Build:** `python3 -I tools/backport/belt_port.py --mod <mod> --stock <pac/prop> --main <main> --cut <cut> --out <dir> --metalize --gold-hue 35`
   (plus `--strap R,G,B`, `--gloss` to taste). Built in and checked automatically:
   - **Facing:** normals/winding flipped to the 2K19 convention (inward). Without it the plate's back faces show = flat colour.
   - **File size at or below stock:** ZLIB blocks, <= 6000 vertices before splitting. Oversized pacs froze match loading.
   - **Metal coverage (VITAL for a non-dull belt):** stock plates are ~61% fully metal with bright base colour (lum ~204). Mods
     ported from newer games usually mark far less (IWGP: 23-26%), and in 2K19 non-metal gold renders as dull brown paint no matter
     the gloss. `--metalize` fixes it; the builder **warns if plate metal fraction < 0.45 or metal base lum < 160**.
   - **Strap triangle span <= ~3 cm along the belt** (stock max 3.2 cm). Decimation made 27 cm triangles and the strap end stuck
     out at the back; `split_long` re-splits them. The builder warns above 3.3 cm.
   - **Gold hue:** stock gold = 35 deg. Check the menu render next to a stock belt.
4. **Read the WARNING lines and `manifest.json` (`quality`) before installing.** No warnings = ready.
5. **Menu picture / name:** `belt_menu.py` (championship select image), `tools/build/titlename.py` (all name variants, 7 languages;
   the game reads both `mods/SuperString/string_win.pac` copies).
6. **Install, record MD5s in the handoff, test:** entrance (worn, back view too), title presentation, several arenas.

## 16. Customisation: white strap, gloss, menu picture, title name (2026-11-14)
- `belt_port.py --strap R,G,B --gloss G`: recolours the strap front (mod colour map v 0..0.234, keeps the leather grain as
  relative brightness) and divides roughness by G. v5 = `--strap 236,233,226 --gloss 2.0`. The strap back/edges (black band
  v .234-.46) and the maroon leather visible around the plate photo are unchanged.
- `beltshot.py`: per-pixel renderer with 2K19 back-face culling (control: stock 2905 renders the Brahma Bull plate correctly).
- Menu picture: `pac/menu/win/Assets/wwe19_texture/belt/ltag_belt_all_win.pac` = SHDC, entry 0 layout with 91 names
  (`000_wwe_heavy` ... `023_wwe_champ_bull` ...), entries 1-90 = 512x256 BC7 DDS (DX10, no mips) in name order; identity
  rebuild with `belt_port.write_prop` is byte-exact. `belt_menu.py` renders the prop and replaces one picture
  (Brahma Bull = entry 21), framed like stock (zoom 1.65, exposure 2.4).
- Title name: live strings are `mods/SuperString/pac/string/win/string_win.pac` (pac/string/win has only .bak). Title 23 =
  Brahma Bull; variants 2100NN/2101NN/2102NN/2103NN/2108NN/2109NN/2110NN/2111NN/2120NN + 602003. `tools/build/titlename.py`
  renames all of them in all 7 language tables (exactly 10 strings per table changed, verified). Now 'AEW United States Championship'.

## 17. Gold hue (2026-11-14)
Matthew: the IWGP gold looked 'sickly yellow' next to the Stone Cold skull belt. Measured on gold pixels (hue 25-70, sat > 0.3):
stock 2K19 gold (skull and Brahma Bull menu pictures) hue 35 deg, mean RGB 156,132,98; IWGP colour map hue 50, R/G 1.08.
`belt_port.py --gold-hue 35` (`gold_hue()`) rotates only gold pixels (soft mask on hue/saturation) to the target hue; silver,
enamel and leather untouched. Result on the menu render: hue 36.2, mean RGB 148,123,86. `writeup/img/belt_gold_hue.png`
(top: skull, middle: before, bottom: after). Build `aew_us_v6` = v5 + `--gold-hue 35`.

## 18. Dull plate fixed by measurement, not by gloss (2026-11-14)
In game v6 looked dull/bronze under arena lights. Plate material vs stock Brahma Bull (front-facing plate faces, sampled through UVs):
| | metal fraction | base colour on metal | base lum | roughness |
|---|---|---|---|---|
| stock 2905 | 0.61 | 251,214,148 | 204 | 22 |
| v6 | 0.26 | 188,179,156 | 174 | 17 |
| v7 (`--metalize`) | 0.53 | 196,184,159 | 179 | 12 |
The mod's metal map marks only part of the gold; in 2K19's shader non-metal gold is diffuse brown, so gloss alone could not help.
`--metalize`: gold pixels (hue 20-70, sat > .2) in the plate/keeper part of the texture plus the mod's own metal -> metal 255,
base colour scaled toward stock brightness. Build `aew_us_v7` = v6 + `--metalize`.

## 19. WWE '91 arena freeze (2026-11-14, open)
After several good runs with v6 (pacs 1.39 MB, below stock), a freeze loading the WWE '91 arena. ~30 arena pacs were added/changed
by the arena work today. Not attributed. Control run: stock belts + tracer, same arena, before blaming either side.

## 20. Strap end sticking out at the back (2026-11-14)
Matthew: in v7 the strap end didn't sit at the back. Measured, not assumed: weights/bones identical to stock (same palette, 264 vs
255 verts on the end bones, same x ranges), end thickness within 3 mm of stock. Difference: **triangle length along the belt**,
max 27.4 cm after decimation vs 3.2 cm stock (bones 6-10 cm apart), so flat facets cut across the bends. `split_long` splits
x-spans > 3 cm (v8: max 2.99 cm, 6,796 / 7,020 vertices, 1.40 / 1.42 MB, still below stock). Builder `quality()` now checks
metal fraction, metal brightness, strap span and pac size and prints WARNING lines.

## 21. Freeze with v8, traced (2026-11-14)
Session trace `wwe2k19_filetrace_41036359.log`: match 1 loaded fine (prop 2905 read at 67.9 s and 72.0 s, cutscene 5038 at 142.4 s,
title presentation shown). The freeze came on the NEXT match load at 320 s: last opened file `pac/arena/ringmat/arringmatcm00000.pac`;
in a good load the next files are `pac/root/audience_p30/p10/audience.pac` then `pac/ch/*`. The belt was not being read at the
moment of the hang (it was loaded earlier in the session). Tracer v1's sampler never fired: unlogged I/O (audio) reset its idle
timer. Asked Matthew for a Task Manager full dump of the frozen process. Tracer v2 (`dinput8_filetrace.c`): samples threads when no
.pac has been opened for 15 s, and on a `DUMP_NOW` file next to the exe.

## 22. Full dump of the v8 freeze (Task Manager dump, 2026-11-14)
`C:\Users\Acer\AppData\Local\Temp\WWE2K19_x64.DMP` (3.97 GB, not copied; read in place with `minidump` on the laptop).
- 144 threads, **all blocked in Windows waits, none running**: a deadlock / wait on a signal that never comes, not a crash or a loop.
- Main thread (24776): waiting at exe+ab06a -> exe+127fea0 on the global job object at 0x1425e8920 (waits for a batch of
  background jobs).
- Loader / file thread (30008, the one that logged every open): a `CGameWorkerThread`, idle in its sleep-poll loop
  (exe+8f7ea5 tests [obj+0x58]; obj 0x787a210 has 0 = no work). Its object references SOUNDPAC / `/SOND/DUPL/` names.
- 18 pool workers idle at exe+1298895 (waiting for jobs).
So: the main thread waits for a job that no worker holds (it never started or was dropped). The dump does not name the asset.
Not attributed to the belt: the belt was loaded and displayed earlier in the session; the hang is on the next match load.
Plan (control, per WORKFLOW): tracer v2 + STOCK belts, several back-to-back matches including WWE '91. If stock never
freezes in the same sequence, bisect v8 vs stock (model block only / texture block only).
Session tools: `$HOME/dmp/hang.py` (per-thread wait sites), `obj.py`, `wwedisasm.py` (note: never name a script dis.py).

## 23. Title-match intro video (2026-11-14)
Matthew: the AEW/IWGP title has no title-match intro animation. Findings:
- `pac/menu/win/Assets/wwe19_anime/ltag_cutscene_belt_win.pac` + `Projects/ltpj_cutscene_belt*_win.pac` are the
  Create-a-Championship name-card styles (basic/classic/dark/default/hardcore fonts), not per-belt.
- Per-title intro videos are `movies/titantron/bel_NNNN_0_0.bk2` (Bink 2 'KB2j', 1920x1080, 300 frames, 29.97/30 fps, 10 s,
  ~20 MB). NNNN = the championship number used by the menu pictures (`005_united_states` -> bel_0005).
  Present: 0-3,5-8,10-13,16,18,20,25,33-35,46,50,52-61. **23 (Brahma Bull) has none** -> no intro.
- Test 1 (mechanism): `bel_0023_0_0.bk2` = copy of `bel_0005` (US title video, md5 ac71460b7f03bf39492c66052d485f57).
  New file, nothing overwritten; delete it to undo.
- For a real IWGP video: render 300 frames 1920x1080 (beltshot-style) and encode Bink 2 with RAD Video Tools (Windows).
- Test 1 result: **no intro played** with `bel_0023_0_0.bk2` present. So the video file alone does not enable an intro for
  title 23; which titles get one is decided elsewhere (not found). Matthew: "it's fine", dropped. Placeholder moved out to
  `_moddingwwe2k19_builds\belt\removed\`. Lead if revisited: a per-title flag/table referencing the bel_ ids (not searched).
- Deeper look (2026-11-14, after Matthew asked): the exe builds the name with `bel_%04d_%d_%d` at exe+0x49bd52 from a
  **video id**: id // 100000 selects the category (5 = belt video), then NNNN = (id // 100) % 1000, a = (id // 10) % 10,
  b = id % 10. So `bel_0023_0_0` = video id **502300**.
- `pac/root/misc01_start.pac` (+ `_p10`, `_p20`, raw, uncompressed) hold sequential video-id lists (500000, 500100 ... 503900,
  4 lists, with 1038xx/1071xx entries before them); 502300 is already in every list, so they are not what blocks title 23.
- The per-championship setting (which video a title match intro plays) was NOT found: searching for the Brahma Bull prop
  pair 2905/5038 (u16/u32, adjacent) in pac/root, misc, universe, match_make, ingame, edit.pac, menu found only coincidences.
  Next step if resumed: find the championship table by the title-name string ids (2100NN) or by tracing callers of
  exe+0x49bd52 back to where the video id comes from.
- 22 of 62 numbered titles have no bel_ video in vanilla (e.g. 4, 9, 14, 15, 17, 19, 21-24, 26-32), so a missing intro is
  normal for legacy titles in this game.
- Static trace (2026-11-14): the name builder is function exe+0x49ba20 (args: rcx buf, rdx, r8d = video id, r9d = type);
  8 callers. The arena-screen player exe+0x156ec20 (rcx = titantron object, video id at [obj+0x84]) labels the clip
  'Championship' or 'Titantron' (flag in ebx at exe+0x156ed79) and calls the builder with [obj+0x84]. The id is NOT computed
  from a constant in code (only 500000 immediate in .text is unrelated audio setup), so it comes from data.
- Tracer v3 (`dinput8_filetrace.c`): execution breakpoints (DR0-DR2, no debugger) on exe+0x156ec20, +0x156ed79, +0x49ba20,
  logging the video ids, champ flag and return addresses. Plan: one title match with a title that has an intro (e.g. WWE US,
  bel_0005) and one with the AEW/IWGP title (slot 23), then compare.
