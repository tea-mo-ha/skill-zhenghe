---
name: managed-skill-creator
description: Create or update repository-managed skills in this repo. Use when adding a new managed skill under addy-skills/ or extra-skills/, tightening an existing managed skill's scope, or wiring the skill into inventory, routing, docs, and regressions.
---

# Managed Skill Creator

Create or revise repository-owned skills without drifting from the orchestrator contract. This skill is for `skill-zhenghe` managed skills only.

## Use This For

- adding a new managed skill under `addy-skills/` or `extra-skills/`
- renaming or tightening an existing managed skill
- wiring a managed skill into inventory, routing docs, and regression coverage
- aligning a managed skill with `scripts/sync_managed_skills.py` publishing semantics

## Do Not Use This For

- copying platform-native `SKILL.md` files into this repo
- installing external skills from a marketplace or GitHub
- plugin-owned workflows under `plugins/`
- broad architecture work that does not actually create or revise a managed skill

If the need is external capability discovery, use `find-skills`. If the need is only task decomposition, use `planning-and-task-breakdown`.

## Provenance First

Before editing files, classify the target:

| Target type | Action |
|---|---|
| Managed workflow skill owned by this repo | Create or edit a folder under `addy-skills/` or `extra-skills/` |
| Platform-native skill provided by the host | Update `skill-inventory.md` routing text only; do not add a local copy |
| Plugin-owned capability | Keep it out of default routing unless the user explicitly asks for plugin flows |

Avoid names that collide with platform-native skills already exposed by the host runtime. Prefer a repo-specific name when collision risk exists.

## Placement Rules

| Place | Use when |
|---|---|
| `addy-skills/` | Engineering workflow, planning, review, testing, delivery, or governance skill |
| `extra-skills/` | Complementary browser, design, or utility skill that is not part of the core engineering pipeline |
| Inventory only | Host-provided skill that should be routable but not version-managed here |

## Minimal Skill Shape

A new managed skill normally needs only:

- `SKILL.md` with precise `name` and `description`
- optional references only when the core file would otherwise become too long
- no extra README, changelog, or setup docs inside the skill folder

Keep the body focused on:

- trigger conditions
- execution boundary
- required workflow
- validation expectations
- repo-specific constraints that Codex cannot infer on its own

## Required Repo Wiring

When a managed skill is added or materially repurposed, update the affected repo surfaces in the same change:

1. `skill-suite-orchestrator/references/skill-inventory.md`
2. `skill-suite-orchestrator/references/routing-matrix.md`
3. `skill-suite-orchestrator/SKILL.md` if scenario entry points or heuristics change
4. `skill-suite-orchestrator/references/route-profiles.yaml` only if a governed route changes
5. `README.md` when user-facing counts, scenarios, or usage examples change
6. `CHANGELOG.md`
7. `evals/promptfoo/orchestrator-routing.promptfoo.yaml` when routing behavior should stay regression-protected

## Implementation Workflow

1. Define the skill's provenance, scope, and non-goals.
2. Pick a collision-safe name and the correct folder (`addy-skills/` vs `extra-skills/`).
3. Write the smallest useful `SKILL.md`.
4. Wire inventory and routing so the orchestrator can actually select it.
5. Add or update regression coverage when the route contract changes.
6. Validate docs and counts stay in sync.
7. Use `scripts/sync_managed_skills.py` when the runtime copy needs to be refreshed after merge.

## Validation Checklist

A managed skill change is not complete until:

- [ ] the skill name is unique within the routed inventory
- [ ] `skill-inventory.md` reflects the new source of truth
- [ ] routing docs point to the right skill instead of `find-skills` or a platform-native fallback
- [ ] `README.md` and counts are consistent with the filesystem
- [ ] `CHANGELOG.md` records the structural change
- [ ] routing regressions cover the new path if orchestrator behavior changed
