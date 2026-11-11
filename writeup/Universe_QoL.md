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
- 2026-11-10 21:21 Correction (Matthew): the broken matches were **Keith Lee (champion) vs Angel Garza (slot 512)**,
  title on the line (Raw and SmackDown). Ace Austin was a champion but never wrestled. Works: Keith Lee vs HHH (title),
  and the non-title control. Open split: Angel Garza vs a vanilla wrestler (title / non-title) -> is it Angel's slot,
  or two overflow wrestlers in one title match?
- 2026-11-10 21:27 test3b probe: 0x140bbe5e0 called at 200 s with obj 0x76c24d20 for ids 689-756 only (no overflow
  ids); reading obj later gave all zeros (temporary object, freed). So this lookup is not the roster table; it was a
  wrong lead. Matthew's match in progress (Angel Garza vs a vanilla wrestler, title): entrances normal.
- 2026-11-10 21:30 **Angel Garza vs vanilla wrestler, title match: normal** (entrances + match). No exceptions in the
  log. So no single overflow wrestler breaks a title match; the only broken setup so far is **two overflow wrestlers
  in the same title match** (Keith Lee vs Angel Garza, twice). To confirm with a different pair: Keith Lee vs Ace
  Austin (title), with a log mark before/after so the new TRACE callers of that match can be isolated.
- 2026-11-10 21:38 **Keith Lee vs Ace Austin, title match: normal** (entrances + match; no new TRACE/exception lines
  after log line 3086). So "two overflow wrestlers in a title match" is NOT the trigger either. Only failing case:
  Keith Lee vs Angel Garza (title), on show 1, twice. Remaining candidates: that exact pairing/title; state of the
  fresh Universe on show 1 (e.g. phantom managers attached at the time); something since fixed by a reload. Next:
  rerun Keith Lee vs Angel Garza (title) now.
- 2026-11-10 21:44 **Keith Lee vs Angel Garza (title) rerun: normal**, entrances fine; the three phantom CAW managers
  are no longer shown. Only new log line: TRACE pofo-by-id from 0x1404c748a (harmless getter caller).
  **Conclusion:** the show-1 breakage (skipped entrances, falling/glitching) was tied to the fresh Universe state,
  most likely the phantom managers that every overflow wrestler got at Universe creation (removing them per match
  was not enough; after the managers were cleared and the save reloaded, all title matches work).
  Status: overflow wrestlers survive save/reload and work in title and non-title matches **once the phantom managers
  are gone**. Remaining bug: Universe creation assigns them 3 copies of a CAW as managers. Next: find where Universe
  creation picks default managers (per-superstar default relationship data, likely read by profile index / 509-wide
  table) and give overflow slots "none"; verify on a fresh test Universe. Until fixed: after creating a Universe,
  remove those managers in the roster/relationship menu before booking.
- 2026-11-10 22:00 **SAVE DECODED.** The real obfuscation is XOR with a **128-byte key** indexed by file offset mod 128
  (the 4-byte key was only its first bytes); key in `tools/universe/savedecode.py`. Decoded file: magic `VCGD`, chunk
  directory of 12-byte tags + u32 size; BODY chunks = `ZLIB` + csize/usize + zlib. **Universe = `UNVS*` chunks** near
  the end of the file (`UNVSHEAD0000/0001`, `UNVSBIGH0000/0001`, `UNVSBODY0000` (0x30 bytes), `UNVSBODY0001`
  (0x777b zlib -> **3,304,944 bytes**)). The Universe blob holds show/PPV names (SMACKDOWN LIVE, AEW DYNAMITE, NXT
  TAKEOVER..., WRESTLEMANIA, ...), superstar/team names (incl. "Test Wrestler 3", "THE DELETERS OF WORLDS") and ids as
  u16. Overflow ids 938/939/940 occur (u16 at 0x3abe2.., 0x193e14.., 0x1955ac..); 937/941/942 do not. Save diffs
  show 1 -> 2 -> 3 change bytes only in the UNVS area (plus header/time and a small block at 0x29b6f40) and the file
  grows each show -> results appear to be appended. Next: map the Universe blob (rosters, titles, managers, match
  history) by diffing UNVSBODY0001 across the three backed-up saves.
