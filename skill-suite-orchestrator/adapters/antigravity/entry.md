# skill-suite-orchestrator for antigravity

Use this file as the antigravity-facing single entry for `skill-suite-orchestrator`.

Do not replace the core logic in [../../SKILL.md](../../SKILL.md).
Do not duplicate child skill content.
Do not change the routing strategy defined in [../../references/routing-matrix.md](../../references/routing-matrix.md).

## Operating Sequence

For every task, follow this order:

1. Identify the dominant user intent.
2. Choose the smallest sufficient subskill set from the existing local skill sources.
3. Output `chosen_subskills`.
4. Continue with `plan`.
5. Continue with `execution`.
6. Finish with `validation`.

## Dispatch Rules

- Start from one primary skill.
- If one skill is enough, stop there.
- Add a helper skill only when the task has an explicit unmet requirement.
- Do not add extra skills because they might be useful.
- Prefer exactly one browser skill at a time.
- Prefer exactly one debugging protocol at a time.
- Treat `using-agent-skills` as a meta-skill, not a normal default route.

## Shared Skill Sources

Select only from these real local sources:

- `../../../addy-skills/`
- `../../../extra-skills/`
- `../../../copied-existing-skills/`

Do not fabricate skills.
Do not enable every skill at once.
Do not treat `../../../plugins/` as part of the default routing surface unless the user explicitly asks for plugin-owned flows.

## Scenario Guidance

- 审核项目: start from `code-review-and-quality`
- 架构分析: default to `spec-driven-development` -> `api-and-interface-design` -> `planning-and-task-breakdown`; only front-load `idea-refine` or `brainstorming` when the request is clearly vague
- 页面生成: prefer `frontend-design` for style-led prompts and `frontend-ui-engineering` for implementation-led prompts
- 调试修复: choose exactly one of `systematic-debugging` or `debugging-and-error-recovery`
- 浏览器验证: choose exactly one of `webapp-testing`, `browser-testing-with-devtools`, or `agent-browser`
- 交付上线: start from `shipping-and-launch`
- 文件规划与辅助技能发现: start from `planning-with-files-zh` or `find-skills`

Read the full policy from:

- [../../SKILL.md](../../SKILL.md)
- [../../references/routing-matrix.md](../../references/routing-matrix.md)
- [../../references/skill-inventory.md](../../references/skill-inventory.md)

## Output Contract

Always emit the following sections in order:

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

## Adapter Boundary

This adapter exists only to make the core orchestrator easier for antigravity to consume.

- Keep Codex and antigravity on the same routing logic.
- Keep the adapter thin.
- Push routing changes into the shared core, not into this wrapper, unless the change is presentation-only.
