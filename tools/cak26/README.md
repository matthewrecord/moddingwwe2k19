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
