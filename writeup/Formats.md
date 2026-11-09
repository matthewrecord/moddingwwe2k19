# Yuke's container formats (WWE 2K19 PC) — measured 2026-11-09

Sources: our own decoding of game files, checked against the IL of **rePac** (`D:\Pictures\WWE 2K19\A - rePac\rePac.exe`,
not obfuscated; disassembled with `dnfile`+`dncil`, script `/tools/exe/cildump.py`). Status: **measured** unless marked.

## HSPC (outer pac container, e.g. `pac/audio/assetconv_p30.pac`, `pac/string/win/string_win.pac`)

64-byte header, u32 little-endian:

| Word | rePac name | Example (assetconv_p30) | Meaning |
| --- | --- | --- | --- |
| 0 | magic | `HSPC` | |
| 1 | tag | 2010 | version |
| 2 | headersize | 0x40 | |
| 3 | alignment | 0x800 | sector size |
| 4 | crc | 0x23767F06 | **not updated by rePac; not checked by the game** (TitantronFix changed content, same value) |
| 5 | data1offset | 1 | directory section, in alignment units (0x800) |
| 6 | data1size | 0x14 | 20 bytes x files |
| 7 | data2offset | 2 | file table, in alignment units (0x1000) |
| 8 | data2size | 0x0C | 12 bytes x files |
| 9-13 | (skipped) | 0x11, 0x70, 0x12, 0x800, 0 | name-directory/plugin blocks (zlib `EOP5/plugin version` + path names at the end) |
| 14 | filecount | 1 | |
| 15 | size | 0x7000 | rewritten by rePac at offset 60 |

File-table `size` field: rePac reads each file up to the **next file's offset** (not by size). SuperString's
`string_win.pac` has an English table that overruns the next file's start (a latent bug in that mod, harmless in
English). Our writer therefore never re-lays out: `HSPC.replace_append` appends the modified file and repoints one
entry; verified: every other byte identical.

- Directory entry (20 bytes): u64 name hash, u32 0, u32 file-table offset, u32 0xFFFFFFFF.
- File-table entry (12 bytes): **offset in 2048-byte sectors, size in 256-byte units, extension tag** (e.g. 0xC0000).
- Files are 2048-aligned. Trailing zlib blocks (`ZLIB`, u32 ?, u32 compressed, u32 uncompressed, stream) hold the
  virtual path names (`/MusicAndVideoList/PATCH30` …) and an `EOP5/plugin version` string.

## SHDC (inner container; also the decoded `_startup_*` scripts)

Same 64-byte header layout (alignment 1, offsets in bytes): data1 = hashed directory (20-byte entries),
data2 = file table of 16-byte entries **(id, offset, size, 0)**, word 14 = file count, word 15 = open (not the size;
SuperString's oversized English table keeps another language's value and works; our writer leaves it unchanged).
Example: decoded `_startup_audio_p30` = 8 files (10, 11, 12, 13, 100, 101, …).

## String table (file #0 of each language SHDC in `string_win.pac`)

`u32 0, u32 count, count x (offset, length, id), pool` — offsets from the start of this file (= SHDC+0x64), length includes
the NUL. SuperString's copy: 6 language SHDCs, 26,674-26,675 strings each. Music name = id 13000 + music id.

## BPE (`BPE ` blocks, e.g. `pac/root/_startup_*`)

Philip Gage byte-pair encoding, little-endian 16-bit block sizes; header `BPE `, 0x100, compressed size, uncompressed
size, checksum; data at +0x10. Decoder `tools/audio/bpe.py`. rePac ships a native `YukesBPE.dll` (encoder, not yet read).

## GCOM scripts (decoded `_startup_audio_pNN`)

Files are tagged `GMCG` (61 numbered command defs 0-3, 1000-…), `AMCG`, `OMCG` (237 x 32-byte ops), `SMCG` (string
pool: records `(1, offset of next record, padded string)`, 550 records: package names with `INIT`/`FULL` load modes,
bank names `DLC_30_E_S`, `Entrance_Music_E_S`, … , `/SoundScripts/PATCHnn` + `nn:SOUNDPAC`). A small bytecode VM;
**not needed for the chosen route** (we add to a bank the script already loads).

## Create-an-Entrance item lists

`pac/menu/cae_item[_pNN].pac` (HSPC) holds `/ENEX30/*.lsd` lists: `BGM.lsd` (entrance music list, by name),
`titantron.lsd`, `minitron.lsd`, `entrance*.lsd`, `CAE_*.lsd`, `winning_*.lsd`, … The community "CAE Item Adder"
edits these. Format of `.lsd` and whether `BGM.lsd` gates the in-game music list: next to map.
