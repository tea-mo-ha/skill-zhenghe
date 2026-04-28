# Promptfoo Routing Evals

This directory contains a minimal live regression suite for `skill-suite-orchestrator`.

It uses `promptfoo` to call the local `codex exec` CLI and verifies that the orchestrator still respects the repository's routing contract in a few critical scenarios.
The provider remains Python-based, while the assertions run in native JavaScript to avoid promptfoo's Python assertion accounting drift.

The provider intentionally runs in a lightweight routing-check mode:

- disables Codex plugins by default
- runs `codex exec` in `workspace-write` sandbox mode so child read commands and routing probes can execute
- creates a temporary writable `CODEX_HOME` clone for the child `codex exec`, avoiding writes into the user's live `~/.codex`
- forwards only a small allowlisted environment into the child Codex process
- prepends a routing-only instruction block so eval prompts stay in audit mode instead of drifting into real implementation
- sets `model_reasoning_effort=low`
- reads only the final completed assistant message from `codex exec --json`
- uses short per-attempt timeouts with a retry instead of one long blocking run
- uses shorter, contract-focused prompts instead of full task delivery

## Run

```bash
npx promptfoo@latest eval --no-cache -c evals/promptfoo/orchestrator-routing.promptfoo.yaml
```

## What It Checks

- `chosen_subskills` is present
- `skill_file_reads` is present
- `routing_context`, `execution`, and `validation` are present
- `skill_file_reads` contains only real child `SKILL.md` paths
- architecture analysis uses the forced local chain
- managed skill creation stays on the local skill-management route
- page generation stays on local frontend skills
- debugging does not enable both debug protocols together

## Notes

- The provider script calls `codex exec` with `--ephemeral`.
- The provider disables plugins, lowers reasoning effort, retries once on flaky live runs, isolates the child `CODEX_HOME`, uses `workspace-write` to keep routing probes functional, and extracts only the final completed assistant message so the eval behaves like a routing regression check rather than a full implementation run.
- The suite exercises the live runtime instead of fixture outputs, so failures can reveal real environment drift.
- The live suite requires a locally authenticated `codex exec`; if the child process returns `401 Unauthorized`, fix runtime auth first before treating the eval as a routing regression.
- If your runtime intentionally exposes different platform-native skills, update the assertions rather than loosening the orchestrator contract.