- 2026-11-10 22:10 **The Universe save keeps a MATCH LOG** (no in-game screen for it). In UNVSBODY0001 at ~0x19a0f0:
  records of **0x28 bytes**: +0 u32 (varies: 0x275, 0x2715, 0x28d, 0x187, 0x31f, 0xb9: match type/stipulation or
  rating?), +4 u32 small increasing (0x71, 0x72, 0x76: show/date index), +8 5 x u16 participant ids (0x400 = empty;
  0x38/0x35 + 0xff entries look like team or title refs), +0x12 5 x u16 (copy of the first group in all records so far:
  likely winners or side B), +0x1C u32 (0, 2, 0xa), +0x20 u8 1, u8 x2 (0x1f/0x03), pad. Empty slot = ff..ff pattern.
  Show-1 save had none of these filled; the current save (after shows with Keith Lee 939 / Angel Garza 940 /
  Ace Austin 938 / HHH ...) has 7. Overflow ids appear normally (u16 0x3aa-0x3ac). Also u16 id lists with 0x400 = empty
  at ~0x3ab80 (rosters/brand lists). => record keeping can be read straight from the save; a tracker that copies this
  log after every save never loses history. Next: decode each field (type, show, winner, title) against known
  matches, then the champion/title-history table and the manager table.
- 2026-11-10 22:20 Match-log record layout, refined (0x28 bytes, start 4 bytes earlier than first guessed):
  +0 u32 **kind** (10005 = promo segment; 629/653/391/799/185 = match kinds, probably match type id), +4 u32 **day**
  (113, 114, 118, 119: Universe calendar day), +8 u16 0, +0xA 5 x u16 **participants** (0x400 empty), +0x14 5 x u16
  second group (identical to participants so far; winner order / sides still to check), +0x1E..: flags (0x400/0xff
  pattern), u32 (0, 1, 2, 10: likely match rating/quality or show slot). Promo records: participant + promo id
  (56, 53, 150) + 0xff padding. Overflow ids map: **937 Alex Shelley (slot 510), 938 Keith Lee, 939 Angel Garza,
  940 Ace Austin, 941 Darby Allin, 942 Moose** (slots 510-515 = index 509-514; the 40-byte source ids in the log).
  Matthew's show tonight (to decode winner/title fields once saved): Angel Garza def. Keith Lee (custom "AEW US
  Championship"); Uhaa Nation & Kenny King def. Tyler Breeze (pinned) & Jon Curtis (Fandango) & Alexa Bliss & Bayley?
  [chat: "Uhaa Nation and Kenny King beat Tyler Breeze who took the pin and Jon y Curtis (Fandango) barely [= Bayley]
  beat Alexa Bliss" -> read as: Uhaa Nation & Kenny King def. Tyler Breeze (pinned) & ...; Jon Curtis (Fandango) &
  Bayley def. Alexa Bliss - to confirm against the log]; Dash Wilder (pin) & Scott Dawson def. Hikuleo (pinned) & Bo Dallas; Seth Rollins vs KENOH promo
  (KENOH won); Brock Lesnar (with Marq Quen as manager although the image showed Paul Heyman: a vanilla wrestler with a wrong manager
  -> manager mix-up is not only an overflow-slot problem) def. Triple H (with Kylie
  Rae); Roman Reigns def. John Cena. Latest SAVEDATA (md5 d970fe63...) does not contain this show yet.
- 2026-11-10 22:30 Save after tonight's show (21:53, md5 d970fe63..., backup `saves\20261110_2155_after_show3`).
  Partial id names from notes/characters/cct_superstar_slots_with_notes.tsv: 625 Uhaa Nation (Apollo Crews slot),
  371 Kenny King (Titus slot), 608 KENOH (Elias slot), 369 Seth Rollins, 708 Cedric Alexander, 883 Mark Davis.
  * 0x19a0ec log (0x28 records): day 119 holds `kind 653: 369 vs 608` = **Seth Rollins vs KENOH promo battle**
    (Matthew: KENOH won) and `kind 10005` promo by 939. So it is a segment log, but only ~9 entries: possibly a
    rolling/recent list or only some segment kinds. Field +0x1E u16 (0,2,10,1) still unknown.
  * Second structure at 0x31aee8: **u16 pairs** (939,576) (939,708) (753,715) **(939,938)** (940,883) (623,612)
    (112,630) (610,610) (324,324) (610,625) **(625,371)** (371,622) (608,139): contains tonight's Angel Garza (939)
    over Keith Lee (938) and Uhaa Nation (625) / Kenny King (371). Another list at 0x31b57c with (938,939) reversed.
    Candidates: win/loss pairs, rivalry/feud links, or match-card pairings. 0x31a8b8..: u16 lists of ids per
    show/brand (rosters).
  Needed next: a complete id -> name table (game string table / SuperString, name string = 13000-range per id?) so
  every id in these structures can be named; then field-by-field decode against tonight's card.
