# Rebuild inventory: what Matthew's years of modding consist of (survey 2026-11-11 13:10)

Purpose: Matthew wants to redo the game on top of Genesis (500 native slots etc.) while preserving his own work.
This file lists that work as found in `D:\Pictures\WWE 2K19\A - Resources` (listing-level survey: folder names, file
names, dates, the notes and spreadsheets; individual packs were not opened) plus what the repo already knows.

## A. Items Matthew listed, with where the evidence is
| Item | Evidence in Resources |
| --- | --- |
| Tron aspect/availability recoding | `Changing to Make All Trons Available.xlsx` (ids 100+ with hex, per smacktalks assetconv tutorial), `Back - Added Titantrons File` (assetconv_p30 versions 2022-04 .. 2024-08, cae_item base "mine", cae_item_p20 lists 0000/0001/002A/002B/002C edited 2024-08), two smacktalks PDFs |
| AEW arenas | `Back - Arenas and Arena GFX` (All Out 21, Dark 21, DoN 19, Dynamite 20/22, Full Gear -> Fastlane slot, Grand Slam -> slot 163, Rampage 21, Revolution, Road Rager, All In; also NXT 2.0 -> slot 164, Raw 18 -> slot 96, ROH Death Before Dishonor, Tokyo Dome, Summerslam 09, RR 2020, RR Retro, Smackdown 21, ported 2K15-18 arenas), `Back - Misc01, Misc 04 and InitPosition` (misc01_start, misc04_arena, initposition, 0398.dat, light params, how-to), tutorials (mp4/html), `Fix Floating on Air Issue.txt` (stage number in misc01_start), loose `arentrance00164.pac` |
| CAWless + CCT slot routing | `Back - CAW Slots to Usable`: pack options 1-7 and Matthew's own series 91-99 (53 -> 85 CAW slots assigned), data.xml per step, `My Data Backup.xlsx` (CCT data table) |
| 15 irreplaceable CAWs | **Nothing in Resources.** They exist only in the save (and `Main Roster Renders\CAW`). |
| Custom GFX per mod, music baked into trons | `Back - Titantrons` (2,452 .bk2), `Back - Music Added to Trons` (bk2 + source mp4 + moveset for Bam Bam, Boss Man, Beefcake, Godfather, Luger, Papa Shango, Martel, Rock n Roll Express, Sid ...), per-wrestler folders in `D:\Pictures\WWE 2K19` (about 400) |

## B. Work found that was NOT in Matthew's list
1. **Announcer and commentary slot corrections** (`Back - Announcer and Commentary Corrected Slots`, 2025-05): edited
   `sound_p30.pac` parts, `0067.dat`, `0015.rass`.
