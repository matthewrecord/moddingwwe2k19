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

## v3 result and v4 diagnostic (2026-11-09 18:30)

- **v3 in game:** entry still not listed.
- **v4diag installed** (v3 + markers, `tools/build/diag_markers.py`): The Rock's BGM entry label -> 3109; string 3101
  -> 'STEVE AUSTIN TEST'. Reading: Rock shows ALEX SHELLEY label => game reads our BGM.lsd (problem = adding entries);
  Austin shows TEST => game reads our string table; neither => our pac edits are not loaded at all.

## v4 result and v5 (2026-11-09 18:35)

- **v4diag in game (Matthew):** both markers appeared and worked -> the game reads our `cae_item.pac` BGM list and
  our string table. The added base entry was the only thing missing.
- Cause: CAE lists form one combined index filled in order base -> p10 -> p20 -> p30; headers are (own count, running
  end): BGM base (304,308), p10 (3,307), p20 (1,308), p30 (7,315). A base append sits at index 304 and is overwritten
  by p10's first entry. (Field-based filtering ruled out: listed tracks include rows identical in kind to row 109.)
- **v5 installed** (`_moddingwwe2k19_builds\slot109_v5`): markers gone, base `cae_item.pac` original, entry appended to
  the p30 BGM list -> (8,316). Pac Editor-style relayout (file1 moved 5 -> 7, word 15 8192 -> 12288).

## v5/v6 results and v7 diagnostic (2026-11-09 23:45)

- **v5:** not listed. **v6diag:** Lio Rush relabel worked (p30 is read); an appended duplicate of The Rock (100000,
  label 3100) SHOWED at the end; our 109000/3109 entry did not -> filtering is specific to our entry's content.
- **v7diag installed:** p30 BGM ends with A (100000, label 3109), B (109000, label 3100), C (109000, label 3109).
  A shows 'ALEX SHELLEY (CUSTOM 109)' => new strings work; B shows a third 'THE ROCK' => music id 109 accepted.

## v7 result and v8 (2026-11-09 23:59)

- **v7diag:** A (100000 + label 3109) SHOWED as 'ALEX SHELLEY (CUSTOM 109)' and played The Rock; B (109000 + label
  3100) hidden -> the menu rejects music id 109 itself. Not the VMUM lookup (The Rock, 100, is unreachable by bsearch
  in vanilla yet listed).
- Found the gate candidate: **MEMU music-info table** (`pac/root/misc05_save_pNN.pac`, SHDC file 6): 'MEMU', count,
  32-byte records (superstar string, song title string, album/99999, value, type 0xFFFF0600 for music, u16 id|0xFFFF,
  flags 0xFFFF or 0x1EFFFF (DLC p30), 0). Base 202 records, p30 213 (DLC music added). Every listed track has one.
- **v8 installed** (clean, no diagnostics): v5 + MEMU record (3109 'ALEX SHELLEY (CUSTOM 109)', 13109 title, 99999,
  109000, music, 109, base flags). MEMU 213 -> 214. Five files changed now (adds `pac/root/misc05_save_p30.pac`).
