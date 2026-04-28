from __future__ import annotations

import json
from pathlib import Path
import sys

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from runtime_control import (
    RetryLimits,
    RetryState,
    append_telemetry_event,
    apply_reviewer_policy,
    apply_retry_policy,
    build_invalid_reviewer_result,
    build_failure_event,
    build_reviewer_prompt,
    build_reviewer_profile,
    build_telemetry_event,
    build_validation_missing_event,
    create_artifact_root,
    normalize_error_excerpt,
    output_claims_validation_passed,
    parse_reviewer_result,
    should_run_reviewer,
    write_reviewer_artifact,
    write_final_telemetry,
)


def test_normalize_error_excerpt_redacts_paths_ids_timestamps_and_line_numbers() -> None:
    raw = (
        "\x1b[31m2026-04-28T12:34:56Z ERROR /Users/mo/work/app/module.py:42:13 "
        "thread 1234567890abcdef request 550e8400-e29b-41d4-a716-446655440000\x1b[0m"
    )

    normalized = normalize_error_excerpt(raw)

    assert "/Users/mo" not in normalized
    assert "2026-04-28" not in normalized
    assert "1234567890abcdef" not in normalized
    assert "550e8400-e29b-41d4-a716-446655440000" not in normalized
    assert "<ABS_PATH>" in normalized
    assert "<ABS_PATH>:<LINE>" in normalized


def test_build_failure_event_extracts_failing_tests_and_artifact(tmp_path: Path) -> None:
    artifact_root = create_artifact_root(tmp_path / "artifacts")
    command_execution = {
        "exit_code": 1,
        "command": "pytest -q",
        "aggregated_output": (
            "FAILED tests/test_runtime_control.py::test_example - AssertionError\n"
            "ERROR tests/test_other.py::test_other - RuntimeError\n"
        ),
    }

    event = build_failure_event(command_execution, artifact_root=artifact_root, attempt=1)

    assert event.event_type == "validation_failed"
    assert event.exit_code == 1
    assert event.failed_command == "pytest -q"
    assert event.failing_tests == [
        "tests/test_runtime_control.py::test_example",
        "tests/test_other.py::test_other",
    ]
    assert len(event.artifact_paths) == 1
    assert Path(event.artifact_paths[0]).is_file()


def test_retry_policy_trips_same_error_circuit_breaker(tmp_path: Path) -> None:
    artifact_root = create_artifact_root(tmp_path / "artifacts")
    state = RetryState()
    limits = RetryLimits(same_error_retry_limit=3, no_progress_limit=99, total_attempt_limit=99)

    event = build_failure_event(
        {
            "exit_code": 1,
            "command": "pytest -q",
            "aggregated_output": "FAILED tests/test_loop.py::test_repeat - AssertionError\n",
        },
        artifact_root=artifact_root,
        attempt=1,
    )

    for _ in range(2):
        state, decision = apply_retry_policy(state, event, limits=limits)
        assert decision.action == "retry"

    state, decision = apply_retry_policy(state, event, limits=limits)
    assert decision.action == "abort"
    assert decision.reason == "same_error_retry_limit"
    assert decision.final_state == "circuit_broken"
    assert state.same_error_count == 3


def test_retry_policy_trips_no_progress_circuit_breaker(tmp_path: Path) -> None:
    artifact_root = create_artifact_root(tmp_path / "artifacts")
    limits = RetryLimits(same_error_retry_limit=99, no_progress_limit=2, total_attempt_limit=99)

    first = build_failure_event(
        {
            "exit_code": 1,
            "command": "pytest -q",
            "aggregated_output": "FAILED tests/test_loop.py::test_one - AssertionError\n",
        },
        artifact_root=artifact_root,
        attempt=1,
    )
    second = build_failure_event(
        {
            "exit_code": 1,
            "command": "pytest -q",
            "aggregated_output": "FAILED tests/test_loop.py::test_two - AssertionError\n",
        },
        artifact_root=artifact_root,
        attempt=2,
    )
    third = build_failure_event(
        {
            "exit_code": 1,
            "command": "pytest -q",
            "aggregated_output": "FAILED tests/test_loop.py::test_three - AssertionError\n",
        },
        artifact_root=artifact_root,
        attempt=3,
    )

    state, decision = apply_retry_policy(RetryState(), first, limits=limits)
    assert decision.action == "retry"

    state, decision = apply_retry_policy(state, second, limits=limits)
    assert decision.action == "retry"
    assert decision.progress_signal == "no_change"

    state, decision = apply_retry_policy(state, third, limits=limits)
    assert decision.action == "abort"
    assert decision.reason == "no_progress_limit"


def test_validation_missing_event_and_detection(tmp_path: Path) -> None:
    artifact_root = create_artifact_root(tmp_path / "artifacts")
    event = build_validation_missing_event(
        artifact_root=artifact_root,
        attempt=1,
        reason="Validation claimed success without tools.",
    )

    output = """validation
- validation_profile_used: Python: pytest+ruff
- commands_run: []
- status: passed
"""

    assert event.event_type == "validation_missing"
    assert output_claims_validation_passed(output) is True


def test_telemetry_writers_emit_jsonl_and_final_summary(tmp_path: Path) -> None:
    artifact_root = create_artifact_root(tmp_path / "artifacts")
    telemetry = build_telemetry_event(
        task_id="task-123",
        session_id="session-123",
        skill_name="skill-suite-orchestrator",
        duration_ms=120,
        validation_result="failed",
        reviewer_status="skipped",
        final_state="circuit_broken",
        attempt_count=3,
        same_error_count=3,
        output_text="sample output",
        error_fingerprint="abc",
        exit_code=1,
        failed_command="pytest -q",
        retry_reason="same_error_retry_limit",
        artifact_paths=["/tmp/example.log"],
    )

    jsonl_path = Path(append_telemetry_event(artifact_root, telemetry))
    final_path = Path(write_final_telemetry(artifact_root, telemetry))

    jsonl_payload = json.loads(jsonl_path.read_text(encoding="utf-8").strip())
    final_payload = json.loads(final_path.read_text(encoding="utf-8"))

    assert jsonl_payload["final_state"] == "circuit_broken"
    assert final_payload["task_id"] == "task-123"
    assert final_payload["artifact_paths"] == ["/tmp/example.log"]


