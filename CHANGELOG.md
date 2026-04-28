# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- **skill-suite-orchestrator telemetry contract**: Made `telemetry` mandatory in the primary operating sequence and response skeleton so live routing evals do not omit it before reaching the stricter audit trace section.
- **Browser route mutual exclusion**: Clarified that browser validation must keep exactly one browser skill in the final route, even when the selected browser path fails and records a structured validation event.
- **Routing-only normalization hardening**: Clarified that page-generation and debugging route-validation prompts still require their scenario-specific downstream skill, and that the two debugging routes are mutually exclusive primary routes rather than composable helpers.
- **Shipping route hardening**: Clarified that shipping/launch route validation must select `shipping-and-launch` and must not substitute the planning route for concise-plan prompts.
- **Architecture route hardening**: Clarified that the governed architecture route must keep the full `spec-driven-development` → `api-and-interface-design` → `planning-and-task-breakdown` chain and must not collapse to planning alone.
- **Fast-path boundary hardening**: Clarified that explicit route-validation prompts and requests for routing trace sections must not use the trivial fast-path bypass.
- **Fast-path output hardening**: Clarified that trivial factual answers must not emit empty routing section placeholders such as `chosen_subskills: []`.
- **Managed skill route hardening**: Clarified that repo-managed skill creation must use `managed-skill-creator` without adding the platform-native `skill-creator`.
- **Project review route hardening**: Clarified that project review route validation must select `code-review-and-quality` and must not substitute the planning route for concise routing traces.
- **Reviewer risk routing**: Reviewer activation is now driven by an automatic risk profile for security, auth, secrets, payment, deployment, production, rollback, destructive, and migration-sensitive tasks, while retaining explicit config overrides.
- **Phase 3 reviewer gate**: Added a structured reviewer contract and optional second-stage reviewer pass so high-risk tasks can be independently approved or rejected with machine-readable JSON instead of free-form markdown.
- **Phase 3 runtime control layer**: Extracted failure normalization, validation-missing detection, retry/circuit-break policy, and telemetry artifact writing into a reusable `evals/promptfoo/runtime_control.py` module instead of leaving the control logic inline in the promptfoo provider.
- **promptfoo provider Phase 3 integration**: The live eval provider now emits structured failure events, computes normalized error fingerprints, enforces same-error / no-progress / total-attempt limits, and writes per-attempt plus final telemetry artifacts.
- **route-profiles.yaml v2**: Expanded governed scenario profiles from 3 to 8, covering all routing matrix entry points: project review, browser validation, shipping/launch, planning/discovery, and autonomous pipeline.
- **Context Budget Optimization**: Compacted `routing-matrix.md` from 13KB down to 1.5KB, moving detailed examples to an on-demand `intent-examples.md` file.
- **SKILL.md Deferred Reading**: Re-ordered the orchestrator contract so `plan` is formulated *before* `skill_file_reads` triggers a `view_file` on child skills. This drops the massive child-skill context load out of the planning phase, reducing cognitive token load and increasing routing speed.
- **promptfoo eval suite**: Expanded regression tests from 4 to 8 scenarios; added project review, shipping/launch, browser validation, and fast-path bypass coverage. Parameterized `repo_root` via `SKILL_ZHENGHE_ROOT` environment variable for CI readiness. Updated required sections to match the new deferred-reading contract.
- **openai.yaml**: Converted 1200-character single-line default_prompt to readable YAML block scalar for maintainability.
- **sync_managed_skills.py**: Added `--status` flag to compare source skill hashes against live runtime copies without modifying anything.

### Removed

- **assertions.py**: Removed unused Python assertions duplicate; the canonical assertion module is `assertions.mjs`.

### Added

- **Reviewer risk tests**: Added pytest coverage for automatic reviewer risk classification, low-risk bypass, configured overrides, and provider-level automatic reviewer invocation.
- **Reviewer schema tests**: Added unit tests for reviewer JSON parsing, rejection policy, reviewer-trigger matching, reviewer artifacts, and provider-level retry after reviewer rejection.
- **Phase 3 runtime control tests**: Added pytest coverage for error normalization, failure event extraction, validation-missing handling, retry/circuit-break policy, and telemetry JSON writers.

- **sync_managed_skills.py**: Upgraded the runtime sync script into a versioned publisher. Releases are now built before cutover, promoted per skill through resumable staging transactions, and tracked with release manifests instead of one-shot overwrite semantics.
- **promptfoo provider hardening**: Switched the live Codex eval provider to an allowlisted child environment with isolated Codex state while keeping the child run in `workspace-write` sandbox mode so routing probes can execute without touching the user's live Codex state.
- **Regression contract coverage**: The promptfoo suite now requires `routing_context`, `execution`, and `validation`, matching the orchestrator's published execution protocol instead of only checking the early routing fields.
- **Deployment governance**: Managed skills are now documented as source-of-truth artifacts that should be refreshed into runtime copies with the sync script, instead of implying that copied runtimes stay automatically in lockstep.
- **frontend-design**: Tightened the visual accessibility contract so design outputs now explicitly declare contrast, focus visibility, reduced-motion handling, and non-color-only cues.
- **promptfoo provider runtime isolation**: The live eval provider now runs child `codex exec` calls with an isolated temporary `CODEX_HOME` and `workspace-write` sandboxing so routing regressions can run inside restricted parent environments without writing into the user's live Codex state.

### Added

- **sync_managed_skills.py**: Added a repeatable runtime sync script for refreshing managed skills into Antigravity and Codex runtime directories without manually copying folders.
- **Rollback support**: Added `--rollback-release <release_id>` for publishing an earlier managed-skill release back into a runtime target.
- **Regression parser hardening**: Updated the JS assertions so skill extraction reads the selected skill token itself, not arbitrary backticked text embedded later in the rationale.
- **managed-skill-creator**: Added a repo-owned managed skill for creating or updating local managed skills without colliding with the platform-native `skill-creator`.
- **Skill-management routing**: Added inventory, routing, README, and promptfoo coverage for the local managed-skill creation path.
- **skill-suite-orchestrator**: Restored a hard execution rule that every selected downstream skill must have its real `SKILL.md` read before execution. Removed the bypass wording that let "straightforward" skills skip file reads.
- **Platform-native routing**: Added an explicit availability gate so `agency-*` and other platform-native skills are only legal route targets when the live runtime actually exposes them.
- **README contract**: Updated the public output contract to include `skill_file_reads` and `routing_context`, matching the orchestrator's real audit trace.
- **Governed route normalization**: Added a machine-readable `route-profiles.yaml` and updated the orchestrator prompt/policy so governed routes are normalized before `chosen_subskills` is emitted.
- **Architecture analysis hardening**: Minimal route validation, dry runs, and brief-plan architecture requests now stay on the full `spec-driven-development -> api-and-interface-design -> planning-and-task-breakdown` chain.
- **promptfoo routing evals**: Added a minimal regression harness under `evals/promptfoo/` to verify architecture, page-generation, and debugging routes against the live orchestrator.
- **route-profiles.yaml**: Added declarative required / optional / forbidden / mutually-exclusive route profiles for the core governed scenarios.

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
