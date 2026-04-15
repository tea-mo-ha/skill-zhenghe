from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any


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

    repo_root = config.get("repo_root", os.getcwd())
    timeout_sec = int(config.get("timeout_sec", 240))
    max_attempts = int(config.get("max_attempts", 2))
    codex_bin = config.get("codex_bin", "codex")
    model = config.get("model")
    model_reasoning_effort = config.get("model_reasoning_effort", "low")
    profile = config.get("profile")
    search = bool(config.get("search", False))
    disable_features = list(config.get("disable_features", ["plugins"]))
    add_dirs = list(config.get("add_dirs", []))
    env_overrides = dict(config.get("env", {}))

    cmd = [
        codex_bin,
        "exec",
        "--cd",
        repo_root,
        "--sandbox",
        "workspace-write",
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

    env = os.environ.copy()
    for key, value in env_overrides.items():
        env[str(key)] = str(value)

    last_result: dict[str, Any] | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = _run_codex_once(
                cmd,
                repo_root=repo_root,
                env=env,
                timeout_sec=timeout_sec,
            )
            result.setdefault("metadata", {})
            result["metadata"]["attempt"] = attempt

            if result.get("output"):
                return result

            last_result = result
        except subprocess.TimeoutExpired as exc:
            partial_stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            partial_stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            partial_output = _extract_final_agent_message(partial_stdout)
            last_result = {
                "output": partial_output,
                "error": f"codex exec timed out after {timeout_sec}s",
                "metadata": {
                    "stdout": _trim(partial_stdout),
                    "stderr": _trim(partial_stderr),
                    "command": cmd,
                    "attempt": attempt,
                },
            }

        if attempt < max_attempts:
            time.sleep(2)

    return last_result or {
        "output": "",
        "error": "codex exec failed without producing output",
        "metadata": {
            "command": cmd,
            "attempt": max_attempts,
        },
    }


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    print(json.dumps(call_api(prompt, {"config": {"repo_root": os.getcwd()}}, {}), ensure_ascii=False, indent=2))