def test_parse_reviewer_result_accepts_fenced_json() -> None:
    raw = """```json
{
  "schema_version": "1.0",
  "status": "rejected",
  "severity": "medium",
  "blocking_issues": ["missing validation evidence"],
  "non_blocking_issues": [],
  "required_changes": ["run pytest"],
  "evidence": ["validation section lacks commands"],
  "confidence": 0.82
}
```"""

    result = parse_reviewer_result(raw)

    assert result.status == "rejected"
    assert result.severity == "medium"
    assert result.blocking_issues == ["missing validation evidence"]
    assert result.confidence == 0.82


def test_invalid_reviewer_result_is_structured_rejection() -> None:
    result = build_invalid_reviewer_result("not json", "Reviewer output parsing failed")

    assert result.status == "rejected"
    assert result.severity == "high"
    assert result.blocking_issues == ["reviewer_output_invalid"]
    assert result.required_changes == ["Reviewer output parsing failed"]


def test_reviewer_policy_retries_then_manual_intervention() -> None:
    medium_rejection = parse_reviewer_result(
        json.dumps(
            {
                "schema_version": "1.0",
                "status": "rejected",
                "severity": "medium",
                "blocking_issues": ["needs more evidence"],
                "non_blocking_issues": [],
                "required_changes": ["add reviewer evidence"],
                "evidence": [],
                "confidence": 0.6,
            }
        )
    )
    critical_rejection = parse_reviewer_result(
        json.dumps(
            {
                "schema_version": "1.0",
                "status": "rejected",
                "severity": "critical",
                "blocking_issues": ["security breach"],
                "non_blocking_issues": [],
                "required_changes": ["manual review"],
                "evidence": [],
                "confidence": 0.9,
            }
        )
    )

    retry_decision = apply_reviewer_policy(
        medium_rejection,
        rejection_count=0,
        limits=RetryLimits(reviewer_rejection_limit=2),
    )
    abort_decision = apply_reviewer_policy(
        critical_rejection,
        rejection_count=0,
        limits=RetryLimits(reviewer_rejection_limit=2),
    )
    second_abort = apply_reviewer_policy(
        medium_rejection,
        rejection_count=1,
        limits=RetryLimits(reviewer_rejection_limit=2),
    )

    assert retry_decision.action == "retry"
    assert retry_decision.final_state == "failed"
    assert abort_decision.action == "abort"
    assert abort_decision.final_state == "manual_intervention_required"
    assert second_abort.action == "abort"


def test_reviewer_helpers_match_patterns_and_write_artifact(tmp_path: Path) -> None:
    assert should_run_reviewer(
        "请检查这个安全上线方案",
        reviewer_enabled=True,
        reviewer_required_patterns=[r"安全", r"上线"],
    )
    assert not should_run_reviewer(
        "普通文档修订",
        reviewer_enabled=True,
        reviewer_required_patterns=[r"安全", r"上线"],
    )

    prompt = build_reviewer_prompt(
        task_prompt="审核这个上线任务",
        candidate_output="validation\n- status: passed",
        validation_result="passed",
        reviewer_skill="agency-security-engineer",
    )
    assert "agency-security-engineer" in prompt
    assert "JSON only" in prompt

    artifact_root = create_artifact_root(tmp_path / "artifacts")
    result = parse_reviewer_result(
        json.dumps(
            {
                "schema_version": "1.0",
                "status": "approved",
                "severity": "low",
                "blocking_issues": [],
                "non_blocking_issues": [],
                "required_changes": [],
                "evidence": ["validation commands present"],
                "confidence": 0.7,
            }
        )
    )
    artifact_path = Path(write_reviewer_artifact(artifact_root, attempt=2, reviewer_result=result))
    assert artifact_path.is_file()


def test_reviewer_profile_auto_routes_high_risk_tasks() -> None:
    security_profile = build_reviewer_profile("请检查这个 auth token 处理是否安全")
    launch_profile = build_reviewer_profile("准备 production deploy 和回滚方案")
    low_profile = build_reviewer_profile("整理 README 的文字说明")

    assert security_profile.reviewer_required is True
    assert security_profile.risk_level == "critical"
    assert security_profile.reviewer_skill == "security-and-hardening"
    assert "secret handling" in security_profile.reasons

    assert launch_profile.reviewer_required is True
    assert launch_profile.risk_level == "high"
    assert launch_profile.reviewer_skill == "shipping-and-launch"

    assert low_profile.reviewer_required is False
    assert low_profile.risk_level == "low"


def test_reviewer_profile_keeps_configuration_overrides() -> None:
    disabled = build_reviewer_profile("上线生产环境", reviewer_enabled=False)
    forced = build_reviewer_profile("普通文案", reviewer_always=True, reviewer_skill="code-review-and-quality")
    configured = build_reviewer_profile(
        "普通文案但是命中自定义",
        reviewer_required_patterns=[r"自定义"],
        reviewer_skill="security-and-hardening",
    )

    assert disabled.reviewer_required is False
    assert disabled.source == "disabled"
    assert forced.reviewer_required is True
    assert forced.source == "forced"
    assert configured.reviewer_required is True
    assert configured.source == "configured_patterns"
    assert configured.reviewer_skill == "security-and-hardening"
