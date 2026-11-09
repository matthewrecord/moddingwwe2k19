# Music map: how WWE 2K19 stores and finds music (survey 2026-11-09, read-only)

All facts below were measured on the **unmodded** install unless noted (tools in `tools/audio/`). Status words:
**measured** = read from the files; **inferred** = a reasoned guess still to test.

## 1. Three layers

A music track needs three things to exist and be used:

1. **Audio** (.wem streams) inside Wwise AKPK packages in `sound/`.
2. **Wwise events** `Play_MUS_<id>_<var>_<x>_<mode>` in soundbanks that point at those streams.
3. **A row in the game's music/movie table** (VMUM, `WWE2K_MusicMovie.bin` in `pac/audio/assetconv*.pac`) that tells
   the game the music ID exists, its name/menu entry, and which entrance video goes with it.

CCT (section 6) is a fourth consumer to satisfy.

## 2. Audio packages (`sound/*.pck`, AKPK v1) — measured

| Package | Banks | Streams | Role |
| --- | --- | --- | --- |
| `music_0_m.pck` … `music_3_m.pck` | 0 | 55 / 59 / 60 / 25 | Superstar themes (streams only) |
| `music_misc_1_m.pck`, `music_misc_2_m.pck` | 0 | 69 / 15 | Generic themes |
| `music_show_m.pck` | 0 | 37 | Show music |
| `music_e_s.pck` | 9 | 0 | **Music soundbanks** (events) |
| `patch_10.pck` / `patch_20.pck` / `patch_30.pck` | 2 each | 6 / 2 / 10 | **DLC music**: own Init bank + one content bank + streams |
| `patch_day1.pck` | 2 | 0 | Day-1 patch bank |

