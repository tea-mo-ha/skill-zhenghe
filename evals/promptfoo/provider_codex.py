from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

try:
    from .runtime_control import (
        RetryLimits,
        RetryState,
        append_telemetry_event,
        apply_reviewer_policy,
        apply_retry_policy,
        build_invalid_reviewer_result,
        build_failure_event,
        build_reviewer_prompt,
        build_reviewer_profile,
        build_session_id,
        build_task_id,
        build_telemetry_event,
        build_validation_missing_event,
        create_artifact_root,
        output_claims_validation_passed,
        parse_reviewer_result,
        render_retry_feedback,
        render_reviewer_feedback,
        write_reviewer_artifact,
        write_final_telemetry,
    )
except ImportError:  # pragma: no cover - direct script execution fallback
    from runtime_control import (  # type: ignore
        RetryLimits,
        RetryState,
        append_telemetry_event,
        apply_reviewer_policy,
        apply_retry_policy,
        build_invalid_reviewer_result,
        build_failure_event,
        build_reviewer_prompt,
        build_reviewer_profile,
        build_session_id,
        build_task_id,
        build_telemetry_event,
        build_validation_missing_event,
        create_artifact_root,
        output_claims_validation_passed,
        parse_reviewer_result,
        render_retry_feedback,
        render_reviewer_feedback,
        write_reviewer_artifact,
        write_final_telemetry,
    )

SAFE_ENV_KEYS = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "SHELL",
    "TMPDIR",
    "TMP",
    "TEMP",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
    "COLORTERM",
    "NO_COLOR",
    "CLICOLOR",
    "CLICOLOR_FORCE",
    "CODEX_HOME",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    "XDG_DATA_HOME",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
)

ROUTING_EVAL_PREAMBLE = """Routing-only regression check for skill-suite-orchestrator.
Do not edit files, create skills, apply patches, or make any repository changes.
Output only the requested sections.
In `chosen_subskills`, list only delegated child skills and never include `skill-suite-orchestrator`.
In `skill_file_reads`, list only child `SKILL.md` files that were actually read, and never include `skill-suite-orchestrator` or non-child files.
"""


