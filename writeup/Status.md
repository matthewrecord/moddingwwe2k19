# WWE 2K19 mod project: start here (state as of 2026-11-09)

## 1. What the project is

Matthew's modding of **WWE 2K19** (PC, Steam). First mod: **not yet chosen**. Record the goal and its decisions here.

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
5. Add new rules here as Matthew states them, with the date.

## 4. Files in this project

See `writeup/README.md` (write-up), `handoff/` (session notes), `notes/` (references), `tools/` (scripts).

## 5. Open project-wide issues

- Choose the first mod.
- Confirm the laptop can push to GitHub on its own (git present; no credentials or `gh` found 2026-11-09).
- Survey the modded vs unmodded install and inventory the tools in `D:\Pictures\WWE 2K19`.
