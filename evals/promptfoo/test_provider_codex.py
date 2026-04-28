from __future__ import annotations

from pathlib import Path
import sys

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import provider_codex


def test_call_api_retries_after_reviewer_rejection(monkeypatch, tmp_path: Path) -> None:
    outputs = [
        {
            "output": "validation\n- validation_profile_used: Python: pytest\n- commands_run: [`pytest -q`]\n- status: passed\n",
            "metadata": {
                "stdout": '{"type":"item.completed","item":{"type":"command_execution","exit_code":0,"command":"pytest -q","aggregated_output":"ok"}}\n',
                "stderr": "",
                "command": ["codex", "exec"],
                "exitCode": 0,
            },
        },
        {
            "output": (
                '{"schema_version":"1.0","status":"rejected","severity":"medium",'
                '"blocking_issues":["needs evidence"],"non_blocking_issues":[],'
                '"required_changes":["show reviewer-safe validation"],"evidence":[],'
                '"confidence":0.7}'
            ),
            "metadata": {"stdout": "", "stderr": "", "command": ["codex", "exec"], "exitCode": 0},
        },
        {
            "output": "validation\n- validation_profile_used: Python: pytest\n- commands_run: [`pytest -q`]\n- status: passed\n",
            "metadata": {
                "stdout": '{"type":"item.completed","item":{"type":"command_execution","exit_code":0,"command":"pytest -q","aggregated_output":"ok"}}\n',
                "stderr": "",
                "command": ["codex", "exec"],
                "exitCode": 0,
            },
        },
        {
            "output": (
                '{"schema_version":"1.0","status":"approved","severity":"low",'
                '"blocking_issues":[],"non_blocking_issues":[],"required_changes":[],'
                '"evidence":["pytest ran"],"confidence":0.8}'
            ),
            "metadata": {"stdout": "", "stderr": "", "command": ["codex", "exec"], "exitCode": 0},
        },
    ]

    calls: list[str] = []

    def fake_run(cmd, *, repo_root, env, timeout_sec):
        calls.append(cmd[-1])
        return outputs.pop(0)

    monkeypatch.setattr(provider_codex, "_run_codex_once", fake_run)

    result = provider_codex.call_api(
        "请安全上线这个任务",
        {
            "config": {
                "repo_root": str(tmp_path),
                "max_attempts": 2,
                "artifact_root": str(tmp_path / "artifacts"),
                "isolate_codex_home": False,
            }
        },
        {},
    )

    assert "error" not in result
    assert result["metadata"]["reviewerStatus"] == "approved"
    assert result["metadata"]["reviewerProfile"]["reviewer_required"] is True
    assert result["metadata"]["reviewerProfile"]["reviewer_skill"] == "security-and-hardening"
    assert len(calls) == 4
    assert "[Reviewer Feedback]" in calls[2]
    assert Path(result["metadata"]["finalTelemetry"]).is_file()


def test_call_api_skips_reviewer_for_low_risk_task(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_run(cmd, *, repo_root, env, timeout_sec):
        calls.append(cmd[-1])
        return {
            "output": "validation\n- validation_profile_used: Python: pytest\n- commands_run: [`pytest -q`]\n- status: passed\n",
            "metadata": {
                "stdout": '{"type":"item.completed","item":{"type":"command_execution","exit_code":0,"command":"pytest -q","aggregated_output":"ok"}}\n',
                "stderr": "",
                "command": ["codex", "exec"],
                "exitCode": 0,
            },
        }

    monkeypatch.setattr(provider_codex, "_run_codex_once", fake_run)

    result = provider_codex.call_api(
        "整理 README 文案",
        {
            "config": {
                "repo_root": str(tmp_path),
                "max_attempts": 2,
                "artifact_root": str(tmp_path / "artifacts"),
                "isolate_codex_home": False,
            }
        },
        {},
    )

    assert result["metadata"]["reviewerStatus"] == "skipped"
    assert result["metadata"]["reviewerProfile"]["reviewer_required"] is False
    assert len(calls) == 1
