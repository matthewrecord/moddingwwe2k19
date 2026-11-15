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
