# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project loosely follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `gacli.py` — one-shot CLI frontend: single prompt → response → exit. Reads
  prompt from arg or stdin (pipe-friendly), writes answer to stdout and logs
  to stderr so output redirects cleanly. Flags: `--llm_no`, `--quiet`,
  `--raw`, `--no-stream`. Reuses `gatui.py`'s `clean()` and queue-drain
  pattern. #260429-21
- `gatui.py` — terminal (TUI) frontend reusing the same agent backend; raw-mode
  line reader with ESC-to-clear, UTF-8/CJK aware, Ctrl-C aborts current turn,
  Ctrl-D exits. Falls back to plain `input()` on Windows / non-TTY. #260429-21
- README: documented `gatui.py` under *Alternative App Frontends* and surfaced
  the full slash-command list (`/help /status /stop /new /restore /continue /llm`)
  — previously only `/new` and `/continue` were listed. #260429-21
- `CLAUDE.md` — codebase guide for AI agents (architecture, directory map,
  backend API, run instructions, conventions, gotchas). #260429-21

## [Earlier]

History prior to this changelog lives in `git log`. See in particular:

- `89567d2` docs: add Mintlify documentation site under `docs/mint/`
- `d587cfd` docs: cover reflect/, plugins/, sys_prompt, session-log gaps
- `b86bf79` i18n: translate memory SOPs and stapp UI to Korean
- `513fec9` cleanup: remove NextWillSummary, add supervisor_sop, fix streaming
  fence protection, tighten L1 rules

[Unreleased]: https://github.com/dkmin/GenericAgent/compare/main...HEAD
