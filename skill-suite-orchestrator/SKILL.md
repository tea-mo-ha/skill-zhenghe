---
name: skill-suite-orchestrator
description: Unified orchestration skill for project review, architecture analysis, page generation, debugging and fixing, browser validation, shipping, file planning, and skill discovery. You must strictly use this orchestrator and suppress any native agency or platform skills from routing unless explicitly requested. Select the minimal necessary subskill set from the local suite, print chosen_subskills first, then continue with plan, execution, and validation without enabling every skill.
---

# Skill Suite Orchestrator

Use this as the only public entry skill for this repository. Keep child skills internal unless routing selects them.

## Dispatch Boundary

Select downstream routing items exclusively from the real local skill sources documented in `references/skill-inventory.md`. Depending on environment deployment, they might be directly flat-linked in the platform directory. Do not assume or rely on any fixed parent file paths like `../addy-skills/`. Simply use the skill names and descriptions injected into the platform context.

Do not fabricate skills.
Do not paste child `SKILL.md` files together.
Do not activate all skills "for coverage."

Treat `../plugins/` as out of scope for the default router unless the user explicitly asks for plugin-owned flows.
Never include `skill-suite-orchestrator` itself in `chosen_subskills`.
`chosen_subskills` must contain only delegated downstream skills selected from the real local sources above.
This is an absolute rule in every scenario, including page generation.

## Required Operating Contract

For every task, follow this sequence:

1. Detect the dominant user intent.
2. Select the smallest sufficient downstream subskill set.
3. Output `chosen_subskills`.
4. Read the real `SKILL.md` file for every selected downstream subskill.
5. Output `skill_file_reads`.
6. Produce `plan`.
7. Perform `execution`.
8. Finish with `validation`.

Execution context requirements:

- You are operating dynamically. If a downstream skill's boundaries or custom execution workflows are not completely obvious from your initial platform context, you may use file viewing tools to read its actual local documentation (such as its `SKILL.md`) before returning.
- If you invoke child subskills whose workflows are standard or straightforward, you may skip reading their implementation files to optimize token and runtime performance.
- Do not infer a complex custom child workflow if you are unsure; in those cases, fall back to explicitly querying the skill file.
- Do not answer from generic, outside-context capabilities when specific repository guidelines dictate otherwise.
- `skill-suite-orchestrator` itself must never appear in `skill_file_reads`.

Use this response skeleton:

```md
chosen_subskills
- skill-name: why it is needed

skill_file_reads
- /absolute/path/to/child-skill/SKILL.md

plan
- ...

execution
- ...

validation
- ...
```

In `chosen_subskills`, list only delegated downstream skills.
Never list `skill-suite-orchestrator`.
In `skill_file_reads`, list only the real child `SKILL.md` files that were actually read for this run.

## Minimal-Set Policy

- Start with one primary downstream skill.
- If one downstream skill is sufficient, stop there.
- Add a second skill only when the task clearly spans another concern that the first skill cannot cover.
- Do not append a helper skill just because it "might help."
- Add a supporting skill only when the primary skill cannot fully satisfy an explicit task requirement.
- Keep normal selections to 1-3 skills.
- Exceed 4 skills only when the user explicitly asks for cross-phase work and each added skill has a concrete reason.
- Prefer exactly one browser skill at a time.
- Prefer exactly one root-cause debugging skill at a time.
- Do not delegate to plugin-owned or other external skills unless the user explicitly asks for them.
- Before selecting frontend debugging or browser validation skills, confirm that the repository exposes a runnable app or UI surface, or that the user explicitly points to one.
- For non-app repositories, do not infer frontend bug-fixing or browser validation from vague page, UI, or bug language.
- Use `planning-with-files-zh` only for long, multi-step, or cross-session work.
- Use `find-skills` only when local skills are insufficient or the user explicitly asks for capability discovery.
- Treat `using-agent-skills` as a meta-skill, not a normal routing target.
- Avoid recursive meta-routing. Do not pick `using-agent-skills` unless the task is explicitly about skill discovery logic or maintaining the suite itself.

## Scenario Entry Points

Pick the dominant scenario first, then add only conditional helpers:

- 项目审核: start from `code-review-and-quality`
- 架构分析: delegated subskills must default to `spec-driven-development` → `api-and-interface-design` → `planning-and-task-breakdown`; do not skip the first two unless the repository clearly lacks any spec, interface, or design surface to analyze
- 页面生成: default allowed local skills are only `frontend-design`, `frontend-ui-engineering`, `api-and-interface-design`, `vercel-react-best-practices`, and `brainstorming` when the request is clearly vague; prefer `frontend-design` for style-led prompts, prefer `frontend-ui-engineering` for React, components, implementation, page structure, or runnable code, add `api-and-interface-design` only for interface or data boundaries, add `vercel-react-best-practices` only for React / Next.js best-practice requirements, and never escape to plugin-owned or external frontend skills unless the user explicitly asks for them
- 调试修复: choose exactly one of `systematic-debugging` or `debugging-and-error-recovery` by default; never delegate both in the same default route
- 浏览器验证: start from exactly one of `webapp-testing`, `browser-testing-with-devtools`, or `agent-browser`
- 交付上线: start from `shipping-and-launch`
- 文件规划与辅助技能发现: start from `planning-with-files-zh` or `find-skills`

