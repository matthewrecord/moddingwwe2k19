# Handoff 008: build tool productised; Data Editor + Sound Editor integration (2026-11-10)

## Scope change (Matthew, 2026-11-10 12:17)
Validation is not just CCT: new slots must work properly with **Data Editor** and **Sound Editor**; CCT is not the main
way he assigns music.

## How the two tools see music (measured)
- **Data Editor** (`A - Data Editor 2k19`): dropdown from plain text `Data/DataLists/Modded/EntranceMusicID.data`,
  CRLF, `<id*1000> <name>`; unused ids are present as blank lines (`109000`). So any new slot is already assignable by
  number; we now write its name there. `SettingsExternalToolsCanModifyLists = True` (CCT may also rewrite the lists).
- **Sound Editor** (`Z - Sound Editor New`, .NET, Wwise/ww2ogg/ffmpeg): opens `sound/*.pck`, names streams by Wwise
  source id from `database/WWE 2K19/data.xml` (every patch_30 DLC stream is named `THEME <wrestler>`), plus user names
  in `custom_data.xml` (was empty). We add `<sound id="<source id>" name="THEME <name>" />`. Our stream ids are
  `fnv('wwe2k19mod_wem_%04d' % id)`. Its settings point at `D:\Steam\...` and database "WWE 2K23" (Matthew's settings,
  untouched).
- **CCT**: packed .NET, no music list on disk, only works attached to the running game. Matthew asked to check the
  dropdown with v14 installed (result pending).

## Tool changes (branch claude/productise, merged)
- `musicslot.py --list-free`: 592 free ids (empty VMUM row, key above sorted tail, no event/BGM/MEMU, strings 13000+id
  and 3000+id empty). ID 150 is excluded (string 3150 = Michael Cole, the v14 clobber).
- `--spec songs.json`: `[{"name", "wem", optional "id", optional "label"}]`, different .wem per song, free ids picked
  automatically. Old `--wem/--id/--name` still works and is byte-identical to the old tool (regression run).
- `--tools "<modding folder>"`: also builds the Data Editor list and Sound Editor custom_data.xml (outputs under
  `<build>/tools/`, manifest `root: tools`). `install.py ... --tools "<modding folder>"` backs them up
  (`.orig_musicslot`) and restores them on uninstall, same MD5 gates as game files.
- All 343 `.wem` files in `D:\Pictures\WWE 2K19` pass the format check (Wwise Vorbis, as the game).
- Dry run on copies: build -> install -> status -> uninstall -> status all byte-exact.

## Build ready, NOT installed: `_moddingwwe2k19_builds/songs4_v15` (spec `songs4_v15.spec.json`)
| id | name | wem |
| --- | --- | --- |
| 109 | Alex Shelley Theme | Alex Shelley/Alex Shelley Theme.wem |
| 116 | Let's Light It Up | AJ Lee/...aj_lee_4th_theme_song...wem |
| 117 | American Alpha | American Alpha/.../American Alpha.wem |
| 807 | Kill The Messenger | Andrade El Idolo/...Kill The Messenger...wem |
Output MD5s: pck e450d82e…, vmum 83564739…, str d6553b08…, cae 67550741…, memu 4d3edb0e…, de ed53429e…, se 2fed93ae….
Game currently still has `multi_v14_nounlock` (status MODDED, backups present).

## Swap procedure (game closed)
```
install.py uninstall --build .../multi_v14_nounlock --game "$G"
install.py install   --build .../songs4_v15 --game "$G" --tools "$HOME/mnt/WWE 2K19"
```
Note: a CAW already assigned a v14 TEST id keeps that number; 109/807 stay valid, 150/200/500/650/850/999 become
unused (no audio).

## Next
1. Matthew's test of v15: CAE list (4 named songs, each its own audio), Data Editor dropdown shows names and a .pofo
   assigned 116000 plays in game, Sound Editor shows THEME names in patch_30.pck, CCT dropdown.
2. Sound Editor replace-by-id on our streams: does it rewrite the bank's in-memory prefetch size? (Ours is computed
   per wem; a replacement with a different file may need that field updated.) Test once v15 is in.
3. Matthew's own songs: need .wem (Wwise Vorbis). Sound Editor bundles Wwise templates + ffmpeg and can convert; or we
   convert. Ask what format his songs are in.
4. Write-up: fold the recipe + tool integration into writeup/Music_map.md and Status.md.
