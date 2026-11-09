# Audio tools (read-only decoders)

Run on the laptop through the agent shell (`device_bash`), never against a file being written. Always `python3 -I`.

| Script | What |
| --- | --- |
| `akpk.py` | Wwise AKPK (.pck) index: banks and streams |
| `bnk.py` | Banks inside a .pck, HIRC object counts |
| `evmatch.py` | Resolve `Play_MUS_*` event names from FNV-1 hashes |
| `vmum.py` | The VMUM music/movie table in `pac/audio/assetconv*.pac` |

Findings: `writeup/Music_map.md`.
