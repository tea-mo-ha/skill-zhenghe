---
name: skill-suite-orchestrator
description: Unified orchestration skill for project review, architecture analysis, page generation, debugging and fixing, browser validation, shipping, file planning, and skill discovery. Use when Codex or 反重力 should expose one entry skill that selects the minimal necessary subskill set from addy-skills, extra-skills, and copied-existing-skills, prints chosen_subskills first, then continues with plan, execution, and validation without enabling every skill.
---

# Skill Suite Orchestrator

Use this as the only public entry skill for this repository. Keep child skills internal unless routing selects them.

## Dispatch Boundary

Route only to skills that physically exist under:

- `../addy-skills/`
- `../extra-skills/`
- `../copied-existing-skills/`

Do not fabricate skills.
Do not paste child `SKILL.md` files together.
Do not activate all skills "for coverage."

Treat `../plugins/` as out of scope for the default router unless the user explicitly asks for plugin-owned flows.

## Required Operating Contract

For every task, follow this sequence:

1. Detect the dominant user intent.
2. Select the smallest sufficient subskill set.
3. Output `chosen_subskills`.
4. Produce `plan`.
5. Perform `execution`.
6. Finish with `validation`.

Use this response skeleton:

```md
chosen_subskills
- skill-name: why it is needed

plan
- ...

execution
- ...

validation
- ...
```

## Minimal-Set Policy

- Start with one primary skill.
- If one skill is sufficient, stop there.
- Add a second skill only when the task clearly spans another concern.
- Do not append a helper skill just because it "might help."
- Add a supporting skill only when the primary skill cannot fully satisfy an explicit task requirement.
- Keep normal selections to 1-3 skills.
- Exceed 4 skills only when the user explicitly asks for cross-phase work and each added skill has a concrete reason.
- Prefer exactly one browser skill at a time.
- Prefer exactly one root-cause debugging skill at a time.
- Use `planning-with-files-zh` only for long, multi-step, or cross-session work.
- Use `find-skills` only when local skills are insufficient or the user explicitly asks for capability discovery.
- Treat `using-agent-skills` as a meta-skill, not a normal routing target.
- Avoid recursive meta-routing. Do not pick `using-agent-skills` unless the task is explicitly about skill discovery logic or maintaining the suite itself.

## Scenario Entry Points

Pick the dominant scenario first, then add only conditional helpers:

- 项目审核: start from `code-review-and-quality`
- 架构分析: default to `spec-driven-development` → `api-and-interface-design` → `planning-and-task-breakdown`; only front-load `idea-refine` or `brainstorming` when the request is visibly vague
- 页面生成: start from `frontend-design` when the user emphasizes style, visual direction, references, or brand feel; start from `frontend-ui-engineering` when the user emphasizes React, components, implementation, or runnable code
- 调试修复: choose exactly one of `systematic-debugging` or `debugging-and-error-recovery` by default
- 浏览器验证: start from exactly one of `webapp-testing`, `browser-testing-with-devtools`, or `agent-browser`
- 交付上线: start from `shipping-and-launch`
- 文件规划与辅助技能发现: start from `planning-with-files-zh` or `find-skills`

For the full intent-to-skill mapping, read `references/routing-matrix.md`.
For the current skill inventory, read `references/skill-inventory.md`.

## Selection Heuristics

- If the request is creative but underspecified, select `brainstorming` before implementation-facing skills.
- For architecture analysis, prefer `spec-driven-development` first, then `api-and-interface-design`, then `planning-and-task-breakdown`; prepend `idea-refine` or `brainstorming` only when goals or boundaries are still unclear.
- For page generation, prefer `frontend-design` for style-led prompts and `frontend-ui-engineering` for implementation-led prompts.
- If framework or library correctness matters, add `source-driven-development`.
- If public contracts or module boundaries are changing, add `api-and-interface-design`.
- If the work should land in slices, add `incremental-implementation`.
- If the fix needs regression protection, add `test-driven-development`.
- Use `systematic-debugging` for ambiguous, cross-layer, repeatedly failed, or root-cause-unclear debugging; use `debugging-and-error-recovery` for standard reproducible test, build, and runtime failures with a clearer failure surface.
- Do not select both debugging skills by default. Escalate from one to the other only when validation shows the first choice was insufficient.
- If launch risk is the focus, add `ci-cd-and-automation`, `deprecation-and-migration`, `security-and-hardening`, `performance-optimization`, or `documentation-and-adrs` only when the request actually calls for them.
- If local browser validation is required after page work, add one validation skill after the build skill, not before it.

## Validation Rules

- `validation` must prove that the selected subskill set was sufficient.
- If validation exposes a missing concern, append only the next necessary skill instead of restarting with a full set.
- Review tasks need review evidence, debugging tasks need repro and fix evidence, browser tasks need browser evidence, and launch tasks need checklist or rollout evidence.
- Do not claim blanket validation when only one slice of the task was checked.

## Maintenance

- Update `references/skill-inventory.md` when skills are added, removed, or renamed.
- Update `references/routing-matrix.md` when scenario routing changes.
- Keep this file focused on orchestration policy, not child skill internals.
