# Handoff 014: managers, main teams, person ids (2026-11-11 04:15)

Branch `claude/universe-qol` (pushed; not yet merged to main this round). Full log: `writeup/Universe_QoL.md` from
"Stale main manager / main team links" on.

## What was wrong and what is fixed
1. **Wrong main teams** (A-Kid/Trent show GOD, Beth Phoenix shows Death Triangle...). The main team is not stored:
   display code (0x140d32eb7) takes a runtime field, else the first team (0..99) with a "member", and membership
   compares **pofo +4 (person id)**. CCT-injected pofos carried donor person ids (53 shared ids). **Fixed**: 98 pofos
   given unique +4 (live poke into MyWWE pofo array 0x142840600 + idx*484, saved; verified after restart by Matthew).
   List `notes/characters/person_id_fix_2026-11-11.tsv`.
2. **Stale managers** (vanilla pairings of the slot's original occupant: Trent/Maryse -> Miz, Miz -> Miztourage...).
   Four copies of the 0xD88 superstar records: three in the save (live 0x142e6f9b0 + k*0x1EA9C8, managers 3 x u32 at
   +0x58) and the **panel table** rebuilt every launch by NGlobalData::InitCharProfile from
   **`mods/PerfectPlextra/pac/profile/profile_pro.pac`** (0x488-byte records, header 08 00 88 04, i16 idx, u16 flag
   (+0x1cb); managers at +0x3B8, main team u32 +0x3D0) into 0x143700000 + idx*0xD88. **Fixed at the source**
   (`tools/build/managerfix.py`; rule: clear if either side's slot was replaced; keep Brie/Nikki, Owens/Zayn,
   Mickie/Alexa, Liv/Sarah, Diesel->HBK'97, UE trio). Backups `profile_pro.pac.orig_managers`, `.before_teammgrs`.
3. **Team managers set per Matthew** (rules + his per-team picks; see Universe_QoL.md 03:45-04:15 and
   `notes/characters/team_managers_2026-11-11.log`), written live (poke files `team_managers*.poke`,
   `idfix_managers5.poke` in `_moddingwwe2k19_builds`) and into profile_pro.pac.
4. **Six pofos had the wrong slot id at +0** (Cassady 627->115, Kay Lee Ray 659->147, Vincent 672->160, Xia Li
   450->194, Scorpio Sky 978->210, idx 156 767->255). Fixed live (save layer). CCT source pofos still wrong.

## State at handoff (verify first)
- Game was running with everything poked live. **Matthew was asked to save "everywhere" and quit.** Check the save
  (decode MAINBODY, copy-0 managers at 0x88e5b0-170*0xD88 + idx*0xD88 + 0x58; pofo array at 0x117f0 - 148*484)
  contains the new managers and the 6 id fixes. If not, re-apply the poke files (old-value checked) and have him save.
- **DLL test12 (manager sync save -> panel table) built, NOT installed**: `_moddingwwe2k19_builds/dinput8.dll.test12`
  (md5 aa5b46ef...). Installed is test10 (92e6b9d5...). Install when the game is closed (backup current as
  `dinput8.dll.test10_installed_bak`). Then test: set a manager in game, save, restart, still there?
- Save backups: `SAVEDATA.before_manager_fix`, `.before_person_ids`, `.before_idfix` in `_moddingwwe2k19_builds`.
- Leftover dumps `slots_full_*.dmp` (~2 GB each) in the game folder: Matthew can delete.

## Open items (triage order)
1. Install test12 + verify sync; verify managers after restart (Bray, Hikuleo, Ziggler, Dominik, Brock -> none;
   team picks present).
2. STATE reminder: re-add Dark Order, Private Party, The Kingdom to the team list, then manager picks.
3. Existing Universes keep their own (old) copies; new Universes inherit fixes. Optionally fix Universe copies.
4. Overall rating formula (not stored anywhere; computed at display). Watchpoints so far hit only copies.
5. Sabin = overflow 937 (no 0xD88 record; overflow slots need their own manager storage).
6. Fix the 6 wrong ids and person ids in the CCT source pofos so re-injection doesn't undo them.
7. Earlier Universe QoL items: match-type names, contender rankings, in-game record display.
