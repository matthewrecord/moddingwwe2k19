# Match-up screens (match cards): how they bind to an arena, and how to add one to an arena that has none
Written 2026-11-14 23:5x from the arena work on `claude/slots50-gfx` plus a fresh look at the game files. Sections are
marked **[verified]** (tested in game or read from files) or **[hypothesis]** (not yet tested). Read the warnings at the end first.

## 1. How the game picks a card [verified unless marked]
- Card files: `pac\menu\win\Assets\wwe19_anime\match_up\ltag_<NNN>_<label>_win.pac`. 143 exist: 000–162 (gaps), 400–407,
  `10024_wideuse`, `30001`–`30022` (Create-a-Show set).
- **misc01_start row, field `select2` (u16 at offset 6) chooses the card AND the transition group** (`pac\mov\transition\<NNNNNN>.pac`,
  `transition_replay` likewise). Evidence: WM32 GFX creator README ("change the select num from 24 to 115"), stock rows
  (modded 96 → 1 = Raw card, 163 → 3 = Dynamite). Tool: `tables.misc01_get/set` (field `select2`).
- **select2 = 24 means "no card of its own": the generic `ltag_10024_wideuse_win.pac`** (exe string `MatchUp_wideuse_2K19`) and
  transition `000024`. 90 of 213 misc01 rows use 24. **Never edit 10024 or transition 000024: 90 arenas share them.**
- The exe resolves cards by hashed name (`/LTAG/%08x`), not by the file label. The label after the number is cosmetic.
  Many slot cards (115, 125, 139, 141, 160 ...) are byte-clones of 10024 (same header stamp `7f82fa22` at 0x10) that differ only
  in the 8-byte directory hash at 0x800 (+0x814). Our re-stamp rule (used for every HSPC re-slot): copy 0x10–0x14, 0x800–0x808,
  0x814–0x81c and each SHDC id (+16) from the target slot's own file (`reslot_stage.restamp`).
- A file the def doesn't list is invisible: every new path needs a `chunk0.def` line (install_native.py adds them), then a chunk rebuild.
- Current select2 examples: 5 → 24 (Tokyo Dome, generic card), 140 → 11 (shares group 11), 96/115/125/141 → own number.

## 2. Anatomy of a card (HSPC > SHDC, 8 files in the stock 4.69 MB layout) [verified]
| file | content | notes |
| --- | --- | --- |
| 0 | header (OODL) | leave |
| 1 | **background movie** (Bink BIKi/KB2j; stock = OODL-compressed) | replace with a ZLIB-wrapped Bink: `b'ZLIB'+pack('<III',0x1230,len(z),len(raw))+z`. No Bink encoder exists here: use an existing movie (the arena's own transition or, better, its longer `ar_mini` loop; check it isn't a still: median Bink frame size). Playback speed = the Bink header fps (edited for the AEW cards). |
| 2 | OODL | leave |
| 3 | **foreground strip**: DDS 1024x256 BC7 (ZLIB) | build from the mod's FG art: crop to the art (alpha bbox, or by hand if there's an opaque band), pad to 6.7:1 centred, resize, BC7 (`etcpak.compress_bc7`), reuse the 148-byte DDS header of `cards\fg_130.zlib`. |
| 4 | FTPK font | swap only to change the name font (Raw '20 uses the 96 card's file 4) |
| 5, 6 | OODL textures | leave |
| 7 | ATB0 layout (wrestler names) | `cards\layout_noname.zlib` hides the names (scale 0); the same layout bytes across 4.69 MB cards. Raw-style text: see Arena_inventory "Raw card names". |
- Decode OODL entries: `pip install --break-system-packages pyooz`; `raw,comp = unpack('<II', b, 0x10)`; `ooz.decompress(b[0x18:], raw)`.
- Container-side builder: `tools/arena/cardb3.py <template card> <movie.bik> <fg image> <fg_130.zlib> <out>` (pip: etcpak texture2ddecoder pyooz).
  Laptop-side variants: `cards_b2.py` / `cards_b2fix.py` (replace files 1/3/7 in a slot's own card).
- A mod's own card (e.g. a 9-file WM layout or 205 Live layout) **cannot be dropped in whole**: its layout's texture names are
  tied to the slot it was made for; the whole-card swap on 158 gave no card at all. Take only its movie and foreground art.

## 3. Recipes
### A. Slot already has its own card (select2 = its own number, `ltag_<slot>` exists) [verified: 107–160 in batches 1–3]
Replace files 1 and 3 (and 7 for no names) inside the slot's own file. Back it up first. Nothing else changes.

### B. Slot has no card of its own (select2 = 24 or another slot's number)
Ranked by risk. Whatever you choose, **the transition group moves with select2**, so the target number must have
`transition\<6-digit>.pac` (and ideally `transition_replay`) or the game will look for a video that isn't there.
1. **Use an existing card number whose transition video exists and which no kept arena uses** [hypothesis, most promising]:
   pick N where `ltag_<N>` exists, `pac\mov\transition\<N>` exists, and no other misc01 row has select2 = N (or only rows of
   discarded/unwanted arenas). Rebuild that card's files 1/3/7 (recipe A on `ltag_<N>`), set the arena's select2 = N. The
   transition N will also show, so replace transition N with the arena's own transition (re-slot into N's container).
   Most natural N = the slot's own number if both `ltag_<slot>` and `transition\<slot>` exist and no kept arena uses it.
