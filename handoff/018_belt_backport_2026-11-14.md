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