def _trim(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _extract_final_agent_message(stdout: str) -> str:
    final_message = ""

    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or not line.startswith("{"):
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") != "item.completed":
            continue

        item = event.get("item") or {}
        if item.get("type") == "agent_message" and item.get("text"):
            final_message = str(item["text"]).strip()

    return final_message


def _extract_command_executions(stdout: str) -> list[dict[str, Any]]:
    executions = []
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or not line.startswith("{"):
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "command_execution":
                executions.append(item)
    return executions


def _build_child_env(overrides: dict[str, str], extra_allowlist: list[str]) -> dict[str, str]:
    env: dict[str, str] = {}
    allowed = set(SAFE_ENV_KEYS)
    allowed.update(str(key) for key in extra_allowlist)

    for key in allowed:
        value = os.environ.get(key)
        if value:
            env[key] = value

    for key, value in overrides.items():
        env[str(key)] = str(value)

    return env


def _codex_home_source(env: dict[str, str]) -> str:
    codex_home = env.get("CODEX_HOME")
    if codex_home:
        return codex_home
    home = env.get("HOME") or os.path.expanduser("~")
    return os.path.join(home, ".codex")


def _copy_if_exists(source: str, destination: str) -> None:
    if not os.path.exists(source):
        return
    if os.path.isdir(source):
        shutil.copytree(source, destination)
        return
    shutil.copy2(source, destination)


def _prepare_isolated_codex_home(env: dict[str, str]) -> str:
    source_root = _codex_home_source(env)
    isolated_root = tempfile.mkdtemp(prefix="promptfoo-codex-home-")

    for name in ("auth.json", "config.toml", "installation_id", "version.json", "AGENTS.md"):
        _copy_if_exists(os.path.join(source_root, name), os.path.join(isolated_root, name))

    for name in ("skills", "plugins", "rules"):
        _copy_if_exists(os.path.join(source_root, name), os.path.join(isolated_root, name))

    return isolated_root


def _run_codex_once(
    cmd: list[str],
    *,
    repo_root: str,
    env: dict[str, str],
    timeout_sec: int,
) -> dict[str, Any]:
    completed = subprocess.run(
        cmd,
        cwd=repo_root,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )

    output = _extract_final_agent_message(completed.stdout)
    if not output:
        output = completed.stdout.strip()

    result = {
        "output": output,
        "metadata": {
            "exitCode": completed.returncode,
            "stdout": _trim(completed.stdout),
            "stderr": _trim(completed.stderr),
            "command": cmd,
        },
    }

    if completed.returncode != 0 and not output:
        result["error"] = _trim(completed.stderr or completed.stdout or "codex exec failed")

    return result


def call_api(prompt: str, options: dict[str, Any] | None, context: dict[str, Any] | None) -> dict[str, Any]:
    options = options or {}
    config = options.get("config", {})
    original_prompt = prompt
    prompt = f"{ROUTING_EVAL_PREAMBLE}\n\n{original_prompt}"

    raw_repo_root = config.get("repo_root", "")
    import re
    # Handle ${VAR:-default} syntax
    def replacer(m):
        return os.environ.get(m.group(1), m.group(2))
    resolved_root = re.sub(r'\$\{([A-Za-z0-9_]+):-([^}]+)\}', replacer, raw_repo_root)
    resolved_root = os.path.expandvars(resolved_root)
    repo_root = resolved_root if resolved_root else os.getcwd()
    timeout_sec = int(config.get("timeout_sec", 240))
    max_attempts = int(config.get("max_attempts", 2))
    codex_bin = config.get("codex_bin", "codex")
    model = config.get("model")
    model_reasoning_effort = config.get("model_reasoning_effort", "low")
    profile = config.get("profile")
    search = bool(config.get("search", False))
    disable_features = list(config.get("disable_features", ["plugins"]))
    add_dirs = list(config.get("add_dirs", []))
    sandbox_mode = str(config.get("sandbox_mode", "read-only"))
    extra_env_allowlist = list(config.get("env_allowlist", []))
    env_overrides = dict(config.get("env", {}))
    isolate_codex_home = bool(config.get("isolate_codex_home", False))
    retry_limits = RetryLimits(
        same_error_retry_limit=int(config.get("same_error_retry_limit", 3)),
        no_progress_limit=int(config.get("no_progress_limit", 2)),
        total_attempt_limit=int(config.get("total_attempt_limit", 5)),
        reviewer_rejection_limit=int(config.get("reviewer_rejection_limit", 2)),
    )
    artifact_root = create_artifact_root(config.get("artifact_root"))
    task_id = build_task_id(original_prompt)
    session_id = build_session_id()
    reviewer_enabled = bool(config.get("reviewer_enabled", True))
    reviewer_always = bool(config.get("reviewer_always", False))
    reviewer_required_patterns = list(
        config.get(
            "reviewer_required_patterns",
            [],
        )
    )
    configured_reviewer_skill = config.get("reviewer_skill")
    reviewer_profile = build_reviewer_profile(
        original_prompt,
        reviewer_enabled=reviewer_enabled,
        reviewer_always=reviewer_always,
        reviewer_required_patterns=reviewer_required_patterns,
        reviewer_skill=str(configured_reviewer_skill) if configured_reviewer_skill else None,
    )
    reviewer_rejection_count = 0

    cmd = [
        codex_bin,
        "exec",
        "--cd",
        repo_root,
        "--sandbox",
        sandbox_mode,
        "--skip-git-repo-check",
        "--ephemeral",
        "--color",
        "never",
    ]

    if model:
        cmd.extend(["--model", str(model)])
    if model_reasoning_effort:
        cmd.extend(["-c", f'model_reasoning_effort="{model_reasoning_effort}"'])
    if profile:
        cmd.extend(["--profile", str(profile)])
    if search:
        cmd.append("--search")
    for feature in disable_features:
        cmd.extend(["--disable", str(feature)])
    for add_dir in add_dirs:
        cmd.extend(["--add-dir", str(add_dir)])

    cmd.extend(["--json", prompt])

    env = _build_child_env(env_overrides, extra_env_allowlist)
    isolated_codex_home: str | None = None

    if isolate_codex_home:
        isolated_codex_home = _prepare_isolated_codex_home(env)
        env["CODEX_HOME"] = isolated_codex_home
        env["XDG_CACHE_HOME"] = os.path.join(isolated_codex_home, "xdg-cache")
        env["XDG_CONFIG_HOME"] = os.path.join(isolated_codex_home, "xdg-config")
        env["XDG_DATA_HOME"] = os.path.join(isolated_codex_home, "xdg-data")

        for key in ("XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME"):
            os.makedirs(env[key], exist_ok=True)

    try:
        last_result: dict[str, Any] | None = None
        current_prompt = prompt
        retry_state = RetryState()

        for attempt in range(1, max_attempts + 1):
            attempt_started = time.monotonic()
            try:
                # Update prompt in cmd for retries
                cmd[-1] = current_prompt

                result = _run_codex_once(
                    cmd,
                    repo_root=repo_root,
                    env=env,
                    timeout_sec=timeout_sec,
                )
                result.setdefault("metadata", {})
                result["metadata"]["attempt"] = attempt
                if isolated_codex_home:
                    result["metadata"]["isolatedCodexHome"] = isolated_codex_home

                output = result.get("output", "")
                stdout = result.get("metadata", {}).get("stdout", "")
                executions = _extract_command_executions(stdout)
                failures = [e for e in executions if e.get("exit_code") not in (0, None)]

                if output:
                    if failures:
                        failure_event = build_failure_event(
                            failures[-1],
                            artifact_root=artifact_root,
                            attempt=attempt,
                        )
                        retry_state, decision = apply_retry_policy(
                            retry_state,
                            failure_event,
                            limits=retry_limits,
                        )
                        telemetry = build_telemetry_event(
                            task_id=task_id,
                            session_id=session_id,
                            skill_name="skill-suite-orchestrator",
                            duration_ms=int((time.monotonic() - attempt_started) * 1000),
                            validation_result="failed",
                            reviewer_status="skipped",
                            final_state=decision.final_state,
                            attempt_count=retry_state.attempt_count,
                            same_error_count=retry_state.same_error_count,
                            output_text=output,
                            error_fingerprint=decision.error_fingerprint,
                            exit_code=failure_event.exit_code,
                            failed_command=failure_event.failed_command,
                            retry_reason=decision.reason,
                            artifact_paths=failure_event.artifact_paths,
                        )
                        telemetry_jsonl = append_telemetry_event(artifact_root, telemetry)
                        result["metadata"]["artifactRoot"] = str(artifact_root)
                        result["metadata"]["telemetryJsonl"] = telemetry_jsonl

                        if decision.action == "abort":
                            final_telemetry = write_final_telemetry(artifact_root, telemetry)
                            result["error"] = (
                                f"Circuit breaker tripped: {decision.reason} "
                                f"(attempts={decision.attempt_count}, same_error={decision.same_error_count}, "
                                f"no_progress={decision.no_progress_count})"
                            )
                            result["metadata"]["circuit_broken"] = True
                            result["metadata"]["finalTelemetry"] = final_telemetry
                            return result

                        current_prompt += render_retry_feedback(failure_event, decision)
                        last_result = result
                        continue

                    if output_claims_validation_passed(output) and not executions:
                        failure_event = build_validation_missing_event(
                            artifact_root=artifact_root,
                            attempt=attempt,
                            reason=(
                                "Validation claimed success without executing a tangible validation tool "
                                "from the whitelist."
                            ),
                        )
                        retry_state, decision = apply_retry_policy(
                            retry_state,
                            failure_event,
                            limits=retry_limits,
                        )
                        telemetry = build_telemetry_event(
                            task_id=task_id,
                            session_id=session_id,
                            skill_name="skill-suite-orchestrator",
                            duration_ms=int((time.monotonic() - attempt_started) * 1000),
                            validation_result="validation_missing",
                            reviewer_status="skipped",
                            final_state=decision.final_state,
                            attempt_count=retry_state.attempt_count,
                            same_error_count=retry_state.same_error_count,
                            output_text=output,
                            error_fingerprint=decision.error_fingerprint,
                            retry_reason=decision.reason,
                            artifact_paths=failure_event.artifact_paths,
                        )
                        telemetry_jsonl = append_telemetry_event(artifact_root, telemetry)
                        result["metadata"]["artifactRoot"] = str(artifact_root)
                        result["metadata"]["telemetryJsonl"] = telemetry_jsonl

                        if decision.action == "abort":
                            final_telemetry = write_final_telemetry(artifact_root, telemetry)
                            result["error"] = (
                                "Circuit breaker tripped: validation_missing exceeded retry policy "
                                f"({decision.reason})"
                            )
                            result["metadata"]["circuit_broken"] = True
                            result["metadata"]["finalTelemetry"] = final_telemetry
                            return result

                        current_prompt += render_retry_feedback(failure_event, decision)
                        last_result = result
                        continue

                    validation_result = "passed" if executions else "validation_missing"
                    reviewer_status = "skipped"
                    reviewer_artifacts: list[str] = []

                    if validation_result == "passed" and reviewer_profile.reviewer_required:
                        reviewer_skill = reviewer_profile.reviewer_skill
                        reviewer_prompt = build_reviewer_prompt(
                            task_prompt=original_prompt,
                            candidate_output=output,
                            validation_result=validation_result,
                            reviewer_skill=reviewer_skill,
                        )
                        reviewer_cmd = list(cmd)
                        reviewer_cmd[-1] = reviewer_prompt
                        reviewer_run = _run_codex_once(
                            reviewer_cmd,
                            repo_root=repo_root,
                            env=env,
                            timeout_sec=timeout_sec,
                        )
                        reviewer_output = reviewer_run.get("output", "")
                        try:
                            reviewer_result = parse_reviewer_result(reviewer_output)
                        except Exception as exc:
                            reviewer_result = build_invalid_reviewer_result(
                                reviewer_output,
                                error=f"Reviewer output parsing failed: {exc}",
                            )

                        reviewer_artifact = write_reviewer_artifact(
                            artifact_root,
                            attempt=attempt,
                            reviewer_result=reviewer_result,
                        )
                        reviewer_artifacts.append(reviewer_artifact)
                        reviewer_decision = apply_reviewer_policy(
                            reviewer_result,
                            rejection_count=reviewer_rejection_count,
                            limits=retry_limits,
                        )
                        reviewer_rejection_count = reviewer_decision.rejection_count
                        reviewer_status = reviewer_decision.reviewer_status

                        if reviewer_decision.action == "abort":
                            telemetry = build_telemetry_event(
                                task_id=task_id,
                                session_id=session_id,
                                skill_name=reviewer_skill,
                                duration_ms=int((time.monotonic() - attempt_started) * 1000),
                                validation_result=validation_result,
                                reviewer_status=reviewer_status,
                                final_state=reviewer_decision.final_state,
                                attempt_count=max(retry_state.attempt_count, attempt),
                                same_error_count=retry_state.same_error_count,
                                output_text=output + "\n" + reviewer_output,
                                retry_reason=reviewer_decision.reason,
                                artifact_paths=reviewer_artifacts,
                            )
                            telemetry_jsonl = append_telemetry_event(artifact_root, telemetry)
                            final_telemetry = write_final_telemetry(artifact_root, telemetry)
                            result["error"] = "Independent reviewer blocked the attempt and requested manual intervention."
                            result["metadata"]["artifactRoot"] = str(artifact_root)
                            result["metadata"]["telemetryJsonl"] = telemetry_jsonl
                            result["metadata"]["finalTelemetry"] = final_telemetry
                            result["metadata"]["reviewerResult"] = reviewer_result.to_dict()
                            result["metadata"]["reviewerProfile"] = reviewer_profile.to_dict()
                            return result

                        if reviewer_status == "rejected":
                            telemetry = build_telemetry_event(
                                task_id=task_id,
                                session_id=session_id,
                                skill_name=reviewer_skill,
                                duration_ms=int((time.monotonic() - attempt_started) * 1000),
                                validation_result=validation_result,
                                reviewer_status=reviewer_status,
                                final_state=reviewer_decision.final_state,
                                attempt_count=max(retry_state.attempt_count, attempt),
                                same_error_count=retry_state.same_error_count,
                                output_text=output + "\n" + reviewer_output,
                                retry_reason=reviewer_decision.reason,
                                artifact_paths=reviewer_artifacts,
                            )
                            telemetry_jsonl = append_telemetry_event(artifact_root, telemetry)
                            result["metadata"]["artifactRoot"] = str(artifact_root)
                            result["metadata"]["telemetryJsonl"] = telemetry_jsonl
                            result["metadata"]["reviewerResult"] = reviewer_result.to_dict()
                            result["metadata"]["reviewerProfile"] = reviewer_profile.to_dict()
                            current_prompt += render_reviewer_feedback(reviewer_result, reviewer_decision)
                            last_result = result
                            continue

                    telemetry = build_telemetry_event(
                        task_id=task_id,
                        session_id=session_id,
                        skill_name="skill-suite-orchestrator",
                        duration_ms=int((time.monotonic() - attempt_started) * 1000),
                        validation_result=validation_result,
                        reviewer_status=reviewer_status,
                        final_state="completed",
                        attempt_count=max(retry_state.attempt_count, attempt),
                        same_error_count=retry_state.same_error_count,
                        output_text=output,
                        artifact_paths=reviewer_artifacts,
                    )
                    telemetry_jsonl = append_telemetry_event(artifact_root, telemetry)
                    final_telemetry = write_final_telemetry(artifact_root, telemetry)
                    result["metadata"]["artifactRoot"] = str(artifact_root)
                    result["metadata"]["telemetryJsonl"] = telemetry_jsonl
                    result["metadata"]["finalTelemetry"] = final_telemetry
                    result["metadata"]["reviewerStatus"] = reviewer_status
                    result["metadata"]["reviewerProfile"] = reviewer_profile.to_dict()
                    if validation_result == "validation_missing":
                        result["metadata"]["validation_missing"] = True
                    return result

                last_result = result
            except subprocess.TimeoutExpired as exc:
                partial_stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
                partial_stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
                partial_output = _extract_final_agent_message(partial_stdout)
                telemetry = build_telemetry_event(
                    task_id=task_id,
                    session_id=session_id,
                    skill_name="skill-suite-orchestrator",
                    duration_ms=int((time.monotonic() - attempt_started) * 1000),
                    validation_result="failed",
                    reviewer_status="skipped",
                    final_state="failed",
                    attempt_count=max(retry_state.attempt_count, attempt),
                    same_error_count=retry_state.same_error_count,
                    output_text=partial_output or partial_stdout or partial_stderr,
                    retry_reason="timeout",
                    artifact_paths=[],
                )
                telemetry_jsonl = append_telemetry_event(artifact_root, telemetry)
                final_telemetry = write_final_telemetry(artifact_root, telemetry)
                last_result = {
                    "output": partial_output,
                    "error": f"codex exec timed out after {timeout_sec}s",
                    "metadata": {
                        "stdout": _trim(partial_stdout),
                        "stderr": _trim(partial_stderr),
                        "command": cmd,
                        "attempt": attempt,
                        "artifactRoot": str(artifact_root),
                        "telemetryJsonl": telemetry_jsonl,
                        "finalTelemetry": final_telemetry,
                    },
                }
                if isolated_codex_home:
                    last_result["metadata"]["isolatedCodexHome"] = isolated_codex_home

            if attempt < max_attempts:
                time.sleep(2)

        fallback = last_result or {
            "output": "",
            "error": "codex exec failed without producing output",
            "metadata": {
                "command": cmd,
                "attempt": max_attempts,
                **({"isolatedCodexHome": isolated_codex_home} if isolated_codex_home else {}),
            },
        }
        if "artifactRoot" not in fallback.get("metadata", {}):
            telemetry = build_telemetry_event(
                task_id=task_id,
                session_id=session_id,
                skill_name="skill-suite-orchestrator",
                duration_ms=0,
                validation_result="failed",
                reviewer_status="skipped",
                final_state="failed",
                attempt_count=max(retry_state.attempt_count, max_attempts),
                same_error_count=retry_state.same_error_count,
                output_text=fallback.get("output", "") or fallback.get("error", ""),
                retry_reason="provider_failed",
                artifact_paths=[],
            )
            telemetry_jsonl = append_telemetry_event(artifact_root, telemetry)
            final_telemetry = write_final_telemetry(artifact_root, telemetry)
            fallback.setdefault("metadata", {})
            fallback["metadata"]["artifactRoot"] = str(artifact_root)
            fallback["metadata"]["telemetryJsonl"] = telemetry_jsonl
            fallback["metadata"]["finalTelemetry"] = final_telemetry
        return fallback
    finally:
        if isolated_codex_home:
            shutil.rmtree(isolated_codex_home, ignore_errors=True)


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    print(json.dumps(call_api(prompt, {"config": {"repo_root": os.getcwd()}}, {}), ensure_ascii=False, indent=2))
