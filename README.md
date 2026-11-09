# moddingwwe2k19

Toolkit and project record for Matthew's **WWE 2K19** (PC, Steam) mods.

This repository is the project's **single source of truth**: scripts, tools, mod definitions and diffs, the write-up
(`writeup/`; entry point `writeup/Status.md`), handoffs and all notes. Nothing lives only in a chat, a Claude project
file or a local folder. How agents share it: `WORKFLOW.md`.

Game files, modded builds and large binaries are **never** committed; they live on Matthew's laptop (see
`writeup/Status.md` section 2 for paths). Binary packs, when needed, go on the `assets` branch.

## Rules for every chat

- Start from `STATE.md` (one screen), then `writeup/Status.md` sections 1-3 and `WORKFLOW.md`.
- Commit the source of a change **before** delivering anything to the game folder. A mod whose source or recipe is not in
  this repository must not ship.
- Never modify the clean install. Work on the modded install only; `WWE 2K19 - unmodded` is the pristine reference.
- Back up every game file before it is touched; record the backup name and MD5 in the handoff.
- Chain, never overwrite: every patch/build script asserts the original bytes or hashes it expects.
- Project state lives in `writeup/Status.md` and `handoff/`; the Claude project holds only its instructions.
