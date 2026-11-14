# Current state (one screen; read this first, then writeup/Status.md)

- **2026-11-09 (setup chat): repository scaffolded**, structured like `matthewrecord/botf-tools` (README, CLAUDE.md,
  GEMINI.md, STATE.md, WORKFLOW.md, `writeup/`, `handoff/`, `notes/`, `tools/`, `reference/`, branch `assets`).
  No mod work started. Nothing in the game folders has been changed.
- **Goal (binding, Matthew 2026-11-09):** add brand-new music slots (not replacements) that CCT can see and use. This is
  the validation for the whole project. Status.md section 1.
- **Autonomy (binding):** agents run and verify everything themselves; stop for Matthew only when it genuinely cannot
  be settled from our side. Status.md rule 5.
- **2026-11-09 (music survey, handoff 002):** music path mapped (`writeup/Music_map.md`): audio in `sound/music_*_m.pck`,
  events `Play_MUS_<id>_..` in banks in `music_e_s.pck` and DLC `patch_NN.pck`, music list = VMUM table in
  `pac/audio/assetconv_pNN.pac`. DLC added new IDs this way; p30 table already holds 747 empty IDs. Next: how CCT lists
  music (decompile), whether the game loads patch levels above 30, string table for names, bank authoring.
- **2026-11-09 evening (handoff 003):** loader traced. `.pck` list lives in BPE-compressed `pac/root/_startup_audio_pNN.pac`;
  the exe tries levels 01,10,11,20,21,30,31,40,41, so **p40 is free: a new audio patch needs no exe change**. Music
  table: highest `/MusicAndVideoList/PATCHnn` wins. CCT uses a dropdown (Matthew). Next: runtime patch list for the
  music table, BPE/HSPC re-pack, bank authoring, string table.
- **2026-11-09 night (handoff 004):** route mapped end to end. Runtime patch list = `observe_info.csv` (data).
  DLC track anatomy decoded (Event -> Play -> RanSeq -> Vorbis streamed Sound). Names = string 13000+id. Test slot
  **109** (blank in Data Editor/CCT list, free in game). No checksum on the music table. Remaining: GCOM list record
  format + BPE encoder, HSPC writer for the string table, bank writer, then build.
- **2026-11-09 night (handoff 005): FIRST NEW MUSIC SLOT BUILT AND INSTALLED (slot 109, Alex Shelley test theme).**
  Verified offline (our parsers + wwiser); installed in the modded game with backups (notes/builds/slot109.md).
  v1: boots, but not in the CAE list -> **v2 installed** (entry in base cae_item.pac, Item Adder method).
  v2 not visible either: our pac writer appended past header word 15's data region -> fixed (Pac Editor-style
  relayout). v3 not listed; v4 markers proved our files are read; cause = CAE lists are one combined index (base
  append overwritten by p10). v5/v6/v7 diagnostics: menu rejects music id 109 -> missing MEMU music-info record (misc05_save_p30).
  **v8 installed (adds the MEMU record); waiting on Matthew's check.**
- **2026-11-10 (handoffs 006, 007): NEW MUSIC SLOTS VALIDATED IN GAME.** All 8 test slots of `multi_v14_nounlock`
  show in Create an Entrance > Entrance Music, play, and save/reload. The hidden-slot gate was the BGM entry's
  unlock-requirement fields (u16 +4..+0xC; -1 = none); `musicslot.py` now writes none. Found with an in-game telemetry
  DLL (`tools/telemetry/`). **Next: CCT check, then productise (real names, multiple songs).**
- **2026-11-10 midday (handoff 008): tool productised.** Validation now = works with **Data Editor and Sound Editor**
  (Matthew: CCT is not his main assignment route). `musicslot.py --spec/--list-free/--tools` (per-song .wem, automatic
  free ids, writes Data Editor `EntranceMusicID.data` + Sound Editor `custom_data.xml` names); `install.py --tools`.
  Build `songs4_v15` (4 real songs, ids 109/116/117/807) ready, not installed; v14 still in the game.
- **2026-11-10 afternoon (handoff 009): SLOT BANK INSTALLED.** Plan (Matthew): create slots once, then Sound Editor
  fills songs and Data Editor assigns. All 589 free ids built with a silent placeholder, names "Custom 001..589",
  200 in the CAE menu; drop-in menu files (300/400/500/589/original) in `A - Resources\Extra Music Slots (moddingwwe2k19)`.
  v14 TEST build removed. **13:03: Matthew confirms a song injected with Sound Editor into Custom 001 plays in game. Workflow validated.**
- **2026-11-10 afternoon (survey 001, handoff 010): character slots.** Exe: select screen = playable flag (pofo
  +0x20) + no unowned store/showcase unlockable; **hard cap 509 superstar profiles** (beyond = exe patch). Test
  `charsel_v1` installed (unlock 160/335/330, playable 274); waiting on Matthew's select-screen check.
