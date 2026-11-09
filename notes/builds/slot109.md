# Build: slot 109 test (2026-11-09 night) — INSTALLED in the modded game

- Built by `tools/build/musicslot.py --id 109 --name "Alex Shelley (Custom 109)" --wem "D:\Pictures\WWE 2K19\Alex Shelley\Alex Shelley Theme.wem"`
  from the modded install (`D:\SteamLibrary\steamapps\common\WWE 2K19`).
- Build folder (kept for uninstall): `D:\Pictures\WWE 2K19\_moddingwwe2k19_builds\slot109\` (manifest.json inside).
- Installed with `tools/build/install.py install`; originals kept as `<file>.orig_musicslot` beside each file.
- Undo: `python3 -I tools/build/install.py uninstall --build <build folder> --game <install>` (agent runs it).

| File | Original MD5 | Installed MD5 | Size |
| --- | --- | --- | --- |
| `sound/patch_30.pck` | ffc212ac85d543a69279d98830fa8c5f | 05c72b8365ab5967277c118657c59eba | 30,378,071 -> 31,475,941 |
| `mods/TitantronFix/pac/audio/assetconv_p30.pac` | 7e93433710c27e6b9596fbaceb5802fb | 338ec7ba6ae0cb976486eaa084b20a55 | 88,064 |
| `mods/SuperString/pac/string/win/string_win.pac` | 583a817716659982d34702816f610d0f | 48aa1b6fb7e960e0e6fc3817095d1e37 | 10,952,704 -> 13,750,272 |
| `pac/menu/cae_item_p30.pac` | 8b77395c2bc9d83f09b7d12e69bd4e56 | d516135ffa3dc73659287b2e6905cc3f | 18,432 -> 26,624 |

What changed (all verified by re-reading; bank also by wwiser):
- `DLC_30_E_S` bank: +Sound 2489597736 (Vorbis, streamed, source 2004026480, inMem 0x766E), +RanSeq 3798096623 (parent music
  mixer 126675442), +2 Play actions, +events `Play_MUS_0109_00_0_0` / `_0_1`; mixer child list +1. Stream 2004026480 = the .wem.
  Every other bank/stream byte-identical.
- Music table: row 109 named (fields 0/1 = 592/756), key 10,900,000, moved into the sorted tail (index 108 -> new
  position); bsearch simulation: 390 -> 391 reachable keys, none lost. Field 15 (tron flags) left 0 (no video exists).
- Strings (English table only): 3109 `ALEX SHELLEY (CUSTOM 109)` (menu label), 13109 `Alex Shelley (Custom 109)`.
- CAE `BGM.lsd` (p30): +1 base-style entry (value 109000, id 109, label 3109); header 7/315 -> 8/316.

## v1 result and v2 (2026-11-09 18:15)

- **v1 in game (Matthew):** no crash; the entry did NOT appear in Create an Entrance > Entrance Music. CCT lists every
  id from its own database (incl. unused ones), so CCT showing 109000 proves nothing by itself.
- Cause (most likely): CAE Item Adder 0.2.1 (decompiled from its PyInstaller bundle) only ever adds to the **base**
  list (first SHDC of `pac/menu/cae_item.pac`, both header u16s +1); patch lists hold DLC-flagged entries.
- v1 uninstalled (all four originals restored, MD5-verified). **v2 installed**: same audio, table and strings; CAE
  entry now in base `pac/menu/cae_item.pac` (BGM 304/308 -> 305/309); `cae_item_p30.pac` stays original.
  Build: `D:\Pictures\WWE 2K19\_moddingwwe2k19_builds\slot109_v2\`.
- First attempt to swap failed with "permission denied" because the game was running; `install.py` now refuses up
  front if any target is locked.
- **Decisive CCT test:** before the mod no `Play_MUS_0109_*` event existed in any bank (evmatch over all banks), so if
  assigning 109000 in CCT now plays the Alex Shelley theme, the slot is real, not a database label.

## v2 result and v3 (2026-11-09 18:25)

- **v2 in game (Matthew):** entry still not in the Entrance Music list. Matthew: the files are the right ones.
- Cause found: our writer appended edited files past the end of the pac and repointed the entry, leaving header word
  15 (= data region, first file -> tail) unchanged; Pac Editor instead re-lays out in place and updates word 15. The
  game evidently reads only that region, so v1/v2 edits to `cae_item*.pac` and `string_win.pac` were invisible.
- Writer fixed (`HSPC.build/replace`, Pac Editor-style); roundtrip byte-identical on vanilla `cae_item.pac`, on
  Matthew's Item-Adder/Pac-Editor-edited `cae_item.pac` and on vanilla `cae_item_p30.pac`.
- **v3 installed** (`_moddingwwe2k19_builds\slot109_v3`): `cae_item.pac` keeps its size (entry fits in padding,
  word 15 unchanged); `string_win.pac` re-laid (word 15 = new data region; SuperString's old overlap removed).
