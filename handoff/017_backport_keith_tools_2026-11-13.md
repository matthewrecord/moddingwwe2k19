# Handoff 017: backport after Toni and Keith; tooling complete and documented (2026-11-13 15:50)

Branch `claude/backport-tool` (not merged to main). The full workflow, every gate and every module are in `tools/backport/README.md`. History is in `writeup/Backport.md` §23-26.

## State
| Character | Source | Build | In game |
|---|---|---|---|
| Flash Morgan Webster | 2K25 | v4 | good |
| Mark Briscoe | 2K24 | v4 | "spectacular" |
| Toni Storm | 2K25 (female) | v3 | good, eyes fixed |
| Keith Lee | 2K24 | v3: ring `ch50602` + entrance `ch50604` (pinholes capped, sweatshirt only at the entrance) | **awaiting check** |
| Old 2K20-port Keith | — | `test8_keith\old_keith_eyefix\ch92502/04.pac` (eyes straightened) | **awaiting check** |

Deliveries go to `D:\SteamLibrary\steamapps\common\WWE 2K19 - modded\_moddingwwe2k19_builds\backport\<testN>\`. Matthew installs them himself.

## Per-character recipe
Unzip the mod to `/home/claude/pairs/<NAME>/`, add a config to `build_port.py`, build, then run every gate: `preview`, the face comparison, `morphgrid`, `eyemorphs`, `eyegaze`, `bodypose` and the jaw test. Look at the renders, commit, deliver, and tell Matthew which slot or attire each file goes in.

Use `weights='source'` for new characters.

## Inputs to stage first
Ask Matthew for these in one message:
- The mod from `D:\Pictures\WWE 2K19\A - Resources\Paired Ports`.
- Stock pacs from `WWE 2K19 - modded\pac\ch`: ch68702, ch75602, plus any `prop_from` pac.
- The Fletcher/Willow port pacs and the originals.

## Next
1. Matthew's verdict on Keith v3 and on the old-Keith eye patch.
2. Possibly rebuild Flash and Briscoe with source weights.
3. Merge to main after the verify gate.
4. The simple app (preview, flagged problems, simple fixes, export).
