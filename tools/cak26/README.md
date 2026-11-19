# tools/cak26: read WWE 2K26 .cak archives without the GUI

Built on AuroraForge NT100's public GPL-3.0 source (installed at `C:\Program Files\AuroraForge NT100\resources\sl`):
- Catalog (per-archive key recovery, encrypted file/folder/string tables, name hashes): AuroraForge's own
  `100-538/aur-92f/electron/cak-reader.js`, run on the PC with node (device shell): `cakindex.js` (full index of all
  15 archives, 410,627 files, 99% named) and `cakdump.js` (raw stored bytes + meta.json for chosen files).
- Payloads: `payload.py` = Python port of `cak-foundry/tools/aur-39d/Program.cs` (per-file key from archive key +
  stored size + offset, unscramble of the first 256 bytes, 1 MiB-chunk Oodle via `ooz`). No Windows Oodle DLL needed.
Validated: 218/218 files decode to the catalog's expanded size.

Device-side scripts live in the device scratch home (`~/cakindex.js`, `~/cakdump.js`); copies here.
2K26 install: `D:\Pictures\WWE 2K19\A - Resources\WWE 2k26`.

## Character extraction without the GUI (2026-11-19)
Runs entirely on the PC (device shell; `pip install --user pyooz` there):
1. `node pick.js <cak-reader.js> <2K26 dir> <rawDir> <id,id,...>` - every file under `Characters/<id>_*/`, one version per
   path: models/materials prefer bakedfile100 then 61/80/52/60/51; textures prefer the 1024 tier 61/80/52/60 then 51/100
   (same choice as the earlier AuroraForge extractions).
2. `python3 decode.py <rawDir> <outRoot>` - payloads (payload.py, same as here) + DDS header from the archive's `_textures.tdb`
   (T_DB v6, 56-byte records keyed by FNV-1a64 of the lower-case `.tex` path: width u16 @10, height u16 @12, format hash @36,
   mips @41). Header style copies AuroraForge's (fourcc by block size: 8 -> DXT1, 16 -> DXT5).
Validated on Jevon: 51/59 files byte-identical with the AuroraForge extraction; the other 8 are the **portrait textures**
(shoes, kneepads, pierce), which **AuroraForge's own extraction mislabels as landscape** (height/width swapped -> the texture
shows squashed and doubled). The T_DB order is right (checked visually on shoes_color).
