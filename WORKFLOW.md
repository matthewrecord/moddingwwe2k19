# Workflow: one repo, several agents

The repo `matthewrecord/moddingwwe2k19` is the single source of truth. Nothing lives only in a chat, a Claude project
file or a local folder. Start every session from `STATE.md`, then `writeup/Status.md`.

## Where things are

| Path | What |
| --- | --- |
| `STATE.md` | One-screen current state: read first |
| `writeup/Status.md` | Entry point: install paths, standing rules (section 3), file index |
| `writeup/*.md` | The write-up: findings, file-format maps, mod designs. Index `writeup/README.md` |
| `handoff/` | Short state notes between sessions, `NNN_<topic>_<date>.md`, highest number wins |
| `notes/` | Thread histories, references, ideas, parallel-work coordination |
| `tools/` | Scripts, converters, patchers, mod build recipes |
| `reference/` | Third-party reference material (licences noted), reading only |
| branch `assets` | Binaries and data (tool packs, extracted samples, backups manifests, `MD5SUMS`). Never rewrite a file there; add new names |

Local copies: the working copy on Matthew's laptop is the one place agents run game-touching steps. The game
installs are never in git.

## Branches

- `main` is always verified (see the gate below).
- One task = one short-lived branch, named by agent: `claude/<task>` or `gemini/<task>`. One owner per branch.
- Keep tasks in separate files where possible (one write-up file or one `handoff/` note per task) so two agents never
  edit the same file at once.
- Gemini output is raw material: a `gemini/*` branch may change `notes/`, draft write-up text and analysis scripts;
  anything that writes to the game folder is reviewed by Claude before it reaches `main`.

## Sequence for every task

```bash
git switch main && git pull --ff-only
git switch -c claude/<task>                 # or gemini/<task>
# ... work; commit small steps as you go (a crash must not lose work) ...

# Verify gate before merging:
#  - scripts/tools: they run on a copy of the target file and report expected hashes
#  - write-up changes: links and index (writeup/README.md) updated
#  - any game-file change: backup exists, its MD5 and the new MD5 are in the handoff
git add -A && git commit -m "<task>: <what changed>"

git fetch origin && git rebase origin/main
git push -u origin claude/<task>
git switch main && git pull --ff-only && git merge --ff-only claude/<task> && git push
git push origin --delete claude/<task>
```

If `main` moved and the fast-forward fails, rebase the branch again and retry.

## Debugging in-game problems (lesson from the belt port, 2026-11-14)
The belt port lost a day to guessing: each test build changed several things, results were judged by eye against an offline
renderer that had never been validated, and wrong theories (memory, UV misreads) cost Matthew a game run each. What found the
real cause in one run was a **control**. Rules:
1. **Control first.** Before blaming your own data, run the stock asset through the same test (stock mesh + test texture, stock
   file + one changed block). If the stock asset behaves as your model predicts, the fault is in your data; if not, your model of
   the game is wrong. Do this before the second failed in-game test, not after the sixth.
2. **One variable per build.** Each in-game test changes one thing from a known-good build.
3. **Write the prediction down (commit it) before Matthew runs the test.** Compare against it, not against memory.
4. **Measure, don't eyeball.** Use test textures with fine structure (grid lines) so 'matches' is checkable.
5. **Say what is proven and what is inferred.** Don't present a theory as the cause until a test has separated it from the alternatives.
6. **Leave the diagnostics in place until the work is closed.** The tracer was removed after the first success, and the next
   freeze (WWE '91 arena) went unrecorded. Remove instrumentation only when Matthew signs the work off.
7. **Your offline tools must model what the game does** (e.g. back-face culling). A renderer that draws both sides hid the bug.

## Handoff (end of every session)

1. Update `STATE.md` and `writeup/Status.md` (current state, next step) and/or add `handoff/NNN_<topic>_<date>.md`.
2. Merge to `main` and push (above). A new thread then needs only: "Read `STATE.md`; task X; branch `claude/x`."
3. New binaries (tool packs, samples): add them to the `assets` branch under new names and record MD5s in `MD5SUMS`.

## Delivery to the game

1. Source/recipe committed and pushed first.
2. Back up every file about to be replaced (name `<file>.bak_<date>`), record MD5s.
3. Apply to the **modded** install only; verify the new MD5s; note them in the handoff.
4. Matthew tests in game; his result goes into the next handoff.