2. **Ported entrances pack** (`Back - Ported Entrances`): pac/evt, mov, menu, audio, gimmick, particle, prop + a
   string_win with about 140 added names; sheet "Entrances and Victories" lists added entrance ids (DX 2K15, New Age
   Outlaws, Moustache Mountain, Uso's 2K20 ...). cae_item_p20 lists 0003/0004 (entrances) and 0015 (victories) were
   edited too, not only the tron lists.
3. **Tag team definitions**: `Tag Team Info`, 73 `.team_info` files (2024-08), e.g. Dark Order, Private Party.
4. **Moveset / pofo corrections**: `Movesets Adjusted` (24), `Pofos adjusted` (248, 2021-04), `Updated Entrances`
   (2), library `Movesets & pofo's` (4,073 files), separate folder `A - Updated Pofos`.
5. **Extra attires**: `Extra Attires.xlsx` (about 40 wrestlers with named alternate attires, e.g. RVD x9, Kofi x9).
6. **Sound bank edits**: `Back - Sound` holds .pck backups; `music_0..3_m.pck` and `music_misc_1` (2020-10 .. 2021-04)
   and `crowds_m.pck` (2021-03) are newer than the rest, i.e. replaced theme music / crowd audio; AEW Dynamite and
   SmackDown themes as .wem.
7. **Presentation GFX beyond arenas**: matchup screens (AEW), AEW / NJPW title GFX, copyright + locator screens
   (AEW, NJPW, ROH), AEW crowd shirts, ceiling light, Raw PPV stage, "Old WWE 2k GFX", Raw intro folder.
8. **Renders**: `Renders` (978 .dds), `Main Roster Renders`.
9. **"Needs Re-injection" list**: Big E, Bray Wyatt, Dash Wilder, Eric Young, Erick Rowan '14, Liv Morgan, Luke
   Harper '14, Otis, Scott Dawson (models + pofo + moveset) = unfinished work.
10. **Downloaded character ports not yet sorted**: `2k19 Characters` (59 archives), `2k23 Ports` (25), `2k24 and 25
    Ports` (34).
11. **Mod base backups**: `Back - Mods` (CCT, PerfectPlextra, SuperString, TitantronFix, Universal Alternate Attire
    Unlock).
12. Tool folders next to Resources imply further edits to check with Matthew: Data Editor 2k19, Item Adder, PC
    Trainer, Sound Editor, X-Packer, Ninja Ripper, rePac; CCT `replaced_data.xml` also has Teams and Matches lists.
13. This project's own work (repo): 589 music slots, Universe fixes + manager sync (DLL), manager/team/id save
    repairs, tracker, gfx_v1 menu entries, 6 test overflow slots.

## C. Facts settled by the notes in Resources
- cae_item list ids (note in `Back - Added Titantrons File`): **0000 titantron, 0001 minitron, 0002 BGM, 0003 entrance,
  0004 tag, 0005 trio, 0008-000B + 0010 advanced entrance motions, 0011 champ entrances, 0015-0026 victories,
  002A ramp, 002B apron, 002C wall, 002D MITB entrances.** So gfx_v1 covered mini/ramp/apron/wall and left the
  titantron list (0000) out.

## D. Risks seen while surveying
- **Genesis CAWLESS overlay vs the CAWs.** Matthew's profile_dat.pac before Genesis (e52943c4...) is 9 bytes from the
  pack's "90 CAW slots assigned" option, i.e. about 10 CAW slots stayed real CAW slots. Genesis's CAWLESS is described
  as 105 slots (all 100 CAW slots) and its file differs from Matthew's in 693 bytes. Whether the CAWs stay reachable
  is unverified. The pre-Genesis file exists in three places (`profile_dat.pac.orig_musicslot`, Genesis backup,
  none in Resources); the save with the CAWs is copied in `snapshot_pre_genesis_slots_20261111\SAVEDATA`.
- The CAWs have no backup outside the save file.

## E. Rebuild rules set by Matthew (13:26)
- **Ground truth = the installed game + the save**, not the per-wrestler folders: pofo/moveset in game carry his
  in-game rating edits; every wrestler has working graphics and a render in game. Folders only fill in the dozen or
  so wrestlers not installed yet.
- Fewer than 400 mods vs 500 new Genesis slots: on a fresh install the mods go into new slots only; CAW, MyCareer
  and legend slots stay untouched.
- **No music baked into GFX any more** (real music slots exist): strip audio from every tron.
- Name strings: copy from the existing string file. Renders in game are the source; a few custom renders he wants
  to change (details to come).
- Moving a mod = movies (count varies), moveset re-pointed, render, model(s) per attire (+ pofo id, name string).
## F. First measurements of the installed roster (chunk0.def + CCT names, 13:30)
- Models: 491 ids (100-999) have model files; 921 model pacs under `mods\CCT\characters`, the same 921 again under
  `mods\Genesis\characters` (Genesis migration copied them; both sets are now in chunk0.def = the duplicate names),
  310 base. Attires per id: 416 with one, 43 two, 11 three, 10 four, 11 with five to ten.
- 374 slots carry a CCT replaced name (= Matthew's mods), 368 of them have model files.
- Screen trons: 402 ids have all four (wall/mini/ramp/apron); of the 374 named slots 320 have all four, 36 none.
- `movies\titantron`: 2,553 .bk2 (ent 2231, tag 273, bel 31, cre 7, uni 6, car 3, bray 2).
- Plan: read-only exporter that packages every installed wrestler from the game (models, render, trons, name) and
  the save (pofo, moveset) into one normalized package per wrestler + a roster table; then an importer for Genesis
  slots once their layout is known.

## G. What Genesis "Character Slot Expansion (500)" did (installed 13:32, diffed against the snapshot manifest)
- **It is an exe patch, not a DLL.** `WWE2K19_x64.exe` 41,065,640 -> 43,078,144 bytes: two new sections `.attire`
  (249 bytes) and `.chslots` (2,011,400 bytes at VA 0x14367E000...), 257 bytes changed in the original image in 37
  runs (header; file offsets 0x20b614, 0x24a13b-0x24aa10, 0x49e52d-0x49e8b0, 0x4c6a30, 0x4c8bd0, 0x4c8cd0,
  0x9649a0-0x964b70, 0xbf1508-0xbfc8fe, 0x190dd81-0x190e8d8). Original exe kept by Genesis
  (`genesis_backups\Character_Slot_Expansion_(500)`) and in our snapshot.
- Replaced (Genesis backed each up): PerfectPlextra `profile_dat.pac` 294,912 -> 514,048, `profile_pro.pac`
  671,744 -> 1,185,792 (**our stale-manager clear in profile_pro is gone from the live file**), `profile_mvs.pac`
  1,314,816 -> 2,330,624; `mods\Universal Alternate Attire Unlock\pac\root\misc01_start_p30.pac` 77,824 -> 229,376.
  Added `pac\ch\ch93702.pac`, `ch93802.pac` (49 MB each), marker in `genesis_mods\`. chunk0.def regenerated (same
  size), Chunk0.arc cleared. Log: "installed a 514,048-byte profile_dat.pac (CAWLESS's is 294,912); incompatible,
  leaving the new file in place" = the CAWLESS overlay is superseded.
- **Slot map published by Genesis**: `A - Genesis\_internal\DATABASE\ROSTER\expansion\All_500_Slots.json`: 500
  records {character_id, physical_index, pofo_address, moveset_address, sizes, selectable_by_default}; physical
  index 509-1008; ids = the unused ids from 109 up to 1007 plus 1023 (9 ids >= 1000); pofo records at 0x200 spacing
  from 0x143682000, movesets 0xD90 apart; 2 selectable by default (937, 938 = the two shipped models). Same folder:
  "WWE 2K19 Memory Sheet" xlsx for MyWWE and Universe1-3, data.xml.
- **Collision with our work:** our 6 test slots use index 509-514 and ids 937-942, all inside Genesis's map; our DLL
  patches several of the same code sites. `dinput8.dll` (test12) was not touched by Genesis; **renamed 13:36 to
  `dinput8.dll.test12_disabled_for_genesis`** so the first launch tests Genesis alone. Consequence while disabled:
  no Universe fixes / manager sync / overflow slots / team import from our DLL. The 589 music slots are data files
  and should not depend on the DLL (to confirm in game).
- Next: Matthew launches (no saving), reports; then a DLL build without the slot code and with its exe checks
  matched to the Genesis exe (sha256 551c1e34...).

## H. Genesis "Universe Match Table Expansion" (installed 13:42, diffed against `snapshot_after_slot_expansion_20261111`)
- Only one game file changed: `pac\universe\wunidata.pac` (32,768 bytes, 411 bytes differ; was the vanilla file
  526bd92a..., now 2249cb40...; Genesis backup in `genesis_backups\Universe_Match_Table_Expansion`). Exe unchanged
  (de4d3756...), chunk0.def regenerated at the same size, marker added.
- No overlap with our files: our Universe team work changed `wunistable.pac` (still our version, 04:51 today); our
  DLL does not touch wunidata. Baseline for the next module: `snapshot_after_match_module_20261111`.

## I. Genesis "Attire Slot Expansion (1000)" (installed 13:49, diffed against `snapshot_after_match_module_20261111`)
- Exe rewritten but **byte-identical** (de4d3756...): the slot expansion had already installed the combined
  "CH+Attire" exe (the `.attire` section was there since 13:32). Log: "installed combo CH+Attire (Steam) exe".
- `mods\Universal Alternate Attire Unlock\pac\root\misc01_start_p30.pac` rewritten at the same size (229,376;
  e556c887... -> bb47c6e1...). Log: "No existing attire definitions to carry over."
- **To verify:** Matthew's own attire file (77,824 bytes, dated 2023-10-25) was replaced by the slot expansion at
  13:32, before the attire module looked for definitions to carry over. It is preserved in
  `genesis_backups\Character_Slot_Expansion_(500)\mods\Universal Alternate Attire Unlock\pac\root\`. His extra-attire
  definitions (Extra Attires.xlsx, about 40 wrestlers) are probably not in the live file now.
- Baseline for the entrances/victory module: `snapshot_after_attire_20261111` (manifest; MD5 of 9,669 files in
  pac/menu, audio, gimmick, particle, prop and most of pac/evt; key-file MD5s incl. string_win).

## J. Genesis "Ported Entrance & Victory Motions Pack" (installed 14:09, existing strings kept)
- Source per Genesis log: archive.org "Ported entrance and victory motions from 2k20 and previous games.zip"
  (567 MB), 924 files overlaid, 46 extra files from 30 "additional entrance" options, 920+ originals backed up to
  `genesis_backups\Ported_Entrance_&_Victory_Motions_Pack`. Exe, string_win untouched (only a readme added).
- Check of Matthew's guess ("same as what I installed years ago"): each of the 929 backed-up originals compared
  with the file now live (`snapshot_after_entrances_20261111\entrance_pack_compare.tsv`):
  **897 identical, 32 different.**
- The 32 that changed (Matthew's previous versions are in the Genesis backup):
  - **`pac\menu\cae_item_p20.pac` 59,392 -> 45,056**: Matthew's version held his own menu-list edits (tron lists
    0000/0001/002A/002B/002C, entrances, victories; 124 entries per tron list). The pack's stock file replaced it.
  - **`pac\audio\sound_p30.pac`** (same size, content differs): Matthew's 2025-05 announcer/commentary corrections
    were in this file.
  - `pac\evt\evt_light.pac`; 14 entrance files with a different size (00150, 00288, 00358, 00377, 00432 Steve
    Austin 2k20, 00469 + 00483 + 00681 CM Punk, 00560 Tazz, 00967 Dean Ambrose Shield, 01033 Daniel Bryan Champ,
    01049 Roman Reigns champ, 01811, 08100); 13 `pac\evt\effect` files; `pac\gimmick\gmev0636_TakerwithDruids.pac`;
    `pac\prop\6342.pac`. Whether Matthew's or the pack's version is the better one for these is not known.
- Recommendation: restore Matthew's cae_item_p20.pac and sound_p30.pac from the Genesis backup (clear losses);
  decide the other 30 after an in-game look. Not done yet (waiting for Matthew).
- Baseline for the moves pack: key-file MD5s (89 files) in `snapshot_after_entrances_20261111`; full-tree listing
  became too slow to repeat, so the next diff relies on Genesis's own backup folder + log, as done here.
- Entrance pack, new vs already present (zip listing vs Genesis backup): the zip has 924 files; **920 overwrote a
  file Matthew already had** (pac/evt 755, particle 57, gimmick 54, prop 43, mov 8, menu 2, audio 1), of which 897
  identical; new from the core pack = `pac\audio\sound_evt.pac` only (+ readme; its string_win was declined).
  The **"Additional entrances" options (46 files from 30 options) are the new material**: 37 new files, 9 replaced
  existing ones (pac/evt 00150, 00288, 00358, 00377, 01811, 08100, two effect files, prop 6342). Matthew's old
  install kept those options out ("OPTIONAL FILES - do not copy"). So of the 32 differing files, 9 are options and
  23 are core-pack files where his copy differed.

## K. Genesis "Ported Moves & Animations Pack" (installed 14:32)
- Source: archive.org "Ported moves mod pack from 2k15-2k20.zip" (121 MB). Installed as its own mod folder
  `mods\Ported Moves and Animations Pack` (66 files, zip root `pac/` stripped); nothing in `pac\` overwritten, no
  backup folder needed.
- All 66 shadow an existing base file: `ingame\motion\body\NN_mpc/_param.pac` (34), `ingame\mot_*_patch_p10/p20`,
  `motion_param_pcdb`, `diving_param(+_p30)`, `peoples_script`, `root\createmode(+p10/p20/p30)`, `audio\attr\*` (19),
  `audio\sound_p30.pac`. Compared with Matthew's `pac\` copies: **61 differ (49 larger), 5 identical** = this pack
  was not in his game before; it is new material.
- chunk0.def now lists both copies (e.g. `pac\audio\sound_p30.pac` and `mods\ported moves and animations
  pack\audio\sound_p30.pac`); which one the game loads is untested.
- **Three different sound_p30.pac now exist**: Matthew's with the announcer corrections (Genesis backup, 4054b49f),
  the entrance pack's (live in pac\audio, 27564138), the moves pack's (mods folder, de0741ff). Each carries its own
  sound entries, so the end state needs a merge, not a pick.
- Seen in `A - Genesis\_internal\Mods`: **"1000 Extra Music Slots.zip"**, "Additional Universe Mode Matches.zip",
  "Womens Tag Team and Extra Championships", "Dark Mode", "Empty Attire Slots.zip", PerfectPlextra1.5, SuperString,
  TitantronFix.

## L. Genesis "1000 Extra Music Slots" (package read 14:45, NOT installed)
- `A - Genesis\_internal\Mods\1000 Extra Music Slots.zip` (10 KB, packaged 2026-10-25): `tools/MusicSlots/
  music_slots.py`, README, `EntranceMusicID_additions.txt` (500 lines, 9013000..9512000; README says 1000 slots
  9013..10012, script default count 500), empty `slots/`.
- Method (script read in full): never touches the exe. Clones the stock theme event `Play_MUS_8005_00_9_0`
  (event/action/container/sound) once per slot into the main music bank 0xE85DDA21 inside `sound\music_e_s.pck`
  (events for mode 0 and 9 + an alias name for the raw stream id), adds the new containers to the parent ActorMixer,
  and appends one stream per slot (id 0x6D000000 + n, silent 0.1 s placeholder) to `sound\music_3_m.pck`. Rebuilds
  always start from its own backup of those two files; keeps audio injected earlier; `sync` fixes PCM/Vorbis plugin
  tags; `verify`, `restore` commands. Moveset music value = ID*1000 + 9.
- **It adds no in-game menu entries**: no BGM list entry in cae_item, no assetconv/VMUM row, no MEMU record, no
  name string. Assignment is done outside the game, in Genesis's moveset editor ("Open Theme NNNN").
- Versus our bank (589 slots): ours lives in `sound\patch_30.pck` (DLC_30 bank), ids from the free 100-999 pool,
  with VMUM rows, menu entries and registry records so slots are selectable in Create an Entrance in game.
  **No file overlap and no id overlap** between the two; they can coexist. Same core idea (clone a stock theme's
  Wwise objects, append a stream).
- Untested: whether a moveset value in the 9013+ range plays in game without a VMUM row; Genesis's Audio tab flow.
