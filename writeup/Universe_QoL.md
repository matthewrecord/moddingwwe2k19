# Universe mode QoL: requirements and plan (thread started 2026-11-10)

## Matthew's answers (interview 2026-11-10 20:21)
- Record keeping: wants all of it: W-L per wrestler, match history (opponents, show, result, match type), streaks,
  per-show/brand records, tag-team records, rankings/power list ("would be phenomenal").
- Title history: core complaint = history is attributed per slot/variant: HHH, HHH '02, HHH '13 counted separately;
  worse, when a slot was reused for a different wrestler, the old reigns stayed with the slot. So history must be keyed
  by a stable *person* identity (alias groups like HHH variants), not by game slot/character id.
- Other stats (star ratings, match of the night, rivalry history, appearances, PPV results, year-end awards): wanted.
- Pain point: roster changes import into Universe, **tag teams do not**; custom teams must be recreated by hand.
- Today: tracks in a spreadsheet `wrestlingratings.xls` (path to be confirmed: not in Documents/OneDrive/modding folder).
- No Universe running now; no saves exist (Steam userdata 93452036 has no WWE 2K19 app folder). Starting fresh is fine.
- Display: in game is the long-term goal; external is acceptable first.

## Plan (triage order; nothing trimmed)
1. **Overflow-slot save safety** (blocks real use of slots 510-515). Matthew starts a throwaway Universe with Test
   Wrestlers on a show and one holding a title; save, quit, reload. Agent: locate the save folder on first save, back
   up every step, read `wwe2k19_slots.log` TRACE/VFS lines and take `slots_snapshot.request` dumps at each step.
2. **Save format survey**: container/compression/checksum, Universe sections (shows, roster/brands, titles+reign
   history, match results, rivalries, teams); how each is keyed (char id vs profile index). Snapshot diffs per show.
3. **External tracker v1** (save -> history): match log, W-L, streaks, title lineage with days/defenses, keyed by a
   person-identity map Matthew controls (merges variants, splits reused slots by date). Output layout follows his
   `wrestlingratings.xls`. Appends after each show so history survives slot reuse.
4. **Tag-team import**: find team records in the Universe save (and the roster/teams source the game imports from);
   tool to write custom teams into a Universe save or patch the import.
5. **Stats layer**: star ratings, match of the night, PPV results, rivalries, appearances, year-end awards.
6. **In game (long term)**: DLL hooks so title history/records use the person identity and/or show our records in menus.

## Findings log
- 2026-11-10 20:50 **Save location found**: Steam app id is **817130** (steam_appid.txt; not 960090), saves in
  `C:\Program Files (x86)\Steam\userdata\93452036\817130\remote\SAVEDATA` + `SAVEDATA_BACKUP` (identical, 49,922,765
  bytes, md5 2bfe6591a0a9b873537ec69ef9c97b7d after Universe show 1). Steam Cloud syncs this folder (remotecache.vdf).
  Backup: `<game>\_moddingwwe2k19_builds\saves\20261110_2044_universe_after_show1\`.
  Options files (not saves) are in `D:\Documents\WWE2K19\`.
- Save format first look: whole file is obfuscated; header begins `aurr3198`; recurring `35 36 35 36` / `36 35 36 37`
  where plaintext is presumably zero -> looks like a simple position-keyed XOR/additive stream, not compression or
  encryption. First ~36 MB high entropy (7.98 bits/byte: compressed or random-keyed), tail lower (4.4-6.2). To decode
  in step 2 (exe: `CUserSaveDataIOThread`, `yCSetProfileMainSaveData`, `CDefaultSaveDataMaker`).
- Matthew's Universe show 1 (20:44) with Test Wrestlers **Angel Garza (slot 512)** and **Keith Lee (slot 511)**, each
  holding a title. Observed:
  1. Every Test Wrestler defaults to **three copies of one CAW as manager** in Universe (bug; hypothesis: a 509-wide
     per-superstar Universe table read at index >= 509 lands in neighbouring data, e.g. the CAW block).
  2. Neither entrance played (both champions). Earlier, without titles, entrances played in some arenas.
  3. In their match wrestlers fell randomly, then glitched: one could not get up, the other could not grab him;
     repeated the same on SmackDown. (Hypothesis: the manager/run-in AI or a bad Universe per-superstar record.)
  Slots log for this session: no crash/exception records; TRACE lines only from known getters.
  The previous throwaway Universe save was overwritten by this one (only one Universe save slot file).
- 2026-11-10 20:55 **Matthew's tracker** `D:\Documents\wrestling ratings.xlsx` (read-only look). Sheets: KOTR Rules,
  Size (height/weight class), Events (month -> show/PPV per brand WWE/WCW/NXT, WHC), Ratings / Ratings (2) / Sheet3
  (per-wrestler brand, team, tier, est. rating + attribute columns), Music, **Wrestlers** (968 rows: Wrestler, Brand,
  Team, Mod/CC/CAW, Gen, **Character Slot** e.g. "408 - Robert Gibson" for Dalton Castle, Tron, Music; plus a team
  list with trons/songs/motions), History and Ideas (draft notes), and per-PPV sheets (Aug - Summerslam, Sep - NXT
  Takeover, Oct|Nov - AEW PPV ...) with results by year ("X def. Y", champion marked ©).
  => The **Wrestlers sheet is already the person -> game slot map** the tracker needs (fixes the HHH/slot-reuse
  problem), and the **team list** is the source for the tag-team import (step 4). PPV sheets = his existing
  results/title-history format; tracker output should extend that, not replace it.
- 2026-11-10 20:59 Reload test (Matthew): champions were **Keith Lee (slot 511) and Ace Austin (slot 513)** (correction:
  not Angel Garza). After quit + relaunch + load both are **still champions**: overflow slots survive save/reload at
  least for title holders. Universe has no screen for past results (confirms the need for an external/in-game log).
  **Control match** (managers removed, non-title): entrances play and the match is normal. So bugs 2+3 come from
  either the phantom managers or the title match path; next split: title match without managers.
