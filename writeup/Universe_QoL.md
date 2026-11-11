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
