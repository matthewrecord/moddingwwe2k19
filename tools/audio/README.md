# Audio tools (read-only decoders)

Run on the laptop through the agent shell (`device_bash`), never against a file being written. Always `python3 -I`.

| Script | What |
| --- | --- |
| `akpk.py` | Wwise AKPK (.pck) index: banks and streams |
| `bnk.py` | Banks inside a .pck, HIRC object counts |
| `evmatch.py` | Resolve `Play_MUS_*` event names from FNV-1 hashes |
| `hspc.py` | Unpack ZLIB blocks of HSPC pacs (`pac/audio/sound*.pac`) |
| `bpe.py` | Decode Yuke's BPE compression (`pac/root/_startup_audio_pNN.pac`) |
| `vmum.py` | The VMUM music/movie table in `pac/audio/assetconv*.pac` |

Findings: `writeup/Music_map.md`.
