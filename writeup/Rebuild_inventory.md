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
