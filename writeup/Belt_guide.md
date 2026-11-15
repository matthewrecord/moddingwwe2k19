# Title belts in WWE 2K19: what we did, what we learned, how to backport the next one

This file is the condensed guide. `Belt_backport.md` is the full lab notebook (sections 1–41), with every
experiment, number and image. Read this file first.

Worked example: the 2K23 "IWGP / AEW United States" mod, ported into the Brahma Bull slot (title 23; props
`pac/prop/2905.pac` main, `5038.pac` cutscene/folded) of the plain install. It was signed off in game on 2026-11-15 as
"damn fine looking" (v17 belt plus the photo menu picture).

---

## 1. What was done to the AEW US belt (final state)

| Piece | File(s) | How |
|---|---|---|
| Model + textures | `pac/prop/2905.pac`, `5038.pac` | `tools/backport/belt_port.py` (mesh from the 2K23 mod, re-skinned to the 2K19 belt skeleton, decimated, textures rebuilt as below) |
| Name | `mods/SuperString/.../string_win.pac` (both copies) | `tools/build/titlename.py` → "AEW United States Championship", 10 strings × 7 languages |
| Title-match intro video | `movies/titantron/bel_0023_0_0.bk2` | `photo_intro.py` renders frames from the reference photo; encoded as **Bink 1 (BIKi) with alpha**, renamed .bk2 |
| Championship table row | `pac/evt/evt_data.pac` + `evt_data_p10.pac` (table id 13) | `tools/build/titletable.py --set "23 502300 600"` (video id, frames) |
| Belt-correction lighting | `pac/misc/parameter/todo/todo_wwe19_champion_belt_too_dark.pac` | `tools/build/beltdark.py --on TitleMatch --on Winning` (stock is Entrance only) |
| Menu picture | `pac/menu/win/Assets/wwe19_texture/belt/ltag_belt_all_win.pac`, entry 21 `023_wwe_champ_bull` | `belt_menu.py --image assets/belt/aew_us_reference_cutout.png --zoom 0.8` |

Final belt build (v17; MD5s are in `handoff/`):
```
python3 -I tools/backport/belt_port.py --mod <mod> --stock <backup_originals> --main 2905 --cut 5038 --out <dir> \
  --strap 214,220,224 --metalize --stock-metal 252,221,164 --leather-rough 0.4 --strap-smooth 0.75 \
  --pillow 1.2 --stock-enamel --banner-letters
```
v19 (Ultra-Deluxe-style: 2048 px, `--metal-rough 0.18 --nstrength 1.5 --cavity 1.0 --leather-rough 0.25`) was tested in game on 2026-11-15; **Matthew preferred v17**, so v17 is installed.

---

## 2. How 2K19 shades a belt (decoded from `pac/shader/win/ysh_win.pac`, shader `yPBR_RTCS_Belt`)

- Textures in the prop's texture pack:
  - `belt` = base colour (DXT1).
  - `belt_n` = normal (BC5: R = x, G = inverted y versus 2K23).
  - `belt_p` = **R metalness, G roughness. B and A are never read** (checked: sampled as `.xy` only).
- Lighting is split-sum image-based lighting (IBL) from the arena's probe cubemaps (`pac/arena/ibl/ariblNNNNN.pac`):
  - base^2.2; F0 = lerp(0.04, base, metal).
  - Specular comes from a pre-filtered cube at lod = rough·6.
  - Diffuse comes from an irradiance cube.
  - There are no strong lights on the belt: **what the metal shows is a blurred reflection of the arena**, which is
    mostly dark crowd and a bright canvas.
- **Belt correction** (the material flag `g_bChampionBeltCorrection`) does the following:
  - roughness = max(rough·mul, min);
  - specular × SpcMul (stock 2.0, floor 0.2);
  - irradiance × IrrMul.
  
  It only runs in the scenes switched on in the `todo_wwe19_champion_belt_too_dark.pac` file. Stock has Entrance
  on only, which is why a belt can look fine in the entrance and dull in the title presentation.

---

## 3. Insights: what makes a belt look good

### Metal
1. **Domed plates matter most.** Stock plates are domed: front normals are tilted a median of 40–46°. A flat plate
   (2K23 mods are about 8°) reflects one patch of dark arena and reads as a brown slab. `--pillow 1.2` bends every
   plate's normals toward its rim, one dome per plate.
2. **Flat metal colour; put the detail in the normal map.** Stock gold albedo is one flat colour (252,221,164) with
   ±2% variation. Photo-sourced albedo carries baked grime and highlights that fight the real lighting. Use
   `--stock-metal`.
   - *Refinement (Big Gold New, Ultra Deluxe):* darkening the engraving **crevices** in the base colour (`--cavity`)
     adds definition without grime.
3. **Do not make it glossier than stock.** More gloss means a sharper mirror of a dark arena, so the metal gets
   *darker*. Stock metal roughness is about 0.10. The Ultra Deluxe belts go *rougher*, about 0.18, varying with
   the relief: recesses rougher, raised areas smoother. That reads as rich gold under any arena.
4. **Bright glare painted in the photo becomes "silver"** once it is converted to metal. Detect it (low saturation,
   high value) and replace it with flat gold. Keep only the real silver parts silver.
5. **Gold hue.** Stock hue is about 38°. Bigger Gold mods use 47° (more yellow). The reference photo was warmer and
   more copper. Keep the hue between 35 and 40 unless you want a deliberate look.

