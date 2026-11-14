# Current state (one screen; read this first, then writeup/Status.md)

- **2026-11-14 final (handoff 019, latest): drag-and-drop Arena Pack final: 434 files, verified. Waiting on Matthew's tests (see handoff 019).**
- **2026-11-14 later: Raw '20 → 141, SmackDown '20 → 153 installed; light byte-order bug fixed on 124/143/128/160; SS22 hang fixed (crowd seats -2); pack 434 files. Waiting on Matthew's test.**
- **2026-11-14: batch 4 confirmed. Drag-and-drop Arena Pack built in Resources (`_Arena Pack (moddingwwe2k19) 2026-11-14`, 387 files, MD5-verified) for Matthew's from-scratch install; modded-game survey done (candidates: port versions of 104/106/108/110/111/115). See Arena_inventory.md last section.**
- **2026-11-13 night (handoff 018): AEW polish + batch 4 (127 NXT 2.0, 128 NXT W&G, 5 Tokyo Dome, 123 All In) installed, waiting on Matthew's test. Work folder now `common\WWE2K19_arena_work`.**
- **2026-11-13 evening: installs looked broken because chunk0.def was rebuilt over `_arena_work` (backup tables shadowed the live ones). Work folder moved to `common\WWE2K19_arena_work`, def cleaned; retest pending.**
- **2026-11-13 (handoff 017, latest): batch 2 fixes + 8 batch 3 arenas (125, 132, 135, 53, 134, 124, 143, 160) installed, waiting on Matthew's test. WM31 tried in 140/141/153 and reverted; original WM31 is slot 105.** Read `handoff/017_batch2fix_batch3_2026-11-13.md`; next-chat prompt in `handoff/PROMPT_next_chat.md`.
- **2026-11-12 (handoff 016): Genesis clean rebuild + arena installs.** Read `handoff/016_genesis_arenas_2026-11-12.md` and
  `writeup/Arena_inventory.md`. 10 arenas confirmed; batch 2 has 5 fixes pending (Grand Slam won't load). Next: those fixes, then batch 3.

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
- **2026-11-11 04:15 (handoff 014, claude/universe-qol): managers & main teams.** Wrong main teams fixed (unique pofo person ids); stale managers fixed at the source (`profile_pro.pac`); Matthew's team managers set; 6 wrong pofo slot ids fixed. DLL test12 (manager sync) installed 04:12; save verified. Start with `handoff/014_managers_teams_2026-11-11.md`.
- **2026-11-11 08:20 (handoff 015, claude/slots50-gfx): groundwork for CCT-filled slots.** Target 64 overflow character slots (CCT bridge = DLL test13, designed, not built) and entrance-video (GFX) slots: list loader/menu filter decoded (no fixed size), **gfx_v1 installed** (+~229 entries per video menu); waiting on Matthew's in-game check. Start with `handoff/015_slots64_gfx_2026-11-11.md`.
- **Latest handoffs:** `handoff/012_test_wrestler_2026-11-10.md` (slots), `handoff/013_universe_qol_2026-11-10.md` (Universe), `handoff/014_managers_teams_2026-11-11.md` (managers/teams).
- **Where things are:** source and scripts `tools/`; write-up `writeup/*.md`; notes `notes/`; references `reference/`;
  binaries (if ever needed) on the `assets` branch.

## Reminder (Matthew, 2026-11-11)
- Add **Dark Order**, **Private Party** and **The Kingdom** back into the MyWWE team list (missing from the game's 100
  team slots). Then set their managers (ask Matthew for picks) live + in profile_pro.pac.