- 2026-11-10 22:40 **id -> name table** from CCT's `A - CCT\data.xml` (original slots: slotNumber, slotId, name) +
  `replaced_data.xml` (current names): `tools/universe/idnames.py` (613 ids + overflow 937-942). Pair list at 0x31aee8
  named: Angel Garza>Finn Balor, Angel Garza>Cedric Alexander, Bianca Belair>Lars Sullivan, **Angel Garza>Keith Lee**,
  Ace Austin>Judgment Day(883), Carmella>Charlotte, Jeff Hardy>Shinsuke Nakamura, AJ Styles=AJ Styles,
  Daniel Bryan=Daniel Bryan, AJ Styles>Uhaa Nation, Uhaa Nation>Kenny King, Kenny King>Bayley, KENOH>John Cena.
  Self-pairs and pairs that never wrestled tonight (KENOH-Cena, Kenny King-Bayley) => **not results**: this looks
  like relationship/rivalry or card-generation data. Segment log: 629 Becky Lynch vs Carmella, 653 Kairi Sane vs Bianca
  Belair, 391 Ace Austin vs Keith Lee, 799 AVAILABLE GFX(214) & ... vs Karl Anderson & Marufuji/Dominik(400/401),
  185 Jeff Hardy vs Shinsuke Nakamura, 653 Seth Rollins vs KENOH. These are earlier (AI/sim) shows + tonight's promo;
  tonight's played matches (Garza-Lee title etc.) are NOT in it -> the real results store is still to be found
  (next: diff show-3 save against show-2 at the u16 level for tonight's participant ids).
- 2026-11-10 22:55 **MATCH RESULTS DECODED** (`tools/universe/matches.py`, verified against Matthew's card). Output for
  the save after tonight's show:
  ```
  day 119 non-title kind 5: Uhaa Nation won (pin), Kenny King won, Dana Brooke (manager) | Tyler Breeze lost (pinned), Dirty Johnny Curtis lost
  day 119 non-title kind 0: Seth Rollins lost (pinned) | KENOH won (pin)
  day 119 non-title kind 2: Brock Lesnar won (pin), slot 374 (manager) | Triple H lost (pinned), Kay Lee Ray (manager)
  day 119 non-title kind 0: Roman Reigns won (pin) | John Cena lost (pinned)
  title 150 kind 0: Keith Lee lost (pinned) | Angel Garza won (pin)        (150 = AEW US Championship)
  non-title kind 1: Alexa Bliss lost (pinned), Mickie James (manager) | Bayley won (pin)
  non-title kind 3: Hikuleo lost (pinned), Bo Dallas (425) lost | Dash Wilder (615) won (pin), Scott Dawson (618) won
  ```
  Entry format, result codes, manager role and title byte: see the docstring. Seth vs KENOH is stored as a match
  (promo battle). Key fact for record keeping: **the save only holds the current/latest show's cards** (the show-1
  and show-2 saves have none left), so history must be captured after every show -> tracker v1 = run
  savedecode + matches after each save and append to a permanent log. Manager notes: Brock's manager is slot 374
  (Paul Heyman's original slot, now "AVAILABLE GFX" in CCT); Matthew saw "Marq Quen" on screen. **Marq Quen is the
  name in CAW slot id 0** (CCT data: id 0 = CAW "Marq Quen"), and the overflow wrestlers' "three copies of one CAW"
  managers fit a manager field holding **0 instead of 0x400 (none)**: strong lead for the phantom-manager fix.
- 2026-11-10 23:05 **Tracker v1 delivered** (`tools/universe/tracker.py`; uses savedecode.py + matches.py).
  Output folder on the PC: `D:\Documents\WWE2K19 Universe Tracker\`: `history.csv` (one row per participant per
  match, permanent; person resolved at capture time), `records.csv` (W, L, pins scored, pinned, title matches,
  streak, last-5 form per person), `titles.csv` (reigns: champion, won from, defenses, lost to), `log.md` (readable
  results per show), `titles.tsv` (editable title names; 150 = AEW US Championship), optional `aliases.tsv`
  (merge variants, e.g. "Triple H '13<TAB>Triple H"). Person names come from Matthew's Wrestlers sheet ('Character
  Slot' number = game id; rows with Gen M/F only), then CCT's current name; freed "AVAILABLE GFX" slots fall back to
  the original name (Dash Wilder, Scott Dawson, Bo Dallas, Paul Heyman resolved correctly). Re-running on the same
  save adds nothing (match_key dedupe). Capture 1 = tonight's 7 matches. `Update tracker.cmd` in that folder runs
  it with Windows Python (needs python + openpyxl on Windows, unverified) — or the agent runs it via the shell.
  Known limits v1: Universe day is 0 for some cards (in-progress region); show name/brand not yet decoded; match
  type ("kind") not named; tag teams listed as their members.
- 2026-11-10 23:15 **Automatic capture** (Matthew asked for automatic): DLL test4 (md5 5e10d6a4...) installed, with
  `universe_capture.ini` -> every Universe save drops `unvs_<date_time>.bin` (~30 KB) into
  `D:\Documents\WWE2K19 Universe Tracker\captures\` while the game runs (also once at game start). Capture never misses
  a show as long as the game runs ~10 s after the save. Turning captures into the reports: `tracker.py --archive`
  (processed.txt remembers what was read; matches dedupe). That step runs automatically only if line 3 of the ini
  holds a command and Windows has Python + openpyxl (unknown); otherwise the agent runs it on request, or Matthew
  double-clicks `Update tracker.cmd`. Tested: synthetic captures of two saves -> 7 matches, rerun adds nothing.
- 2026-11-10 23:20 Matthew installed Python (Store, `C:\Users\Acer\AppData\Local\Python\pythoncore-3.15-64\python.exe`)
  + openpyxl. `universe_capture.ini` line 3 now runs `tracker_auto.cmd` (hidden; output to `last_run.txt`) after
  every capture -> **fully automatic**. `Update tracker.cmd` = same with a visible window, for manual runs.
- 2026-11-10 23:35 Tracker v1.1 (Matthew: one row per match, drop md5/match_key, nicer standings):
  `history.csv` = **one row per match** (show, captured, day, title, winners, losers, pinfall_by, pinned, managers);
  per-participant store moved to `_data\participants.csv` (dedupe keys live there; v1 file copied to
  `_data\history_v1.csv`). New **`standings.html`** (self-contained, dark theme): champions cards, standings table
  (W, L, win %, pins, pinned, title matches, streak, last-5 form chips), title history, results by show (newest
  first). If a report is open in Excel, the tracker writes `<name> (new).csv` instead of failing. First automatic
  run (22:17, show 2 simmed: Jeff Hardy, Randy Orton, Mistico, Daniel Bryan, Carmella, Andrade, AJ Styles winners)
  worked: 14 matches in history.
  Show names: the Universe blob holds the show list (SMACKDOWN LIVE, AEW DYNAMITE, PPV names) and cards sit in
  separate blocks (0x58500, 0x66400, 0x6ae00, 0x6f880, 0x195xxx) -> mapping block -> show is the next decode item.
- 2026-11-10 23:55 Tracker v1.2 (Matthew: filter non-roster talent; seasons with offseason; all-time separate):
  * Standings grouped by brand (settings.tsv `roster_brands`, default WWE,AEW,NXT from the Wrestlers sheet's Brand
    column); everyone else under a collapsed "Not on a roster". `roster.tsv` (person<TAB>brand|none) overrides.
    Caveat: the sheet's Brand column is out of date vs the game (e.g. Brock Lesnar "Inactive" but on a show), so the
    real fix is reading rosters from the save. Located: id lists (0x400 = empty) at UNVSBODY0001 0x38bee-0x3abf0
    (show/brand roster or rivalry lists, not yet decoded).
  * Seasons: new season when the Universe day jumps back > season_reset_drop (100) days; offseason = days
    offseason_first_day..last_day (121-212 = May-July if day 1 = 1 Jan; unconfirmed); `count_offseason no` keeps
    offseason dummy shows out of all standings. Pages: current-season standings + all-time table (records_all_time.csv).
- 2026-11-10 22:29 (Matthew) The sheet/game mismatch is because tonight's Universe is a throwaway test; the
  Wrestlers sheet's Brand column reflects his real roster. => Sheet-based brand filter is valid for real use;
  save-based roster decoding drops to a nice-to-have (useful for test Universes / catching sheet drift).
- 2026-11-10 22:33 **Universe calendar decoded** (Matthew's calendar screenshot): 12 months x 4 weeks x 7 days, day 0 =
  January week 1 Monday. Day 119 = May wk 2 Mon (RAW), day 120 = May wk 2 Tue (SmackDown Live, current). May = 112-139,
  offseason May-July = 112-195 (new default). Show names from weekday (settings.tsv show_mon..show_sun: RAW,
  SmackDown Live, NXT, AEW Dynamite, Sun = PPV). history.csv gains show, date ("May wk 2 Mon"), season, offseason.
  Tonight's test shows are correctly flagged OFFSEASON, so the standings tables are empty by design
  (count_offseason no); they still appear in results/history.
- 2026-11-10 22:50 Tracker v1.3 (Matthew: selectable roster filter; tabs; PPV results; title histories with defenses
  like his "History and Ideas" sheet, cols Z..: reign line [date, champion, event] + indented defenses):
  standings.html tabs = Standings (champion cards + table) | By show (sub-tab per weekly show: standings + results) |
  Pay-per-views (Sunday shows) | Title history (per title: reign rows, indented defense rows: date, opponent, show)
  | All results | All-time. "Roster only" + per-brand checkboxes filter every standings table (remembered between
  visits). titles.csv now in his sheet layout (reign row, then "   vs. opponent" defense rows). Verified in headless
  Chrome (no JS errors; screenshots checked).
  Idea from his sheets for later: per-title contender rankings (Main Roster Stats: C + ranked contenders with W, L,
  PPV W/L, pct).
- 2026-11-10 22:45 (Matthew) New Universes start in **May**. Seasons now run May..April: new season when the day enters
  May from Jan-Apr, or jumps back within May-Dec (a new Universe). January no longer splits a season.
  Tested: days [112,200,330,5,100,112,130,300,112] -> seasons [1,1,1,1,1,2,2,2,3].
## Remaining plan (triage order, 2026-11-10 22:45)
1. Phantom-manager fix (overflow wrestlers get 3x CAW slot 0 "Marq Quen"; also wrong manager names for vanilla).
2. PPV names per Sunday (show list in the save) + match-type names (kind byte).
3. Tag-team import (custom teams into Universe; source: Matthew's Wrestlers/team list).
4. Title contender rankings (like his Main Roster Stats sheet), MOTN/star ratings if the save holds them.
5. Save-based rosters (catch sheet drift); in-game display of records (long term).
- 2026-11-10 22:50 Phantom managers, status: Matthew cannot reproduce them in the current Universe. Save evidence:
  overflow ids 937/941/942 never appear in the Universe blob (show-1 or show-3 save) and no manager pairing for
  Brock(343)/Heyman(374) exists in the blob -> manager assignments are not Universe-blob data; they likely come from
  the per-superstar profile copies (CCT data.xml: universe1/2/3 superstar pofo arrays = the 509-wide per-save copies,
  getter 0x1409655a0 returns null for index >= 509) and/or defaults applied at Universe creation. Hypothesis: at
  creation the game reads manager defaults for every roster entry; for overflow slots it reads outside the 509-wide
  copy (or a zeroed field) -> id 0 = CAW slot 0 "Marq Quen", and the choice is then cleared by the reload/edit.
  2K19 has 3 Universe save slots (universe1/2/3 in CCT data.xml), so a reproduction can use a spare slot without
  touching the current Universe. Plan: (a) static: find the manager fields in the pofo (compare vanilla pofos that
  have managers) and the code that copies them on Universe creation; (b) Matthew creates a fresh Universe in a spare
  slot with the TRACE/UNIV probes on; (c) patch: give overflow slots "none" (0x400) or extend the copy.
- 2026-11-10 23:05 Phantom managers, static pass 1:
  * Not in the pofo. Compared all 301 Data Editor template pofos (484 bytes) with the six overflow pofos: the only
    u16 fields where templates are mostly 0x400 (none) are 0x60-0x74 = an 11-entry **relationship list** (e.g. Alexa
    Bliss -> Becky 611, 355, 613, Bayley 622; Angel Garza clone -> Zelina Vega 762, Andrade 687, 123, 805). Overflow
    pofos hold 0x400 or real ids there, never 0. So the pofo does not carry a "manager = 0".
  * Not as a pair in the Universe blob (no Brock 343 <-> Heyman 374 link anywhere).
  * Candidate: UNVSBODY0001 ~0x3c280+ holds many u16 0 ("Marq Quen" when read as ids) in a regular pattern with
    "170"/0x400 fields: possibly per-superstar Universe records where 0 is a default that the game treats as a real
    id when the record is missing/out of range. Not confirmed.
  Conclusion: static search is slow without a reproduction; next step is a controlled repro (fresh Universe in a
  spare slot) with save captures before/after creation + DLL memory reads, then diff for the three id-0 fields.
- 2026-11-10 22:54 Matthew created a new Universe (save 03:53:50 UTC, md5 b6b898da..., backup
  `saves\20261110_2254_new_universe`). It went to a **second Universe slot: UNVSBODY0002** (+ UNVSBIGH0002,
  UNVSHEAD0002); slot 1 (UNVSBODY0001) is the earlier test Universe, unchanged. The new Universe blob contains
  **none of the overflow ids 937-942** -> they are not on any roster at creation; any Universe data for them is created
  on demand (or looked up and missed). Waiting on Matthew: do the Test Wrestlers show phantom managers here?
  **Tracker impact:** DLL capture + tracker read only UNVSBODY0001 -> a Universe in slot 2/3 is not tracked yet. Fix
  planned: capture every UNVSBODY000N, tracker setting `universe_slot`.
- 2026-11-10 22:58 **Not reproducible in a fresh Universe** (slot 2): no phantom managers, Keith Lee vs Angel Garza
  title match normal. Best explanation: the slot-1 test Universe carried stale state. It was the earlier "throwaway"
  Universe, created before Test Wrestlers 2-6 were swapped (19:40: slots 511/515 changed from Rhea Ripley/Toni Storm
  to Keith Lee/Moose with the same ids), so its per-superstar data no longer matched the slot contents.
  Status: closed as not reproducible; no fix shipped. Rule for Matthew: after changing who is in an overflow slot,
  start a new Universe (or check that wrestler's managers). Reopen if it shows up in a Universe created after the
  slot contents were final.
- 2026-11-10 23:15 **Multiple Universe slots.** Tracker now writes one folder per save slot
  (`Universe 1\`, `Universe 2\`, ... each with its own standings.html, history.csv, settings.tsv, titles.tsv,
  roster.tsv); slot 1 inherited the earlier history; old root files moved to `_old\root_v1\`. The tracker reads every
  UNVSBODY000N from captures and (new) straight from SAVEDATA (`--save` added to tracker_auto.cmd / Update tracker.cmd),
  so all slots are tracked even before the new DLL is in. DLL test5 (md5 fa8f1d76...) captures all slots into one
  file; staged at `_moddingwwe2k19_builds\dinput8.dll.test5`, to install when the game is closed.
- 2026-11-10 23:20 DLL test5 INSTALLED (fa8f1d76...; backup `_moddingwwe2k19_builds\dinput8.dll.test4_installed_bak`).
  Universe 2 tracked (2 matches so far). PPV names: the save's show table (UNVSBODY000N 0x3c618, records 0x2D8 bytes,
  names only for renamed shows: SMACKDOWN LIVE, AEW DYNAMITE, NXT TAKEOVER..., ROYAL RUMBLE, WRESTLEMANIA, ...) does
  not expose month/week in an obvious field, and a 336-day calendar array was not found (pattern search). Shipped
  instead: settings.tsv `ppv_<Month>_<week>` names (Backlash = May wk 1 from Matthew's calendar); PPV tab = every
  Sunday show. Decoding the schedule from the save remains open. Match type ("kind" byte) still unnamed.
- 2026-11-10 23:30 **PPV CALENDAR DECODED** (Matthew added AEW Revolution on May week 3; diff of slot-2 blob):
  48 bytes at UNVSBODY000N **0x19C038**, one per week from January week 1 (index = month*4 + week-1), value =
  show-record index + 1 (0xFF none). Show records at **0x3C618 + i*0x2D8**, custom name at +0. Revolution = record 23
  -> byte 0x18 at index 18 (May wk 3). Full slot-2 calendar: Jan3 NXT TakeOver Philadelphia, Jan4 Royal Rumble,
  Feb4 Elimination Chamber, Mar2 Full Gear, Apr1 NXT TakeOver New Orleans, Apr2 WrestleMania, May1 AEW Revolution
  (record 21; shown with the Backlash logo = renamed show), May3 AEW Revolution (new), Jun1 Extreme Rules, Jul1 NXT
  TakeOver Chicago, Jul2 Money in the Bank, Aug2 NXT TakeOver Brooklyn III, Aug4 SummerSlam, Sep4 Hell in a Cell,
  Oct4 TLC, Nov4 Survivor Series, Dec4 Clash of Champions. Shows with built-in names (RAW, NXT, Backlash...) store no
  text -> weekday names / settings override. Tracker writes `_data\ppv_calendar.tsv` per Universe from the newest
  capture; settings `ppv_` lines override.
  Also: matches.py now requires a winner and a loser among >= 2 wrestlers (two false records in slot 2 removed;
  Universe 2 rebuilt from captures: 6 matches).
- 2026-11-10 23:14 (Matthew) May wk 1 PPV: the Backlash arena was replaced by the AEW Revolution arena, so the show
  keeps legacy Backlash bits (logo) with the Revolution name. **Future idea (Matthew):** redo the game install from
  scratch, using the project's "add new slots instead of replacing" methods (music slots done, character slots done;
  arenas/shows not yet investigated) to avoid replacements like this. Logged for a later thread; not started.
- 2026-11-10 23:45 **Tag-team import, survey 1.**
  * Save chunk inventory (non-asset): MAIN (14.2 MB raw: main game data, like the in-memory main block), TMMA/TMU0/TMU1
    (1 MB each: an embedded **SQLite database** "RecentMatches" with 155 integer columns; MA + two Universe slots;
    slot-1 db had 1 row: 1,0,58,0,24577024,7,0,0,150,255,...), TRMA/TRU0/TRU1 and TSMA/TSU0/TSU1 (zeroed in this save),
    LOGO, UNVS (Universe blobs, one per slot), plus ~470 creation-asset chunks (CAAS/CASS/CCAC...).
  * **Universe team table** in each UNVSBODY000N: records of **0x1B8 bytes (= CCT teamLength 440)**, name (uppercase,
    NUL-terminated) at the record's +0x54-ish position; first 27 records from 0x31A844 in slot 2: (14 empty), THE
    DELETERS OF WORLDS, THE B-TEAM, THE REVIVAL, HEATH SLATER & RHYNO, TITUS WORLDWIDE, THE ASCENSION, BREEZANGO,
    THE RIOTT SQUAD, KEVIN OWENS & SAMI ZAYN, THE AUTHORS OF PAIN, THE BAR, GALLOWS & ANDERSON, THE BLUDGEON BROTHERS.
    Member ids (u16 pair) sit 0x100 bytes before each name (e.g. THE REVIVAL -> 615 Dash Wilder, 618 Scott Dawson).
  * Main (non-Universe) team table: in MAINBODY around 0x3C000 (team names found there, e.g. REVIVAL, DIY); exact
    record base/stride not pinned yet (first stride guess failed). CCT reads it live at 0x14287C860 (data.xml).
  * Route options: (a) offline save writer (decode -> edit UNVS team records -> zlib -> XOR -> fix chunk sizes; HEAD
    chunks carry 4-byte hashes that may need recomputing -> risk); (b) **in-game via the DLL**: copy teams into the
    live Universe team table while the Universe is loaded and let the game save it itself (no save-format risk).
    Preferred: (b), with (a) as fallback. Next: pin the main team record layout (CCT data.xml offsets + live memory
    read with slots_mem.request), then Universe table base/count, then a dry-run diff tool.
- 2026-11-10 23:55 **Team tables pinned** (live read of CCT's main team table 0x14287C860, game open):
  * Record = **0x1B8 bytes**: +0x00 5 x u16 member ids (0x400 = empty), +0x0E u8 member count (2/3/4), +0x10 u16
    team value (logo/graphic id; same value in main and Universe copies, e.g. THE REVIVAL 0x079E), +0x100 name
    (NUL-terminated, 0x58 bytes), +0x158 second name copy. Main table = **200 records** (0-99 custom/edited teams,
    100+ vanilla). Snapshot kept: `_moddingwwe2k19_builds\main_teams_20261110.bin`.
  * **Universe team table** (UNVSBODY0002, slot-2 test Universe): same record layout, records from 0x31A8FC + 13*0x1B8
    (100 slots); only **25 vanilla teams** filled, **75 free**. Dry run: of Matthew's 80 main-table teams,
    **63 are missing** from the Universe (e.g. #DIY, American Wolves, Time Splitters, Bullet Club, The Bloodline,
    The Shield, Judgment Day, The Elite, Imperium, LAX, Golden Lovers, War Raiders, Evolution, ...); 17 exist by name
    (names match, members may differ). 63 fit in the 75 free slots.
  * Next: writer. Preferred = offline save edit on the test Universe first (format fully understood: chunk tag,
    u32 size, "ZLIB", 0x1230, csize, usize, zlib; XOR key), with game closed and Steam Cloud considered; verify in
    game that the teams appear and matches load. Live-memory route stays as alternative.
- 2026-11-11 00:05 (Matthew) Prefer making the game's own import bring teams (like superstars) over brute-force
  writing. Finding: the slot-2 Universe's 25 teams are the **game's default team list**, not copies of the main
  (MyWWE) table: e.g. Universe THE REVIVAL members are 618,615 while main #2 THE REVIVAL is 615,618, and Universe teams
  like THE DELETERS OF WORLDS / THE B-TEAM / HEATH SLATER & RHYNO have no named counterpart in the main table. So
  Universe creation seeds teams from a default source and never reads the main table. Static search for the copy
  code is impractical (0x1B8 appears in ~4,000 instructions). Plan: telemetry watchpoint (tools/telemetry) / DLL
  probe on reads of the main team table and writes to the Universe team table during one Universe creation ->
  locate the seeding routine -> DLL patch to seed from the main table (custom teams 0-99 + defaults), i.e. the game
  does the import itself. Needs one more Universe creation by Matthew (spare slot) with the probe build.
- 2026-11-11 00:40 **Universe team seeding located** (watchpoint run: Matthew created Universe 3 with his MyWWE roster).
  * Live Universe blob of slot 2 was at 0x6dd40010 (heap, 0x380000 region); team table = **blob + 0x31BF54**,
    100 records x 0x1B8 (0xABE0 bytes). The write watch only caught the freed buffer being reused (memset of a new
    0x850 object from 0x14099bd90 <- loop 0x140996b10 over [obj+0x90] records x 0x1B8, count [obj+0x70]: builds
    per-team runtime objects).
  * Static: 16 code sites use 0x31BF54. 0x140fce978 = blob constructor (clears the 100 team records via
    0x1404ca380). 0x140fdf614 = whole-blob copy. **0x140FFF130 = the seeder**: (buffer, size) -> 0x1404cc200 copies
    and validates the buffer, then for each entry i (< 100) 0x1404cc410 converts it into a 0x1B8 record (local) and
    it is stored at Universe blob ([[0x1425e7e20]+0x22F0]+8) + 0x31BF54 + i*0x1B8 (two near-identical loops at
    0x140fff1f0 / 0x140fff3a0). Not called directly: registered as handler of data type **4** in a table at
    0x14259E3A0 {4, 0x141035470, 0, 0x140FFF130} -> the default Universe teams come from a **game data file** handed
    to this loader, not from the MyWWE table.
  * Fix options: (A) generate that data file from the MyWWE team table (data-file edit; pac tools exist from the
    music work) so every new Universe seeds Matthew's teams; (B) DLL hook on 0x140FFF130 that, after the default
    seeding, appends the MyWWE custom teams into the free Universe slots. Next: identify the file (log VFS/file opens
    during Universe creation; trace caller of the type-4 handler) and the entry format of 0x1404cc410.
- 2026-11-11 00:45 Candidate data file for the default Universe teams: **`pac\universe\wunistable.pac`** (38,912 bytes,
  HSPC container) with patch **`wunistable_p10.pac`** (12,288 bytes); neighbours `wunidata.pac` / `wunidata_p30.pac`
  (Universe defaults). "stable" = teams/stables in 2K19's naming. Not yet confirmed: next = unpack with the repo's
  HSPC/BPE tools, match entries against the 25 default teams (members 113/398 = Deleters, 618/615 = Revival), and
  confirm with a VFS open log during Universe creation. The highest patch level present wins (p10 here).
- 2026-11-11 00:55 **Default team file confirmed: `pac\universe\wunistable.pac`.** HSPC container; at 0x1864 an
  uncompressed **LBTS** table ('LBTS', u32 0x110 = entry size, u32 100 = entries, pad), entries of **0x110 bytes**:
  +0x00 5 x u16 members (0x400 empty), +0x0E u8 member count, +0x10 u16 logo/team value (0xFFFF none), +0x18 u16
  (1317..1377; name or record id?), +0x2A.. rating/AI fields. Entries 0-22 + 24 = the 25 Universe default teams in
  Universe order (0 Deleters 113/398 0x956, 1 B-Team 397/425, 2 Revival 618/615 0x79E, 3 Slater & Rhyno, 4 Titus
  Worldwide, ... 22 Undisputed Era, 24 Bella Twins); 23 and 25-99 empty. `wunistable_p10.pac` holds a zlib LBTS with
  100 empty template entries (apparently not what fills Universes; the base file's 25 teams are what appear).
  Names: not found as strings in SuperString string_win.pac file 0; the entry carries no text -> name source TBD.
  Experiment 1 (`tools/universe/stable_test1.py`): #DIY (691+461) in entry 23, copied from THE REVIVAL entry ->
  shows which name the game gives it. Built: wunistable_test1.pac md5 08d20ecc... (original eeab1af0...).
- 2026-11-11 01:10 **Experiment 1 result (Matthew): the #DIY entry appeared in the new Universe as "The Revival"**
  -> the file approach works, and names come from **+0x100 (full) / +0x104 (short) u32 string ids** (copied from
  THE REVIVAL = 16035/16135). Team name strings live in SuperString string_win.pac (HSPC > SHDC > table) at
  16000+n / 16100+n (e.g. #DIY 16051, THE DELETERS OF WORLDS 16060/16084, THE SHIELD 16001).
  **Team import tool `tools/universe/teamimport.py`**: vanilla wunistable.pac (from .orig_teams) + MyWWE team dump ->
  new wunistable.pac + string_win.pac. Run 1 (teamimport_v1): **63 teams added** into entries 23, 25-86; names reuse
  existing strings where the text exists (#DIY 16051, THE SHIELD 16001, AMERICAN ALPHA 16036, WYATT FAMILY 16075,
  WAR RAIDERS 16085, EVOLUTION 16003), 57 new strings 39600-39656. Template per size: 2 -> Revival, 3 -> Titus
  Worldwide, 4 -> Undisputed Era. Notes: TABERNAK DE TEAM uses CAW slots 3/1; TIME SPLITTERS includes overflow id 937
  (Test Wrestler 1). Outputs verified by re-parsing (27,915 strings vs 27,858). Install waits for the game to close.
