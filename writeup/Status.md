# WWE 2K19 mod project: start here (state as of 2026-11-09)

## 1. What the project is

Matthew's modding of **WWE 2K19** (PC, Steam).

**Top priority and project validation (Matthew 2026-11-09): add brand-new music slots** to the game (not replacing
existing tracks) and have **CCT** see and use the new tracks. The DLC added music after release, so the game can take
new entries; no published community mod has done more than replace existing music. Success = a new track that did not
exist in the game plays in game and is selectable/assignable in CCT, with the original tracks still intact.

## 2. Install layout and toolkit (as found 2026-11-09, read-only survey)

Game installs (on Matthew's laptop, never in git):

| Path | What |
| --- | --- |
| `D:\SteamLibrary\steamapps\common\WWE 2K19` | The **modded** install (~161 GB). Working target |
| `D:\SteamLibrary\steamapps\common\WWE 2K19 - unmodded` | Pristine reference copy (~50 GB). Never modify |
| `D:\Pictures\WWE 2K19` | Matthew's modding folder: tool folders (`A - CCT`, `A - Data Editor 2k19`, `A - Item Adder`, `A - Ninja Ripper`, `A - Oodle Tools`, `A - PC Trainer`, `A - Pac Editor`, `A - Resources`, ...) plus unrelated media |

Top level of the install: `WWE2K19_x64.exe`, `Chunk0.arc`/`Chunk0.def`, `pac/`, `gameresource/`, `movies/`, `sound/`,
`mods/` (currently: CCT, PerfectPlextra, SuperString, TitantronFix, Universal Alternate Attire Unlock), DLLs.
Not yet surveyed in depth: which mods are applied to the modded copy, what differs from the unmodded copy.

## 3. Standing rules (Matthew)

1. Everything is saved and documented in this repository so work hands off between agents with no friction.
2. Commit source/recipes before delivering anything to the game folder.
3. Never modify `WWE 2K19 - unmodded`. Back up every game file before touching the modded install; record MD5s.
4. No game files or large binaries in git (`.gitignore`); tool packs and samples go on the `assets` branch.
5. **Autonomy (Matthew 2026-11-09):** agents work as autonomously as possible. Matthew does not want to run code or
   bench-test findings himself. Agents run, test and verify everything they can on their own, and only stop for
   Matthew when something genuinely cannot be settled from their side (e.g. a visual/audible in-game check that no
   tool can make, or a decision that is his). When asking, batch the questions and make each one quick to answer.
6. **Git (Matthew 2026-11-09, "most expedient"):** commits and pushes go from the agent's cloud clone; game files are
   read and written on the laptop through the agent shell. No laptop clone for now.
7. Add new rules here as Matthew states them, with the date.

- 2026-11-12: thread **model backport tool** (newer 2K -> 2K19), feasibility passed; see `writeup/Backport.md`, handoff 015.
- 2026-11-14: thread **title belt backport** (branch `claude/belt-backport`, `writeup/Belt_backport.md`, handoff 018).
  IWGP US title (2K23 mod) onto the Brahma Bull WWE Championship (`pac/prop/2905.pac` + `5038.pac`) in the **plain**
  `WWE 2K19` install (Matthew: belt work uses the plain game). Builder `tools/backport/belt_port.py`. Solved: belt prop
  format, stock-size ZLIB pacs (stored-Oodle pacs froze match loading), facing convention (2K19 props point normals/winding
  into the belt; unflipped, the plate's back faces were drawn = flat gold). `iwgp_brahma_v4` WORKS in game (2026-11-14).
  Merged to main 2026-11-14 (Matthew), together with `claude/backport-tool`. Tracer DLL `tools/telemetry/dinput8_filetrace.c` is installed in plain
  as `dinput8.dll` (remove after the belt is done).

## 4. Files in this project

See `writeup/README.md` (write-up), `handoff/` (session notes), `notes/` (references), `tools/` (scripts).

## 5. Open project-wide issues

- Survey the modded vs unmodded install and inventory the tools in `D:\Pictures\WWE 2K19`.
