# Handoff 012: Test Wrestler in overflow slot 509 installed (2026-11-10 ~18:00)

Matthew 17:28: put a wrestler from the pictures folder into "the 510 slot", named Test Wrestler. (Done before his
test0 check; test0 dll kept as `dinput8.dll.test0_bak`.)
- Slot: profile index **509** (the 510th; CCT's list ends at 508), character id **937** (a PerfectPlextra
  placeholder id whose row was dead because of the 509 cap; no CCT assets used it).
- Source: `D:\Pictures\WWE 2K19\Alex Shelley` (.pofo/.moveset; Alex is id 779 / index 438 in game) via
  `tools/build/charslot.py`; name string 39370 "Test Wrestler" (SuperString English table) in pofo name fields
  +0x08..+0x1C, +0x1D0.
- Proxy test1 (`tools/slots`, md5 79927c88...): caps 510 in the 3 lookup functions; thread injects
  `slots\0509_0937.*` after the id map is built (profile table rows for >= 509 are still skipped by the loader).

## Installed (game folder), backups `.orig_charslot`
| file | before | after |
| --- | --- | --- |
| mods/SuperString/pac/string/win/string_win.pac | 049d9cb2... | 54361b8d... |
| Chunk0.def (+10 lines, 937 copies of the 779 CCT entries) | e2be6749... | 07395947... |
| dinput8.dll | test0 5b97d8d3... | test1 79927c88... |
| slots/0509_0937.pofo / .moveset (new) | - | 2fa4aab4... / 7158f8d6... |
New files (copies of Alex's): mods/CCT/characters/pac/ch/ch937{02,04,12,14}.pac, movies ss_*/093700.pac,
renders custom_typea|b/093700.pac. Build copy: `_moddingwwe2k19_builds/testwrestler_v1`.
Uninstall: restore the two `.orig_charslot` files, rename dinput8.dll; the new files are inert without them.

## Matthew's check
Boot; superstar select: Test Wrestler (Alex's render)? Pick him in Exhibition: model, moveset, entrance.
Then read `wwe2k19_slots.log`. Unknowns: unlock (HID) entries for id 937; other "idx <= 508" checks
(48 jae/6 ja sites) may hide him in some menus or crash; the 40-byte per-slot table entry is left zero.

## 17:36 crash -> test1b installed (dinput8.dll md5 eef5cca4...)
Cause and fix: notes step 1g (missed image-relative writes of the index->id table). test1b also logs exceptions
(registers, exe stack addresses) to wwe2k19_slots.log. Old log kept as wwe2k19_slots_test1_crash.log. The game itself
writes minidumps to CrashDump\ (read with tools/exe/crashdump.py). Other installed files unchanged.

## 17:50 test1c installed (dinput8.dll md5 235eb27a...), not yet booted
= test1b fix + file-activity recorder (tools/slots/README.md "Diagnostics"). test1b was never booted.

## 17:51 RESULT test1c: Test Wrestler APPEARS in the select screen (first character beyond 509 in game). Match start HANGS.
No exception, no minidump; log (kept as wwe2k19_slots_test1c_hang.log) ends at boot; map rebuilt once at ~26 s
(slot re-registered). test1d installed (md5 703b1130...): F12 also snapshots every thread (rip + exe stack addresses).
Next: Matthew reproduces the hang, presses F12 twice ~5 s apart during it; read the snapshot.

## 18:04 test1d BLOCKED by Windows security (game would not start; DLL never ran: log untouched). Defender is off,
so likely Smart App Control / reputation heuristics reacting to SuspendThread+GetThreadContext on all threads.
test1e installed (md5 36f19407...): no thread suspension; F12 asks dbghelp.dll (game's own copy) for a minidump
`slots_snapshot_<s>.dmp` in the game folder (read: tools/exe/crashdump.py <dmp> --all). If test1e is also blocked:
fall back to `_moddingwwe2k19_builds/testwrestler_v1/dinput8.dll.test1c` (known to run).

## 18:15 test1e hang snapshots read (notes step 1h); test1f installed (md5 a6f6ea73...)
Old snapshots + log moved to `_moddingwwe2k19_builds/logs/`. Next: Matthew boots test1f, tries the match again.

## 18:20 test1f hung too; test1g installed (md5 bb0f3fd9...), slot files renamed slots\0509_0937_0779.* (notes 1h)

## 18:30 test1h installed (md5 d1f1f159...; remote snapshot trigger: create `slots_snapshot.request` in the game folder).
Hang snapshots read (notes 1i). Chunk0.def re-sorted (md5 dfc88fa3...). Next: Matthew retries the match.

## 18:35 Alex Shelley control match loads with the DLL; Test Wrestler hangs. test1i installed (md5 169e2089...):
caller tracer (TRACE lines). Note: F11/F12 do not register once the game hangs; use the request file.

## 18:55 ROOT CAUSE FOUND (notes 1j): copied pacs kept Alex's internal virtual names. All 10 renamed in place
(models 00093702.., trons M093700, renders 59B44362/821CFB09). test1k DLL stays (md5 ab6d01bb...). Next: Matthew retries.

## 18:54 RESULT: TEST WRESTLER LOADS INTO A MATCH (Matthew: "You did it"). First playable character beyond the 509 cap.
Log: no exceptions; only /CASD misses (normal, vanilla characters have them too).
Installed state: dinput8.dll test1k (ab6d01bb...), slots\0509_0937_0779.*, Chunk0.def dfc88fa3..., SuperString
string_win.pac 54361b8d..., 10 renamed asset copies for id 937. Backups: *.orig_charslot.
