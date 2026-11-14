# Handoff 018: title belt backport (IWGP US title), 2026-11-14

Branch `claude/belt-backport` (on top of `claude/backport-tool`). Write-up: `writeup/Belt_backport.md`.
- Built `iwgp_us_v1` replacing the US Championship (`pac/prop/2003.pac` + `5003.pac`), delivered to
  `_moddingwwe2k19_builds\belt\iwgp_us_v1\` with README. Not installed (Matthew installs).
- Waiting on Matthew's in-game check: entrance (worn/shoulder), match, title presentation cutscene.
- If the game rejects ZLIB blocks: try uncompressed blocks or Oodle (oo2core_6_win64.dll is in the game folder).
- Rebuild: stage the mod to /tmp/mod (mdl files + Textures/), stage pac/prop/2003.pac + 5003.pac, run belt_port.py.

- **Update:** Matthew asked for the Brahma Bull WWE Championship instead: build `iwgp_brahma_v1` (props 2905 + 5038) delivered; US build superseded.

- **2026-11-14:** Matthew tested before install (the builds were only in the builds folder). Installed `iwgp_brahma_v1` into `WWE 2K19 - modded\pac\prop\` (2905, 5038); originals backed up to `_moddingwwe2k19_builds\belt\backup_originals\`. Awaiting retest.
- **Correction (Matthew):** belt work targets the PLAIN install `D:\SteamLibrary\steamapps\common\WWE 2K19`. Modded install restored to stock 2905/5038. `iwgp_brahma_v1` installed in the plain game; originals in `WWE 2K19\_moddingwwe2k19_builds\belt\backup_originals\`.
- v1 in game: geometry/weights OK, textures wrong (unaligned DDS in texture pack). v2 built and installed in plain (backups unchanged).
- v2 in game: still stock-looking gold plate. v3 = Oodle-stored blocks instead of ZLIB, installed in plain.
- v3 in game: still gold. Switched to diagnostics: `belt_diag.py` (magenta/green checker + coloured v-bands, metal 0, flat normal) installed in plain as `diag_textures`. Magenta -> our texture pack is used (problem = material/shading); gold -> textures come from elsewhere.
- 2026-11-14 ~02:45: Matthew: matches will not load after diag_uvgrad install. Stock 2905/5038 restored at once. BUT another session (arena work, `WWE2K19_arena_work`, wm32 graphics) rewrote the plain chunk0.def at 02:41 (+30 arena pacs) and was writing arena files at the same time, so the load failure is not yet attributable. diag_uvgrad differs from the working diag_textures only in texture pixels (same container code). Not touching the arena files.
- 03:30 recheck after Matthew finished arena work: chunk0.def consistent (no dups; only stock debug entries missing on disk), belts were stock. diag_uvgrad re-verified (all replaced blocks decode, identical structure to working diag_textures) and reinstalled.
- 6k uvgrad also froze (same place) -> NOT memory. Stock restored. Byte diff: checker build (loaded) vs uvgrad build (froze) differ ONLY in the `belt` colour DXT1 pixels (model, belt_n, belt_p, all other blocks byte-identical). No crash dump (hang). Open question for Matthew: same match setup for both tests? Next: rerun the checker build in the freezing setup to separate "build" from "setup"; telemetry DLL in plain install needs his OK.
- Matthew: freeze is at the loading screen, bar ~1/5. Built tools/telemetry/dinput8_filetrace.c; installing in PLAIN with diag_uvgrad_6k (freezing build) for one traced run (Matthew approved).

## Current state (end of 2026-11-14 session)
- Freeze: fixed by ZLIB blocks / pac at or below stock size (stored-Oodle 3.3-5.6 MB pacs froze at ~1/5 of the bar).
  Size vs stored-chunk format not separated (optional test: ZLIB pac padded to 3.3 MB).
- Flat gold plate: ROOT CAUSE found via control experiment (stock mesh + UV gradient, prediction committed first):
  2K19 props point normals/winding into the belt; ours pointed out, so the plate's back faces were drawn. Fixed in
  `belt_port.mod_mesh` (normals negated, winding follows). writeup sections 13-14.
- Installed in PLAIN `WWE 2K19`: `pac/prop/2905.pac`, `5038.pac` = `iwgp_brahma_v4`; `dinput8.dll` = filetrace tracer.
  Originals: `WWE 2K19\_moddingwwe2k19_builds\belt\backup_originals\`.
- Next: Matthew's v4 screenshot. If the plate shows the flag/banner: tune belt_p (metal/roughness) and check normal-map
  green sign against stock; add back-face culling (2K19 convention) to `beltview.py`; remove dinput8.dll; merge to main.

## Result: v4 WORKS in game (Matthew, 2026-11-14)
Game files changed (plain install `D:\SteamLibrary\steamapps\common\WWE 2K19`):
| File | Original MD5 (backup in `_moddingwwe2k19_builds\belt\backup_originals\`) | Installed MD5 (iwgp_brahma_v4) |
|---|---|---|
| `pac\prop\2905.pac` | 95b0f2f1c20944cddf162e2e451b36bd | 412bdd0ebcaecf6bdfd94500ed0c2d02 |
| `pac\prop\5038.pac` | 69876b7d363a901c410ff66d9abbdcaa | 8d35811f1199d5da17fd5c5492c454cb |
`dinput8.dll` (tracer) removed from the game folder; moved with logs to `_moddingwwe2k19_builds\telemetry\removed\`.
Modded install: 2905/5038 restored to stock earlier (same original MD5s).
Open: cutscene close-up check; shine/normal tuning; beltview back-face culling; merge decision (branch sits on the unmerged
`claude/backport-tool`, 58 commits ahead of main).

## v5 "AEW United States Championship" installed (plain install, 2026-11-14), awaiting Matthew's check
White strap + gloss 2.0, menu picture replaced, title 23 renamed in all 7 language tables.
| File | Original MD5 (backup in `_moddingwwe2k19_builds\belt\backup_originals\`) | Installed MD5 (`aew_us_v5`) |
|---|---|---|
| `pac\prop\2905.pac` | 95b0f2f1c20944cddf162e2e451b36bd | ddb19edb5f47145fb9b221f4bb00aab9 |
| `pac\prop\5038.pac` | 69876b7d363a901c410ff66d9abbdcaa | baaf12b088ca8904930458e7d647e9f5 |
| `pac\menu\win\Assets\wwe19_texture\belt\ltag_belt_all_win.pac` | e72280236c51e027692ef2f34a6d770b (`ltag_belt_all_win.pac`) | bb063e5ea08d60b9163fd80163a3da08 |
| `mods\SuperString\string_win.pac` and `mods\SuperString\pac\string\win\string_win.pac` (game opens both, per trace) | efd9ef151e94382e6e8a90b7673354f9 (`SuperString_string_win.pac`) | 0d33081684460020a3e63755db46e007 |

## v6 installed (gold hue 35), 2026-11-14
| File | Installed MD5 (`aew_us_v6`) |
|---|---|
| `pac\prop\2905.pac` | e47a3f049943fb0c6cff21b09164382e |
| `pac\prop\5038.pac` | 7e288e0ac8d3dc66e7db98b76fc508c2 |
| `pac\menu\win\Assets\wwe19_texture\belt\ltag_belt_all_win.pac` | 28083e9b30b51a7a55c43586de761792 |
Strings unchanged from v5. Originals (MD5s in the tables above) in `backup_originals\`.

## Merged to main (2026-11-14, Matthew approved)
Fast-forward of `claude/belt-backport` (includes all of `claude/backport-tool`) into `main`.

## WWE 91 freeze control (2026-11-14)
Installed for the control: STOCK 2905/5038 (95b0f2f1..., 69876b7d...) + tracer dinput8.dll (dbf4dd53...). Menu picture and strings stay v5/v6. v7 waits in `aew_us_v7\`. Prediction: if the arena freezes with stock belts, the freeze is the arena work, not the belt.
- Matthew: the tracer should have stayed installed (the WWE 91 freeze happened while it was removed, so no log). Reinstalled; it stays until the belt work is signed off.
- Control result: 1 run in the WWE 91 arena with STOCK belts loaded fine (trace 40359125, no hang). Not conclusive alone (intermittent). Matthew was surprised to see the Brahma Bull (control not clear enough in my message). Installed v7 (2905 4dad90b087ef1dc3b6697ab623b0fd52, 5038 d124df9134d71629438897559560558e, menu 3ffc8739cbd592d03197e90b60c0e334) with the tracer kept in: any freeze is now logged directly.

## v8 installed (plain), 2026-11-14
| File | Installed MD5 (`aew_us_v8`) |
|---|---|
| `pac\prop\2905.pac` | a463c4316dff6ea4e8c7ff3cc4b1f69c |
| `pac\prop\5038.pac` | f25e5bf188687cdf527d1a1b441ebc63 |
| `pac\menu\win\Assets\wwe19_texture\belt\ltag_belt_all_win.pac` | cab920af12d0ce55ec6123061bdf84b6 |
Tracer still installed. v7 run (trace 40618828) did not freeze.

## Intro fix installed (2026-11-14)
| File (plain install) | MD5 | Stock MD5 (backup in `_moddingwwe2k19_builds\belt\backup_originals\`) |
|---|---|---|
| `pac/evt/evt_data.pac` | ebf691de461e52f03ee18755100bcd18 | c9664b0c848f14c4ffe0b9513965783c |
| `pac/evt/evt_data_p10.pac` | f32df2a491b19289abe42fd0ff48cdad | eb8e71bf9dc05183a35982d41965ec6f |
| `movies/titantron/bel_0023_0_0.bk2` | ac71460b7f03bf39492c66052d485f57 (placeholder = copy of the US title's bel_0005) | (new file) |
Matthew's own encode replaces the placeholder: same name, Bink2, 10 s. Tracer v3c is still installed.