2. **Point select2 at another arena's existing card** [verified pattern in stock data, untested for our arenas]: the arena then
   shares that card and transition (fine for a look-alike, e.g. a second NXT arena sharing NXT's).
3. **Brand-new card number** [untested, highest risk]: a new `ltag_<N>` needs the hashed `/LTAG/%08x` name to resolve and a
   matching def entry; nobody has worked out the hash. Don't start here.

**What went wrong last time (Tokyo Dome, slot 5, 2026-11-13):** card 100 (Starrcade '83, used by no row) was rebuilt and re-stamped
as card 100, and slot 5's select2 was set to 100. **Tokyo froze on load.** Both were reverted (card100 419cd93e, select2 24) and
Tokyo has used the generic card since. The cause was never isolated, but **there is no `pac\mov\transition\000100.pac` and no
`transition_replay\000100.pac`**, so the likeliest cause is the missing transition for group 100, not the card. If you retry
card 100 for a slot, first install a transition (and transition_replay) at 000100 (re-slot the arena's own, `reslot_stage.py`), add the
def lines, and test only that one change.

## 4. Checklist for one arena
1. Read the slot's misc01 row: `select2`. Is it its own number? Does `ltag_<select2>` exist? Do `transition/transition_replay <select2>` exist?
2. Find every other misc01 row with the same select2 (all of them will change if you edit that card).
3. Back up the card, the transition files and `misc01_start.pac` (installer backups or `_arena_work\backup_<task>`).
4. Build the card (files 1/3/7) from the arena's own art; check the foreground preview image before installing.
5. Set select2 if it changes; add def lines for any new path; rebuild chunk0.
6. Ask Matthew to test that slot (card + entrance transition), then record the result in `writeup/Arena_inventory.md`, and rebuild
   the Arena Pack (`build_pkg.py`, `copy_pkg.py`, MD5 verify; see handoff 019).

## 5. Warnings (2026-11-14 late)
- **Another session is working on this now:** `ltag_140_survivor_2017_win.pac` was written at 2026-11-15 04:39 UTC (stamp
  `8910fc22`, unlike the `7f82fa22` clones) and is **not in chunk0.def yet**; `misc01_start.pac` was changed at 03:46 UTC. Slot 140
  currently has select2 = 11. Coordinate before touching cards, 140 or misc01 (`notes/parallel_work.md`).
- Work folders now live outside the game folder (`common\WWE2K19_arena_work\`): a chunk rebuild indexes everything inside the game folder.
- Wrong history in older notes: Arena_inventory (2026-11-13) says "slot 140 has no match card file". That was true then; see above.

## 6. In-game result that contradicts section 1 (2026-11-15, claude/ss26-arena, Matthew tested)
- Slot 140 (Survivor Series '26, copy of SS '17) set to **select2 = 11** (misc01 only, no other change, def/chunk unchanged).
  Result: **the SS '17 transition played, but the match-up screen was the generic card**, not `ltag_011_survivor_2017`.
  So select2 drives the transition, but in this case **not the card**. Either the card is chosen by something else (slot/select1,
  or a per-row field not yet found), or the card lookup needs a chunk rebuild / another field. Treat "select2 picks the card" as
  **[hypothesis]** until a test shows a card change from select2 alone.
- Registry test (also negative): renaming the list record `wwe19_anime\match_up\011_survivor_2017` → `140_survivor_2017` in
  `pac\menu\win\ltst_lt_wwe19_win.pac` (+ a copy `ltag_140_survivor_2017_win.pac`, def line) still gave the generic card.
  Restored (registry dc977a28, def line removed). The stray `ltag_140_survivor_2017_win.pac` (stamp 8910fc22, copy of 011) was
  **this test, not another session**; it is unindexed and can be ignored or deleted. Details: handoff 020.
