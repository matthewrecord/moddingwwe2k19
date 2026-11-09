# Audio tools (read-only decoders)

Run on the laptop through the agent shell from a read-only clone: `git clone https://github.com/matthewrecord/moddingwwe2k19 ~/repo` (in the
agent's home, not in a game folder), `git -C ~/repo pull` before use. Never against a file being written. Always `python3 -I`.

| Script | What |
| --- | --- |
| `akpk.py` | Wwise AKPK (.pck) index: banks and streams |
| `bnk.py` | Banks inside a .pck, HIRC object counts |
| `evmatch.py` | Resolve `Play_MUS_*` event names from FNV-1 hashes |
| `hspc.py` | Unpack ZLIB blocks of HSPC pacs (`pac/audio/sound*.pac`) |
| `bpe.py` | Decode Yuke's BPE compression (`pac/root/_startup_audio_pNN.pac`) |
| `unpackall.py` | All ZLIB/BPE blobs in any pac |
| `strtab.py` | String tables (ids -> text) in `string_win.pac` |
| `bankdump.py` | Every HIRC object of one bank, hex |
| `codecs.py` | Codec histogram over all banks |
| `vmum.py` | The VMUM music/movie table in `pac/audio/assetconv*.pac` |

Findings: `writeup/Music_map.md`.
