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
- 2026-11-10 21:10 **Save decode, first layer.** XOR with the 4-byte key `37 36 35 36` (position mod 4) turns the
  header into magic `VCGD`, then a directory of tagged chunks: 738 tags of the form 4+4 letters + 4 digits
  (`CAASADDT0000`, `CASSBODY0001`, `CCACBIGH0000`, `CASSDHHW7367`, ...), each followed by a u32 size and a 4-byte
  hash; many payloads start `ZLIB` (zlib) or carry 0x40/0x80 flags. These are the creation-suite assets (CAW/CAA/
  CAE images, bodies, heads) in roughly 0x0-0x2200000 (high entropy). The structured tail 0x2200000-0x2600000
  (~4 MB, 40% zero after XOR) is the candidate for profile + Universe data. Caveat: some tail runs read as clear ASCII
  *before* XOR (e.g. `WWE2K17*(UYHDAKJ`), so the key may change per block: next step is to map block boundaries in
  the tail and confirm the key per block, then diff against a save taken after show 2.
  Decoder scratch: device `/tmp/sav.xor` (not kept). Exe anchors: `CUserSaveDataIOThread`, `CDefaultSaveDataMaker`.
- 2026-11-10 21:05 Correction (Matthew): managers were removed in **every** match, including the broken ones. So the
  only difference between the broken matches (no entrance, falling/glitching) and the normal control match is
  **title vs non-title**. Leading hypothesis now: the title-match path (champion entrance / belt / title data) looks
  up the champion in a 509-wide table or asset index and gets bad data for overflow slots. The phantom-manager bug
  is a separate default-data bug. Next tests: same overflow wrestler in a title match vs a vanilla opponent, and a
  vanilla champion in a title match (control), with snapshots + TRACE lines during the entrance.
- 2026-11-10 21:30 **Universe per-superstar table (static).** Cluster 0x140bb0000-0x140bd5000 holds ~250 loops bounded
  by 0x1FD (509). Function 0x140bbe5e0 (called from 0x140bbf2f8, 0x140bbf5df) linearly searches an array of **509
  records x 0x450 bytes** at obj+8 for a **character id at +0x38c** (0x400 = none), then reads +0x36c (value < 6)
  and a 6 x 0x48 sub-array at +0xC (entries with -1 = empty, +0x14 == 2 checked by the caller). A 0x4000-byte init
  at 0x140bc47c0 sets several (count 0, cap 0x1FD, default 0x400) lists. Hypothesis: this is the Universe roster
  (one record per superstar, keyed by id, 509 max); overflow wrestlers either occupy free rows (fine) or get
  half-initialised rows (managers = leftover/default data). Most-referenced globals in the cluster: 0x1425e7e20 (13),
  0x1425e6968 (9) -> candidate Universe manager pointers. Next: read them live with DLL test3 (`slots_mem.request`).
- Save: ids 937-939 do not occur as u32 anywhere in the decoded save; 940-942 only sporadically -> the Universe
  section is probably compressed (zlib chunks) or keyed differently; decoding continues after the live dump.
- 2026-11-10 21:12 (Matthew) **Keith Lee (overflow, champion) vs HHH (vanilla), title match: works** (entrance + match
  normal). So a title match with one overflow champion is fine. Hypotheses narrowed to the specific broken setup:
  two overflow wrestlers in one title match, or champion vs champion (two belts), or that specific opponent/slot.
- 2026-11-10 21:25 Live reads (test3) work: [0x1425e7e20] = heap 0x4dcc1150, [0x1425e6968] = 0x5330010. A full-memory
  dump (slots_full_107.dmp, 2.0 GB, Universe main screen) scanned with `tools/universe/dmpscan.py` for the 509 x
  0x450 id table found **no** contiguous table (only noise). So the object passed to 0x140bbe5e0 is not where we
  guessed, or that table is only built while booking a show. Static: its caller 0x140bbef80 receives it as arg 3.
  => test3b DLL (md5 ad10100d...) adds a probe on 0x140bbe5e0 logging each new (object, id) pair (`UNIV lookup`).
