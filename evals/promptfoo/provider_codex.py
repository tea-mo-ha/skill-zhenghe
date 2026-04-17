from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

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
    prompt = f"{ROUTING_EVAL_PREAMBLE}\n\n{prompt}"

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
    sandbox_mode = str(config.get("sandbox_mode", "read-only"))
    extra_env_allowlist = list(config.get("env_allowlist", []))
    env_overrides = dict(config.get("env", {}))
    isolate_codex_home = bool(config.get("isolate_codex_home", False))

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
                if isolated_codex_home:
                    result["metadata"]["isolatedCodexHome"] = isolated_codex_home

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
                if isolated_codex_home:
                    last_result["metadata"]["isolatedCodexHome"] = isolated_codex_home

            if attempt < max_attempts:
                time.sleep(2)

        return last_result or {
            "output": "",
            "error": "codex exec failed without producing output",
            "metadata": {
                "command": cmd,
                "attempt": max_attempts,
                **({"isolatedCodexHome": isolated_codex_home} if isolated_codex_home else {}),
            },
        }
    finally:
        if isolated_codex_home:
            shutil.rmtree(isolated_codex_home, ignore_errors=True)


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    print(json.dumps(call_api(prompt, {"config": {"repo_root": os.getcwd()}}, {}), ensure_ascii=False, indent=2))