For the full intent-to-skill mapping, read `references/routing-matrix.md`.
For the current skill inventory, read `references/skill-inventory.md`.

## Selection Heuristics

- If the request is creative but underspecified, select `brainstorming` before implementation-facing skills.
- For architecture analysis, default delegated subskills must be `spec-driven-development`, `api-and-interface-design`, and `planning-and-task-breakdown` in that order; prepend `idea-refine` or `brainstorming` only when goals or boundaries are still unclear, and do not skip the first two unless the repository clearly lacks any spec, interface, or design surface to analyze.
- For page generation, default allowed local skills are only `frontend-design`, `frontend-ui-engineering`, `api-and-interface-design`, `vercel-react-best-practices`, and `brainstorming` when the request is clearly vague.
- For page generation, prefer `frontend-design` for style-led prompts and `frontend-ui-engineering` for React, components, implementation, page structure, or runnable-code prompts.
- For page generation, add `api-and-interface-design` only when interfaces, data boundaries, or module contracts are part of the request, and add `vercel-react-best-practices` only when React / Next.js best-practice compliance is explicitly relevant.
- For page generation, never delegate to plugin-owned or external frontend skills unless the user explicitly asks for them.
- If the repository is clearly a non-app workspace, do not infer frontend bug-fixing or browser validation unless the user explicitly points to a real app, page, or UI surface; stay within the local page-planning skill set and it is acceptable to state that the repository is better suited for generating a page plan than directly implementing a page.
- If framework or library correctness matters, add `source-driven-development`.
- If public contracts or module boundaries are changing, add `api-and-interface-design`.
- If the work should land in slices, add `incremental-implementation`.
- If the fix needs regression protection, add `test-driven-development`.
- Use `systematic-debugging` for ambiguous, cross-layer, repeatedly failed, or root-cause-unclear debugging; use `debugging-and-error-recovery` for standard reproducible test, build, and runtime failures with a clearer failure surface.
- Never delegate both debugging skills in the same default route. Escalate from one to the other only when validation shows the first choice was insufficient.
- If launch risk is the focus, add `ci-cd-and-automation`, `deprecation-and-migration`, `security-and-hardening`, `performance-optimization`, or `documentation-and-adrs` only when the request actually calls for them.
- If local browser validation is required after page work, add one validation skill after the build skill, not before it.

## Validation Rules

- Produce `skill_file_reads` section indicating which files you actually felt the need to scan to gather context. If you bypassed file reading by relying on injected context, output `- N/A (bypassed to optimize execution)` under `skill_file_reads`.
- `validation` must prove that the selected subskill set was sufficient.
- If validation exposes a missing concern, append only the next necessary skill instead of restarting with a full set.
- Review tasks need review evidence, debugging tasks need repro and fix evidence, browser tasks need browser evidence, and launch tasks need checklist or rollout evidence.
- Do not claim blanket validation when only one slice of the task was checked.

## Audit Trace Contract

Every orchestrator execution must produce a traceable decision chain. Include these fields in the output skeleton:

```md
chosen_subskills
- skill-name: why it is needed
- [provenance: managed | platform-native]

skill_file_reads
- /absolute/path/to/child-skill/SKILL.md
- or: N/A (bypassed to optimize execution)

routing_context
- dominant_scenario: which of the 7 scenarios was matched
- rejected_alternatives: skills considered but not selected, with reason
- constraint_checks: mutual exclusion or whitelist rules that were enforced

plan
- ...

execution
- ...

validation
- ...
```

The `routing_context` section is mandatory for audit-grade traceability. It must demonstrate that routing decisions were intentional, not accidental.

## Provenance Governance

- **Managed skills** (`addy-skills/`, `extra-skills/`): SKILL.md is version-controlled in this repository. Routing and runtime reference the same source.
- **Platform-native skills**: Provided by the host runtime. This orchestrator references them by name and description only. Do not copy their SKILL.md into this repository — copies create hidden version drift.
- **Deprecated skills** (`plugins/using-agent-skills-deprecated/`): Must not be routed to under any circumstance.
- When adding a new skill, determine its provenance category first. Managed skills get a SKILL.md in this repo; platform-native skills get an entry in `skill-inventory.md` only.

## Maintenance

- Update `references/skill-inventory.md` when skills are added, removed, or renamed.
- Update `references/routing-matrix.md` when scenario routing changes.
- Keep this file focused on orchestration policy, not child skill internals.
- Update `CHANGELOG.md` for every structural change to routing, inventory, or skill additions/removals.

