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
| 15 | flags, e.g. 0x10101 (open) |

Rows per level: base 375, p01 388, p10 389, p20 390, **p30 1,147**. p30 = the 390 real rows **plus 757 unnamed rows
that fill every ID 0-999. 747 of those IDs have no Wwise event at all: empty, reserved slots** (`tools/audio/vmum.py`).

## 5. Route to a new slot (plan, see section 7)

Take an unused ID (e.g. one of the 747), then:
1. build a soundbank with `Play_MUS_<id>_00_0_0` / `_0_1` pointing at a new stream, and package it like `patch_30.pck`
   (or a new `patch_40.pck` if the game loads further patch levels — to check in the exe);
2. give its VMUM row a name index and menu index (or add a row) in a new top patch level of `assetconv`;
3. add the display name to the game's string table (location to find: `pac/string/`);
4. check the menu lists it and the event plays; then CCT.

## 6. CCT — measured so far

`D:\Pictures\WWE 2K19\A - CCT\Custom_Character_Tools.exe` is an obfuscated .NET (Mono) program that edits game memory
(`data.xml` = addresses and CAW/superstar/team/match lists; **no music list**). Its music names therefore come from
game memory or its own resources: to establish by decompiling (next step). If it reads the game's in-memory table, a
new VMUM row is enough for CCT too.

## 7. Open questions (in order)

1. How CCT lists music (decompile).
2. Whether the game loads patch levels above 30 (`PATCH%02d` loop bounds; `sound.pac`/`SoundScripts` bank list) or the
   new bank must go into `patch_30.pck` / a replaced p30 table.
3. Where display names live (string tables) and what field 1 indexes.
4. Tooling to author a v128 soundbank: Wwise 2016.2 authoring (matching bank version) or hand-built HIRC (a small
   Sound + Action + Event set, as in `patch_20`'s 519-byte bank).
5. The one check only Matthew can do: hear it in game and see it in CCT (asked once everything else is done).
