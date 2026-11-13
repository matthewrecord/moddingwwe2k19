# Handoff 014: model backport tool (new thread), 2026-11-12

## Goal (Matthew)
Build a tool that backports character models from newer WWE games (2K22+) to WWE 2K19.
Not expected to be 100% automatic. Matthew does NOT use Blender: Blender may run headless
as an engine, but the user-facing last mile must be a simple app (preview the model in
stress poses, flagged problem areas, plain buttons/sliders for common fixes, export to 2K19).
Characters the tool can't finish get labelled "needs a human touch-up".

## Data
- About 60 matched pairs: original model from a newer game + the finished 2K19 port,
  all ported for Matthew by one porter (scorpionxxx, now unreachable; no public write-up of
  his method found). One porter = consistent style, good for learning.
- First 4 pairs: `D:\Pictures\WWE 2K19\A - Resources\Paired Ports`.
- Do NOT commit model files to GitHub (2K assets + porter's work; size). Keep them on
  Matthew's drive or in the workspace; commit only scripts, mapping tables, findings.

## Planned design
Deterministic pipeline (extract, bone map, rest-pose snap, PBR->2K19 texture conversion,
poly/hair budget, neck seam, pack to chXXXX .pac) + a small learned weight-correction model
trained per-vertex on the 60 pairs (hold out ~10 for testing). Learn the porter's fixed
rules (bone map, texture curves) by diffing pairs.
Treat claims in the AI write-up Matthew attached in the first chat as unverified
(e.g. ".0014 texture archives", "Fast-Geom-Skin").

## Next step: feasibility test (do first)
1. Inventory the 4 pairs: file types, which game each original came from, any extra files from the porter.
2. Confirm we can read both formats (2K19 .pac/.yobj; modern 2K archives) into meshes + skeletons.
   Check existing community tools first.
3. Recover the porter's bone mapping; measure naive weight transfer vs his weights.
4. Record results in a new `writeup/Backport.md` as you go; branch `claude/backport-tool`.

## Open questions for Matthew (ask together, once)
- Which game each original came from (if not obvious from the files).
- Any extra files/messages from scorpionxxx (.blend/.fbx, tool names).
