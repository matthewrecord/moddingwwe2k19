# Handoff 020: 2K26 character sources extracted (2026-11-15 night)

Branch `claude/2k26-cak`. Details: `writeup/Cak_2k26.md`.

- Route: AuroraForge NT100 > Inspect & Convert > Aurora CAK Foundry (GUI, driven via computer use). Open All Game CAKs,
  search `Characters/<id>_<Name>/`, select page(s), extract with "Replace same-name files" ON (newest patch wins).
  GUI quirks: short typed text is dropped (paste needs >=17 chars; paste long then BackSpace); select-all is per page.
- Output: `D:\Pictures\WWE 2K19\A - Resources\2K26 Extracted\Characters\` (17 wrestlers, ~890 MB, log `_log.md`).
- Skipped: Pagano (no model in this copy), Royce Keys (texture patch only).
- **Next (porting):** `build_port.open_model()` must find the `MDL!` chunk inside 2K26 `MCD!` (not fixed offset 12;
  parse from tag+4). Hide table: use the `HPL!` chunk embedded in the attire `.mcd` (mods ship it as `.hpl`).
  Verified: Rhea base 8 meshes/175 bones, attire 15 meshes/352 bones parse with `mdlfmt.MDL`. Textures are plain DDS.
