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
- **2026-11-10 ~18:00 (handoff 012): Test Wrestler (Alex Shelley clone) installed in overflow slot 509 (id 937) via slots proxy test1. Waiting on Matthew's boot.**
- **Latest handoff:** `handoff/012_test_wrestler_2026-11-10.md`.
- **Where things are:** source and scripts `tools/`; write-up `writeup/*.md`; notes `notes/`; references `reference/`;
  binaries (if ever needed) on the `assets` branch.
