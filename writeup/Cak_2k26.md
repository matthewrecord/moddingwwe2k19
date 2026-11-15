# 2K26 `.cak` archives: can we read them ourselves? (2026-11-15)

Branch `claude/2k26-cak`. Source of the method: CakeTools 2023 v9982p108 (2K23 build), disassembled statically in the
agent workspace (never run).

## Findings
- 2K26 install: 15 `bakedfileNN.cak` + `oo2core_9_win64.dll` (Oodle). `bakedfile00.cak` (249 B) and `bakedfile50.cak`
  (6.7 KB) are `FDIR` index files.
- FDIR header (8 bytes, big-endian u64): 2K23 = `46444952 08070081`; 2K26 = `46444952 09090085`. Version bumped.
- 2K23 cipher (CakeTools `0x140012420`): over big-endian u32 pairs, `a = c0 ^ k; k = c1 ^ a; out a, k`; tail bytes
  chained with `k>>24`. Net effect: plaintext word i = (XOR of cipher words 0..i) ^ key. Keys are hard-coded per
  archive name (`bakedfile00.cak` = 0x21d40e0a, `01` = 0x6c2f2e94, `02` = 0x4d358d0d, `03` = 0xa48e8bb3, ...; 31 in
  the table). Keys are not CRC32/CRC32C of the name. CRC32C (poly 0x82f63b78) is used for name hashes.
- 2K23 reader: decrypts a 0x50-byte header block at offset 8 (offsets/sizes), then the sections it points to.
- **2K26 does not use this scheme.** No 2K23 key gives structure. Under the 2K23 cipher any key would leave the
  header's small offset/size values sharing top bytes; the 2K26 header block shows none (BE or LE). So either the
  cipher or the header layout changed (header version 09/09/85).

## Conclusion
Static reuse of CakeTools 2023 cannot open 2K26. The 2K26 key and cipher live in the 2K26 game executable, which is
Denuvo-protected. Not pursued.

## Better route for 2K26 characters
Community 2K26 character mods ship as loose `.mdl`/`.mtls`/DDS files (same 2K22+ family `tools/backport/mdl.py`
already reads; see `writeup/Backport.md`). Those need no `.cak` access.

## Update (2026-11-15 night): AuroraForge reads 2K26; what a backport needs
- AuroraForge NT100's CAK Foundry (GUI, run by Matthew/Claude via the screen) opens all 15 archives read-only:
  410,348 files. Characters live at `Characters/<id>_<Name>/BaseModel/` and `Characters/<id>_<Name>/<attire>/`.
- Community 2K26 mods (Downloads: Kenny Omega, Hangman Page, Dalton Castle, Christopher Daniels, "Jeff_Cobb_PWG2016"
  which is actually JC Mateo 1456) share one layout: `baseModel.mcd` + `.mtls` + `Materials/*.jmtl` + `Textures/*.dds`
  (body/head/eye/eyelash colour+nrm), and per attire `Attire.mcd` + `.mtls` + `.ycl` + `Materials/` + `Textures/`
  (`_color`, `_nrm`, hair `_flow`/`_rai`).
- Pipeline (`build_port.py`, Backport.md §23-26) already reads `.mcd` (2K25 MCD! wrapper). Needs: base + one attire
  `.mcd`, their Textures, and `.hpl` (hide table) if present. Not needed: `.ycl` (cloth, dropped), Movies/, audio, UI.
- Open: game textures show as type `tex!` in the archive; check whether they extract as plain DDS.

## Extraction done (2026-11-15 night)
17 of 19 requested wrestlers extracted (default model + default attire). Pagano and Royce Keys have no model in this
copy. 2K26 `.mcd` = `MCD!` + chunks (`CTG!`, `MDL!`, `HPL!`); `mdlfmt.MDL` parses the MDL from tag+4. See handoff.
