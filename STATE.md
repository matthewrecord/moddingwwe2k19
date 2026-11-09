# Current state (one screen; read this first, then writeup/Status.md)

- **2026-11-09 (setup chat): repository scaffolded**, structured like `matthewrecord/botf-tools` (README, CLAUDE.md,
  GEMINI.md, STATE.md, WORKFLOW.md, `writeup/`, `handoff/`, `notes/`, `tools/`, `reference/`, branch `assets`).
  No mod work started. Nothing in the game folders has been changed.
- **Goal (binding, Matthew 2026-11-09):** add brand-new music slots (not replacements) that CCT can see and use. This is
  the validation for the whole project. Status.md section 1.
- **Autonomy (binding):** agents run and verify everything themselves; stop for Matthew only when it genuinely cannot
  be settled from our side. Status.md rule 5.
- **2026-11-09 (music survey, handoff 002):** music path mapped (`writeup/Music_map.md`): audio in `sound/music_*_m.pck`,
  events `Play_MUS_<id>_..` in banks in `music_e_s.pck` and DLC `patch_NN.pck`, music list = VMUM table in
  `pac/audio/assetconv_pNN.pac`. DLC added new IDs this way; p30 table already holds 747 empty IDs. Next: how CCT lists
  music (decompile), whether the game loads patch levels above 30, string table for names, bank authoring.
- **Latest handoff:** `handoff/002_music_survey_2026-11-09.md`.
- **Where things are:** source and scripts `tools/`; write-up `writeup/*.md`; notes `notes/`; references `reference/`;
  binaries (if ever needed) on the `assets` branch.
