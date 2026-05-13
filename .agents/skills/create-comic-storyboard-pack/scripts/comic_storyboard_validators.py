#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


SPATIAL_CONTRACT_VALIDATOR = "spatial_contract"
PHYSICAL_CAUSALITY_VALIDATOR = "physical_causality"
REQUIRED_IMAGE_STAGE_VALIDATORS = (SPATIAL_CONTRACT_VALIDATOR, PHYSICAL_CAUSALITY_VALIDATOR)
VALIDATION_REPORT_VERDICTS = {"pass", "needs_rerun", "reconciled"}
PASSING_VALIDATION_REPORT_VERDICTS = {"pass", "reconciled"}


def as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_runner_module(runner_path: Path):
    spec = importlib.util.spec_from_file_location("_comic_storyboard_runner_for_validation", runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load runner module: {runner_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_checked_artifacts(value: Any, report_dir: Path) -> list[str]:
    artifacts: list[str] = []
    for artifact in as_list(value):
        raw = str(artifact or "").strip()
        if not raw:
            continue
        path = Path(raw)
        if not path.is_absolute():
            path = report_dir / path
        artifacts.append(str(path.resolve(strict=False)))
    return artifacts


def normalize_validation_report(
    report: dict[str, Any],
    *,
    report_path: Path,
    expected_validator: str,
    run_dir: Path,
    page: dict[str, Any],
    stage_id: str,
) -> dict[str, Any]:
    errors = validation_report_errors(
        report,
        report_path=report_path,
        expected_validator=expected_validator,
        run_dir=run_dir,
        page=page,
        stage_id=stage_id,
    )
    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Validation report rejected:\n{details}")
    normalized = dict(report)
    normalized["validator"] = expected_validator
    normalized["run_dir"] = str(run_dir.resolve(strict=False))
    normalized["page_id"] = str(page.get("id") or "")
    normalized["filename"] = str(page.get("filename") or "")
    normalized["stage"] = stage_id
    normalized["verdict"] = str(report.get("verdict") or "")
    normalized["summary"] = str(report.get("summary") or "").strip()
    normalized["issues"] = normalize_report_issues(report.get("issues"))
    normalized["checked_artifacts"] = normalize_checked_artifacts(report.get("checked_artifacts"), report_path.parent)
    normalized["report_path"] = str(report_path.resolve(strict=False))
    if normalized["verdict"] != "reconciled":
        normalized["reconciliation_note"] = str(report.get("reconciliation_note") or "")
    else:
        normalized["reconciliation_note"] = str(report.get("reconciliation_note") or "").strip()
    return normalized


def validation_report_errors(
    report: dict[str, Any],
    *,
    report_path: Path,
    expected_validator: str,
    run_dir: Path,
    page: dict[str, Any],
    stage_id: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report root must be a JSON object."]
    validator = str(report.get("validator") or "").strip()
    if validator != expected_validator:
        errors.append(f"validator must be {expected_validator}, got {validator or '<missing>'}.")
    report_run_dir = str(report.get("run_dir") or "").strip()
    if report_run_dir:
        if Path(report_run_dir).resolve(strict=False) != run_dir.resolve(strict=False):
            errors.append(f"run_dir does not match active run: {report_run_dir}.")
    else:
        errors.append("run_dir is required.")
    page_id = str(report.get("page_id") or "").strip()
    filename = str(report.get("filename") or "").strip()
    if page_id != str(page.get("id") or ""):
        errors.append(f"page_id must be {page.get('id')}, got {page_id or '<missing>'}.")
    if filename != str(page.get("filename") or ""):
        errors.append(f"filename must be {page.get('filename')}, got {filename or '<missing>'}.")
    stage = str(report.get("stage") or "").strip()
    if stage != stage_id:
        errors.append(f"stage must be {stage_id}, got {stage or '<missing>'}.")
    verdict = str(report.get("verdict") or "").strip()
    if verdict not in VALIDATION_REPORT_VERDICTS:
        errors.append(f"verdict must be one of {', '.join(sorted(VALIDATION_REPORT_VERDICTS))}.")
    if not str(report.get("summary") or "").strip():
        errors.append("summary is required.")
    if verdict == "reconciled" and not str(report.get("reconciliation_note") or "").strip():
        errors.append("reconciliation_note is required when verdict is reconciled.")
    if not isinstance(report.get("issues", []), list):
        errors.append("issues must be a list.")
    for issue_index, issue in enumerate(as_list(report.get("issues")), start=1):
        if not isinstance(issue, dict):
            errors.append(f"issues[{issue_index}] must be an object.")
            continue
        if not str(issue.get("id") or "").strip():
            errors.append(f"issues[{issue_index}].id is required.")
        if not str(issue.get("finding") or "").strip():
            errors.append(f"issues[{issue_index}].finding is required.")
    for artifact in normalize_checked_artifacts(report.get("checked_artifacts"), report_path.parent):
        if not Path(artifact).exists():
            errors.append(f"checked_artifact does not exist: {artifact}")
    return errors


def normalize_report_issues(value: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, issue in enumerate(as_list(value), start=1):
        if not isinstance(issue, dict):
            continue
        normalized.append(
            {
                "id": str(issue.get("id") or f"issue-{index}"),
                "severity": str(issue.get("severity") or "error"),
                "panel": issue.get("panel", ""),
                "finding": str(issue.get("finding") or ""),
                "evidence": str(issue.get("evidence") or ""),
                "rerun_required": bool(issue.get("rerun_required", True)),
            }
        )
    return normalized


def report_issue(
    issue_id: str,
    finding: str,
    *,
    panel: Any = "",
    evidence: str = "",
    severity: str = "error",
    rerun_required: bool = True,
) -> dict[str, Any]:
    return {
        "id": issue_id,
        "severity": severity,
        "panel": panel,
        "finding": finding,
        "evidence": evidence,
        "rerun_required": rerun_required,
    }


def report_from_issues(
    *,
    validator: str,
    run_dir: Path,
    page: dict[str, Any],
    stage_id: str,
    issues: list[dict[str, Any]],
    checked_artifacts: list[str],
    summary_prefix: str,
) -> dict[str, Any]:
    verdict = "needs_rerun" if any(issue.get("rerun_required", True) for issue in issues) else "pass"
    return {
        "validator": validator,
        "run_dir": str(run_dir.resolve(strict=False)),
        "page_id": str(page.get("id") or ""),
        "filename": str(page.get("filename") or ""),
        "stage": stage_id,
        "verdict": verdict,
        "summary": f"{summary_prefix}: {len(issues)} issue(s).",
        "issues": normalize_report_issues(issues),
        "checked_artifacts": checked_artifacts,
        "reconciliation_note": "",
    }


def page_panel_count(page: dict[str, Any]) -> int:
    return len(as_list(page.get("panels")))


def panel_number(panel: dict[str, Any], fallback: int) -> int:
    try:
        return int(panel.get("panel_no") or panel.get("order") or fallback)
    except (TypeError, ValueError):
        return fallback


def vector(value: Any, dimensions: int) -> tuple[float, ...] | None:
    if not isinstance(value, list) or len(value) < dimensions:
        return None
    try:
        return tuple(float(value[index]) for index in range(dimensions))
    except (TypeError, ValueError):
        return None


def vector_dot(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    left_len = math.sqrt(sum(item * item for item in left))
    right_len = math.sqrt(sum(item * item for item in right))
    if left_len == 0 or right_len == 0:
        return 0.0
    return sum(left[index] * right[index] for index in range(min(len(left), len(right)))) / (left_len * right_len)


def movement_or_effect_vectors(entity_state: dict[str, Any]) -> tuple[tuple[float, ...] | None, tuple[float, ...] | None]:
    motion = (
        vector(entity_state.get("trajectory_vector"), 3)
        or vector(entity_state.get("motion_vector"), 3)
        or vector(entity_state.get("velocity_vector"), 3)
        or vector(entity_state.get("trajectory_vector"), 2)
        or vector(entity_state.get("motion_vector"), 2)
        or vector(entity_state.get("velocity_vector"), 2)
    )
    effect = (
        vector(entity_state.get("effect_line_vector"), len(motion or []))
        or vector(entity_state.get("force_vector"), len(motion or []))
        or vector(entity_state.get("impact_vector"), len(motion or []))
    )
    return motion, effect


def state_tags(state: dict[str, Any]) -> set[str]:
    tags = {str(tag).strip().lower() for tag in as_list(state.get("state_tags")) if str(tag).strip()}
    for key in ["state", "damage_state", "door_state", "prop_state"]:
        value = str(state.get(key) or "").strip().lower()
        if value:
            tags.add(value)
    return tags


def has_transition_cause(contract: dict[str, Any], entity_id: str, panel: Any) -> bool:
    panel_value = str(panel)
    for transition in as_list(contract.get("transitions")):
        if not isinstance(transition, dict):
            continue
        if entity_id and str(transition.get("entity") or transition.get("entity_id") or "") not in {"", entity_id}:
            continue
        if str(transition.get("to_panel") or transition.get("panel") or "") not in {"", panel_value}:
            continue
        if transition.get("cause") or transition.get("cause_panel") or transition.get("cause_page"):
            return True
    for constraint in as_list(contract.get("constraints")):
        if not isinstance(constraint, dict):
            continue
        constraint_type = str(constraint.get("type") or "")
        if constraint_type not in {"allowed_transition", "requires_cause"}:
            continue
        if entity_id and str(constraint.get("entity") or constraint.get("subject") or constraint.get("object") or "") not in {"", entity_id}:
            continue
        if str(constraint.get("to_panel") or constraint.get("panel") or "") not in {"", panel_value}:
            continue
        if constraint.get("cause") or constraint.get("cause_panel") or constraint.get("cause_page"):
            return True
    return False


def physical_causality_issues_for_page(page: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    contract = page.get("spatial_contract") or {}
    snapshots = [snapshot for snapshot in as_list(contract.get("panel_snapshots")) if isinstance(snapshot, dict)]
    irreversible_tags = {
        "opened",
        "open",
        "broken",
        "damaged",
        "destroyed",
        "injured",
        "wounded",
        "fallen",
        "fell",
        "dropped",
        "transferred",
        "grabbed",
        "released",
    }
    first_effect_panel: dict[str, int] = {}
    first_cause_panel: dict[str, int] = {}
    previous_entity_states: dict[str, dict[str, Any]] = {}
    for index, snapshot in enumerate(snapshots, start=1):
        panel = snapshot.get("panel") or index
        try:
            panel_int = int(panel)
        except (TypeError, ValueError):
            panel_int = index
        for state in as_list(snapshot.get("entities")):
            if not isinstance(state, dict):
                continue
            entity_id = str(state.get("id") or "")
            tags = state_tags(state)
            if tags & {"contact", "impact", "collision", "hit", "push", "pull", "throw", "kick", "shot", "release", "cause"}:
                first_cause_panel.setdefault(entity_id, panel_int)
            if tags & irreversible_tags:
                first_effect_panel.setdefault(entity_id, panel_int)
                if not has_transition_cause(contract, entity_id, panel):
                    prior = previous_entity_states.get(entity_id)
                    prior_tags = state_tags(prior or {})
                    if not (prior_tags & tags):
                        issues.append(
                            report_issue(
                                f"{page.get('id')}-cause-required-{entity_id or 'entity'}-{panel}",
                                "State changes that read as opening, damage, injury, falling, transfer, grab, drop, or release need an approved cause.",
                                panel=panel,
                                evidence=f"entity={entity_id}; state_tags={sorted(tags)}",
                            )
                        )
            motion, effect = movement_or_effect_vectors(state)
            if motion is not None and effect is not None and len(motion) == len(effect):
                dot = vector_dot(motion, effect)
                if dot < 0:
                    issues.append(
                        report_issue(
                            f"{page.get('id')}-opposite-motion-effect-{entity_id or 'entity'}-{panel}",
                            "Motion/effect vectors point in opposite directions.",
                            panel=panel,
                            evidence=f"entity={entity_id}; dot={dot:.3f}",
                        )
                    )
            previous_entity_states[entity_id] = state
    for entity_id, effect_panel in first_effect_panel.items():
        cause_panel = first_cause_panel.get(entity_id)
        if cause_panel is not None and effect_panel < cause_panel:
            issues.append(
                report_issue(
                    f"{page.get('id')}-effect-before-cause-{entity_id or 'entity'}",
                    "A result appears before the contact/impact/action that should cause it.",
                    panel=effect_panel,
                    evidence=f"entity={entity_id}; effect_panel={effect_panel}; cause_panel={cause_panel}",
                )
            )
    return issues


def build_physical_causality_report(
    *,
    runner_path: Path,
    run_dir: Path,
    page_ref: str,
    stage_id: str,
) -> dict[str, Any]:
    runner = load_runner_module(runner_path)
    state = runner.load_state(run_dir)
    page = runner.resolve_page(state, page_ref)
    stage = runner.stage_state(page, stage_id)
    checked_artifacts = [
        str(path)
        for path in [
            Path(stage.get("output_path") or ""),
            Path(stage.get("description_path") or ""),
            run_dir / "approved_storyboard_plan.json",
        ]
        if str(path) and path.exists()
    ]
    return report_from_issues(
        validator=PHYSICAL_CAUSALITY_VALIDATOR,
        run_dir=run_dir,
        page=page,
        stage_id=stage_id,
        issues=physical_causality_issues_for_page(page),
        checked_artifacts=checked_artifacts,
        summary_prefix="physical causality validation",
    )


def build_spatial_contract_report(
    *,
    runner_path: Path,
    run_dir: Path,
    page_ref: str,
    stage_id: str,
) -> dict[str, Any]:
    runner = load_runner_module(runner_path)
    state = runner.load_state(run_dir)
    page = runner.resolve_page(state, page_ref)
    stage = runner.stage_state(page, stage_id)
    issues_text = runner.spatial_plan_issues(state.get("pages", []), state.get("spatial_continuity_plan"))
    page_aliases = {
        str(page.get("id") or ""),
        str(page.get("filename") or ""),
        Path(str(page.get("filename") or "")).stem,
    }
    page_issues = [
        report_issue(
            f"{page.get('id')}-spatial-{index}",
            issue,
            evidence="deterministic spatial plan check",
        )
        for index, issue in enumerate(issues_text, start=1)
        if any(alias and alias in issue for alias in page_aliases)
    ]
    checked_artifacts = [
        str(path)
        for path in [
            Path(stage.get("output_path") or ""),
            Path(stage.get("description_path") or ""),
            run_dir / "approved_storyboard_plan.json",
            run_dir / "spatial_contract_preview.html",
        ]
        if str(path) and path.exists()
    ]
    return report_from_issues(
        validator=SPATIAL_CONTRACT_VALIDATOR,
        run_dir=run_dir,
        page=page,
        stage_id=stage_id,
        issues=page_issues,
        checked_artifacts=checked_artifacts,
        summary_prefix="spatial contract validation",
    )