- **2026-11-10 17:35 (handoff 011): character slots stage 1: test0 proxy `dinput8.dll` installed (behaviour-neutral patch mechanism check). Waiting on Matthew's boot + one match.**
- **2026-11-10 18:54-19:07 (handoff 012): FIRST CHARACTER BEYOND THE 509 CAP WORKS (Exhibition singles + tag, Universe).** Open: entrance skipped in some arenas. Test Wrestler (Alex Shelley clone) in overflow slot 509, id 937, via `tools/slots` proxy dinput8.dll (test1k) + `tools/build/charslot.py`. Root cause of the earlier hangs: copied asset pacs must carry their new internal names (notes/characters step 1j). The DLL also carries permanent diagnostics (crash log, file log, code trace, VFS not-found log, remote snapshot).
- **Next thread (Matthew 20:14): Universe QoL (record keeping, title history) incl. overflow-slot save safety: `handoff/013_universe_qol_2026-11-10.md`.**
- **2026-11-11 01:46 (handoff 013, claude/universe-qol, merged): Universe QoL.** Tracker live (auto capture -> D:\Documents\WWE2K19 Universe Tracker\Universe N\standings.html; PPV calendar from the save). **Team import works**: DLL test8 swaps the Universe team seed for Matthew's 68 MyWWE teams when he imports his MyWWE superstars. Earlier notes:
- **2026-11-10 21:44 (handoff 013, branch claude/universe-qol): Universe QoL thread.** Requirements + plan in
  `writeup/Universe_QoL.md` (Matthew's tracker `D:\Documents\wrestling ratings.xlsx`; saves `Steam\userdata\93452036\817130\remote`,
  XOR key 37 36 35 36). Overflow wrestlers survive Universe save/reload and work in title/non-title matches; bug:
  Universe creation gives them 3 phantom CAW managers (show-1 glitches tracked to that). DLL test3b installed (memory
  reads + Universe probe).
- **2026-11-12 (handoff 014): NEW THREAD: model backport tool** (newer 2K games -> 2K19, ~60 matched pairs by one porter). Feasibility test next: `handoff/014_backport_tool_2026-11-12.md`.
- **2026-11-12 night (handoff 015, branch claude/backport-tool): backport FEASIBILITY DONE.** Own readers for 2K22+ MDL and 2K19 JBOY (`tools/backport/`). The porter's body weights = a fixed 2K19 template (male ports predict each other at ~90% dominant-bone agreement vs 75-79% for a naive name copy); 2K19 takes 7 influences. Matthew: no new tools on his side; Python yes, Blender no. Next: find the template among stock 2K19 bodies, decode JBOY indices/materials/textures. `writeup/Backport.md`.
- **2026-11-13 ~01:00 (handoff 015, cont.): templates found** (men = stock ch687 Andrade, women = ch756); textures, materials and strips decoded. JBOY fully mapped incl. 119 face morph targets (regenerated by the porter; source not a superstar head). Next: writer (round trip first), then face morph transfer. `writeup/Backport.md` sections 6-12.
- **2026-11-13 ~04:45: BACKPORT TEST 1 INSTALLED** (Willow slot 865 in Genesis, with pipeline-generated shoes + kneepads; backup in `_moddingwwe2k19_builds\backport\test1_willow`). JBOY writer round-trips 62/62 models; pac writer; regen pipeline v0. **Result: CRASH at select screen; original restored. (Matthew asked for no installs during that conversation only; ask before installing.)** **Cause found: our pac writer omitted his 2,048-byte EOP5 footer, so the size field cut off the last block.** Fixed (container rebuild byte-identical 7/7). **B2 and C2 both WORK in game (Matthew 00:31): first in-game validation of the backport pipeline.** `notes/builds/backport_test1_willow.md`.
- **2026-11-13 00:50: FLETCHER FULL REGEN (v2) LOOKS GREAT IN GAME** (body/hair/attire/textures from 2K24 files; face still the porter's). Next: face step (head + 119 morphs + grafted stock parts), then donor-based build on ch687.
- **2026-11-14 (handoff 018): title belt backport.** IWGP US title (2K23) onto the Brahma Bull WWE Championship (prop 2905 + 5038), PLAIN install, `tools/backport/belt_port.py`. Freeze fixed (ZLIB, stock-size pacs); flat-gold plate fixed (2K19 facing convention, normals flipped). `iwgp_brahma_v4` **works in game** (Matthew 2026-11-14); tracer removed. `writeup/Belt_backport.md` sections 13-14 are the current state.
- **Latest handoffs:** `handoff/017_backport_keith_tools_2026-11-13.md` (backport, latest), `handoff/012_test_wrestler_2026-11-10.md` (slots), `handoff/013_universe_qol_2026-11-10.md` (Universe), `handoff/015_backport_feasibility_2026-11-12.md` (backport).
- **Where things are:** source and scripts `tools/`; write-up `writeup/*.md`; notes `notes/`; references `reference/`;
  binaries (if ever needed) on the `assets` branch.


## 2026-11-13 backport
First from-scratch port works: Flash Morgan Webster (2K25), `_moddingwwe2k19_builds/backport/test5_fmw/` (v4 delivered via chat), slot ch50602. Branch `claude/backport-tool`. Tools: `tools/backport/build_fmw.py`, `pose.py`, `facecheck.py`. Open: hovering hands. Next: generalize the builder. Details: writeup/Backport.md §23-24.

## 2026-11-13 (later) backport
General builder works: `tools/backport/build_port.py` (configs BRISCOE, FLASH); both v3 builds look spectacular in game. Workflow + bench gates: `tools/backport/README.md`. Handoff: `handoff/016`. Next: female template, then the app.

## 2026-11-13 (afternoon) backport
Validated in game: Flash v4 (pending re-check), Briscoe v4, **Toni Storm v3 (first female; eyes fixed via container eye masks)**. Templates male/female in `tools/backport/build_port.py`; full gates in `tools/backport/README.md`. Next: Toni facepaint / B&W variants (same config, different source folder), then the app.

## 2026-11-13 (15:50) backport: handoff 017
Keith Lee v3 delivered: ring `ch50602` and entrance `ch50604`, pinholes capped. The old 2K20 Keith's eyes are patched with the new `eyepatch.py`. Both await Matthew's check. Every tool and gate is documented in `tools/backport/README.md` (module map, per-character recipe, patching existing pacs). Branch `claude/backport-tool`. Next: verdicts, then merge, then the app. **Read `handoff/017` first.**
