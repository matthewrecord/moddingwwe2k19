# Handoff 016: Genesis reconciliation + arena rebuild (2026-11-12)

Branch **claude/slots50-gfx** (not merged; claude/universe-qol is also unmerged). All detail is in **writeup/Arena_inventory.md**
(slot table, binding rules, every install and lesson) and writeup/Rebuild_inventory.md (Genesis module diffs).

## Where things stand
- Matthew rebuilt on a **clean Genesis game**: `D:\SteamLibrary\steamapps\common\WWE 2K19`. The old modded game in
  `...\WWE 2K19 - modded` is ground truth for settings and files. Our DLL is disabled under Genesis.
- Arena binding rule: an arena only goes into a slot Matthew named as unwanted (list in Arena_inventory.md). Back up
  everything. Save each confirmed arena back to its Resources folder as "Installed - slot N <date>" with a README.
- **Confirmed in game:**
  - Dynamite '22 (158);
  - All Out 118, Double or Nothing 119, Dark 117 (Dark's logo fix still unverified);
  - WrestleMania 35 (130), Raw (96; the card font fix is unverified), ROH Death Before Dishonor (138);
  - AEW crowd shirts = crowd 3; AEW rope = rope 7.
- **Batch 2 installed, partly OK:** Rampage 139, Road Rager 149, Grand Slam 159, Revolution 112, Full Gear 133,
  Dynamite '20 107.
- Forbidden Door dropped. SummerSlam '22 added to batch 3 → slot 160.

## Do next (in order)
1. Batch 2 fixes (Arena_inventory.md, "Batch 2 test (23:31)"):
   - (5) **Grand Slam doesn't load**: suspect IBL 88 is missing in the clean game, then ST74, then the entrance.
   - (1) Own apron per AEW arena, not Double or Nothing 137; keep ring mat 18 (ask whether that's what he meant).
   - (2) Rampage nameplate without the header.
   - (3) Hide the names on the Dynamite '20 card.
   - (4) Rampage/Road Rager card movie = the ar_mini/ar_wall loop instead of the transition.
2. Save WM35/Raw/DBD and batch 2 back to Resources (the AEW four + Dynamite '22 are done).
3. Batch 3: WM27→125, WM31→140, WM38→132, RR Retro→124, RR2020→135, SS09→143, SD21→53, ROH'05→134, SS22→160.
   Then batch 4: NXT 2.0→127, NXT W&G→128, Tokyo Dome→5, All In→123. Reserve list in Arena_inventory.md.

## Tools (repo tools/arena; laptop copies in `_arena_work\cardfix`)
- install_native.py: plan JSON, parts/mov/GFX/tables/names, exclude regex.
- reslot_stage.py: slot S→T restaging.
- tables.py, epk.py, shdc2.py, card_fg_fit.py, crowd_reslot.py.
- Laptop only: stage_b2.py, cards_b2.py (card build: movie file 1, foreground file 3, layout 7, font 4).

## Key lessons
- An HSPC part carries its id stamps: header @0x10, hashes @0x800/0x814, inner SHDC ids. Re-stamp from the stock file of the
  target id. New HSPC ids don't load; convert to a named EPAC instead.
- Crowd ids 0–14 only.
- Card layout ATB0 keyframes start at 0xf60: prop 0 = position, prop 1 = scale, colour at +0x20. The font is the FTPK (file 4).
- Graphics files can have odd names ("117- ..."). String edits go to both string_win copies.
- The device can't delete files: use fresh folders or the exclude regex.
- A device_bash call is limited to 180 s: background long jobs with nohup and poll the log file (not pgrep).

## Older open items
Dark Order/Private Party/Kingdom picks; DLL rebuild for Genesis (managers without slot code); cae_item_p20/sound_p30
restore; attire defs lost to Genesis; gfx_v1 untested; remove the bootstrap_repo.sh mention.
