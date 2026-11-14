# Handoff 018: title belt backport (IWGP US title), 2026-11-14

Branch `claude/belt-backport` (on top of `claude/backport-tool`). Write-up: `writeup/Belt_backport.md`.
- Built `iwgp_us_v1` replacing the US Championship (`pac/prop/2003.pac` + `5003.pac`), delivered to
  `_moddingwwe2k19_builds\belt\iwgp_us_v1\` with README. Not installed (Matthew installs).
- Waiting on Matthew's in-game check: entrance (worn/shoulder), match, title presentation cutscene.
- If the game rejects ZLIB blocks: try uncompressed blocks or Oodle (oo2core_6_win64.dll is in the game folder).
- Rebuild: stage the mod to /tmp/mod (mdl files + Textures/), stage pac/prop/2003.pac + 5003.pac, run belt_port.py.

- **Update:** Matthew asked for the Brahma Bull WWE Championship instead: build `iwgp_brahma_v1` (props 2905 + 5038) delivered; US build superseded.

- **2026-11-14:** Matthew tested before install (the builds were only in the builds folder). Installed `iwgp_brahma_v1` into `WWE 2K19 - modded\pac\prop\` (2905, 5038); originals backed up to `_moddingwwe2k19_builds\belt\backup_originals\`. Awaiting retest.
