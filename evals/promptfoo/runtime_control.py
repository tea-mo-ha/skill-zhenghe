from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

SCHEMA_VERSION = "1.0"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
UNIX_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:[^/\s:]+/)+[^/\s:]+")
WINDOWS_PATH_RE = re.compile(r"\b[A-Za-z]:\\(?:[^\\\s:]+\\)+[^\\\s:]+")
TIMESTAMP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?\b"
)
TIME_ONLY_RE = re.compile(r"\b\d{2}:\d{2}:\d{2}(?:\.\d+)?\b")
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")
LONG_ID_RE = re.compile(r"\b[a-f0-9]{12,}\b", re.IGNORECASE)
LINE_NUMBER_RE = re.compile(r"([A-Za-z0-9_./\\-]+\.[A-Za-z0-9]+):\d+(?::\d+)?")
PYTEST_FAIL_RE = re.compile(r"^(?:FAILED|ERROR|FAIL)\s+([^\s]+)", re.MULTILINE)
NODEID_RE = re.compile(r"\b([A-Za-z0-9_./-]+::[A-Za-z0-9_./\[\]-]+)\b")


ProgressSignal = Literal["improved", "no_change", "regressed"]
RetryAction = Literal["retry", "abort"]
FinalState = Literal["completed", "failed", "circuit_broken", "manual_intervention_required"]
ReviewerStatus = Literal["skipped", "approved", "rejected"]
ValidationResult = Literal["passed", "failed", "validation_missing"]
ReviewSeverity = Literal["low", "medium", "high", "critical"]
RiskLevel = Literal["low", "medium", "high", "critical"]

DEFAULT_REVIEWER_PATTERNS: tuple[tuple[str, RiskLevel, str, str], ...] = (
    (r"\b(api[_ -]?key|secret|token|password|private[_ -]?key)\b|密钥|令牌", "critical", "security-and-hardening", "secret handling"),
    (r"\b(auth|oauth|jwt|permission|rbac|login|session)\b|鉴权|权限|登录|认证", "high", "security-and-hardening", "auth or permission boundary"),
    (r"\b(security|vulnerab(?:le|ility)|xss|csrf|sql injection)\b|安全|漏洞", "high", "security-and-hardening", "security-sensitive task"),
    (r"\b(prod|production|deploy(?:ment)?|release|rollback|rollout)\b|上线|发布|回滚|灰度", "high", "shipping-and-launch", "production delivery task"),
    (r"\b(payment|billing|stripe|invoice)\b|支付|账单|计费", "high", "security-and-hardening", "payment or billing task"),
    (r"\b(delete|destructive|migration|migrate)\b|删除|破坏性|迁移", "medium", "code-review-and-quality", "destructive or migration-sensitive task"),
)


@dataclass(frozen=True)
class FailureEvent:
    event_type: str
    exit_code: int | None
    failed_command: str
    normalized_error_excerpt: str
    failing_tests: list[str] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProgressMetrics:
    failing_test_count: int
    error_line_count: int


@dataclass(frozen=True)
class RetryLimits:
    same_error_retry_limit: int = 3
    no_progress_limit: int = 2
    total_attempt_limit: int = 5
    reviewer_rejection_limit: int = 2


@dataclass(frozen=True)
class RetryState:
    attempt_count: int = 0
    same_error_count: int = 0
    no_progress_count: int = 0
    last_error_fingerprint: str | None = None
    last_progress_metrics: ProgressMetrics | None = None


@dataclass(frozen=True)
class RetryDecision:
    action: RetryAction
    reason: str
    progress_signal: ProgressSignal
    error_fingerprint: str
    attempt_count: int
    same_error_count: int
    no_progress_count: int
    final_state: FinalState


@dataclass(frozen=True)
class TelemetryEvent:
    schema_version: str
    task_id: str
    session_id: str
    skill_name: str
    duration_ms: int
    token_estimate: int
    validation_result: ValidationResult
    reviewer_status: ReviewerStatus
    final_state: FinalState
    attempt_count: int
    same_error_count: int
    error_fingerprint: str | None = None
    exit_code: int | None = None
    failed_command: str | None = None
    retry_reason: str | None = None
    artifact_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewerResult:
    schema_version: str
    status: ReviewerStatus
    severity: ReviewSeverity
    blocking_issues: list[str] = field(default_factory=list)
    non_blocking_issues: list[str] = field(default_factory=list)
    required_changes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewerPolicyDecision:
    action: RetryAction
    reviewer_status: ReviewerStatus
    final_state: FinalState
    rejection_count: int
    reason: str


