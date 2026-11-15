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
- v3 run (trace 43463687): US title match -> video ids 61000000 then **500500** (bel_0005, intro shown), both via
  exe+0x573940 (screen player, id from [obj+0x20]; 'Championship' label when id // 100000 == 5). AEW/IWGP slot 23 ->
  12500000 only, **no 5023xx request**. So the title intro is scheduled upstream as its own screen object; nothing schedules
  one for title 23. v3b logs the call chain for every exe+0x573940 / 0x49ba20 hit to find the scheduler.
- v3b run (trace 43804859): the 500500 screen object (vtbl +21065c8) comes from exe+0x582f80 (create screen object), called at
  exe+0x5815d0 in a jump-table case of exe+0x5814c0 (title-match sequence steps, case = [step+4], 0..0x14). That case:
  `edx = exe+0x5501a0(0)` (current championship number, must be < 245; byte [0x14266f6f5] must be 0), then
  `exe+0x4a0d80(table=[[0x1425e3800]+0x40], key=championship, field=1, &id)` -> id = the title's intro video (500500 for US).
  exe+0x4a0d80 is a generic DB query over a base table ([+0x298]) plus a list of extra tables ([+0x2a8], count [+0x18]).
- Tracer v3c: breakpoints on the step switch (+0x5814e6), the lookup call (+0x581594, key) and its result (+0x581599).
- v3c run (trace 44155984): US title match -> sequence step 8 ran, `title_video_lookup(key=5, field=1) -> 500500`, and
  `pac/evt/29000.pac` ("29000_Titlematch_Belt_Scene") loaded at that moment. AEW/IWGP match -> step 8 never ran, no lookup,
  no 29000. BUT the event files loaded before were wrestler entrances: `evt/00105` = AJ Styles, `evt/00125` = Big Show
  (evt pacs = HSPC -> BPE (`tools/audio/bpe.py`): file 0 '0FOP' event, file 1 SHDC assets). The two matches differed in
  wrestler AND title, so title vs wrestler is not separated (my error: two variables). Control needed: same wrestler,
  US title vs AEW title.

### 24. Same-wrestler control (2026-11-14, log `wwe2k19_filetrace_44758203.log`)

Big Show entered (evt 00125) both times; only the title changed.

| Match | Belt props | Sequence steps hit | Title-belt scene | Video lookup |
|---|---|---|---|---|
| WWE US title | 2003 / 5003 | 1, then **8** | evt 29000 loaded | key=5, field=1 → found, **500500** |
| AEW US title (slot 23) | 2905 / 5038 | 1 only | never loaded | never called |

**Proven:** the wrestler isn't the variable. For title 23, sequence step 8 (the title-belt scene, which also looks up the video) is never queued at all. The video file and the DB lookup aren't the blocker. Whatever builds the intro sequence decides per title whether to add step 8.
**Also learned:** the lookup key for the US title is 5, not its slot number. It's a separate per-title video/scene index, so title 23 probably has no entry, or a flag that's off.
**Next:** find the code that queues step 8 (the writer of `[step+4]=8`), and see which per-title field it tests.

### 25. What gates the title intro: the championship table in `pac/evt/evt_data.pac` (2026-11-14)

Found by reading the game's DB object out of the full dump (`[[exe+0x25e3800]+0x40]`) back to its source SHDC, then matching
that SHDC's BPE entry bytes against files on disk.

- `pac/evt/evt_data.pac`: HSPC → SHDC with 62 BPE-compressed text tables. **Id 13 = championship table**. `evt_data_p10.pac`
  carries a full copy of id 13 (it is a patch layer, so edit both). p20/p30 don't touch it.
- Row format (12 columns): `title_id intro_video intro_frames cutscene_prop main_prop 0 str_a str_b 0 0 0 0`.
  The US title (id 5) is `5 500500 540 5003 2003 ...`. Title 23 (Brahma Bull → AEW US) was `23 0 0 5038 2905 ...`.
- Titles with video 0 never get match-intro step 8 (the title-belt scene). The step-8 handler looks up field 1 (video id) by
  the title id from `exe+0x5501a0`. This also explains why the stock Brahma Bull belt never had an intro.
- Edit: `23 502300 600 5038 2905 ...` → plays `movies/titantron/bel_0023_0_0.bk2`. 600 = the frame count the other
  10-second intros use.
- Tool: `tools/build/titletable.py` (`--show`, `--set "ID VIDEO FRAMES"`). It includes a BPE *encoder*: Gage pair
  table in the layout `tools/audio/bpe.py` decodes; skip bytes >127 are followed by exactly one entry. Codes are only reused
  when free in the data *and* in every earlier pair. Unedited round trips of both pacs are byte-identical. The edited
  entry is the same size as stock (1232 bytes), so both pacs keep their stock sizes.
- Prediction (written before the test): with a .bk2 at `bel_0023_0_0.bk2`, the AEW title match shows the step-8 scene, the
  tracer logs `seq_step case=8` and a lookup with key=23, and the result is 502300.
- **Result (2026-11-14): confirmed in game.** The intro played for the AEW US title. The tracer logged `seq_step case=8`,
  lookup key=23 → found, video 502300, exactly as predicted.

### 26. Intro video made from the belt itself (2026-11-14)
`tools/backport/belt_intro.py MAIN.pac OUT.mp4 --name "..."` rasterises the 2K19 prop once (beltshot geometry + culling) into a
G-buffer, then relights it every frame: light sweep, slow push-in, flare, glow, title name and an underline that fade in. Output is
1920x1080, 30 fps, 300 frames (10 s, the stock intro length), H.264 for Matthew to convert to Bink2 as
`movies/titantron/bel_0023_0_0.bk2`. The first render is at `_moddingwwe2k19_builds\belt\intro\aew_us_title_intro.mp4`.
- v2 (Matthew's notes: the colours were gray and washed out, the sweep slightly slow, and the background should be transparent):
  - All stock `bel_NNNN` intros are Bink2 **with alpha** (header flags 0x100012, bit 0x100000), 1920x1080, 240–301 frames.
  - The renderer now writes RGBA: belt, glow, flare and text over a transparent background, with no black plate.
  - Saturation is ×1.6 plus slight contrast, the strap diffuse is brighter, and the sweep finishes at 62% of the clip instead of 75%.
  - Deliverables are in `_moddingwwe2k19_builds\belt\intro\`: `aew_us_title_intro_alpha.mov` (PNG codec, RGBA),
    `..._frames_rgba.zip` (300 PNGs) and `..._preview_on_gray.mp4` (viewing only). Enable alpha when converting to Bink2.

## 27. Smoother white strap: v9 (2026-11-14)
Matthew: the strap looks a little grainy and textured; he wants it smoother and whiter without looking cartoony.
- `belt_port.py --strap-smooth K` (0..1), applied to the strap-front band only (mod colour map v 0..0.234):
  - Colour: the leather grain (relative brightness minus a blurred copy) is scaled by 1-K. The broad shading is kept, and its
    contrast is halved at K=1.
  - Normal map: the bump vectors are pulled toward neutral by K.
  - Roughness: the variation around its mean is scaled by 1-K, so the sheen is even instead of speckled.
- v8 rebuilds byte-identically from `--strap 236,233,226 --gloss 2.0 --gold-hue 35 --metalize`, so v9 is v8 plus `--strap-smooth 0.75`.
  No quality warnings. The pacs are 1.27 MB, still below stock.
- Intro v3 (video only, Matthew: exaggerate the smooth strap in the video):
  - Rendered from a `--strap-smooth 1.0` build, plus `belt_intro.py --strap-soft 0.9`. Strap texels (non-metal, unsaturated,
    bright) get a heavily blurred colour lifted to warm white, with even gloss.
  - Frames are in `_moddingwwe2k19_builds\belt\intro\frames_rgba_v3\`.

## 28. Colour match to Matthew's reference photo of the real belt: v10 belt + intro v4 (2026-11-14)
Reference: a studio photo of the real IWGP US belt. Measured from it:
- Gold is rose/copper: hue 29, saturation 0.66, value 0.78.
- Stripes are magenta-red (hue about 336, fully saturated). The blue field is hue 206, saturation 0.8. The banners are glossy neutral black.
- The strap is a cool white (202,210,212). The key light comes from the top: the strap is bright at the top and darker toward the bottom.

Belt textures (`belt_port.py`):
- `--gold-hue 29` plus a new `--grade 1.0` (plates and keepers only): gold saturation ×1.55 and value ×0.9; reds pushed toward 338
  with saturation ×1.35; blues toward 208 with saturation ×1.3.
- `--strap 214,220,224`, a cool white instead of the warm 236,233,226.
- Result: metal gold hue 29.1, saturation 0.64. Metal fraction 0.50, no warnings. The pac is 1.26 MB, below stock.
- v10 = `--strap 214,220,224 --gloss 2.0 --gold-hue 29 --metalize --strap-smooth 0.75 --grade 1.0`.

Intro renderer (`belt_intro.py`), video only:
- Key-light falloff from the top-left, with cool lavender in the white's shadows.
- Deeper gold shadows, and a soft highlight shoulder (1-exp) instead of hard clipping.
- Extra saturation and warmth on metal.
- Enamel pass: magenta-red stripes, bright blue, neutral black banners.
- The dark strap outline is replaced with strap white, and the orange halo with a soft drop shadow.

## 29. Intro from the reference photo instead of a render (2026-11-14)
Matthew asked for a video made from the actual photo, with the background isolated, the stand removed, and the belt not held in shadow.
- Cut-out (`assets/belt/aew_us_reference_cutout.png`):
  - rembg (isnet and u2net) keeps the plate and keepers but drops the white strap, because it blends into the pale backdrop.
  - Fix: union of the isnet mask and two hand-drawn strap polygons, refined with OpenCV GrabCut, then keep the largest component.
  - The photo's edited background patch at the right strap end is excluded (x ≥ 1424 above y 400).
  - The acrylic stand's two posts (in front of the plate's lower white border) are cut from the mask. The belt edge across them is
    interpolated from the neighbouring columns, and the hidden pixels are filled with `cv2.inpaint` (Telea).
- `tools/backport/photo_intro.py`: the photo stays fully lit, never shadowed, with slight richness and lift. Animation: a specular
  sweep across metal pixels (copper, detected by hue/saturation, and silver), a flare with orange and purple streaks riding the
  sweep, a soft drop shadow, a push-in, and copper title text. Output is RGBA, 1920x1080, 30 fps, 300 frames.
- photo2: the flare and sweep now run from 6% to 94% of the belt's width instead of starting and ending off it. The flare's
  strength also scales with the (blurred) belt coverage under its centre. Frames are in `intro\frames_rgba_photo2\`.
- Matthew's Bink encode of photo2 (2026-11-14) is installed as `movies/titantron/bel_0023_0_0.bk2` (MD5 0357f848a3fa3e157c0f1a194c97ac4b):
  - Header is `KB2n`, 1920x1080, 300 frames, 30 fps, alpha (flags 0x140012).
  - **Risk:** the stock intros are `KB2i`/`KB2j`, and the game's `bink2w64.dll` contains revision tags only up to `KB2m`. A `KB2n`
    file may not play. Not yet tested in game.
  - The previous placeholder (US-title copy) is saved in `intro\installed_before_photo\`.
- **Result: the `KB2n` file hangs the game at the intro** (trace 86111015):
  - Step 8 ran at 259.8 s, with key 23 → 502300, then no further I/O.
  - So the game's `bink2w64.dll` (which lists up to `KB2m`) opens the file but can't play it, and doesn't fail cleanly.
  - `/Slices2` does not change the tag (the 2026.10 encoder always writes `n`).
  - Old public RAD Video Tools releases only encode Bink 1 (the Bink 2 encoder ships with the licensed SDK).
  - Placeholder restored. The hung file is kept as `intro\photo_KB2n_hung.bk2`.
  - Remaining routes: patch the tag to `m` (works only if the bitstream is unchanged), or ship a newer `bink2w64.dll`.
- **Bink 1 route:** the game's `bink2w64.dll` also lists `BIKi`/`BIKk`, and 8 titantrons in `movies/titantron` are Bink 1 (`BIKi`)
  renamed to `.bk2`. Matthew's Bink 1 encode of photo2 (old RAD tools, alpha on, forced 30 fps, no audio) is `BIKi`, 1920x1080,
  300 frames, 30/1, flags 0x100000 (alpha). It is installed as `bel_0023_0_0.bk2` (MD5 e3a445af1b555fbe19725e76b9308a16), pending an in-game test.
  Untested: Bink 1 *with alpha* (the existing Bink 1 titantrons have none).

## 30. v11: brighter plate (2026-11-14)
- The Bink 1 intro (`BIKi`, alpha) **plays correctly in game**.
- Matthew: v10 is "a notch too red" and much too dark in game (screenshot: the plate reads near-black under arena light).
- Measured: v10's metal albedo is not darker than stock (lum 188 vs 203). The difference is **roughness**. `--gloss 2.0` put
  metal texels at 0.047 vs stock 0.089, a near-mirror that reflects the dark arena, so it reads as black. Gloss raised
  brightness on the flat preview and darkened the belt in game; the preview renderer has no environment reflections.
- v11 = `--strap 214,220,224 --gloss 1.0 --gold-hue 30 --metalize --strap-smooth 0.75 --grade 1.0`. The gold grade is now hue 28,
  saturation ×1.35, value ×1.08 (was ×1.55 / ×0.9). Result: metal roughness 0.102 (about stock), metal lum 193, metal hue 34.5. No warnings.
- Installed: 2905 = 2059222f559b8214688d2dcd67725b8b, 5038 = 3b5f6435c2f62765c464468a73edf31b. v10 is kept in `aew_us_v10_installed\`.
- Lesson for the recipe: **don't push gloss above stock roughness on metal**. In a dark arena, low roughness reads as dark, not shiny.

## 31. Stock-belt survey: how our plate differs from every stock belt (2026-11-14)
Matthew: v11 is dramatically worse (plate near-black and dirty in game). He asked to compare against all the stock belts,
including how the underlying elements look, not just settings.
Measured on 12 stock title props (2001-2010, 2904, 2910, 2915, 2933, stock 2905), using only texels the mesh actually uses:

| | stock (typical) | ours v8/v10/v11 |
|---|---|---|
| Metal albedo | **flat constant** (252,221,164), ±3 between the 5th and 95th percentile | the 2K23 *photo* of the plate |
| Metal fine-detail contrast (lum − blur) | 1.6–8.7 | **44–48** (≈10×) |
| Dark metal texels (lum < 0.35) | 0–2 % | 10–13 % |
| Metal hue / saturation | 38.7 / 0.35–0.41 (identical across belts) | 29–37 / 0.20–0.27 |
| Metal roughness | ~0.10 | 0.05 (v8/v10), 0.11 (v11) |
| Leather roughness | 0.18–0.6 (mean ~0.4) | 0.08–0.17 (glossy) |
| Engraving | normal map only (tilt 0.08–0.33) | normal map (0.165) **plus** baked into albedo |

Conclusion: 2K19 belts put **all** detail in the normal map and give metal one flat gold colour. The game's lighting makes it
read as gold. Our plate carried the 2K23 photo's baked lighting, grime and dark crevices into a metal albedo. Under 2K19's
metal shading every dark texel becomes a dark reflection, so the plate looks black and dirty. `--metalize` (brighten ×2.2) made
grime brighter but kept it. Hue grading and gloss were treating the symptom.

v12 = `--strap 214,220,224 --metalize --stock-metal 252,221,164 --leather-rough 0.4 --strap-smooth 0.75` (no grade, gloss 1):
- Metal texels get the flat stock gold (unsaturated metal gets flat silver 225,225,230), with only ±6% very low-frequency shading.
- Leather roughness is 0.4, like stock.
- Result: metal lum 209 (stock 211) and hue 38.7 (stock 38.7). Dark metal is 2%. HF is 30, from the plate edges and silver/gold
  boundaries. No warnings. Pacs are 1.23/1.25 MB.
- Installed: 2905 = bb9dcdcca4671d33ce4e80927073b800, 5038 = 90a18f744332cb28c0226c729c5bbcb7.
- Caveat: the preview renderer shows flat cream (it has no normal map or environment), so only the game shows the real result.

## 32. In-game look emulator `tools/backport/gamelook.py` and a stock comparison sheet (2026-11-14)
What it models:
- Per-pixel normal mapping (belt_n, tangents from UVs) and metal/roughness from belt_p.
- Reflections of a synthetic arena: dark ceiling, rig spots, crowd band, bright canvas, and camera-side broadcast light,
  prefiltered by roughness, plus a GGX key light and filmic tone mapping.
- Sheet: `writeup/img/stock_vs_aew_gamelook.png` (16 belts; labels are from the SuperString names per title slot, and some don't match the prop shown).

**Validation failed for our belt.** The emulator renders v12 as clean pale gold, but the game shows v12 dark and blotchy. So the game
does something to our prop that the emulator (and every offline check so far) doesn't model. Ruled out by measurement:
vertex colour (all 255 like stock), the stored-tangent convention (= +dP/du like stock), front-face UV handedness (0.99 vs stock 0.98),
normal-map statistics (tilt and high frequency within the stock range), and metal albedo/roughness (v12 matches stock).
Next: an in-game **swap test** to separate mesh from textures (A: stock Brahma textures on our mesh; B: our v12 textures on the
stock Brahma mesh), before any further look tuning.

## 33. Closed (2026-11-14)
Matthew ended the look work: no more in-game tests. v10 is restored as the installed belt (the last version he called better);
v11/v12 are kept in their builds folders. The intro (Bink 1 with alpha, from the reference photo) works.
Open and unexplained: why our prop renders darker in game than its textures predict. Documented in section 32, including the swap test
that would split mesh from textures, if anyone picks this up again.
Lesson (process): the cause should have been isolated with a stock-vs-mod emulator and a swap test early on, not tuned by eye
over 12 in-game rounds. Matthew's time is the scarce resource.

## 34. Root cause found offline: flat plate geometry (2026-11-14, no further in-game tests)
- **Shader decoded** (`pac/shader/win/ysh_win.pac`; DXBC → SPIR-V via vkd3d-compiler → GLSL via spirv-cross). Belts use
  `yPBR_RTCS_Belt`. G-buffer PS: base = g_texBaseColor (lerped to a per-object tint), metal/rough = g_texMtlRgh.xy, AO =
  g_texWorldAO at TEXCOORD0.zw (constant for one-UV props, so the same for stock and ours), normal =
  normalize(N − nx·T − ny·cross(N,T)). This confirms our channel layout. The normal-map channel relationship was checked by
  integrability (curl/sym 0.23 for ours, 0.25–0.28 for stock).
- **Real difference:** stock plate *vertex normals* are domed. Front-facing metal normals spread a median of 39–46° (p90 46–70°)
  radially around each plate. The 2K23 plate is flat (median 8°). Facing the camera, flat polished gold mirrors the dark arena behind
  the camera, so it reads dark and muddy, whatever its colour. This explains why every texture-only change failed, and why more gloss made it darker.
- **Emulator re-validated:** with a dark arena behind the camera (as in game), `gamelook.py` now reproduces the in-game pattern
  (stock plates bright and modelled, ours dark and muddy).
- **Fix:** `belt_port.py --pillow 1.2`. It bends each plate's front normals toward its rim (per connected front-facing piece, axis
  auto-detected for the main +y and cutscene +z props), giving a median of 44.6° like stock.
- **v14** = `--strap 214,220,224 --metalize --stock-metal 252,221,164 --leather-rough 0.4 --strap-smooth 0.75 --pillow 1.2`.
  No warnings; winding agreement 1.0. Installed: 2905 = 8cfb33a8cd5923737b01fc320d28c1b1, 5038 = 2c5e8a7419f4a45128ac8d1c5b777216.
  Emulator comparison: `writeup/img/aew_v14_vs_stock.png`.
- **Remaining, visible in the emulator:** the gold reads paler than stock, and the 2K23 normal map adds speckle. Both are tunable
  offline in `gamelook.py` before anything goes to the game.

## 35. v15: stock-style enamel (2026-11-14)
Matthew (v14 in game: big progress). The reds, whites and blues are much duller than on the WWE US title.
Measured enamel albedo (texels used by the mesh):

| | red | blue | white | metal | roughness |
|---|---|---|---|---|---|
| WWE US 2003 (stock) | (222,48,49) v .87 | (60,98,167) v .65 | (255,255,255) | 0 | 0.10–0.15 |
| ours v14 | (82,36,33) v .32 | (16,24,46) v .18 | — | 0.15–0.25 | 0.34 |

`belt_port.py --stock-enamel` classifies enamel on the ORIGINAL mod colours (plate area only): red/blue by hue, and white = bright,
unsaturated texels within 6 px of red/blue. It sets flat stock enamel colours (±15% low-frequency shading), metal 0, roughness ~0.12.
v15 = v14 + `--stock-enamel`. Result: red (227,48,49) v .89, blue (57,93,161) v .63, metal 0.02–0.04, roughness 0.13–0.14 (matches stock). No warnings.
Installed: 2905 = see handoff; emulator crop: `writeup/img/aew_v15_enamel_vs_stock.png`.

## 36. Lighting stage decoded: belts get a "too dark" boost only during entrances (2026-11-14)
The forward lighting PS of `yPBR_RTCS_Belt` (blob 001), decompiled, has belt-specific inputs:
- Material flag `g_bChampionBeltCorrection` (g_tMaterial +12).
- Globals in `g_tGlobal_Light`: `g_fRoughnessMultiplier/Min_ChampionBelt`, `g_fIrradianceMultiplier/Min_ChampionBelt` and
  `g_fIBLSpecularMultiplier/Min_ChampionBelt`.
- With the correction on: roughness = max(rough × mul, min); arena IBL irradiance × IrrMul (floor IrrMin); IBL specular × SpcMul (floor SpcMin).

The values come from Yuke's own `pac/misc/parameter/todo/todo_wwe19_champion_belt_too_dark.pac` (NIBJ table):
- Belt_IrrMul 1.0, **Belt_SpcMul 2.0**, Belt_IrrMin 0, Belt_SpcMin 0.2.
- Switches: **Entrance=1, Winning=0, TitleMatch=0**, CACMenu=0, Always=0.

So every belt (stock too) gets 2× reflections during entrances but not in title-match presentations or winner scenes. That matches
Matthew's screenshots: v14 looked good, and v15 (gold identical to v14) looked dark in title-match scenes.
There's also `..._cutscene_no.pac` (per-cutscene overrides), not changed.

Change: `tools/build/beltdark.py` (`--show`, `--on/--off` switches, `--irrmul/--spcmul/--irrmin/--spcmin`). It sets TitleMatch=1
and Winning=1; the values are unchanged. The unedited round trip of the container is byte-identical.
Installed `pac/misc/parameter/todo/todo_wwe19_champion_belt_too_dark.pac` = a638e5c04132fc60104cb45b3537a3fe
(stock d04c87c49c5e3cb5a80024e3504dfa73, backed up in `backup_originals`).
Effect: all belts look in title-match and winner scenes the way they already look in entrances. It's a global change, but it is Yuke's
own correction, extended to the scenes where it was off.

## 37. Real arena lighting in the emulator; v16 (2026-11-14)
- `tools/backport/arenaibl.py`: arena IBL pacs (`pac/arena/ibl/ariblNNNNN.pac`) = SHDC → Oodle (via `oodl.py`/pyooz) → two BC6H
  cube arrays (DX10 fmt 95, cube flag): 64² irradiance and 256² prefiltered specular (9 mips), 35 cubes, plus a JSON probe layout
  (IBL_12 = the ring probe, at (0,-300,0) cm). Written as equirect npz.
  - **Limitation:** texture2ddecoder/Pillow decode BC6H to clamped 8-bit, so HDR above 1.0 is lost; 30% of mip0 is clipped,
    mostly the canvas. A float BC6H decoder was not available: fetching the bcdec source was blocked in this environment.
- `gamelook.py --ibl NPZ [--yaw DEG] [--nocorr]` uses the decoded lighting path:
  - base^2.2; diffuse = base·(1−metal)·irradiance(N); F0 = lerp(0.04, base, metal).
  - spec = prefilter(R, lod = rough·6)·(F0·A + B), with A/B from Karis' EnvBRDF fit.
  - Belt correction ×2 specular (floor 0.2) unless `--nocorr`.
- With the real ring probe, stock IC vs v15 showed the remaining faults clearly:
  1. **White blotches on the gold:** the photo's desaturated glare had been classified as silver. Silver now = sat < .18 **and** v < .8,
     mode-filtered (9 px).
  2. **Patchy shading:** each of ~21 mesh shells had its own dome. Plates are now found from the x-profile of front plate geometry
     (the main plate is the tall run around x = 0; keepers are the runs between dips). That gives 9 plates, one dome each, on both props.
- **v16** = v15 options + these two fixes. No warnings. Installed: 2905 = see handoff; comparison under real arena light:
  `writeup/img/aew_v16_vs_IC_real_arena_light.png`.

## 38. v17: polished silver letters on black banners (2026-11-14)
Matthew asked for reflective metal on the banner letters only (IWGP / UNITED STATES / CHAMPION, plus the keepers' UNITED STATES CHAMPION), for contrast.
- `belt_port.py --banner-letters`, classified on the ORIGINAL mod colours:
  - Banner = plate texels where near-black (v < .20, unsaturated) covers more than 38% of a size/64 window. Letters are grey islands in it.
  - Letters (v > .26, sat < .28, opened) → flat silver (228,228,234), metal, roughness ~0.07.
  - Field → black (12,12,14), non-metal, roughness 0.35. At 0.12 the field mirrored the bright canvas and read teal-grey.
  - The black atlas padding strip (v .46–.54) is excluded.
- Fix to `--stock-enamel`: red now has to be within 7 px of white stripes/stars. The maroon leather behind the plate photo had
  been turning into a bright red rim.
- Physical limit seen with the real arena IBL: any glossy dielectric reflects ~4% of the bright canvas, so the lower
  (downward-facing) banner reads dark grey rather than pure black. The game uses fixed F0 = 0.04, so this is the same as in game.
- v17 = v16 + `--banner-letters`. No warnings. Installed: 2905 = see handoff; comparison: `writeup/img/aew_IC_v16_v17_real_arena_light.png`.

## 39. Community mods: AO Belt Lighting Patch and Big Gold New
- **AO Belt Lighting Patch** edits only `todo_wwe19_champion_belt_too_dark.pac`: Belt_SpcMul 2.0 → 11.31 and SpcMin 0 → 1.75e-5. The four scene switches change from 0/1 to 0x80000000, and Always becomes 0x50000000, so the switches are bit flags, not booleans. It is a pure specular boost on the belt-correction path. In the emulator, ×11.3 mostly lifts the dark leather and straps to a greyish sheen; the gold barely changes, because gold reflections are already near clipping.
- **Big Gold New** (2009/5009, World Heavyweight) keeps stock geometry, normal maps and material maps. It replaces only the base colour, which grows from 1024² to 4096² with engraving baked into the albedo (cavity darkening; p5/p95 luminance 110/202, against flat 204 in stock). Its gold is also more yellow (hue 47 vs 38, sat .52 vs .41).
- Applied: `belt_port.py --cavity K` bakes crevice darkening from the integrated normal-map height (v18, K=0.7).
