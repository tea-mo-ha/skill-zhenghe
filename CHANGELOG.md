# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.0] - 2026-04-14

### Changed

- **skill-suite-orchestrator**: Updated SKILL.md frontmatter description with `CRITICAL SYSTEM OVERRIDE` to enforce routing selection even on trivial tasks or when execution bypassing ("直接执行") is requested by the user.
- **skill-inventory.md**: Restructured to separate managed skills (addy/extra) from platform-native skills. Added version governance policy preventing hidden version drift.
- **using-agent-skills**: Deprecated and moved to `plugins/using-agent-skills-deprecated/`. Responsibilities fully taken over by `skill-suite-orchestrator`.
- **License alignment**: Removed upstream `license: Complete terms in LICENSE.txt` from `frontend-design` and `webapp-testing` frontmatter to align with repository MIT license.

### Removed

- **copied-existing-skills/**: Deleted entire directory. These 7 skills (`brainstorming`, `find-skills`, `mcp-builder`, `planning-with-files-zh`, `senior-fullstack`, `systematic-debugging`, `vercel-react-best-practices`) are now referenced as platform-native in the inventory, eliminating version drift risk.
- **skill-suite-orchestrator/adapters/**: Removed the Antigravity adapter layer. Orchestrator now uses flat-linked skill names directly.

### Added

- **routing-matrix.md**: 7 anti-pattern declarations at document tail.
- **Orchestrator audit trace**: `skill_file_reads` section in output contract for runtime observability.

## [1.0.0] - 2026-04-10

### Added

- Initial release with `skill-suite-orchestrator` as unified entry point.
- 21 `addy-skills` for engineering workflows (review, debug, ship, test, etc.).
- 3 `extra-skills` for frontend design, browser automation, and webapp testing.
- 7 `copied-existing-skills` for platform-native compatibility.
- `.codex/AGENTS.md` for Codex platform integration.
- `routing-matrix.md` with 7 scenario entry points.
- `skill-inventory.md` as authoritative skill catalog.