Modded vs unmodded: identical stream counts; `music_0_m.pck`, `music_2/3_m`, `music_misc_*`, `game_mode_m` are bigger
in the modded copy (audio appended and index entries repointed: the community's replace method). No mod added an entry.

## 3. Events — measured

Event name template (in `WWE2K19_x64.exe`): `Play_MUS_%MUSICID%_%VARIATION%_%MUSICMODE%`, built as
`MUS_%04d_%02d_%1d_%1d`. Event IDs are Wwise FNV-1 hashes of the lower-case name. 671 of 1,126 bank events resolve
to this template (`tools/audio/evmatch.py`):

| Bank | Where | Play_MUS events |
| --- | --- | --- |
| 3898464801 | `music_e_s.pck` | 629 (main music bank, 1,048 events in all) |
| 4026797958 | `music_e_s.pck` | 8 |
| 863845646 | `patch_day1.pck` | 13 |
| 2859600862 | `patch_10.pck` | 8 (IDs 0133, 0800-0802) |
| 1755985664 | `patch_30.pck` | 14 (IDs 0127, 0731, 0755, 0805, 0806, …) |

Each music ID normally has two events, `_0_0` and `_0_1` (mode 0/1; inferred: full entrance vs short/victory).

**The DLC created brand-new music IDs** (0800-0806 did not exist in the base game) by shipping a new bank in a patch
package plus a new table row. That is exactly the path for custom slots.

## 4. The VMUM music/movie table — measured

File: `WWE2K_MusicMovie.bin` packed as `/MusicAndVideoList/PATCHnn` in `pac/audio/assetconv[_pNN].pac` (HSPC/PAC8
container, table at file offset 0x1800). The exe reads `/MusicAndVideoList/PATCH%02d`. **Each patch level carries the
whole table** and the newest wins.

Header `VMUM, 16, 1000, n`; n records of 64 bytes (16 × u32); then a C-string pool. Strings are offsets from `VMUM`.

| Field | Meaning (status) |
| --- | --- |
| 0 | menu/sort index (inferred) |
| 1 | name index; **0 = unnamed row** (inferred: not listed in menus) |
| 2 | **music ID** (the `%04d` in `Play_MUS_`) |
| 4 | music ID × 100000 (+ variant) (measured pattern) |
| 6 | string: special music cue, e.g. `MUS_9001_00_0_4` (measured) |
| 7 | string: entrance video, e.g. `ent_0101_0_2`, `tag_0071_0_0` (measured) |
| 8-14 | timing/asset values; defaults = ID×1000, ID×100 (measured pattern; meaning open) |
| 15 | flag bytes, e.g. 0x10101; TitantronFix flips these (titantron availability; exact bits open) |

Rows per level: base 375, p01 388, p10 389, p20 390, **p30 1,147**. p30 = the 390 real rows **plus 757 unnamed rows
that fill every ID 0-999. 747 of those IDs have no Wwise event at all: empty, reserved slots** (`tools/audio/vmum.py`).

## 4b. How the game finds the packages and tables — measured (exe + data, 2026-11-09)

- **Package list:** not in the exe. `pac/root/_startup_audio_pNN.pac` (SHDC container, **BPE**-compressed GCOM
  script; `tools/audio/bpe.py`) lists every `.pck` to load, patch packages first (`patch_30.pck`, `patch_30_dialogue.pck`,
  `patch_20.pck`, …, then `music_0_m.pck` …). Records are 4-byte-aligned names with type words (e.g. `INIT` after each
  patch package). The game opens these names under `sound\` (Wwise IO hook at 0x140F17EF1 checks for `.PCK`).
  No folder scan (no FindFirstFile call in the sound module).
- **Patch levels the game tries:** the exe formats `pac\root\_startup_audio_p%02d.pac` in a 9-step loop
  (0x14093EBA0) over the table at 0x142145CC8 = **01, 10, 11, 20, 21, 30, 31, 40, 41**. Only 01/10/20/30 exist, so
  **p31, p40, p41 are free levels the game already looks for**: a custom audio patch needs no exe change.
- **Music table:** the exe (0x1404D17B7) walks a runtime list of patch numbers (vector at 0x1425E68E8), looks up
  `/MusicAndVideoList/PATCHnn` for each, and **keeps the last one found** (highest patch wins). Still to trace: how that
  runtime list is filled (expected: the same 01…41 table).
- **Chunk0.def** (`;PAC_LIST_ARC_EPAC`) is the master list of pac files; the modded install adds ~5,700 lines, so
  community mods register new pacs by listing them there.

- **Runtime patch list = data:** filled by `yCObserveInfoCSV::InitObserve` (writer 0x14093CB84) from
  `observe_info.csv` inside `pac/root/_startup_observeinfo_pNN.pac` (BPE), which reads `1	10	20	30`. Adding `40` there
  (in a p40 or overridden p30 observeinfo pac) makes the game look for `/MusicAndVideoList/PATCH40`.
- **Mods folder:** `Chunk0.def` ends with `mods\<mod>\<original path>` lines (CCT, PerfectPlextra, SuperString,
  TitantronFix, Universal Alternate Attire Unlock). A mod overrides a game pac by shipping the same relative path under
  `mods\<name>\` and listing it. **TitantronFix overrides `pac\audio\assetconv_p30.pac`**: it changes only field 15
  of 53 rows (flag bytes, e.g. 0x10000 -> 0x10101; titantron availability), so **any music-table change must start
  from the TitantronFix table** (`mods\TitantronFix\pac\audio\assetconv_p30.pac`, MD5 7e934337…) or it undoes the fix.
- **"Unmodded" copy is not vanilla:** it carries the same `mods\` folder and Chunk0 entries. Use the base files outside
  `mods\` for vanilla facts.

## 5. Route to a new slot (plan, see section 7)

Take an unused ID (e.g. one of the 747), then:
1. build a soundbank with `Play_MUS_<id>_00_0_0` / `_0_1` pointing at a new stream, packaged as a new
   `sound\patch_40.pck` (own Init bank + content bank + stream, like `patch_30.pck`);
2. ship `pac/root/_startup_audio_p40.pac` = the p30 script plus a `patch_40.pck` entry (BPE re-encode or stored);
3. give the slot's VMUM row a name index and menu index in a new top level `/MusicAndVideoList/PATCH40`
   (`assetconv_p40.pac`) — if the runtime patch list includes 40;
4. add the display name to the game's string table (location to find: `pac/string/`);
5. check the menu lists it and the event plays; then CCT.

## 6. CCT — measured so far

`D:\Pictures\WWE 2K19\A - CCT\Custom_Character_Tools.exe` is an obfuscated .NET (Mono) program that edits game memory
(`data.xml` = addresses and CAW/superstar/team/match lists; **no music list**). Its music names therefore come from
game memory or its own resources. Static decompiling is blocked: the assembly is packed (4 encrypted resources, AES,
clrjit hook; only 17 plain user strings, none about music). Asked Matthew how CCT presents music (dropdown of names vs
a number). If it reads the game's in-memory table, a new VMUM row is enough for CCT too; if it is a number field, any
ID works once the game knows it.

## 6b. Bank anatomy of a DLC track — measured (patch_30 bank 1755985664, MUS_0805)

```
Event  Play_MUS_0805_00_0_0 (fnv)  -> 1 action
Action 0x0403 Play  target = RanSeq 825486892, fade curve 4, bank id = 1755985664 (own bank)
RanSeq 825486892   parent = ActorMixer 126675442 (shared music mixer), 1 child, playlist weight 50000
Sound  541437393   codec plugin 0x00040001 (Wwise Vorbis), stream type 1 (streamed),
                   source id 381712218 = stream in patch_30.pck (3,593,341 bytes), parent = the RanSeq
```
`_0_1` uses an identical Play action. A third, unnamed event per track adds a Stop (0x0103) on the music mixer with a
3,000 ms fade. The ActorMixer 126675442 is re-declared in each patch bank with its child list.
Codecs across all banks: Vorbis only (0x40001; stream types 0/1/2) plus a source plugin 0x650002. Wwise PCM
(0x10001) is in the engine core but unused by the game.

**Audio source for a test:** Matthew's folders already hold community `.wem` files in the game's exact format
(RIFF, fmt tag 0xFFFF Wwise Vorbis, 2 ch, 48 kHz), e.g. `D:\Pictures\WWE 2K19\Alex Shelley\Alex Shelley Theme.wem`.
A new slot can use one directly; making new ones needs Wwise authoring (or a PCM .wem built by our own script).

## 6c. Names, IDs and the tool lists — measured

- **Display name = string id 13000 + music id** for music ids < 1000 (298 of 390 named rows; e.g. 13100 'The Rock' =
  MUS_0100, 13107 'Kane'). Ids >= 1000 (7xxx generic, 8xxx tag, 9xxx soundtrack) are named elsewhere (soundtrack
  titles/artists at 18000-18034 for the jukebox).
- Strings: `pac/string/win/string_win.pac` (overridden by SuperString: `mods/SuperString/pac/string/win/string_win.pac`,
  6 language tables of 26,674-26,675 strings; format in `tools/audio/strtab.py`). 3,597 placeholder strings
  ('EMPTY STRING TO BE FILLED' / 'WRESTLE PLUS CUSTOM STRING', ids 20797-28672) exist, none in the 13xxx range, so a
  new name means **adding an index entry** (rebuild the table).
- **Data Editor's music list** (`A - Data Editor 2k19/Data/DataLists/Modded/EntranceMusicID.data`, plain text,
  `<musicid*1000> <name>`, 1,737 lines) lists every id 100-9012 including **blank entries for unused ids**. Character
  data stores music as id*1000 (+ variation digits, e.g. 346010). CCT (same tool family) shows a dropdown; most likely
  the same list embedded. **629 ids are blank in that list and completely free in the game** (unnamed VMUM row, no
  event): 109, 110, 114, 116, 117, 120, … → **test slot = 109** (CCT should already list 109000).
- Music-table container: TitantronFix differs from base in 99 table bytes only (headers identical) → **no content
  checksum; in-place table edits work.**

## 7. Open questions (in order)

1. CCT shows music as a **dropdown of names** (Matthew 2026-11-09). Where it gets them: game memory (then a new
   table row + name is enough) or its own encrypted list (then CCT needs patching). Decompile blocked by packing.
2. ~~Patch levels above 30~~ answered for the audio script (p31/p40/p41 free); still to confirm for the music table's
   runtime patch list and for loading `assetconv_p40.pac` (Chunk0.def entry?).
3. ~~Where names live~~ string 13000+id (6c). Field 1 meaning still open (not the name id).
4. Tooling to author a v128 soundbank: Wwise 2016.2 authoring (matching bank version) or hand-built HIRC (a small
   Sound + Action + Event set, as in `patch_20`'s 519-byte bank).
5. The one check only Matthew can do: hear it in game and see it in CCT (asked once everything else is done).

## 8. Chosen route for the first test slot (2026-11-09)

Override, don't add levels, where possible (fewest new containers to write):
1. `sound\custom_music.pck` (new file): own bank with `Play_MUS_<id>_00_0_0` and `_0_1` + the stream.
2. `mods\CustomMusic\pac\root\_startup_audio_p30.pac`: the p30 script plus a `custom_music.pck` entry; listed
   in `Chunk0.def` after the existing mods.
3. `mods\CustomMusic\pac\audio\assetconv_p30.pac`: the TitantronFix table with the chosen empty row named and
   given a menu index; listed in `Chunk0.def` after TitantronFix (load order to confirm).
4. Name string (string table, SuperString also overrides it: build on its version).
Fallback if overrides of `pac\root` are ignored: the free p40 levels (section 4b).