@dataclass(frozen=True)
class ReviewerProfile:
    reviewer_required: bool
    risk_level: RiskLevel
    reviewer_skill: str
    reasons: list[str] = field(default_factory=list)
    matched_patterns: list[str] = field(default_factory=list)
    source: str = "auto"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_artifact_root(base_dir: str | os.PathLike[str] | None = None) -> Path:
    if base_dir:
        root = Path(base_dir)
        root.mkdir(parents=True, exist_ok=True)
        return root
    return Path(tempfile.mkdtemp(prefix="skill-zhenghe-telemetry-"))


def build_task_id(prompt: str) -> str:
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"task-{digest[:12]}"


def build_session_id() -> str:
    return f"session-{int(time.time() * 1000)}"


def estimate_tokens(*chunks: str) -> int:
    total_chars = sum(len(chunk or "") for chunk in chunks)
    return max(1, total_chars // 4)


def should_run_reviewer(
    prompt: str,
    *,
    reviewer_enabled: bool,
    reviewer_always: bool = False,
    reviewer_required_patterns: list[str] | None = None,
) -> bool:
    return build_reviewer_profile(
        prompt,
        reviewer_enabled=reviewer_enabled,
        reviewer_always=reviewer_always,
        reviewer_required_patterns=reviewer_required_patterns,
    ).reviewer_required


def build_reviewer_profile(
    prompt: str,
    *,
    reviewer_enabled: bool = True,
    reviewer_always: bool = False,
    reviewer_required_patterns: list[str] | None = None,
    reviewer_skill: str | None = None,
) -> ReviewerProfile:
    if not reviewer_enabled:
        return ReviewerProfile(
            reviewer_required=False,
            risk_level="low",
            reviewer_skill=reviewer_skill or "code-review-and-quality",
            source="disabled",
        )

    if reviewer_always:
        return ReviewerProfile(
            reviewer_required=True,
            risk_level="high",
            reviewer_skill=reviewer_skill or "code-review-and-quality",
            reasons=["forced by configuration"],
            source="forced",
        )

    if reviewer_required_patterns:
        matched = [pattern for pattern in reviewer_required_patterns if re.search(pattern, prompt, re.IGNORECASE)]
        if matched:
            return ReviewerProfile(
                reviewer_required=True,
                risk_level="high",
                reviewer_skill=reviewer_skill or "code-review-and-quality",
                reasons=["matched configured reviewer pattern"],
                matched_patterns=matched,
                source="configured_patterns",
            )

    matched_rules: list[tuple[str, RiskLevel, str, str]] = [
        rule for rule in DEFAULT_REVIEWER_PATTERNS if re.search(rule[0], prompt, re.IGNORECASE)
    ]
    if not matched_rules:
        return ReviewerProfile(
            reviewer_required=False,
            risk_level="low",
            reviewer_skill=reviewer_skill or "code-review-and-quality",
        )

    strongest = max(matched_rules, key=lambda rule: _risk_rank(rule[1]))
    selected_skill = reviewer_skill or strongest[2]
    reasons = []
    matched_patterns = []
    for pattern, _risk, _skill, reason in matched_rules:
        if reason not in reasons:
            reasons.append(reason)
        matched_patterns.append(pattern)

    return ReviewerProfile(
        reviewer_required=True,
        risk_level=strongest[1],
        reviewer_skill=selected_skill,
        reasons=reasons,
        matched_patterns=matched_patterns,
    )


def normalize_error_excerpt(text: str, *, max_lines: int = 20, max_chars: int = 2000) -> str:
    cleaned = ANSI_RE.sub("", text or "")
    lines: list[str] = []

    for raw_line in cleaned.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue

        line = LINE_NUMBER_RE.sub(r"\1:<LINE>", line)
        line = UNIX_PATH_RE.sub("<ABS_PATH>", line)
        line = WINDOWS_PATH_RE.sub("<ABS_PATH>", line)
        line = TIMESTAMP_RE.sub("<TIMESTAMP>", line)
        line = TIME_ONLY_RE.sub("<TIME>", line)
        line = UUID_RE.sub("<ID>", line)
        line = LONG_ID_RE.sub("<ID>", line)
        lines.append(line.strip())

        if len(lines) >= max_lines:
            break

    result = "\n".join(lines)
    if len(result) > max_chars:
        result = result[:max_chars].rstrip()
    return result


def extract_failing_tests(text: str) -> list[str]:
    cleaned = ANSI_RE.sub("", text or "")
    found: list[str] = []

    for regex in (PYTEST_FAIL_RE, NODEID_RE):
        for match in regex.finditer(cleaned):
            candidate = match.group(1).strip()
            if "::" not in candidate:
                continue
            if candidate not in found:
                found.append(candidate)

    return found


def write_validation_artifact(
    artifact_root: Path,
    *,
    attempt: int,
    event_type: str,
    body: str,
) -> str:
    path = artifact_root / f"attempt-{attempt:02d}-{event_type}.log"
    path.write_text(body or "", encoding="utf-8")
    return str(path)


def write_reviewer_artifact(
    artifact_root: Path,
    *,
    attempt: int,
    reviewer_result: ReviewerResult,
) -> str:
    path = artifact_root / f"attempt-{attempt:02d}-reviewer.json"
    path.write_text(json.dumps(reviewer_result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path)


def build_failure_event(
    command_execution: dict[str, Any],
    *,
    artifact_root: Path,
    attempt: int,
) -> FailureEvent:
    raw_output = str(command_execution.get("aggregated_output", "") or "")
    normalized = normalize_error_excerpt(raw_output)
    artifact_path = write_validation_artifact(
        artifact_root,
        attempt=attempt,
        event_type="validation-failed",
        body=raw_output,
    )
    return FailureEvent(
        event_type="validation_failed",
        exit_code=_coerce_int(command_execution.get("exit_code")),
        failed_command=str(command_execution.get("command", "") or ""),
        normalized_error_excerpt=normalized,
        failing_tests=extract_failing_tests(raw_output),
        artifact_paths=[artifact_path],
    )


def build_validation_missing_event(
    *,
    artifact_root: Path,
    attempt: int,
    reason: str,
) -> FailureEvent:
    artifact_path = write_validation_artifact(
        artifact_root,
        attempt=attempt,
        event_type="validation-missing",
        body=reason,
    )
    return FailureEvent(
        event_type="validation_missing",
        exit_code=None,
        failed_command="",
        normalized_error_excerpt=normalize_error_excerpt(reason),
        failing_tests=[],
        artifact_paths=[artifact_path],
    )


def parse_reviewer_result(text: str) -> ReviewerResult:
    payload = _extract_first_json_object(text)

    schema_version = str(payload.get("schema_version", ""))
    status = str(payload.get("status", ""))
    severity = str(payload.get("severity", ""))
    confidence = payload.get("confidence", 0.0)

    if schema_version != SCHEMA_VERSION:
        raise ValueError(f"Unsupported reviewer schema_version: {schema_version!r}")
    if status not in {"approved", "rejected"}:
        raise ValueError(f"Invalid reviewer status: {status!r}")
    if severity not in {"low", "medium", "high", "critical"}:
        raise ValueError(f"Invalid reviewer severity: {severity!r}")
    if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
        raise ValueError(f"Invalid reviewer confidence: {confidence!r}")

    return ReviewerResult(
        schema_version=schema_version,
        status=status,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        blocking_issues=_string_list(payload.get("blocking_issues", []), "blocking_issues"),
        non_blocking_issues=_string_list(payload.get("non_blocking_issues", []), "non_blocking_issues"),
        required_changes=_string_list(payload.get("required_changes", []), "required_changes"),
        evidence=_string_list(payload.get("evidence", []), "evidence"),
        confidence=float(confidence),
    )


def build_invalid_reviewer_result(raw_text: str, error: str) -> ReviewerResult:
    excerpt = normalize_error_excerpt(raw_text or error, max_lines=10, max_chars=500)
    return ReviewerResult(
        schema_version=SCHEMA_VERSION,
        status="rejected",
        severity="high",
        blocking_issues=["reviewer_output_invalid"],
        non_blocking_issues=[],
        required_changes=[error],
        evidence=[excerpt] if excerpt else [],
        confidence=0.0,
    )


def build_error_fingerprint(failure_event: FailureEvent) -> str:
    payload = {
        "event_type": failure_event.event_type,
        "exit_code": failure_event.exit_code,
        "failed_command": failure_event.failed_command,
        "normalized_error_excerpt": failure_event.normalized_error_excerpt,
        "failing_tests": failure_event.failing_tests,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return digest.hexdigest()


def progress_metrics_for_failure(failure_event: FailureEvent) -> ProgressMetrics:
    error_line_count = len(
        [line for line in failure_event.normalized_error_excerpt.splitlines() if line.strip()]
    )
    return ProgressMetrics(
        failing_test_count=len(failure_event.failing_tests),
        error_line_count=error_line_count,
    )


def compare_progress(
    previous: ProgressMetrics | None,
    current: ProgressMetrics,
    *,
    same_error: bool,
) -> ProgressSignal:
    if previous is None:
        return "improved"

    if current.failing_test_count < previous.failing_test_count:
        return "improved"
    if current.failing_test_count > previous.failing_test_count:
        return "regressed"
    if current.error_line_count < previous.error_line_count:
        return "improved"
    if current.error_line_count > previous.error_line_count:
        return "regressed"
    if same_error:
        return "no_change"
    return "no_change"


def apply_retry_policy(
    state: RetryState,
    failure_event: FailureEvent,
    *,
    limits: RetryLimits,
) -> tuple[RetryState, RetryDecision]:
    fingerprint = build_error_fingerprint(failure_event)
    same_error = fingerprint == state.last_error_fingerprint
    same_error_count = state.same_error_count + 1 if same_error else 1
    attempt_count = state.attempt_count + 1
    current_metrics = progress_metrics_for_failure(failure_event)
    progress_signal = compare_progress(
        state.last_progress_metrics,
        current_metrics,
        same_error=same_error,
    )
    no_progress_count = (
        state.no_progress_count + 1 if progress_signal in ("no_change", "regressed") else 0
    )

    next_state = RetryState(
        attempt_count=attempt_count,
        same_error_count=same_error_count,
        no_progress_count=no_progress_count,
        last_error_fingerprint=fingerprint,
        last_progress_metrics=current_metrics,
    )

    if same_error_count >= limits.same_error_retry_limit:
        return next_state, RetryDecision(
            action="abort",
            reason="same_error_retry_limit",
            progress_signal=progress_signal,
            error_fingerprint=fingerprint,
            attempt_count=attempt_count,
            same_error_count=same_error_count,
            no_progress_count=no_progress_count,
            final_state="circuit_broken",
        )

    if no_progress_count >= limits.no_progress_limit:
        return next_state, RetryDecision(
            action="abort",
            reason="no_progress_limit",
            progress_signal=progress_signal,
            error_fingerprint=fingerprint,
            attempt_count=attempt_count,
            same_error_count=same_error_count,
            no_progress_count=no_progress_count,
            final_state="circuit_broken",
        )

    if attempt_count >= limits.total_attempt_limit:
        return next_state, RetryDecision(
            action="abort",
            reason="total_attempt_limit",
            progress_signal=progress_signal,
            error_fingerprint=fingerprint,
            attempt_count=attempt_count,
            same_error_count=same_error_count,
            no_progress_count=no_progress_count,
            final_state="circuit_broken",
        )

    return next_state, RetryDecision(
        action="retry",
        reason="retry_allowed",
        progress_signal=progress_signal,
        error_fingerprint=fingerprint,
        attempt_count=attempt_count,
        same_error_count=same_error_count,
        no_progress_count=no_progress_count,
        final_state="failed",
    )


def apply_reviewer_policy(
    reviewer_result: ReviewerResult,
    *,
    rejection_count: int,
    limits: RetryLimits,
) -> ReviewerPolicyDecision:
    if reviewer_result.status == "approved":
        return ReviewerPolicyDecision(
            action="retry",
            reviewer_status="approved",
            final_state="completed",
            rejection_count=rejection_count,
            reason="reviewer_approved",
        )

    next_rejection_count = rejection_count + 1
    should_abort = (
        next_rejection_count >= limits.reviewer_rejection_limit
        or reviewer_result.severity in {"high", "critical"}
    )
    return ReviewerPolicyDecision(
        action="abort" if should_abort else "retry",
        reviewer_status="rejected",
        final_state="manual_intervention_required" if should_abort else "failed",
        rejection_count=next_rejection_count,
        reason="reviewer_rejected",
    )


def append_telemetry_event(artifact_root: Path, telemetry: TelemetryEvent) -> str:
    path = artifact_root / "telemetry.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(telemetry.to_dict(), ensure_ascii=False) + "\n")
    return str(path)


def write_final_telemetry(artifact_root: Path, telemetry: TelemetryEvent) -> str:
    path = artifact_root / "agent-telemetry.json"
    path.write_text(json.dumps(telemetry.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path)


def build_telemetry_event(
    *,
    task_id: str,
    session_id: str,
    skill_name: str,
    duration_ms: int,
    validation_result: ValidationResult,
    reviewer_status: ReviewerStatus,
    final_state: FinalState,
    attempt_count: int,
    same_error_count: int,
    output_text: str,
    error_fingerprint: str | None = None,
    exit_code: int | None = None,
    failed_command: str | None = None,
    retry_reason: str | None = None,
    artifact_paths: list[str] | None = None,
) -> TelemetryEvent:
    return TelemetryEvent(
        schema_version=SCHEMA_VERSION,
        task_id=task_id,
        session_id=session_id,
        skill_name=skill_name,
        duration_ms=max(0, duration_ms),
        token_estimate=estimate_tokens(output_text),
        validation_result=validation_result,
        reviewer_status=reviewer_status,
        final_state=final_state,
        attempt_count=attempt_count,
        same_error_count=same_error_count,
        error_fingerprint=error_fingerprint,
        exit_code=exit_code,
        failed_command=failed_command,
        retry_reason=retry_reason,
        artifact_paths=artifact_paths or [],
    )


def output_claims_validation_passed(output: str) -> bool:
    if not output:
        return False
    match = re.search(r"(?ms)^validation\s*\n(?P<body>.*?)(?:^\w[\w_-]*\s*$|\Z)", output)
    if not match:
        return False
    return re.search(r"(?mi)^\s*-\s*status:\s*passed\b", match.group("body")) is not None


def render_retry_feedback(failure_event: FailureEvent, retry_decision: RetryDecision) -> str:
    payload = failure_event.to_dict() | {
        "error_fingerprint": retry_decision.error_fingerprint,
        "same_error_count": retry_decision.same_error_count,
        "progress_signal": retry_decision.progress_signal,
        "retry_reason": retry_decision.reason,
    }
    return (
        "\n\n[Orchestrator Feedback] A validation event requires another pass:\n"
        f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```\n"
        "You MUST address this issue, keep the validation output compact, and update telemetry."
    )


def build_reviewer_prompt(
    *,
    task_prompt: str,
    candidate_output: str,
    validation_result: ValidationResult,
    reviewer_skill: str,
) -> str:
    return (
        "You are an independent reviewer in a runtime control layer.\n"
        f"Use the policy of `{reviewer_skill}` as the review persona.\n"
        "Review the candidate output and respond with JSON only. No markdown fences.\n"
        "Required schema:\n"
        '{'
        '"schema_version":"1.0",'
        '"status":"approved|rejected",'
        '"severity":"low|medium|high|critical",'
        '"blocking_issues":[],'
        '"non_blocking_issues":[],'
        '"required_changes":[],'
        '"evidence":[],'
        '"confidence":0.0'
        "}\n\n"
        f"Original task:\n{task_prompt}\n\n"
        f"Validation result: {validation_result}\n\n"
        f"Candidate output:\n{candidate_output}\n"
    )


def render_reviewer_feedback(
    reviewer_result: ReviewerResult,
    reviewer_decision: ReviewerPolicyDecision,
) -> str:
    payload = reviewer_result.to_dict() | {
        "reviewer_reason": reviewer_decision.reason,
        "reviewer_rejection_count": reviewer_decision.rejection_count,
    }
    return (
        "\n\n[Reviewer Feedback] An independent reviewer rejected the last attempt:\n"
        f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```\n"
        "You MUST address the blocking issues, keep validation evidence concrete, and update telemetry."
    )


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list[str]")
    return list(value)


def _extract_first_json_object(text: str) -> dict[str, Any]:
    candidate = (text or "").strip()
    if not candidate:
        raise ValueError("Reviewer output is empty")

    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)
    else:
        object_match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if object_match:
            candidate = object_match.group(0)

    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("Reviewer output must decode to a JSON object")
    return parsed


def _risk_rank(risk_level: RiskLevel) -> int:
    return {
        "low": 0,
        "medium": 1,
        "high": 2,
        "critical": 3,
    }[risk_level]