### Enamel (reds, whites, blues)
6. Stock enamel is **non-metal, glossy (rough ~0.12) and bright**: red (222,48,49), blue (60,98,167), white
   (250,250,252). 2K23 mod enamel was 3–4× darker and partly metallic, which made it grey-green in game.
   `--stock-enamel` reclassifies the enamel on the *original* mod colours.
7. Red is only enamel if it is next to white (within 7 px). Otherwise it catches maroon leather.

### Black banners and lettering
8. Black banners with silver letters: make the **letters mirror metal** (rough ~0.07) and the **field a satin,
   non-metal near-black** (rough 0.35). A glossy black field mirrors the canvas and turns grey. `--banner-letters`
   does this.

### Strap
9. A white strap needs a neutral off-white (214,220,224, not cream) with a smoothed leather grain
   (`--strap-smooth 0.75`), at roughness 0.4. Deluxe belts use glossier leather (0.2–0.3).

### Lighting file
10. Turn belt correction on for **TitleMatch and Winning**, not just Entrance (`beltdark.py`).
11. The community **AO Belt Lighting Patch** is only SpcMul 11.3, with the switches as bit flags (0x80000000). It is a
    blunt boost: it lifts dark leather into a grey sheen and barely changes gold. Not needed once the plates are domed.

### Size and format limits
12. Stock props are 1.8 MB. Deluxe 2048 px props of about 3 MB load fine. A 29k-vertex mesh (2.8 MB JBOY)
    **froze match loading**: decimate to about 6k vertices (`--max-verts`).
13. DDS data in the texture pack must be 16-byte aligned, or the game silently shows stock textures.
14. Intro video: Bink 2 **KB2n** (RAD 2026) hangs the game. Use KB2i/KB2j, or Bink 1 BIKi with alpha renamed to .bk2.

---

## 4. Tools

| Tool | Purpose |
|---|---|
| `tools/backport/belt_port.py` | Build the 2K19 props from a 2K23 mod (all the look flags above) |
| `tools/backport/gamelook.py` | **In-game look emulator**: renders props side by side under a real arena IBL (`--ibl`), with belt correction, tilt and yaw. Use it before every in-game test. |
| `tools/backport/arenaibl.py` | Decode an arena IBL pac into an `.npz` for gamelook |
| `tools/backport/beltshot.py` | Prop loader/renderer, texture sampler |
| `tools/backport/belt_menu.py` | Replace a championship-select picture (from a render, or `--image` cut-out photo) |
| `tools/backport/photo_intro.py`, `belt_intro.py` | Title intro frames (from a photo / from a render) |
| `tools/build/titletable.py` | Championship table (`evt_data.pac`, id 13): video id, frames, props |
| `tools/build/titlename.py` | Title name in every string variant and language |
| `tools/build/beltdark.py` | Belt-correction parameters and scene switches |

---

## 5. Workflow: backporting the next belt

Branch: `claude/belt-<name>`. Back up every game file before touching it (copy it to
`_moddingwwe2k19_builds/belt/...`). Commit before delivering. Verify every installed file by MD5 on the device.

1. **Collect up front, in one message:**
   - the mod folder (`.mdl` + `Textures/`);
   - which stock title slot to replace (main + cutscene prop ids: `titletable.py --show`);
   - a reference photo of the real belt (for colours, the intro and the menu);
   - the desired strap colour and name.
2. **Inspect:** `stockstats.py`-style numbers for the mod textures versus 2 or 3 stock belts: metal %, albedo flatness,
   roughness, normal tilt, enamel brightness. Expect a flat plate, grimy albedo and dark enamel.
3. **Build:** start from the v17 flag set (section 1), the look Matthew chose in game. The deluxe flags (`--cavity`, `--metal-rough`, `--nstrength`, `--size 2048`) looked better in the emulator but worse in game for this belt, so treat them as optional. Adjust strap and hue to the reference. Check the manifest warnings (size, vertex count).
   Adjust strap/hue to the reference. Check the manifest warnings (size, vertex count).
4. **Emulate:** `gamelook.py out.pac:new <stock IC>:IC <deluxe>:deluxe --ibl <arena.npz> --tilt -10`, at several yaws,
   and once with `--nocorr` (scenes without belt correction). Compare against stock and Ultra Deluxe until it
   matches. **No in-game test until the emulator looks right.**
5. **Supporting files:** name (`titlename.py`), lighting switches (`beltdark.py`), menu picture
   (`belt_menu.py --image cutout.png --zoom 0.8`), intro video (`photo_intro.py`, then Bink 1 alpha, then
   `titletable.py --set`).
6. **Install** (backup, then commit to the device under a *new unique file name*, then MD5 check), then **one**
   in-game check: entrance, title match presentation, winner celebration.
7. **Record:** append to `Belt_backport.md`, update this guide's insights if anything new comes up, and put MD5s
   in a `handoff/` note. Push.

---

## 6. Community references (in `D:\Pictures\WWE 2K19\A - Resources`)
- **AO Belt Lighting Patch:** SpcMul 11.3 everywhere (section 3.11).
- **Big Gold New:** 4096 px albedo with the engraving painted in, yellower gold. Stock mesh and maps.
- **Ultra Deluxe Championships:**
  - 2048 px maps.
  - Engraving painted in.
  - Metal roughness 0.18, varying with the relief.
  - Glossier leather.
  - 1.5× normal depth.
  - A cavity mask in `belt_p`.B, which the game ignores.
  
  These are the best "target look" references to emulate against.
