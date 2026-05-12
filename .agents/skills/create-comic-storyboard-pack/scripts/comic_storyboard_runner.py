#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


WORKFLOW = "create-comic-storyboard-pack"
REPO_ROOT = Path("/Users/chasoik/Projects/character-sheet-generator")
DEFAULT_SOURCE_ROOT = REPO_ROOT / "sources"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "output"
PAGE_GENERATION_MODE_SEQUENTIAL_PRIOR_PAGES = "sequential_prior_pages"
PAGE_GENERATION_MODE_PARALLEL_BATCH = "parallel_batch"
PAGE_GENERATION_MODE_VALUES = {
    PAGE_GENERATION_MODE_SEQUENTIAL_PRIOR_PAGES,
    PAGE_GENERATION_MODE_PARALLEL_BATCH,
}
STORYBOARD_CONTI_SKETCH_INK_STAGE = "storyboard_conti_sketch_ink"
FINISH_STAGE = "finish"
TEXT_POLICY_DIALOGUE_SFX_CAPTIONS = "dialogue_sfx_captions"
TEXT_POLICY_SFX_ONLY = "sfx_only"
TEXT_POLICY_TEXT_FREE = "text_free"
TEXT_POLICY_VALUES = {
    TEXT_POLICY_DIALOGUE_SFX_CAPTIONS,
    TEXT_POLICY_SFX_ONLY,
    TEXT_POLICY_TEXT_FREE,
}
STAGES = [
    {
        "id": STORYBOARD_CONTI_SKETCH_INK_STAGE,
        "label": "conti/sketch/light ink",
        "dir": "01_storyboard_conti_sketch_ink",
        "purpose": "comic-page conti, rough sketch, and light clean line pass with spatial validation description",
    },
    {
        "id": FINISH_STAGE,
        "label": "tone/color/finish",
        "dir": "02_finish",
        "purpose": "tone, color, policy-approved lettering/text absence, and final polish pass",
    },
]
STAGE_IDS = [stage["id"] for stage in STAGES]
STAGE_SKILL_NAMES = {
    STORYBOARD_CONTI_SKETCH_INK_STAGE: "create-comic-storyboard-sketch-ink",
    FINISH_STAGE: "create-comic-storyboard-finish",
}
STAGE_GATE_STATUSES = {"pending", "pending_user_feedback", "approved", "stopped"}
FEEDBACK_CHOICE_APPROVE_FINISH = "approve_finish"
FEEDBACK_CHOICE_OPEN_OVERLAY_UI = "open_overlay_ui"
FEEDBACK_CHOICE_STOP_AFTER_STAGE = "stop_after_stage"
FEEDBACK_CHOICES = {
    FEEDBACK_CHOICE_APPROVE_FINISH,
    FEEDBACK_CHOICE_OPEN_OVERLAY_UI,
    FEEDBACK_CHOICE_STOP_AFTER_STAGE,
}
TRANSITIONS = [
    {
        "from_stage": STORYBOARD_CONTI_SKETCH_INK_STAGE,
        "to_stage": FINISH_STAGE,
        "approve_choice": FEEDBACK_CHOICE_APPROVE_FINISH,
        "approve_label": "Approve finish stage",
        "approve_note_placeholder": "<user approved finish>",
        "pending_note": "storyboard_conti_sketch_ink stage-review passed; user feedback is required before finish.",
    },
]
PASS_STATUSES = {"inspected_pass", "complete"}
CURRENT_STATUSES = {"generation_requested", "imported"}
VALID_STATUSES = {"pending", "generation_requested", "imported", "inspected_pass", "complete"}
WORKER_STATUS_VALUES = {"pass", "needs_rerun"}
REVIEW_STATUSES = {"pending", "passed", "needs_rerun"}
REVIEW_CLI_STATUSES = {"pass", "needs_rerun"}
ANCHOR_REVIEW_STATUSES = REVIEW_STATUSES
ANCHOR_REVIEW_CLI_STATUSES = REVIEW_CLI_STATUSES
SPATIAL_VERDICT_VALUES = {"pass", "needs_rerun", "reconciled"}
SPATIAL_CONSTRAINT_TYPES = {
    "aims_at",
    "trajectory_to",
    "cover_between",
    "behind_cover_from",
    "line_of_sight_blocked",
    "no_line_of_fire",
    "not_aims_at",
    "left_of",
    "right_of",
    "same_landmark_relation_as",
    "same_cover_as",
    "state_persists_from",
    "occlusion_persists_from",
    "allowed_transition",
    "requires_cause",
    "on_level",
    "above",
    "below",
    "vertical_separation",
    "same_location_as",
    "visual_evidence_required",
    "distance_less_than",
    "distance_at_least",
    "occluder_between_3d",
    "same_side_as",
    "opposite_side_from",
    "max_transfer_distance",
    "path_via",
}
SCENE_3D_ONLY_CONSTRAINT_TYPES = {
    "on_level",
    "above",
    "below",
    "vertical_separation",
    "same_location_as",
    "distance_less_than",
    "distance_at_least",
    "occluder_between_3d",
    "same_side_as",
    "opposite_side_from",
    "max_transfer_distance",
    "path_via",
}
NON_FIRING_CUES = (
    "not_firing",
    "not firing",
    "does not fire",
    "do not fire",
    "doesn't fire",
    "not fire",
    "발사하지",
    "쏘지 않",
    "존재만으로 압박",
    "support_pressure",
)
BLOCKING_DESCRIPTION_HEADINGS = [
    "## Symbol Legend",
    "## Panel Spatial Map",
    "## Constraint Check",
    "## Temporal Continuity Check",
]
DEFAULT_PACING_NOTES = (
    "Use 3-5 panels by default with measured cinematic pacing. Use 1-2 panels for special staging such "
    "as full-page emotional beats, silence, stillness, or decisive action moments. Split pages instead "
    "of compressing emotional turns, action setup/result, gaze shifts, or quiet pauses into one crowded page."
)
DEFAULT_PANEL_SHAPE_NOTES = (
    "Use experimental freeform panel design by default: diagonal panels, asymmetry, tall vertical panels, "
    "open or borderless panels, inset panels, partial overlaps, and wide negative space are allowed when "
    "reading order and continuity stay clear."
)
DEFAULT_NEGATIVE_SPACE_NOTES = (
    "Leave breathing room around faces, hands, key action, speech balloons, SFX, and quiet mood beats."
)
DEFAULT_DETAIL_DENSITY_NOTES = (
    "Use selective detail density: emphasize focal characters, props, hands, faces, and key action; simplify "
    "backgrounds or low-priority areas when they would distract from the story beat."
)
DEFAULT_VISUAL_EMPHASIS_NOTES = (
    "Plan visual emphasis with focal points, closeup intensity, line weight, black-ink weight, silhouette, "
    "contrast, and background omission or emphasis so important beats read stronger than support beats."
)
DEFAULT_COMIC_EFFECTS_NOTES = (
    "Use comic effect lines only when they serve action, emotion, impact, speed, or eye guidance. Speed lines, "
    "focus lines, impact bursts, emotion lines, and motion streaks must match the action direction and mood."
)
DEFAULT_APPEARANCE_ANATOMY_LOCK_NOTES = (
    "Preserve the approved character appearance/anatomy lock: species/body structure, face structure, eye count "
    "and placement, hand/finger/arm/leg count, silhouette, body proportions, and posture. Use character_locks, "
    "must_match, source references, and page/panel notes as the source of truth for approved anatomy or non-human "
    "exceptions. Unless explicitly approved by the plan or source, reject missing/extra/merged eyes, one-eyed "
    "appearance for a two-eyed character, one-eyed face unless explicitly approved, missing/extra limbs or fingers, "
    "changed species/body type, broken joints, and broken body proportions."
)
DEFAULT_APPEARANCE_ANATOMY_NEGATIVE_TERMS = (
    "missing eyes, extra eyes, merged eyes, one-eyed appearance for a two-eyed character, one-eyed face unless "
    "explicitly approved, missing limbs, extra limbs, missing fingers, extra fingers, merged fingers, changed "
    "species, changed body type, broken joints, broken body proportions"
)
SPATIAL_VALIDATION_OVERLAY_NOTE = "spatial_contract is a validation overlay, not a page or composition driver."
SPATIAL_SCENE_3D_DEFAULT_POLICY = (
    "spatially important panels default to scene_3d unless an exception is explicitly justified; "
    "use panel_screen_2d mainly for graphic/UI shots, symbolic panels, emotion closeups, text/SFX layout, "
    "or cases where 3D inference would create false constraints."
)
SPATIAL_CONTINUITY_PLAN_NOTE = (
    "spatial_continuity_plan is the pre-page location bible for recurring or connected spaces; "
    "same location_id means the same physical set, fixed landmarks, entrances/exits, camera axes, "
    "and allowed state changes unless a page records an explicit transition."
)
TINY_COVER_EXPOSURE_TERMS = {
    "eyes_only",
    "weapon_edge_only",
    "eyes_and_weapon_edge_only",
    "eyes_and_hand_only",
    "side_edge_peek_only",
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def slugify(value: str, fallback: str = "item") -> str:
    value = value.lower().encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or fallback


def as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def normalize_optional_object(value: Any, field_name: str) -> dict[str, Any]:
    if value is None or value == "":
        return {}
    if not isinstance(value, dict):
        raise SystemExit(f"{field_name} must be an object when provided.")
    return dict(value)


def merge_unique(*values: Any) -> list[str]:
    merged: list[str] = []
    for value in values:
        for item in as_list(value):
            item = item.strip()
            if item and item not in merged:
                merged.append(item)
    return merged


def normalize_named_entries(raw_entries: Any, default_prefix: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not raw_entries:
        return entries
    if isinstance(raw_entries, dict):
        iterable = []
        for entry_id, value in raw_entries.items():
            if isinstance(value, dict):
                entry = dict(value)
                entry.setdefault("id", entry_id)
            else:
                entry = {"id": entry_id, "description": str(value)}
            iterable.append(entry)
    elif isinstance(raw_entries, list):
        iterable = raw_entries
    else:
        iterable = as_list(raw_entries)

    for index, raw in enumerate(iterable, start=1):
        if isinstance(raw, dict):
            entry = dict(raw)
            entry_id = str(
                entry.get("id")
                or entry.get("location_id")
                or entry.get("landmark_id")
                or entry.get("name")
                or f"{default_prefix}-{index}"
            ).strip()
            entry["id"] = entry_id
            if entry.get("description") is None and entry.get("summary") is not None:
                entry["description"] = str(entry.get("summary"))
        else:
            entry = {"id": str(raw).strip(), "description": str(raw).strip()}
        if entry.get("id"):
            entries.append(entry)
    return entries


def normalize_spatial_continuity_plan(raw_plan: Any) -> dict[str, Any]:
    if not raw_plan:
        return {
            "scope": "",
            "locations": [],
            "scene_3d_scenes": [],
            "page_sequence": [],
            "continuity_rules": [],
            "allowed_changes": [],
        }
    if not isinstance(raw_plan, dict):
        raise SystemExit("spatial_continuity_plan must be an object when provided.")
    plan = dict(raw_plan)
    plan["scope"] = str(plan.get("scope") or "").strip()
    plan["locations"] = normalize_named_entries(
        plan.get("locations") or plan.get("spaces") or plan.get("sets"), "location"
    )
    for location in plan["locations"]:
        landmarks = (
            location.get("fixed_landmarks")
            or location.get("landmarks")
            or location.get("anchors")
            or location.get("spatial_anchors")
        )
        location["fixed_landmarks"] = normalize_named_entries(landmarks, "landmark")
    plan["scene_3d_scenes"] = normalize_named_entries(
        plan.get("scene_3d_scenes") or plan.get("scene_3d") or plan.get("scenes_3d"),
        "scene_3d",
    )
    for scene in plan["scene_3d_scenes"]:
        scene["status"] = str(scene.get("status") or "provisional").strip()
        scene["usage"] = str(scene.get("usage") or "validation_only").strip()
        scene["levels"] = normalize_named_entries(scene.get("levels"), "level")
        scene["locations"] = normalize_named_entries(scene.get("locations"), "location")
        scene["fixed_entities"] = normalize_named_entries(
            scene.get("fixed_entities") or scene.get("landmarks") or scene.get("anchors"),
            "fixed_entity",
        )
        for location in scene["locations"]:
            location["fixed_landmarks"] = normalize_named_entries(
                location.get("fixed_landmarks") or location.get("landmarks"),
                "landmark",
            )
        for collection_name in ["levels", "locations", "fixed_entities"]:
            for entry in scene.get(collection_name, []):
                if "position" in entry:
                    entry["position"] = normalized_vector(entry.get("position"))
                if "size" in entry:
                    entry["size"] = normalized_vector(entry.get("size"))
                if "z_range" in entry:
                    entry["z_range"] = normalized_vector(entry.get("z_range"))
        if plan["locations"]:
            existing_location_ids = {str(location.get("id") or "") for location in plan["locations"]}
        else:
            existing_location_ids = set()
        for location in scene["locations"]:
            location_id = str(location.get("id") or "")
            if location_id and location_id not in existing_location_ids:
                plan["locations"].append(location)
                existing_location_ids.add(location_id)
    page_sequence = plan.get("page_sequence") or plan.get("page_locations") or []
    if isinstance(page_sequence, dict):
        plan["page_sequence"] = [
            {"page": str(page_key), **(dict(value) if isinstance(value, dict) else {"location_id": str(value)})}
            for page_key, value in page_sequence.items()
        ]
    elif isinstance(page_sequence, list):
        plan["page_sequence"] = page_sequence
    else:
        plan["page_sequence"] = as_list(page_sequence)
    plan["continuity_rules"] = merge_unique(plan.get("continuity_rules"))
    plan["allowed_changes"] = merge_unique(plan.get("allowed_changes"))
    return plan


def spatial_continuity_plan_has_content(plan: Any) -> bool:
    if not isinstance(plan, dict):
        return False
    return bool(
        plan.get("scope")
        or plan.get("locations")
        or plan.get("scene_3d_scenes")
        or plan.get("page_sequence")
        or plan.get("continuity_rules")
        or plan.get("allowed_changes")
    )


def normalize_location_continuity(raw_continuity: Any) -> dict[str, Any]:
    if not raw_continuity:
        return {}
    if not isinstance(raw_continuity, dict):
        return {"location_id": str(raw_continuity).strip()}
    continuity = dict(raw_continuity)
    if "location_id" not in continuity:
        for alias in ["location", "space_id", "set_id"]:
            if continuity.get(alias):
                continuity["location_id"] = str(continuity.get(alias)).strip()
                break
    for key in [
        "fixed_landmarks_visible",
        "visible_landmarks",
        "anchor_landmarks",
        "offscreen_landmarks",
        "must_preserve",
        "changes_from_previous_page",
        "allowed_changes",
    ]:
        if key in continuity:
            continuity[key] = merge_unique(continuity.get(key))
    return continuity


def normalize_text_policy(value: Any) -> str:
    if value is None or value == "":
        return TEXT_POLICY_DIALOGUE_SFX_CAPTIONS
    policy = str(value).strip()
    if policy not in TEXT_POLICY_VALUES:
        choices = ", ".join(sorted(TEXT_POLICY_VALUES))
        raise SystemExit(f"Invalid text_policy: {policy}. Expected one of: {choices}")
    return policy


def path_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def is_output_reference(value: str) -> bool:
    path = Path(value).expanduser()
    parts = [part.lower() for part in path.parts if part not in {"", "."}]
    if "output" in parts:
        return True
    candidate = path if path.is_absolute() else REPO_ROOT / path
    return path_is_under(candidate, DEFAULT_OUTPUT_ROOT)


def validate_reference_paths(references: Any) -> list[str]:
    validated: list[str] = []
    for ref in as_list(references):
        ref = ref.strip()
        if not ref:
            continue
        if is_output_reference(ref):
            raise SystemExit(f"Reference path is under output/ and cannot be used as source data: {ref}")
        if ref not in validated:
            validated.append(ref)
    return validated


def panel_key(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def vector_numbers(value: Any) -> list[float] | None:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        keys = ["x", "y", "z"]
        if "x" not in value or "y" not in value:
            return None
        numbers: list[float] = []
        for key in keys:
            if key not in value:
                continue
            try:
                numbers.append(float(value[key]))
            except (TypeError, ValueError):
                return None
        return numbers if len(numbers) >= 2 else None
    if isinstance(value, (list, tuple)):
        if len(value) < 2:
            return None
        numbers = []
        for entry in value[:3]:
            try:
                numbers.append(float(entry))
            except (TypeError, ValueError):
                return None
        return numbers
    return None


def vector2(value: Any) -> tuple[float, float] | None:
    numbers = vector_numbers(value)
    if not numbers or len(numbers) < 2:
        return None
    return (numbers[0], numbers[1])


def vector3(value: Any) -> tuple[float, float, float] | None:
    numbers = vector_numbers(value)
    if not numbers or len(numbers) < 3:
        return None
    return (numbers[0], numbers[1], numbers[2])


def rect4(value: Any) -> tuple[float, float, float, float] | None:
    if isinstance(value, str):
        parts = [part.strip() for part in re.split(r"[, ]+", value.strip()) if part.strip()]
        if len(parts) < 4:
            return None
        try:
            numbers = [float(part) for part in parts[:4]]
        except ValueError:
            return None
    elif isinstance(value, (list, tuple)):
        if len(value) < 4:
            return None
        numbers = []
        for entry in value[:4]:
            try:
                numbers.append(float(entry))
            except (TypeError, ValueError):
                return None
    else:
        return None
    if not all(math.isfinite(number) for number in numbers):
        return None
    x, y, width, height = numbers
    if width <= 0 or height <= 0:
        return None
    return (x, y, width, height)


def normalized_vector(value: Any) -> Any:
    numbers = vector_numbers(value)
    return numbers if numbers is not None else value


def normalize_spatial_entities(raw_entities: Any) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    if not raw_entities:
        return entities
    if isinstance(raw_entities, dict):
        iterable = []
        for entity_id, value in raw_entities.items():
            if isinstance(value, dict):
                entry = dict(value)
                entry.setdefault("id", entity_id)
            else:
                entry = {"id": entity_id, "type": str(value)}
            iterable.append(entry)
    elif isinstance(raw_entities, list):
        iterable = raw_entities
    else:
        iterable = as_list(raw_entities)

    for index, raw in enumerate(iterable, start=1):
        if isinstance(raw, dict):
            entry = dict(raw)
            entity_id = str(entry.get("id") or entry.get("name") or f"entity-{index}").strip()
            entry["id"] = entity_id
            entry["type"] = str(entry.get("type") or "").strip()
            entry["role"] = str(entry.get("role") or "").strip()
        else:
            entry = {"id": str(raw).strip(), "type": "", "role": ""}
        if entry["id"]:
            entities.append(entry)
    return entities


def normalize_spatial_entity_state(raw_state: Any, index: int) -> dict[str, Any]:
    if isinstance(raw_state, dict):
        entry = dict(raw_state)
    else:
        entry = {"id": str(raw_state)}
    entity_id = str(entry.get("id") or entry.get("entity") or entry.get("name") or f"entity-{index}").strip()
    normalized: dict[str, Any] = {"id": entity_id}
    position = entry.get("position")
    if position is None:
        position = entry.get("world_position")
    if position is None:
        position = entry.get("screen_position")
    if position is not None:
        normalized["position"] = normalized_vector(position)
    vector_aliases = {
        "facing_vector": ["facing_vector", "facing"],
        "gaze_vector": ["gaze_vector", "gaze"],
        "aim_vector": ["aim_vector", "aim"],
        "trajectory_vector": ["trajectory_vector", "trajectory", "motion_vector", "velocity_vector"],
    }
    for target_field, aliases in vector_aliases.items():
        for alias in aliases:
            if alias in entry and entry[alias] is not None and entry[alias] != "":
                normalized[target_field] = normalized_vector(entry[alias])
                break
    for field in [
        "pose",
        "cover",
        "visibility",
        "occlusion",
        "occluded_by",
        "level_id",
        "location_anchor",
        "held_props",
        "state_tags",
        "screen_box",
        "notes",
    ]:
        if field in entry:
            normalized[field] = entry[field]
    return normalized


def normalize_spatial_panel_snapshot(raw_snapshot: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw_snapshot, dict):
        raise SystemExit(f"spatial_contract panel_snapshots[{index}] must be an object.")
    snapshot = dict(raw_snapshot)
    snapshot["panel"] = panel_key(
        snapshot.get("panel")
        or snapshot.get("panel_no")
        or snapshot.get("panel_id")
        or snapshot.get("id")
        or index
    )
    raw_entities = snapshot.get("entities") or snapshot.get("entity_states") or snapshot.get("states") or []
    if isinstance(raw_entities, dict):
        iterable = []
        for entity_id, raw_state in raw_entities.items():
            if isinstance(raw_state, dict):
                entry = dict(raw_state)
                entry.setdefault("id", entity_id)
            else:
                entry = {"id": entity_id, "position": raw_state}
            iterable.append(entry)
    else:
        iterable = raw_entities if isinstance(raw_entities, list) else as_list(raw_entities)
    snapshot["entities"] = [
        normalize_spatial_entity_state(raw_state, entity_index)
        for entity_index, raw_state in enumerate(iterable, start=1)
    ]
    return snapshot


def normalize_spatial_constraint(raw_constraint: Any, index: int) -> dict[str, Any]:
    if isinstance(raw_constraint, dict):
        constraint = dict(raw_constraint)
    else:
        constraint = {"type": str(raw_constraint)}
    constraint["id"] = str(constraint.get("id") or f"constraint-{index}")
    constraint["type"] = str(constraint.get("type") or constraint.get("relation") or "").strip()
    if "panel_no" in constraint and "panel" not in constraint:
        constraint["panel"] = constraint["panel_no"]
    if "reference_panel_no" in constraint and "reference_panel" not in constraint:
        constraint["reference_panel"] = constraint["reference_panel_no"]
    return constraint


def normalize_spatial_records(raw_records: Any, default_prefix: str) -> list[dict[str, Any]]:
    if not raw_records:
        return []
    if isinstance(raw_records, dict):
        iterable = []
        for record_id, value in raw_records.items():
            if isinstance(value, dict):
                entry = dict(value)
                entry.setdefault("id", record_id)
            else:
                entry = {"id": record_id, "value": value}
            iterable.append(entry)
    elif isinstance(raw_records, list):
        iterable = raw_records
    else:
        iterable = as_list(raw_records)
    records: list[dict[str, Any]] = []
    for index, raw in enumerate(iterable, start=1):
        if isinstance(raw, dict):
            record = dict(raw)
        else:
            record = {"rule": str(raw)}
        record["id"] = str(record.get("id") or f"{default_prefix}-{index}").strip()
        if record.get("type") is not None:
            record["type"] = str(record.get("type") or "").strip()
        if record["id"]:
            records.append(record)
    return records


def normalize_spatial_contract(raw_contract: Any) -> dict[str, Any]:
    if not raw_contract:
        return {
            "entities": [],
            "coordinate_space": {},
            "panel_snapshots": [],
            "transitions": [],
            "locks": [],
            "annotations": [],
            "constraints": [],
        }
    if not isinstance(raw_contract, dict):
        raise SystemExit("spatial_contract must be an object when provided.")
    coordinate_space = raw_contract.get("coordinate_space") or {}
    if coordinate_space and not isinstance(coordinate_space, dict):
        coordinate_space = {"description": str(coordinate_space)}
    snapshots = raw_contract.get("panel_snapshots") or raw_contract.get("snapshots") or []
    constraints = raw_contract.get("constraints") or []
    return {
        "entities": normalize_spatial_entities(raw_contract.get("entities")),
        "coordinate_space": coordinate_space,
        "panel_snapshots": [
            normalize_spatial_panel_snapshot(snapshot, index)
            for index, snapshot in enumerate(snapshots, start=1)
        ],
        "transitions": normalize_spatial_records(raw_contract.get("transitions"), "transition"),
        "locks": normalize_spatial_records(raw_contract.get("locks"), "lock"),
        "annotations": normalize_spatial_records(raw_contract.get("annotations"), "annotation"),
        "constraints": [
            normalize_spatial_constraint(constraint, index)
            for index, constraint in enumerate(constraints, start=1)
        ],
    }


def spatial_contract_has_content(contract: Any) -> bool:
    if not isinstance(contract, dict):
        return False
    return bool(
        contract.get("entities")
        or contract.get("coordinate_space")
        or contract.get("panel_snapshots")
        or contract.get("transitions")
        or contract.get("locks")
        or contract.get("annotations")
        or contract.get("constraints")
    )


def spatial_contract_page_count(pages: list[dict[str, Any]]) -> int:
    return sum(1 for page in pages if spatial_contract_has_content(page.get("spatial_contract")))


def location_landmark_ids(location: dict[str, Any]) -> set[str]:
    return {
        str(landmark.get("id") or "")
        for landmark in location.get("fixed_landmarks", [])
        if str(landmark.get("id") or "")
    }


def page_location_continuity(page: dict[str, Any]) -> dict[str, Any]:
    continuity = normalize_location_continuity(page.get("location_continuity"))
    if page.get("location_id") and not continuity.get("location_id"):
        continuity["location_id"] = str(page.get("location_id")).strip()
    return continuity


def page_location_transition_note(page: dict[str, Any], continuity: dict[str, Any]) -> str:
    for key in [
        "location_transition",
        "transition_from_previous",
        "transition_reason",
        "changes_from_previous_page",
    ]:
        value = continuity.get(key)
        if value:
            return format_spatial_value(value)
    return str(page.get("location_transition") or "").strip()


def spatial_continuity_issues(spatial_continuity_plan: dict[str, Any], pages: list[dict[str, Any]]) -> list[str]:
    plan = normalize_spatial_continuity_plan(spatial_continuity_plan)
    if not spatial_continuity_plan_has_content(plan):
        return []
    issues: list[str] = []
    locations = plan.get("locations", [])
    if not locations:
        issues.append("spatial_continuity_plan: at least one location is required when the plan is present.")
        return issues

    locations_by_id = {str(location.get("id") or ""): location for location in locations if location.get("id")}
    previous_location_id = ""
    for page_index, page in enumerate(pages, start=1):
        label = f"{page['id']} location_continuity"
        continuity = page_location_continuity(page)
        location_id = str(continuity.get("location_id") or "").strip()
        if not location_id:
            issues.append(f"{label}: requires location_id from the pre-page spatial_continuity_plan.")
            continue
        if location_id not in locations_by_id:
            issues.append(f"{label}: unknown location_id {location_id}.")
            continue

        location = locations_by_id[location_id]
        landmark_ids = location_landmark_ids(location)
        visible_landmarks = merge_unique(
            continuity.get("fixed_landmarks_visible"),
            continuity.get("visible_landmarks"),
            continuity.get("anchor_landmarks"),
        )
        offscreen_landmarks = merge_unique(continuity.get("offscreen_landmarks"))
        referenced_landmarks = visible_landmarks + [item for item in offscreen_landmarks if item not in visible_landmarks]
        unknown_landmarks = [landmark_id for landmark_id in referenced_landmarks if landmark_id not in landmark_ids]
        if unknown_landmarks:
            issues.append(
                f"{label}: unknown fixed landmark ids for {location_id}: {', '.join(unknown_landmarks)}."
            )
        if landmark_ids and not referenced_landmarks and not continuity.get("location_anchor"):
            issues.append(
                f"{label}: needs fixed_landmarks_visible, offscreen_landmarks, or location_anchor "
                "so the page cannot drift into a different space."
            )
        if page_index > 1 and previous_location_id and location_id != previous_location_id:
            transition_note = page_location_transition_note(page, continuity)
            if not transition_note:
                issues.append(
                    f"{label}: location changed from {previous_location_id} to {location_id} "
                    "without an explicit location_transition or transition_from_previous."
                )
        previous_location_id = location_id
    return issues


def spatial_constraint_value(constraint: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in constraint and constraint[name] is not None and constraint[name] != "":
            return constraint[name]
    return ""


def spatial_snapshots_by_panel(contract: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    snapshots: dict[str, dict[str, dict[str, Any]]] = {}
    for snapshot in contract.get("panel_snapshots", []):
        panel = panel_key(snapshot.get("panel"))
        entities: dict[str, dict[str, Any]] = {}
        for state in snapshot.get("entities", []):
            entity_id = str(state.get("id") or "")
            if entity_id:
                entities[entity_id] = state
        snapshots[panel] = entities
    return snapshots


def constraint_panel(contract: dict[str, Any], constraint: dict[str, Any], issues: list[str], label: str) -> str:
    panel = panel_key(spatial_constraint_value(constraint, "panel", "panel_id"))
    snapshots = contract.get("panel_snapshots", [])
    if panel:
        return panel
    if len(snapshots) == 1:
        return panel_key(snapshots[0].get("panel"))
    issues.append(f"{label}: needs panel when more than one panel snapshot exists.")
    return ""


def snapshot_state(
    snapshots: dict[str, dict[str, dict[str, Any]]],
    panel: str,
    entity_id: str,
    issues: list[str],
    label: str,
) -> dict[str, Any] | None:
    if not entity_id:
        issues.append(f"{label}: missing entity id.")
        return None
    if panel not in snapshots:
        issues.append(f"{label}: unknown panel snapshot {panel}.")
        return None
    state = snapshots[panel].get(entity_id)
    if state is None:
        issues.append(f"{label}: entity {entity_id} has no state in panel {panel}.")
        return None
    return state


def state_position(state: dict[str, Any] | None, issues: list[str], label: str) -> tuple[float, float] | None:
    if not state:
        return None
    position = vector2(state.get("position"))
    if position is None:
        issues.append(f"{label}: entity {state.get('id')} needs a numeric position [x, y].")
    return position


def state_position3(state: dict[str, Any] | None, issues: list[str], label: str) -> tuple[float, float, float] | None:
    if not state:
        return None
    position = vector3(state.get("position"))
    if position is None:
        issues.append(f"{label}: entity {state.get('id')} needs a numeric 3D position [x, y, z].")
    return position


def state_vector(
    state: dict[str, Any] | None,
    fields: list[str],
    issues: list[str],
    label: str,
) -> tuple[float, float] | None:
    if not state:
        return None
    for field in fields:
        vector = vector2(state.get(field))
        if vector is not None:
            return vector
    issues.append(f"{label}: entity {state.get('id')} needs one of {', '.join(fields)}.")
    return None


def state_vector3(
    state: dict[str, Any] | None,
    fields: list[str],
    issues: list[str],
    label: str,
) -> tuple[float, float, float] | None:
    if not state:
        return None
    for field in fields:
        vector = vector3(state.get(field))
        if vector is not None:
            return vector
    issues.append(f"{label}: entity {state.get('id')} needs one of {', '.join(fields)}.")
    return None


def vector_length(vector: tuple[float, float]) -> float:
    return math.hypot(vector[0], vector[1])


def vector3_length(vector: tuple[float, float, float]) -> float:
    return math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)


def vector3_distance(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return vector3_length((left[0] - right[0], left[1] - right[1], left[2] - right[2]))


def vector3_sub(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def vector3_add(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def vector3_scale(vector: tuple[float, float, float], scalar: float) -> tuple[float, float, float]:
    return (vector[0] * scalar, vector[1] * scalar, vector[2] * scalar)


def point_to_segment_distance3(
    point: tuple[float, float, float],
    start: tuple[float, float, float],
    end: tuple[float, float, float],
) -> tuple[float, float]:
    segment = vector3_sub(end, start)
    segment_len_sq = segment[0] ** 2 + segment[1] ** 2 + segment[2] ** 2
    if segment_len_sq == 0:
        return (vector3_distance(point, start), 0.0)
    start_to_point = vector3_sub(point, start)
    projection = (
        start_to_point[0] * segment[0]
        + start_to_point[1] * segment[1]
        + start_to_point[2] * segment[2]
    ) / segment_len_sq
    clamped = min(1.0, max(0.0, projection))
    closest = vector3_add(start, vector3_scale(segment, clamped))
    return (vector3_distance(point, closest), projection)


def dot_matches_direction(
    actual: tuple[float, float] | None,
    origin: tuple[float, float] | None,
    target: tuple[float, float] | None,
    issues: list[str],
    label: str,
    min_dot: float,
) -> None:
    if actual is None or origin is None or target is None:
        return
    expected = (target[0] - origin[0], target[1] - origin[1])
    actual_len = vector_length(actual)
    expected_len = vector_length(expected)
    if actual_len == 0 or expected_len == 0:
        issues.append(f"{label}: cannot validate a zero-length vector.")
        return
    dot = (actual[0] / actual_len) * (expected[0] / expected_len) + (actual[1] / actual_len) * (expected[1] / expected_len)
    if dot < min_dot:
        issues.append(f"{label}: vector points away from the target direction (dot={dot:.3f}, min={min_dot:.3f}).")


def dot_matches_direction3(
    actual: tuple[float, float, float] | None,
    origin: tuple[float, float, float] | None,
    target: tuple[float, float, float] | None,
    issues: list[str],
    label: str,
    min_dot: float,
) -> None:
    if actual is None or origin is None or target is None:
        return
    expected = (target[0] - origin[0], target[1] - origin[1], target[2] - origin[2])
    actual_len = vector3_length(actual)
    expected_len = vector3_length(expected)
    if actual_len == 0 or expected_len == 0:
        issues.append(f"{label}: cannot validate a zero-length vector.")
        return
    dot = (
        (actual[0] / actual_len) * (expected[0] / expected_len)
        + (actual[1] / actual_len) * (expected[1] / expected_len)
        + (actual[2] / actual_len) * (expected[2] / expected_len)
    )
    if dot < min_dot:
        issues.append(f"{label}: vector points away from the target direction (dot={dot:.3f}, min={min_dot:.3f}).")


def dot_exceeds_forbidden_direction(
    actual: tuple[float, float] | None,
    origin: tuple[float, float] | None,
    target: tuple[float, float] | None,
    issues: list[str],
    label: str,
    max_dot: float,
) -> None:
    if actual is None or origin is None or target is None:
        return
    expected = (target[0] - origin[0], target[1] - origin[1])
    actual_len = vector_length(actual)
    expected_len = vector_length(expected)
    if actual_len == 0 or expected_len == 0:
        return
    dot = (actual[0] / actual_len) * (expected[0] / expected_len) + (actual[1] / actual_len) * (expected[1] / expected_len)
    if dot > max_dot:
        issues.append(f"{label}: forbidden vector points toward the target (dot={dot:.3f}, max={max_dot:.3f}).")


def point_in_rect(point: tuple[float, float], rect: tuple[float, float, float, float]) -> bool:
    x, y, width, height = rect
    return x <= point[0] <= x + width and y <= point[1] <= y + height


def orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])


def on_segment(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    return (
        min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
        and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
    )


def segments_intersect(
    p1: tuple[float, float],
    p2: tuple[float, float],
    q1: tuple[float, float],
    q2: tuple[float, float],
    epsilon: float = 1e-9,
) -> bool:
    o1 = orientation(p1, p2, q1)
    o2 = orientation(p1, p2, q2)
    o3 = orientation(q1, q2, p1)
    o4 = orientation(q1, q2, p2)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    if abs(o1) <= epsilon and on_segment(p1, q1, p2):
        return True
    if abs(o2) <= epsilon and on_segment(p1, q2, p2):
        return True
    if abs(o3) <= epsilon and on_segment(q1, p1, q2):
        return True
    if abs(o4) <= epsilon and on_segment(q1, p2, q2):
        return True
    return False


def segment_intersects_rect(
    start: tuple[float, float],
    end: tuple[float, float],
    rect: tuple[float, float, float, float],
) -> bool:
    if point_in_rect(start, rect) or point_in_rect(end, rect):
        return True
    x, y, width, height = rect
    corners = [
        (x, y),
        (x + width, y),
        (x + width, y + height),
        (x, y + height),
    ]
    edges = list(zip(corners, [*corners[1:], corners[0]]))
    return any(segments_intersect(start, end, edge_start, edge_end) for edge_start, edge_end in edges)


def cover_screen_box_between(
    screen_box: tuple[float, float, float, float] | None,
    actor: tuple[float, float] | None,
    threat: tuple[float, float] | None,
    issues: list[str],
    label: str,
) -> None:
    if screen_box is None or actor is None or threat is None:
        return
    if not segment_intersects_rect(actor, threat, screen_box):
        issues.append(f"{label}: screen_box does not intersect the actor/threat line.")


def cover_between_points(
    cover: tuple[float, float] | None,
    actor: tuple[float, float] | None,
    threat: tuple[float, float] | None,
    issues: list[str],
    label: str,
    tolerance_ratio: float,
) -> None:
    if cover is None or actor is None or threat is None:
        return
    segment = (threat[0] - actor[0], threat[1] - actor[1])
    segment_len = vector_length(segment)
    if segment_len == 0:
        issues.append(f"{label}: subject and source positions overlap, so cover_between cannot be validated.")
        return
    actor_to_cover = (cover[0] - actor[0], cover[1] - actor[1])
    projection = ((actor_to_cover[0] * segment[0]) + (actor_to_cover[1] * segment[1])) / (segment_len * segment_len)
    perpendicular = abs(segment[0] * actor_to_cover[1] - segment[1] * actor_to_cover[0]) / segment_len
    max_distance = segment_len * tolerance_ratio
    if projection <= 0 or projection >= 1:
        issues.append(f"{label}: occluding element is not between subject and source.")
    if perpendicular > max_distance:
        issues.append(
            f"{label}: occluding element is too far from the subject/source line "
            f"(distance={perpendicular:.3f}, max={max_distance:.3f})."
        )


def relation_sign(value: float, epsilon: float = 0.001) -> int:
    if value > epsilon:
        return 1
    if value < -epsilon:
        return -1
    return 0


def relation_between(subject: tuple[float, float], anchor: tuple[float, float]) -> tuple[int, int]:
    return (relation_sign(subject[0] - anchor[0]), relation_sign(subject[1] - anchor[1]))


def validate_same_landmark_relation(
    pages_by_id: dict[str, dict[str, Any]],
    page: dict[str, Any],
    constraint: dict[str, Any],
    constraint_index: int,
    issues: list[str],
) -> None:
    label = f"{page['id']} spatial_contract constraint {constraint_index} ({constraint.get('type')})"
    contract = page.get("spatial_contract", {})
    current_panel = constraint_panel(contract, constraint, issues, label)
    reference_panel = panel_key(spatial_constraint_value(constraint, "reference_panel", "from_panel"))
    reference_page_id = str(spatial_constraint_value(constraint, "reference_page", "from_page") or page["id"])
    reference_page = pages_by_id.get(reference_page_id)
    if reference_page is None:
        issues.append(f"{label}: unknown reference_page {reference_page_id}.")
        return
    reference_contract = reference_page.get("spatial_contract", {})
    reference_snapshots = reference_contract.get("panel_snapshots", [])
    if not reference_panel and len(reference_snapshots) == 1:
        reference_panel = panel_key(reference_snapshots[0].get("panel"))
    if not current_panel or not reference_panel:
        issues.append(f"{label}: needs panel and reference_panel.")
        return

    subject = str(spatial_constraint_value(constraint, "subject", "entity", "actor") or "")
    anchor = str(spatial_constraint_value(constraint, "anchor", "target") or "")
    current_snapshots = spatial_snapshots_by_panel(contract)
    reference_snapshots_by_panel = spatial_snapshots_by_panel(reference_contract)

    pairs: list[tuple[str, str]] = []
    if subject and anchor:
        pairs.append((subject, anchor))
    else:
        landmark_ids = {
            str(entity.get("id"))
            for entity in contract.get("entities", [])
            if str(entity.get("type", "")).lower() == "landmark"
        }
        reference_landmark_ids = {
            str(entity.get("id"))
            for entity in reference_contract.get("entities", [])
            if str(entity.get("type", "")).lower() == "landmark"
        }
        common = sorted(landmark_ids & reference_landmark_ids)
        pairs = [(left, right) for index, left in enumerate(common) for right in common[index + 1 :]]
        if not pairs:
            issues.append(f"{label}: needs subject/anchor or at least two shared landmark entities.")
            return

    for pair_subject, pair_anchor in pairs:
        current_subject = state_position(
            snapshot_state(current_snapshots, current_panel, pair_subject, issues, label),
            issues,
            label,
        )
        current_anchor = state_position(
            snapshot_state(current_snapshots, current_panel, pair_anchor, issues, label),
            issues,
            label,
        )
        reference_subject = state_position(
            snapshot_state(reference_snapshots_by_panel, reference_panel, pair_subject, issues, label),
            issues,
            label,
        )
        reference_anchor = state_position(
            snapshot_state(reference_snapshots_by_panel, reference_panel, pair_anchor, issues, label),
            issues,
            label,
        )
        if not current_subject or not current_anchor or not reference_subject or not reference_anchor:
            continue
        current_relation = relation_between(current_subject, current_anchor)
        reference_relation = relation_between(reference_subject, reference_anchor)
        if current_relation != reference_relation:
            issues.append(
                f"{label}: landmark relation drift for {pair_subject}/{pair_anchor} "
                f"(current={current_relation}, reference={reference_relation})."
            )


def page_lookup_aliases(pages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for page in pages:
        aliases = {
            str(page.get("id") or ""),
            str(page.get("filename") or ""),
            Path(str(page.get("filename") or "")).stem,
            slugify(str(page.get("id") or "")),
            slugify(Path(str(page.get("filename") or "")).stem),
        }
        for alias in aliases:
            if alias and alias not in lookup:
                lookup[alias] = page
    return lookup


def constraint_entity_id(constraint: dict[str, Any]) -> str:
    return str(spatial_constraint_value(constraint, "entity", "subject", "actor", "object") or "")


def constraint_reference_entity_id(constraint: dict[str, Any], fallback: str) -> str:
    return str(spatial_constraint_value(constraint, "reference_entity", "from_entity") or fallback)


def constraint_page_ref(constraint: dict[str, Any], current_page: dict[str, Any], *names: str) -> str:
    return str(spatial_constraint_value(constraint, *names) or current_page["id"])


def page_panel_exists(page: dict[str, Any], panel: str) -> bool:
    if not panel:
        return False
    contract = page.get("spatial_contract", {})
    if panel in spatial_snapshots_by_panel(contract):
        return True
    for panel_info in page.get("panels", []):
        aliases = {
            panel_key(panel_info.get("panel_no")),
            panel_key(panel_info.get("order")),
            panel_key(panel_info.get("id")),
        }
        if panel in aliases:
            return True
    return False


def cause_ref_parts(constraint: dict[str, Any], current_page: dict[str, Any]) -> tuple[str, str]:
    cause_ref = str(spatial_constraint_value(constraint, "cause_ref", "cause") or "").strip()
    if cause_ref:
        if ":" in cause_ref:
            page_ref, panel_ref = cause_ref.split(":", 1)
            return page_ref.strip() or current_page["id"], panel_key(panel_ref.strip())
        return current_page["id"], panel_key(cause_ref)
    return (
        constraint_page_ref(constraint, current_page, "cause_page"),
        panel_key(spatial_constraint_value(constraint, "cause_panel", "cause_panel_id")),
    )


def cause_reference_exists(
    pages_by_id: dict[str, dict[str, Any]],
    current_page: dict[str, Any],
    constraint: dict[str, Any],
) -> bool:
    cause_page_ref, cause_panel = cause_ref_parts(constraint, current_page)
    cause_page = pages_by_id.get(cause_page_ref)
    if cause_page is None:
        return False
    return page_panel_exists(cause_page, cause_panel)


def normalize_state_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            return json.dumps(sorted(str(item) for item in value), ensure_ascii=False)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def state_value_matches(left: Any, right: Any) -> bool:
    return normalize_state_value(left) == normalize_state_value(right)


def transition_endpoint(
    pages_by_id: dict[str, dict[str, Any]],
    current_page: dict[str, Any],
    constraint: dict[str, Any],
    label: str,
    issues: list[str],
) -> tuple[str, str, str, str, str] | None:
    entity_id = constraint_entity_id(constraint)
    if not entity_id:
        issues.append(f"{label}: missing entity/subject.")
        return None
    from_page_id = constraint_page_ref(constraint, current_page, "from_page", "reference_page")
    from_panel = panel_key(spatial_constraint_value(constraint, "from_panel", "reference_panel"))
    to_page_id = constraint_page_ref(constraint, current_page, "to_page")
    to_panel = panel_key(spatial_constraint_value(constraint, "to_panel", "panel"))
    if from_page_id not in pages_by_id:
        issues.append(f"{label}: unknown from_page/reference_page {from_page_id}.")
        return None
    if to_page_id not in pages_by_id:
        issues.append(f"{label}: unknown to_page {to_page_id}.")
        return None
    if not from_panel:
        issues.append(f"{label}: needs from_panel/reference_panel.")
        return None
    if not to_panel:
        issues.append(f"{label}: needs to_panel/panel.")
        return None
    if not page_panel_exists(pages_by_id[from_page_id], from_panel):
        issues.append(f"{label}: unknown from_panel/reference_panel {from_panel}.")
        return None
    if not page_panel_exists(pages_by_id[to_page_id], to_panel):
        issues.append(f"{label}: unknown to_panel/panel {to_panel}.")
        return None
    return entity_id, from_page_id, from_panel, to_page_id, to_panel


def transition_allowed(
    pages: list[dict[str, Any]],
    pages_by_id: dict[str, dict[str, Any]],
    entity_id: str,
    from_page_id: str,
    from_panel: str,
    to_page_id: str,
    to_panel: str,
) -> bool:
    for page in pages:
        for constraint in page.get("spatial_contract", {}).get("constraints", []):
            if constraint.get("type") != "allowed_transition":
                continue
            if constraint_entity_id(constraint) != entity_id:
                continue
            allowed_from_page = constraint_page_ref(constraint, page, "from_page", "reference_page")
            allowed_from_panel = panel_key(spatial_constraint_value(constraint, "from_panel", "reference_panel"))
            allowed_to_page = constraint_page_ref(constraint, page, "to_page")
            allowed_to_panel = panel_key(spatial_constraint_value(constraint, "to_panel", "panel"))
            if (
                allowed_from_page == from_page_id
                and allowed_from_panel == from_panel
                and allowed_to_page == to_page_id
                and allowed_to_panel == to_panel
                and cause_reference_exists(pages_by_id, page, constraint)
            ):
                return True
    return False


def temporal_state_pair(
    pages_by_id: dict[str, dict[str, Any]],
    page: dict[str, Any],
    contract: dict[str, Any],
    constraint: dict[str, Any],
    label: str,
    issues: list[str],
) -> tuple[str, str, str, str, str, dict[str, Any] | None, dict[str, Any] | None] | None:
    current_panel = constraint_panel(contract, constraint, issues, label)
    if not current_panel:
        return None
    entity_id = constraint_entity_id(constraint)
    if not entity_id:
        issues.append(f"{label}: missing entity/subject.")
        return None
    reference_entity_id = constraint_reference_entity_id(constraint, entity_id)
    reference_page_id = constraint_page_ref(constraint, page, "reference_page", "from_page")
    reference_page = pages_by_id.get(reference_page_id)
    if reference_page is None:
        issues.append(f"{label}: unknown reference_page/from_page {reference_page_id}.")
        return None
    reference_contract = reference_page.get("spatial_contract", {})
    reference_snapshots = reference_contract.get("panel_snapshots", [])
    reference_panel = panel_key(spatial_constraint_value(constraint, "reference_panel", "from_panel"))
    if not reference_panel and len(reference_snapshots) == 1:
        reference_panel = panel_key(reference_snapshots[0].get("panel"))
    if not reference_panel:
        issues.append(f"{label}: needs reference_panel/from_panel.")
        return None
    current_state = snapshot_state(spatial_snapshots_by_panel(contract), current_panel, entity_id, issues, label)
    reference_state = snapshot_state(
        spatial_snapshots_by_panel(reference_contract),
        reference_panel,
        reference_entity_id,
        issues,
        label,
    )
    return entity_id, reference_page_id, reference_panel, page["id"], current_panel, reference_state, current_state


def temporal_fields_for_constraint(constraint: dict[str, Any], default_fields: list[str]) -> list[str]:
    raw_fields = constraint.get("state_fields") or constraint.get("fields") or constraint.get("attributes")
    fields = [str(field) for field in as_list(raw_fields)] if raw_fields else list(default_fields)
    return [field for field in fields if field]


def validate_temporal_persistence(
    pages: list[dict[str, Any]],
    pages_by_id: dict[str, dict[str, Any]],
    page: dict[str, Any],
    contract: dict[str, Any],
    constraint: dict[str, Any],
    constraint_index: int,
    issues: list[str],
    default_fields: list[str],
) -> None:
    label = f"{page['id']} spatial_contract constraint {constraint_index} ({constraint.get('type')})"
    pair = temporal_state_pair(pages_by_id, page, contract, constraint, label, issues)
    if pair is None:
        return
    entity_id, reference_page_id, reference_panel, current_page_id, current_panel, reference_state, current_state = pair
    if reference_state is None or current_state is None:
        return
    if transition_allowed(pages, pages_by_id, entity_id, reference_page_id, reference_panel, current_page_id, current_panel):
        return
    fields = temporal_fields_for_constraint(constraint, default_fields)
    for field in fields:
        reference_value = reference_state.get(field)
        current_value = current_state.get(field)
        if not state_value_matches(reference_value, current_value):
            issues.append(
                f"{label}: {field} drift for {entity_id} "
                f"(reference={normalize_state_value(reference_value) or 'missing'}, "
                f"current={normalize_state_value(current_value) or 'missing'})."
            )


def validate_allowed_transition(
    pages_by_id: dict[str, dict[str, Any]],
    page: dict[str, Any],
    constraint: dict[str, Any],
    constraint_index: int,
    issues: list[str],
) -> None:
    label = f"{page['id']} spatial_contract constraint {constraint_index} ({constraint.get('type')})"
    transition_endpoint(pages_by_id, page, constraint, label, issues)
    if not cause_reference_exists(pages_by_id, page, constraint):
        cause_page, cause_panel = cause_ref_parts(constraint, page)
        issues.append(f"{label}: allowed_transition requires an existing cause reference ({cause_page}:{cause_panel}).")


def validate_requires_cause(
    pages_by_id: dict[str, dict[str, Any]],
    page: dict[str, Any],
    constraint: dict[str, Any],
    constraint_index: int,
    issues: list[str],
) -> None:
    label = f"{page['id']} spatial_contract constraint {constraint_index} ({constraint.get('type')})"
    if not cause_reference_exists(pages_by_id, page, constraint):
        cause_page, cause_panel = cause_ref_parts(constraint, page)
        issues.append(f"{label}: requires_cause points to a missing cause panel ({cause_page}:{cause_panel}).")


def spatial_contract_coordinate_type(contract: dict[str, Any]) -> str:
    coordinate_space = contract.get("coordinate_space") or {}
    return str(coordinate_space.get("type") or "").strip()


def panel_screen_2d_exception_reason(page: dict[str, Any], contract: dict[str, Any]) -> str:
    coordinate_space = contract.get("coordinate_space") or {}
    extraction = page.get("spatial_contract_extraction") or {}
    candidates = [
        coordinate_space.get("exception_reason"),
        coordinate_space.get("panel_screen_2d_reason"),
        coordinate_space.get("scene_3d_exception_reason"),
        contract.get("exception_reason"),
        contract.get("panel_screen_2d_reason"),
        extraction.get("coordinate_space_exception_reason"),
        extraction.get("panel_screen_2d_reason"),
        extraction.get("scene_3d_exception_reason"),
    ]
    return next((str(candidate).strip() for candidate in candidates if str(candidate or "").strip()), "")


def spatial_contract_has_scene_3d_default_cues(page: dict[str, Any], contract: dict[str, Any]) -> bool:
    constraint_types = {str(constraint.get("type") or "") for constraint in contract.get("constraints", [])}
    if constraint_types & SCENE_3D_ONLY_CONSTRAINT_TYPES:
        return True
    if constraint_types & {
        "cover_between",
        "behind_cover_from",
        "line_of_sight_blocked",
        "trajectory_to",
        "allowed_transition",
        "requires_cause",
        "same_cover_as",
        "state_persists_from",
        "occlusion_persists_from",
    }:
        return True
    if len(contract.get("panel_snapshots", [])) > 1:
        return True
    haystack = json.dumps(
        {
            "narrative_plan": page.get("narrative_plan"),
            "spatial_logic_notes": page.get("spatial_logic_notes"),
            "motion_checks": page.get("motion_checks"),
            "must_match": page.get("must_match"),
            "location_continuity": page.get("location_continuity"),
            "spatial_contract": contract,
        },
        ensure_ascii=False,
    ).lower()
    return bool(
        re.search(
            r"multi[-_ ]?floor|floor_2|floor2|2층|upper|above|below|stair|railing|balcony|level|층|계단|난간|"
            r"distance|거리|line of sight|occlusion|occluder|blocked|blocking|가림|차폐|엄폐|behind|"
            r"path|trajectory|route|movement|transfer|handoff|deliver|throw|roll|pass|전달|던지|굴러|패스|"
            r"vehicle|door|window|pillar|stage|court|room|corridor|hall|차량|문|창문|기둥|무대|코트|복도",
            haystack,
        )
    )


def scene_3d_scenes_by_id(spatial_continuity_plan: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    plan = normalize_spatial_continuity_plan(spatial_continuity_plan)
    return {
        str(scene.get("id") or ""): scene
        for scene in plan.get("scene_3d_scenes", [])
        if str(scene.get("id") or "")
    }


def scene_3d_levels_by_id(scene: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(level.get("id") or ""): level for level in scene.get("levels", []) if str(level.get("id") or "")}


def scene_3d_locations_by_id(scene: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(location.get("id") or ""): location
        for location in scene.get("locations", [])
        if str(location.get("id") or "")
    }


def scene_3d_level_contains_z(level: dict[str, Any], z: float) -> bool:
    z_range = vector_numbers(level.get("z_range"))
    if not z_range or len(z_range) < 2:
        return True
    lower, upper = sorted((float(z_range[0]), float(z_range[1])))
    return lower <= z <= upper


def scene_3d_level_floor_z(level: dict[str, Any] | None) -> float | None:
    if not level:
        return None
    z_range = vector_numbers(level.get("z_range"))
    if not z_range or len(z_range) < 2:
        return None
    return min(float(z_range[0]), float(z_range[1]))


def scene_3d_entity_definitions(scene: dict[str, Any] | None, contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    definitions: dict[str, dict[str, Any]] = {}
    for entity in (scene or {}).get("fixed_entities", []):
        entity_id = str(entity.get("id") or "")
        if entity_id:
            definitions[entity_id] = entity
    for entity in contract.get("entities", []):
        entity_id = str(entity.get("id") or "")
        if entity_id:
            definitions[entity_id] = {**definitions.get(entity_id, {}), **entity}
    return definitions


def scene_3d_snapshot_or_defined_state(
    snapshots: dict[str, dict[str, dict[str, Any]]],
    panel: str,
    entity_id: str,
    scene: dict[str, Any] | None,
    contract: dict[str, Any],
    issues: list[str],
    label: str,
) -> dict[str, Any] | None:
    if not entity_id:
        issues.append(f"{label}: missing entity id.")
        return None
    if panel in snapshots and entity_id in snapshots[panel]:
        return snapshots[panel][entity_id]
    definition = scene_3d_entity_definitions(scene, contract).get(entity_id)
    if definition and vector3(definition.get("position")) is not None:
        return definition
    if panel not in snapshots:
        issues.append(f"{label}: unknown panel snapshot {panel}.")
    else:
        issues.append(f"{label}: entity {entity_id} has no state in panel {panel}.")
    return None


def scene_3d_resolve_position(
    value: Any,
    snapshots: dict[str, dict[str, dict[str, Any]]],
    panel: str,
    scene: dict[str, Any] | None,
    contract: dict[str, Any],
    issues: list[str],
    label: str,
    field_label: str,
) -> tuple[tuple[float, float, float] | None, str]:
    direct = vector3(value)
    if direct is not None:
        return direct, str(value)
    entity_id = str(value or "")
    if not entity_id:
        issues.append(f"{label}: needs {field_label}.")
        return None, field_label
    state = scene_3d_snapshot_or_defined_state(snapshots, panel, entity_id, scene, contract, issues, label)
    return state_position3(state, issues, label), entity_id


def scene_3d_constraint_position(
    constraint: dict[str, Any],
    names: list[str],
    snapshots: dict[str, dict[str, dict[str, Any]]],
    panel: str,
    scene: dict[str, Any] | None,
    contract: dict[str, Any],
    issues: list[str],
    label: str,
) -> tuple[tuple[float, float, float] | None, str]:
    value = spatial_constraint_value(constraint, *names)
    return scene_3d_resolve_position(value, snapshots, panel, scene, contract, issues, label, "/".join(names))


def scene_3d_constraint_path_points(
    constraint: dict[str, Any],
    snapshots: dict[str, dict[str, dict[str, Any]]],
    panel: str,
    scene: dict[str, Any] | None,
    contract: dict[str, Any],
    issues: list[str],
    label: str,
) -> list[tuple[float, float, float]]:
    raw_path = constraint.get("path") or constraint.get("waypoints") or []
    if not isinstance(raw_path, list):
        issues.append(f"{label}: path/waypoints must be a list.")
        return []
    points: list[tuple[float, float, float]] = []
    for index, entry in enumerate(raw_path, start=1):
        point, _ = scene_3d_resolve_position(entry, snapshots, panel, scene, contract, issues, label, f"path[{index}]")
        if point is not None:
            points.append(point)
    return points


def scene_3d_axis_vector(value: Any) -> tuple[float, float, float] | None:
    vector = vector3(value)
    if vector is not None:
        return vector
    axis = str(value or "").strip().lower()
    if axis in {"x", "+x", "east", "right"}:
        return (1.0, 0.0, 0.0)
    if axis in {"-x", "west", "left"}:
        return (-1.0, 0.0, 0.0)
    if axis in {"y", "+y", "north", "forward"}:
        return (0.0, 1.0, 0.0)
    if axis in {"-y", "south", "back"}:
        return (0.0, -1.0, 0.0)
    if axis in {"z", "+z", "up"}:
        return (0.0, 0.0, 1.0)
    if axis in {"-z", "down"}:
        return (0.0, 0.0, -1.0)
    return None


def scene_3d_transition_matches(
    transition: dict[str, Any],
    *,
    entity: str,
    from_panel: Any = None,
    to_panel: Any = None,
    state_change: str = "",
    from_location: str = "",
    to_location: str = "",
) -> bool:
    if entity and str(transition.get("entity") or "") != entity:
        return False
    if from_panel not in (None, "") and panel_key(transition.get("from_panel")) != panel_key(from_panel):
        return False
    if to_panel not in (None, "") and panel_key(transition.get("to_panel")) != panel_key(to_panel):
        return False
    if state_change and str(transition.get("state_change") or "") not in {"", state_change}:
        from_state = str(transition.get("from_state") or "")
        to_state = str(transition.get("to_state") or "")
        if f"{from_state}_to_{to_state}" != state_change:
            return False
    if from_location and str(transition.get("from_location") or "") not in {"", from_location}:
        return False
    if to_location and str(transition.get("to_location") or "") not in {"", to_location}:
        return False
    return True


SCENE_3D_MAJOR_SPATIAL_TERMS = {
    "building",
    "room",
    "street",
    "road",
    "corridor",
    "hall",
    "stage",
    "court",
    "vehicle",
    "car",
    "truck",
    "apc",
    "furniture",
    "sofa",
    "table",
    "desk",
}
SCENE_3D_SINGLE_BOX_ALLOWED_TERMS = {"door", "window", "pillar", "column", "railing", "sign", "marker"}
SCENE_3D_GROUNDED_TERMS = {
    "ground",
    "floor",
    "street",
    "road",
    "rubble",
    "debris",
    "vehicle",
    "car",
    "truck",
    "apc",
    "furniture",
    "table",
    "desk",
    "chair",
    "wall",
    "door",
    "pillar",
    "column",
    "stage",
    "court",
    "platform",
    "crate",
}
SCENE_3D_SLOPE_TERMS = {"sloped", "slope", "ramp", "tilted", "incline", "inclined", "경사", "기울"}


def preview_geometry_for_entity(entity: dict[str, Any]) -> dict[str, Any]:
    geometry = entity.get("preview_geometry") or {}
    return geometry if isinstance(geometry, dict) else {}


def scene_3d_entity_text(entity: dict[str, Any], geometry: dict[str, Any]) -> str:
    payload = {
        "id": entity.get("id"),
        "type": entity.get("type"),
        "role": entity.get("role"),
        "style": geometry.get("style"),
        "shape": geometry.get("shape"),
        "label": geometry.get("preview_label"),
        "description": entity.get("description"),
    }
    return json.dumps(payload, ensure_ascii=False).lower()


def scene_3d_geometry_max_size(geometry: dict[str, Any]) -> float:
    size = vector_numbers(geometry.get("size"))
    if not size:
        return 0.0
    return max(abs(float(value)) for value in size)


def scene_3d_is_major_single_box_entity(entity: dict[str, Any], geometry: dict[str, Any]) -> bool:
    shape = str(geometry.get("shape") or "").lower()
    if shape not in {"box", "building_shell"}:
        return False
    text = scene_3d_entity_text(entity, geometry)
    if any(term in text for term in SCENE_3D_SINGLE_BOX_ALLOWED_TERMS):
        return False
    if not any(term in text for term in SCENE_3D_MAJOR_SPATIAL_TERMS):
        return False
    if scene_3d_geometry_max_size(geometry) < 1.5:
        return False
    parts = geometry.get("parts") or []
    return not isinstance(parts, list) or len(parts) == 0


def scene_3d_is_grounded_entity(entity: dict[str, Any], geometry: dict[str, Any]) -> bool:
    text = scene_3d_entity_text(entity, geometry)
    if any(tag in text for tag in ("airborne", "flying", "thrown", "floating", "suspended")):
        return False
    if any(tag in text for tag in ("railing", "balcony")):
        return False
    return any(term in text for term in SCENE_3D_GROUNDED_TERMS)


def scene_3d_entity_floor_z(scene: dict[str, Any], entity: dict[str, Any], position: tuple[float, float, float]) -> float | None:
    levels = scene_3d_levels_by_id(scene)
    level_id = str(entity.get("level_id") or "")
    if level_id in levels:
        return scene_3d_level_floor_z(levels[level_id])
    containing_levels = [level for level in levels.values() if scene_3d_level_contains_z(level, position[2])]
    if containing_levels:
        return scene_3d_level_floor_z(containing_levels[0])
    floor_values = [scene_3d_level_floor_z(level) for level in levels.values()]
    valid_floor_values = [value for value in floor_values if value is not None]
    if valid_floor_values:
        return min(valid_floor_values)
    return 0.0


def scene_3d_quality_issues(
    page: dict[str, Any],
    contract: dict[str, Any],
    scene: dict[str, Any],
    issues: list[str],
) -> None:
    label_prefix = f"{page['id']} spatial_contract scene_3d quality_gate"
    records: list[tuple[str, dict[str, Any]]] = []
    for entity in scene.get("fixed_entities", []):
        records.append(("fixed_entity", entity))
    for entity in contract.get("entities", []):
        records.append(("contract_entity", entity))
    for snapshot in contract.get("panel_snapshots", []):
        panel = panel_key(snapshot.get("panel"))
        for entity in snapshot.get("entities", []):
            merged = {**scene_3d_entity_definitions(scene, contract).get(str(entity.get("id") or ""), {}), **entity}
            records.append((f"panel {panel}", merged))

    seen: set[tuple[str, str]] = set()
    for source, entity in records:
        entity_id = str(entity.get("id") or "")
        geometry = preview_geometry_for_entity(entity)
        if not geometry:
            continue
        key = (source, entity_id)
        if key in seen:
            continue
        seen.add(key)
        shape = str(geometry.get("shape") or "").lower()
        if scene_3d_is_major_single_box_entity(entity, geometry):
            issues.append(
                f"{label_prefix} {source} {entity_id}: major spatial element uses a single {shape}; "
                "add preview_geometry.parts[] for inspectable floor/wall/opening/pillar/doorway/ramp/occluder/landmark structure."
            )
        position = vector3(entity.get("position"))
        anchor = str(geometry.get("anchor") or "").lower()
        if position is not None and anchor == "base_center" and scene_3d_is_grounded_entity(entity, geometry):
            expected_z = scene_3d_entity_floor_z(scene, entity, position)
            tolerance = float(geometry.get("ground_tolerance", 0.15))
            if expected_z is not None and abs(position[2] - expected_z) > tolerance:
                issues.append(
                    f"{label_prefix} {source} {entity_id}: base_center z={position[2]:.2f} appears to float above floor z={expected_z:.2f}; "
                    "move the base to the floor or mark it as airborne/suspended."
                )
        text = scene_3d_entity_text(entity, geometry)
        if any(term in text for term in SCENE_3D_SLOPE_TERMS):
            pitch = geometry.get("pitch_degrees", geometry.get("pitch"))
            roll = geometry.get("roll_degrees", geometry.get("roll"))
            try:
                pitch_value = abs(float(pitch or 0))
                roll_value = abs(float(roll or 0))
            except (TypeError, ValueError):
                pitch_value = 0.0
                roll_value = 0.0
            if pitch_value < 0.001 and roll_value < 0.001:
                issues.append(
                    f"{label_prefix} {source} {entity_id}: sloped/tilted geometry needs pitch_degrees or roll_degrees."
                )


def validate_scene_3d_contract(
    page: dict[str, Any],
    contract: dict[str, Any],
    spatial_continuity_plan: dict[str, Any] | None,
    issues: list[str],
) -> None:
    coordinate_space = contract.get("coordinate_space") or {}
    scene_id = str(coordinate_space.get("scene_id") or "").strip()
    label_prefix = f"{page['id']} spatial_contract scene_3d"
    scenes = scene_3d_scenes_by_id(spatial_continuity_plan)
    scene = scenes.get(scene_id)
    if not scene_id:
        issues.append(f"{label_prefix}: requires coordinate_space.scene_id.")
        return
    if scene is None:
        issues.append(f"{label_prefix}: unknown scene_3d scene_id {scene_id}.")
        return

    scene_3d_quality_issues(page, contract, scene, issues)

    levels = scene_3d_levels_by_id(scene)
    locations = scene_3d_locations_by_id(scene)
    contract_location_id = str(coordinate_space.get("location_id") or "").strip()
    if contract_location_id and contract_location_id not in locations:
        issues.append(f"{label_prefix}: unknown location_id {contract_location_id} for scene {scene_id}.")
    snapshots = spatial_snapshots_by_panel(contract)
    entity_id_set = {str(entity.get("id") or "") for entity in contract.get("entities", []) if str(entity.get("id") or "")}

    for snapshot in contract.get("panel_snapshots", []):
        panel = panel_key(snapshot.get("panel"))
        snapshot_location_id = str(snapshot.get("location_id") or contract_location_id or "").strip()
        if snapshot_location_id and snapshot_location_id not in locations:
            issues.append(f"{label_prefix} panel {panel}: unknown location_id {snapshot_location_id} for scene {scene_id}.")
        camera = snapshot.get("camera") or {}
        if camera:
            if vector3(camera.get("position")) is None:
                issues.append(f"{label_prefix} panel {panel}: camera.position must be numeric [x, y, z].")
            if vector3(camera.get("look_at")) is None:
                issues.append(f"{label_prefix} panel {panel}: camera.look_at must be numeric [x, y, z].")
        for state in snapshot.get("entities", []):
            entity_id = str(state.get("id") or "")
            if entity_id not in entity_id_set:
                issues.append(f"{label_prefix} panel {panel}: unknown entity {entity_id}.")
            position = vector3(state.get("position"))
            if position is None:
                issues.append(f"{label_prefix} panel {panel}: entity {entity_id} has invalid 3D position.")
                continue
            level_id = str(state.get("level_id") or "").strip()
            if level_id:
                level = levels.get(level_id)
                if level is None:
                    issues.append(f"{label_prefix} panel {panel}: entity {entity_id} references unknown level_id {level_id}.")
                elif not scene_3d_level_contains_z(level, position[2]):
                    issues.append(
                        f"{label_prefix} panel {panel}: entity {entity_id} level_id {level_id} "
                        f"does not match z_range for z={position[2]:.1f}."
                    )
            for field in ["facing_vector", "gaze_vector", "aim_vector", "trajectory_vector"]:
                if field in state and vector3(state.get(field)) is None:
                    issues.append(f"{label_prefix} panel {panel}: entity {entity_id} has invalid 3D {field}.")

    ordered_snapshots = sorted(contract.get("panel_snapshots", []), key=lambda snapshot: panel_key(snapshot.get("panel")))
    transitions = contract.get("transitions", [])
    for previous, current in zip(ordered_snapshots, ordered_snapshots[1:]):
        previous_panel = panel_key(previous.get("panel"))
        current_panel = panel_key(current.get("panel"))
        previous_location = str(previous.get("location_id") or contract_location_id or "")
        current_location = str(current.get("location_id") or contract_location_id or "")
        if previous_location and current_location and previous_location != current_location:
            if not any(
                scene_3d_transition_matches(
                    transition,
                    entity=str(transition.get("entity") or ""),
                    from_panel=previous_panel,
                    to_panel=current_panel,
                    from_location=previous_location,
                    to_location=current_location,
                )
                for transition in transitions
            ):
                issues.append(
                    f"{label_prefix}: location changed from {previous_location} to {current_location} "
                    f"between panel {previous_panel} and {current_panel} without a matching transition."
                )
        previous_states = {str(state.get("id") or ""): state for state in previous.get("entities", [])}
        for state in current.get("entities", []):
            entity_id = str(state.get("id") or "")
            previous_state = previous_states.get(entity_id)
            if not previous_state:
                continue
            previous_level = str(previous_state.get("level_id") or "")
            current_level = str(state.get("level_id") or "")
            if previous_level and current_level and previous_level != current_level:
                if not any(
                    scene_3d_transition_matches(
                        transition,
                        entity=entity_id,
                        from_panel=previous_panel,
                        to_panel=current_panel,
                    )
                    for transition in transitions
                ):
                    issues.append(
                        f"{label_prefix}: entity {entity_id} changed level from {previous_level} to {current_level} "
                        f"between panel {previous_panel} and {current_panel} without a matching transition."
                    )

    for lock in contract.get("locks", []):
        lock_type = str(lock.get("type") or "").strip()
        lock_label = f"{label_prefix} lock {lock.get('id')}"
        if lock_type not in {"hard", "soft", "inferred"}:
            issues.append(f"{lock_label}: lock type must be hard, soft, or inferred.")
            continue
        for entity_id in merge_unique(lock.get("entities")):
            if entity_id not in entity_id_set:
                issues.append(f"{lock_label}: unknown entity {entity_id}.")

    for index, constraint in enumerate(contract.get("constraints", []), start=1):
        constraint_type = str(constraint.get("type") or "")
        label = f"{page['id']} spatial_contract constraint {index} ({constraint_type or 'missing_type'})"
        if constraint_type not in SPATIAL_CONSTRAINT_TYPES:
            issues.append(f"{label}: unsupported constraint type.")
            continue
        if constraint_type == "visual_evidence_required":
            continue
        if constraint_type == "requires_cause":
            entity_id = str(spatial_constraint_value(constraint, "entity", "object", "subject") or "")
            cause_panel = spatial_constraint_value(constraint, "cause_panel", "to_panel", "panel")
            state_change = str(spatial_constraint_value(constraint, "state_change") or "")
            if not any(
                scene_3d_transition_matches(
                    transition,
                    entity=entity_id,
                    to_panel=cause_panel,
                    state_change=state_change,
                )
                for transition in transitions
            ):
                issues.append(f"{label}: requires_cause has no matching transition cause.")
            continue
        if constraint_type == "allowed_transition":
            entity_id = str(spatial_constraint_value(constraint, "entity", "object", "subject") or "")
            from_panel = spatial_constraint_value(constraint, "from_panel")
            to_panel = spatial_constraint_value(constraint, "to_panel")
            if not any(
                scene_3d_transition_matches(
                    transition,
                    entity=entity_id,
                    from_panel=from_panel,
                    to_panel=to_panel,
                )
                for transition in transitions
            ):
                issues.append(f"{label}: allowed_transition has no matching scene_3d transition.")
            continue
        if constraint_type not in {
            "on_level",
            "above",
            "below",
            "vertical_separation",
            "same_location_as",
            "trajectory_to",
            "distance_less_than",
            "distance_at_least",
            "occluder_between_3d",
            "same_side_as",
            "opposite_side_from",
            "max_transfer_distance",
            "path_via",
        }:
            issues.append(f"{label}: unsupported scene_3d constraint type.")
            continue

        panel = constraint_panel(contract, constraint, issues, label)
        if not panel:
            continue
        if constraint_type == "on_level":
            entity_id = str(spatial_constraint_value(constraint, "entity", "subject", "actor") or "")
            expected_level = str(spatial_constraint_value(constraint, "level", "level_id") or "")
            state = snapshot_state(snapshots, panel, entity_id, issues, label)
            actual_level = str((state or {}).get("level_id") or "")
            position = state_position3(state, issues, label)
            if actual_level != expected_level:
                issues.append(f"{label}: entity {entity_id} is on {actual_level or 'no level'}, expected {expected_level}.")
            level = levels.get(expected_level)
            if position is not None and level is not None and not scene_3d_level_contains_z(level, position[2]):
                issues.append(f"{label}: entity {entity_id} z={position[2]:.1f} is outside level {expected_level}.")
        elif constraint_type in {"above", "below", "vertical_separation"}:
            subject_id = str(spatial_constraint_value(constraint, "subject", "actor", "entity") or "")
            anchor_id = str(spatial_constraint_value(constraint, "anchor", "target", "of") or "")
            subject = state_position3(snapshot_state(snapshots, panel, subject_id, issues, label), issues, label)
            anchor = state_position3(snapshot_state(snapshots, panel, anchor_id, issues, label), issues, label)
            if subject is None or anchor is None:
                continue
            tolerance = float(constraint.get("tolerance", 0.001))
            if constraint_type == "above" and not subject[2] > anchor[2] + tolerance:
                issues.append(f"{label}: {subject_id} is not above {anchor_id}.")
            elif constraint_type == "below" and not subject[2] < anchor[2] - tolerance:
                issues.append(f"{label}: {subject_id} is not below {anchor_id}.")
            elif constraint_type == "vertical_separation":
                min_delta_z = float(constraint.get("min_delta_z", constraint.get("min_z_delta", 0)))
                if abs(subject[2] - anchor[2]) < min_delta_z:
                    issues.append(
                        f"{label}: vertical separation between {subject_id} and {anchor_id} "
                        f"is {abs(subject[2] - anchor[2]):.3f}, min={min_delta_z:.3f}."
                    )
        elif constraint_type == "same_location_as":
            subject_id = str(spatial_constraint_value(constraint, "subject", "entity", "actor") or "")
            anchor_id = str(spatial_constraint_value(constraint, "anchor", "target", "of") or "")
            subject_state = snapshot_state(snapshots, panel, subject_id, issues, label)
            anchor_state = snapshot_state(snapshots, panel, anchor_id, issues, label)
            snapshot_location = ""
            for snapshot in contract.get("panel_snapshots", []):
                if panel_key(snapshot.get("panel")) == panel:
                    snapshot_location = str(snapshot.get("location_id") or "")
                    break
            subject_location = str((subject_state or {}).get("location_id") or snapshot_location or contract_location_id or "")
            anchor_location = str((anchor_state or {}).get("location_id") or snapshot_location or contract_location_id or "")
            if subject_location != anchor_location:
                issues.append(f"{label}: {subject_id} is not in the same location as {anchor_id}.")
        elif constraint_type == "trajectory_to":
            object_id = str(spatial_constraint_value(constraint, "object", "projectile", "source", "entity") or "")
            target_id = str(spatial_constraint_value(constraint, "target", "to") or "")
            object_state = snapshot_state(snapshots, panel, object_id, issues, label)
            target_state = snapshot_state(snapshots, panel, target_id, issues, label)
            origin = state_position3(object_state, issues, label)
            target = state_position3(target_state, issues, label)
            actual = state_vector3(object_state, ["trajectory_vector", "motion_vector", "velocity_vector"], issues, label)
            min_dot = float(constraint.get("min_dot", 0.5))
            dot_matches_direction3(actual, origin, target, issues, label, min_dot)
        elif constraint_type == "distance_less_than":
            subject, subject_label = scene_3d_constraint_position(
                constraint, ["subject", "entity", "actor", "a"], snapshots, panel, scene, contract, issues, label
            )
            target, target_label = scene_3d_constraint_position(
                constraint, ["target", "to", "anchor", "b"], snapshots, panel, scene, contract, issues, label
            )
            comparison, comparison_label = scene_3d_constraint_position(
                constraint, ["comparison", "other", "reference", "c", "farther_than"], snapshots, panel, scene, contract, issues, label
            )
            if subject is None or target is None or comparison is None:
                continue
            subject_distance = vector3_distance(subject, target)
            comparison_distance = vector3_distance(comparison, target)
            margin = float(constraint.get("margin", constraint.get("min_delta", 0.001)))
            if subject_distance + margin >= comparison_distance:
                issues.append(
                    f"{label}: {subject_label} is not closer to {target_label} than {comparison_label} "
                    f"(subject_distance={subject_distance:.3f}, comparison_distance={comparison_distance:.3f}, margin={margin:.3f})."
                )
        elif constraint_type == "distance_at_least":
            subject, subject_label = scene_3d_constraint_position(
                constraint, ["subject", "entity", "actor", "a"], snapshots, panel, scene, contract, issues, label
            )
            target, target_label = scene_3d_constraint_position(
                constraint, ["target", "to", "anchor", "b"], snapshots, panel, scene, contract, issues, label
            )
            if subject is None or target is None:
                continue
            min_distance = float(constraint.get("min_distance", constraint.get("distance", constraint.get("min", 0))))
            actual_distance = vector3_distance(subject, target)
            if actual_distance < min_distance:
                issues.append(
                    f"{label}: distance between {subject_label} and {target_label} is {actual_distance:.3f}, "
                    f"min={min_distance:.3f}."
                )
        elif constraint_type == "occluder_between_3d":
            subject, subject_label = scene_3d_constraint_position(
                constraint, ["subject", "actor", "protected", "entity", "target"], snapshots, panel, scene, contract, issues, label
            )
            source, source_label = scene_3d_constraint_position(
                constraint, ["source", "threat", "from", "viewpoint_entity"], snapshots, panel, scene, contract, issues, label
            )
            occluder, occluder_label = scene_3d_constraint_position(
                constraint, ["occluder", "cover", "blocker", "object"], snapshots, panel, scene, contract, issues, label
            )
            if subject is None or source is None or occluder is None:
                continue
            segment_length = vector3_distance(subject, source)
            if segment_length == 0:
                issues.append(f"{label}: subject and source positions overlap, so occluder_between_3d cannot be validated.")
                continue
            tolerance = float(constraint.get("tolerance", segment_length * float(constraint.get("tolerance_ratio", 0.18))))
            tolerance = max(tolerance, 0.15)
            perpendicular, projection = point_to_segment_distance3(occluder, subject, source)
            if projection <= 0 or projection >= 1:
                issues.append(f"{label}: {occluder_label} is not between {subject_label} and {source_label} in 3D.")
            if perpendicular > tolerance:
                issues.append(
                    f"{label}: {occluder_label} is too far from the {subject_label}/{source_label} line "
                    f"(distance={perpendicular:.3f}, max={tolerance:.3f})."
                )
        elif constraint_type in {"same_side_as", "opposite_side_from"}:
            subject, subject_label = scene_3d_constraint_position(
                constraint, ["subject", "entity", "actor"], snapshots, panel, scene, contract, issues, label
            )
            reference, reference_label = scene_3d_constraint_position(
                constraint, ["reference_object", "reference", "anchor", "object"], snapshots, panel, scene, contract, issues, label
            )
            comparison, comparison_label = scene_3d_constraint_position(
                constraint, ["same_as", "as", "target", "comparison", "other"], snapshots, panel, scene, contract, issues, label
            )
            if subject is None or reference is None or comparison is None:
                continue
            normal = scene_3d_axis_vector(spatial_constraint_value(constraint, "normal_vector", "normal", "axis"))
            epsilon = float(constraint.get("tolerance", constraint.get("min_side_distance", 0.001)))
            if normal is not None:
                normal_len = vector3_length(normal)
                if normal_len == 0:
                    issues.append(f"{label}: side normal/axis cannot be zero-length.")
                    continue
                normal = (normal[0] / normal_len, normal[1] / normal_len, normal[2] / normal_len)
                subject_side = (
                    (subject[0] - reference[0]) * normal[0]
                    + (subject[1] - reference[1]) * normal[1]
                    + (subject[2] - reference[2]) * normal[2]
                )
                comparison_side = (
                    (comparison[0] - reference[0]) * normal[0]
                    + (comparison[1] - reference[1]) * normal[1]
                    + (comparison[2] - reference[2]) * normal[2]
                )
                product = subject_side * comparison_side
            else:
                product = (
                    (subject[0] - reference[0]) * (comparison[0] - reference[0])
                    + (subject[1] - reference[1]) * (comparison[1] - reference[1])
                    + (subject[2] - reference[2]) * (comparison[2] - reference[2])
                )
            if abs(product) <= epsilon:
                issues.append(f"{label}: side relation around {reference_label} is too close to the dividing plane to validate.")
            elif constraint_type == "same_side_as" and product < 0:
                issues.append(f"{label}: {subject_label} is not on the same side of {reference_label} as {comparison_label}.")
            elif constraint_type == "opposite_side_from" and product > 0:
                issues.append(f"{label}: {subject_label} is not on the opposite side of {reference_label} from {comparison_label}.")
        elif constraint_type == "max_transfer_distance":
            max_distance = float(constraint.get("max_distance", constraint.get("distance", constraint.get("max", 0))))
            if max_distance <= 0:
                issues.append(f"{label}: max_transfer_distance requires max_distance > 0.")
                continue
            origin, origin_label = scene_3d_constraint_position(
                constraint, ["origin", "from", "source", "sender", "actor"], snapshots, panel, scene, contract, issues, label
            )
            destination, destination_label = scene_3d_constraint_position(
                constraint, ["destination", "target", "to", "recipient"], snapshots, panel, scene, contract, issues, label
            )
            path_points = scene_3d_constraint_path_points(constraint, snapshots, panel, scene, contract, issues, label)
            if origin is None or destination is None:
                continue
            route = [origin] + path_points + [destination]
            actual_distance = sum(vector3_distance(route[index], route[index + 1]) for index in range(len(route) - 1))
            if actual_distance > max_distance:
                issues.append(
                    f"{label}: transfer distance from {origin_label} to {destination_label} is {actual_distance:.3f}, "
                    f"max={max_distance:.3f}."
                )
        elif constraint_type == "path_via":
            start, start_label = scene_3d_constraint_position(
                constraint, ["object", "entity", "subject", "source", "from"], snapshots, panel, scene, contract, issues, label
            )
            via, via_label = scene_3d_constraint_position(
                constraint, ["via", "waypoint", "through"], snapshots, panel, scene, contract, issues, label
            )
            destination, _ = scene_3d_constraint_position(
                constraint, ["destination", "target", "to"], snapshots, panel, scene, contract, [], label
            )
            if start is None or via is None:
                continue
            path_points = scene_3d_constraint_path_points(constraint, snapshots, panel, scene, contract, issues, label)
            if not path_points:
                object_id = str(spatial_constraint_value(constraint, "object", "entity", "subject", "source", "from") or "")
                object_state = scene_3d_snapshot_or_defined_state(snapshots, panel, object_id, scene, contract, [], label)
                motion = state_vector3(object_state, ["trajectory_vector", "motion_vector", "velocity_vector"], [], label)
                if motion is not None:
                    path_points = [vector3_add(start, motion)]
            route = [start] + path_points + ([destination] if destination is not None else [])
            if len(route) < 2:
                issues.append(f"{label}: path_via needs a path/waypoints, destination, or trajectory_vector.")
                continue
            tolerance = float(constraint.get("tolerance", 0.75))
            nearest = min(point_to_segment_distance3(via, route[index], route[index + 1])[0] for index in range(len(route) - 1))
            if nearest > tolerance:
                issues.append(
                    f"{label}: path from {start_label} does not pass near {via_label} "
                    f"(distance={nearest:.3f}, max={tolerance:.3f})."
                )


def scene_3d_contract_warnings(page: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if spatial_contract_coordinate_type(contract) != "scene_3d":
        return warnings
    for lock in contract.get("locks", []):
        lock_type = str(lock.get("type") or "")
        if lock_type not in {"soft", "inferred"}:
            continue
        note = str(lock.get("warning") or lock.get("rule") or "")
        if note:
            warnings.append(f"{page['id']} spatial_contract lock {lock.get('id')}: {lock_type} geometry warning: {note}.")
    return warnings


def contains_non_firing_cue(value: Any) -> bool:
    if isinstance(value, dict):
        return any(contains_non_firing_cue(entry) for entry in value.values())
    if isinstance(value, list):
        return any(contains_non_firing_cue(entry) for entry in value)
    text = str(value or "").lower()
    return any(cue in text for cue in NON_FIRING_CUES)


def has_no_line_of_fire_constraint(contract: dict[str, Any]) -> bool:
    return any(str(constraint.get("type") or "") == "no_line_of_fire" for constraint in contract.get("constraints", []))


def spatial_contract_issues(
    pages: list[dict[str, Any]], spatial_continuity_plan: dict[str, Any] | None = None
) -> list[str]:
    issues: list[str] = []
    pages_by_id = page_lookup_aliases(pages)
    for page in pages:
        contract = page.get("spatial_contract", {})
        if not spatial_contract_has_content(contract):
            continue
        entities = contract.get("entities", [])
        entity_ids = [str(entity.get("id") or "") for entity in entities]
        entity_id_set = {entity_id for entity_id in entity_ids if entity_id}
        if len(entity_id_set) != len([entity_id for entity_id in entity_ids if entity_id]):
            issues.append(f"{page['id']} spatial_contract: duplicate entity ids are not allowed.")
        if not entity_id_set:
            issues.append(f"{page['id']} spatial_contract: at least one entity is required when spatial_contract is present.")
        if spatial_contract_coordinate_type(contract) == "scene_3d":
            validate_scene_3d_contract(page, contract, spatial_continuity_plan, issues)
            continue
        if spatial_contract_coordinate_type(contract) == "panel_screen_2d":
            if spatial_contract_has_scene_3d_default_cues(page, contract) and not panel_screen_2d_exception_reason(page, contract):
                issues.append(
                    f"{page['id']} spatial_contract: spatially important page should use coordinate_space.type scene_3d "
                    "or provide an explicit panel_screen_2d exception_reason."
                )
        snapshots = spatial_snapshots_by_panel(contract)
        non_firing_payload = {
            "narrative_plan": page.get("narrative_plan"),
            "spatial_logic_notes": page.get("spatial_logic_notes"),
            "motion_checks": page.get("motion_checks"),
            "must_match": page.get("must_match"),
            "panels": page.get("panels"),
            "panel_snapshots": contract.get("panel_snapshots"),
        }
        if contains_non_firing_cue(non_firing_payload) and not has_no_line_of_fire_constraint(contract):
            issues.append(f"{page['id']} spatial_contract: non-firing spatial cue requires a no_line_of_fire constraint.")
        for snapshot in contract.get("panel_snapshots", []):
            panel = panel_key(snapshot.get("panel"))
            for state in snapshot.get("entities", []):
                entity_id = str(state.get("id") or "")
                if entity_id not in entity_id_set:
                    issues.append(f"{page['id']} spatial_contract panel {panel}: unknown entity {entity_id}.")
                if "position" in state and vector2(state.get("position")) is None:
                    issues.append(f"{page['id']} spatial_contract panel {panel}: entity {entity_id} has invalid position.")
                if "screen_box" in state and rect4(state.get("screen_box")) is None:
                    issues.append(f"{page['id']} spatial_contract panel {panel}: entity {entity_id} has invalid screen_box.")
                for field in ["facing_vector", "gaze_vector", "aim_vector", "trajectory_vector"]:
                    if field in state and vector2(state.get(field)) is None:
                        issues.append(f"{page['id']} spatial_contract panel {panel}: entity {entity_id} has invalid {field}.")

        for index, constraint in enumerate(contract.get("constraints", []), start=1):
            constraint_type = str(constraint.get("type") or "")
            label = f"{page['id']} spatial_contract constraint {index} ({constraint_type or 'missing_type'})"
            if constraint_type not in SPATIAL_CONSTRAINT_TYPES:
                issues.append(f"{label}: unsupported constraint type.")
                continue
            if constraint_type in SCENE_3D_ONLY_CONSTRAINT_TYPES:
                issues.append(f"{label}: {constraint_type} requires coordinate_space.type scene_3d.")
                continue
            if constraint_type == "same_landmark_relation_as":
                validate_same_landmark_relation(pages_by_id, page, constraint, index, issues)
                continue
            if constraint_type == "same_cover_as":
                validate_temporal_persistence(
                    pages,
                    pages_by_id,
                    page,
                    contract,
                    constraint,
                    index,
                    issues,
                    ["cover"],
                )
                continue
            if constraint_type == "state_persists_from":
                validate_temporal_persistence(
                    pages,
                    pages_by_id,
                    page,
                    contract,
                    constraint,
                    index,
                    issues,
                    ["pose", "cover", "visibility", "occlusion", "location_anchor", "held_props", "state_tags"],
                )
                continue
            if constraint_type == "occlusion_persists_from":
                validate_temporal_persistence(
                    pages,
                    pages_by_id,
                    page,
                    contract,
                    constraint,
                    index,
                    issues,
                    ["cover", "visibility", "occlusion", "occluded_by"],
                )
                continue
            if constraint_type == "allowed_transition":
                validate_allowed_transition(pages_by_id, page, constraint, index, issues)
                continue
            if constraint_type == "requires_cause":
                validate_requires_cause(pages_by_id, page, constraint, index, issues)
                continue

            panel = constraint_panel(contract, constraint, issues, label)
            if not panel:
                continue
            if constraint_type == "aims_at":
                actor_id = str(spatial_constraint_value(constraint, "actor", "source", "shooter", "from", "entity") or "")
                target_id = str(spatial_constraint_value(constraint, "target", "to") or "")
                vector_entity_id = str(spatial_constraint_value(constraint, "weapon", "object", "vector_entity") or actor_id)
                actor_state = snapshot_state(snapshots, panel, actor_id, issues, label)
                vector_state = snapshot_state(snapshots, panel, vector_entity_id, issues, label)
                target_state = snapshot_state(snapshots, panel, target_id, issues, label)
                origin = state_position(vector_state or actor_state, issues, label)
                target = state_position(target_state, issues, label)
                actual = state_vector(vector_state or actor_state, ["aim_vector", "facing_vector", "gaze_vector"], issues, label)
                min_dot = float(constraint.get("min_dot", 0.5))
                dot_matches_direction(actual, origin, target, issues, label, min_dot)
            elif constraint_type == "trajectory_to":
                object_id = str(spatial_constraint_value(constraint, "object", "projectile", "source", "entity") or "")
                target_id = str(spatial_constraint_value(constraint, "target", "to") or "")
                object_state = snapshot_state(snapshots, panel, object_id, issues, label)
                target_state = snapshot_state(snapshots, panel, target_id, issues, label)
                origin = state_position(object_state, issues, label)
                target = state_position(target_state, issues, label)
                actual = state_vector(object_state, ["trajectory_vector", "motion_vector", "velocity_vector"], issues, label)
                min_dot = float(constraint.get("min_dot", 0.5))
                dot_matches_direction(actual, origin, target, issues, label, min_dot)
            elif constraint_type in {"cover_between", "behind_cover_from", "line_of_sight_blocked"}:
                cover_id = str(spatial_constraint_value(constraint, "cover", "blocker", "object") or "")
                actor_id = str(spatial_constraint_value(constraint, "actor", "subject", "protected", "target") or "")
                threat_id = str(spatial_constraint_value(constraint, "threat", "source", "from", "enemy") or "")
                cover_state = snapshot_state(snapshots, panel, cover_id, issues, label)
                actor_state = snapshot_state(snapshots, panel, actor_id, issues, label)
                threat_state = snapshot_state(snapshots, panel, threat_id, issues, label)
                cover = state_position(cover_state, issues, label)
                actor = state_position(actor_state, issues, label)
                threat = state_position(threat_state, issues, label)
                constraint_has_screen_box = "screen_box" in constraint
                screen_box = rect4(spatial_constraint_value(constraint, "screen_box"))
                if constraint_has_screen_box and screen_box is None:
                    issues.append(f"{label}: invalid screen_box.")
                elif screen_box is None and cover_state:
                    screen_box = rect4(cover_state.get("screen_box"))
                if screen_box is not None:
                    cover_screen_box_between(screen_box, actor, threat, issues, label)
                else:
                    tolerance_ratio = float(constraint.get("tolerance_ratio", 0.25))
                    cover_between_points(cover, actor, threat, issues, label, tolerance_ratio)
            elif constraint_type in {"no_line_of_fire", "not_aims_at"}:
                source_id = str(spatial_constraint_value(constraint, "source", "actor", "from", "entity") or "")
                target_id = str(spatial_constraint_value(constraint, "target", "to") or "")
                vector_entity_id = str(spatial_constraint_value(constraint, "weapon", "object", "vector_entity") or source_id)
                source_state = snapshot_state(snapshots, panel, source_id, issues, label)
                vector_state = snapshot_state(snapshots, panel, vector_entity_id, issues, label)
                target_state = snapshot_state(snapshots, panel, target_id, issues, label)
                origin = state_position(vector_state or source_state, issues, label)
                target = state_position(target_state, issues, label)
                actual = state_vector(vector_state or source_state, ["aim_vector", "facing_vector", "gaze_vector", "trajectory_vector"], [], label)
                max_dot = float(constraint.get("max_dot", 0.2))
                dot_exceeds_forbidden_direction(actual, origin, target, issues, label, max_dot)
            elif constraint_type in {"left_of", "right_of"}:
                subject_id = str(spatial_constraint_value(constraint, "subject", "actor", "entity") or "")
                anchor_id = str(spatial_constraint_value(constraint, "anchor", "target", "of") or "")
                subject_state = snapshot_state(snapshots, panel, subject_id, issues, label)
                anchor_state = snapshot_state(snapshots, panel, anchor_id, issues, label)
                subject = state_position(subject_state, issues, label)
                anchor = state_position(anchor_state, issues, label)
                tolerance = float(constraint.get("tolerance", 0.001))
                if subject is None or anchor is None:
                    continue
                if constraint_type == "left_of" and not subject[0] < anchor[0] - tolerance:
                    issues.append(f"{label}: {subject_id} is not left of {anchor_id}.")
                if constraint_type == "right_of" and not subject[0] > anchor[0] + tolerance:
                    issues.append(f"{label}: {subject_id} is not right of {anchor_id}.")
    return issues


def spatial_plan_issues(pages: list[dict[str, Any]], spatial_continuity_plan: dict[str, Any] | None = None) -> list[str]:
    issues = spatial_contract_issues(pages, spatial_continuity_plan)
    if spatial_continuity_plan is not None:
        issues.extend(spatial_continuity_issues(spatial_continuity_plan, pages))
    return issues


def spatial_contract_warnings(pages: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for page in pages:
        contract = page.get("spatial_contract", {})
        if not spatial_contract_has_content(contract):
            continue
        warnings.extend(scene_3d_contract_warnings(page, contract))
    return warnings


def spatial_plan_warnings(pages: list[dict[str, Any]], spatial_continuity_plan: dict[str, Any] | None = None) -> list[str]:
    del spatial_continuity_plan
    return spatial_contract_warnings(pages)


def assert_spatial_contracts_pass(
    pages: list[dict[str, Any]], spatial_continuity_plan: dict[str, Any] | None = None
) -> None:
    issues = spatial_plan_issues(pages, spatial_continuity_plan)
    if issues:
        details = "\n".join(f"- {issue}" for issue in issues)
        raise SystemExit(f"Spatial contract check failed:\n{details}")


def escape_html(value: Any) -> str:
    return html.escape(str(value), quote=True)


def preview_issue_map(pages: list[dict[str, Any]], issues: list[str]) -> dict[str, list[str]]:
    mapped = {str(page.get("id")): [] for page in pages}
    for issue in issues:
        assigned = False
        for page in pages:
            page_id = str(page.get("id") or "")
            aliases = {
                page_id,
                str(page.get("filename") or ""),
                Path(str(page.get("filename") or "")).stem,
            }
            if any(alias and (issue == alias or issue.startswith(alias + " ")) for alias in aliases):
                mapped.setdefault(page_id, []).append(issue)
                assigned = True
                break
        if not assigned:
            mapped.setdefault("_global", []).append(issue)
    return mapped


def build_spatial_preview_model(pages: list[dict[str, Any]], issues: list[str], warnings: list[str] | None = None) -> dict[str, Any]:
    issue_map = preview_issue_map(pages, issues)
    return {
        "title": "Spatial contract preview",
        "source": "",
        "status": "fail" if issues else "pass",
        "issues": issues,
        "warnings": warnings or [],
        "issue_map": issue_map,
        "page_count": len(pages),
        "structured_page_count": spatial_contract_page_count(pages),
        "pages": pages,
    }


def preview_clamp(value: float, minimum: float = 2.0, maximum: float = 98.0) -> float:
    return max(minimum, min(maximum, value))


def preview_point(state: dict[str, Any] | None) -> tuple[float, float] | None:
    if not state:
        return None
    position = vector2(state.get("position"))
    if position is None:
        return None
    return (preview_clamp(position[0] * 100.0), preview_clamp(position[1] * 100.0))


def preview_arrow_end(origin: tuple[float, float], vector: tuple[float, float], length: float) -> tuple[float, float]:
    vector_len = vector_length(vector)
    if vector_len == 0:
        return origin
    return (
        preview_clamp(origin[0] + (vector[0] / vector_len) * length),
        preview_clamp(origin[1] + (vector[1] / vector_len) * length),
    )


def preview_entity_classes(entity: dict[str, Any]) -> str:
    entity_type = slugify(str(entity.get("type") or "entity"), "entity")
    role = slugify(str(entity.get("role") or ""), "")
    classes = ["entity", f"entity-{entity_type}"]
    if "cover" in role:
        classes.append("entity-cover")
    return " ".join(classes)


def preview_state_title(entity: dict[str, Any], state: dict[str, Any]) -> str:
    details = [
        f"id={state.get('id')}",
        f"type={entity.get('type') or 'unknown'}",
    ]
    if entity.get("role"):
        details.append(f"role={entity.get('role')}")
    for field in [
        "position",
        "facing_vector",
        "gaze_vector",
        "aim_vector",
        "trajectory_vector",
        "pose",
        "cover",
        "visibility",
        "occlusion",
        "location_anchor",
        "held_props",
        "state_tags",
    ]:
        if field in state:
            details.append(f"{field}={format_spatial_value(state[field])}")
    return "; ".join(details)


def preview_constraint_title(constraint: dict[str, Any]) -> str:
    fields = [
        f"{key}={format_spatial_value(value)}"
        for key, value in constraint.items()
        if value is not None and value != ""
    ]
    return ", ".join(fields)


def preview_constraint_state(
    states: dict[str, dict[str, Any]],
    constraint: dict[str, Any],
    *names: str,
) -> dict[str, Any] | None:
    entity_id = str(spatial_constraint_value(constraint, *names) or "")
    return states.get(entity_id)


def render_preview_line(
    start: tuple[float, float],
    end: tuple[float, float],
    css_class: str,
    title: str,
    marker: bool = False,
) -> str:
    marker_attr = ' marker-end="url(#arrow)"' if marker else ""
    return (
        f'<line class="{css_class}" x1="{start[0]:.2f}" y1="{start[1]:.2f}" '
        f'x2="{end[0]:.2f}" y2="{end[1]:.2f}"{marker_attr}>'
        f"<title>{escape_html(title)}</title></line>"
    )


def render_spatial_preview_relations(
    contract: dict[str, Any],
    snapshot: dict[str, Any],
    states: dict[str, dict[str, Any]],
) -> list[str]:
    lines: list[str] = []
    panel = panel_key(snapshot.get("panel"))
    for constraint in contract.get("constraints", []):
        constraint_type = str(constraint.get("type") or "")
        constraint_panel_value = panel_key(spatial_constraint_value(constraint, "panel", "panel_id"))
        if constraint_panel_value and constraint_panel_value != panel:
            continue
        title = preview_constraint_title(constraint)
        if constraint_type == "aims_at":
            actor_state = preview_constraint_state(states, constraint, "actor", "source", "shooter", "from", "entity")
            vector_state = preview_constraint_state(states, constraint, "weapon", "object", "vector_entity") or actor_state
            target_state = preview_constraint_state(states, constraint, "target", "to")
            origin = preview_point(vector_state)
            target = preview_point(target_state)
            if origin and target:
                lines.append(render_preview_line(origin, target, "relation relation-aim", title, marker=True))
        elif constraint_type == "trajectory_to":
            object_state = preview_constraint_state(states, constraint, "object", "projectile", "source", "entity")
            target_state = preview_constraint_state(states, constraint, "target", "to")
            origin = preview_point(object_state)
            target = preview_point(target_state)
            if origin and target:
                lines.append(render_preview_line(origin, target, "relation relation-trajectory", title, marker=True))
        elif constraint_type in {"cover_between", "behind_cover_from", "line_of_sight_blocked"}:
            actor_state = preview_constraint_state(states, constraint, "actor", "subject", "protected", "target")
            threat_state = preview_constraint_state(states, constraint, "threat", "source", "from", "enemy")
            cover_state = preview_constraint_state(states, constraint, "cover", "blocker", "object")
            actor = preview_point(actor_state)
            threat = preview_point(threat_state)
            cover = preview_point(cover_state)
            if actor and threat:
                lines.append(render_preview_line(actor, threat, "relation relation-cover-line", title))
            if actor and threat and cover:
                midpoint = ((actor[0] + threat[0]) / 2.0, (actor[1] + threat[1]) / 2.0)
                lines.append(render_preview_line(cover, midpoint, "relation relation-cover-anchor", title))
        elif constraint_type in {"left_of", "right_of"}:
            subject_state = preview_constraint_state(states, constraint, "subject", "actor", "entity")
            subject = preview_point(subject_state)
            if subject:
                label = "&lt;" if constraint_type == "left_of" else "&gt;"
                lines.append(
                    f'<text class="relation-label" x="{subject[0]:.2f}" y="{preview_clamp(subject[1] - 6):.2f}">'
                    f"{label}<title>{escape_html(title)}</title></text>"
                )
    return lines


def render_spatial_preview_vectors(states: dict[str, dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    vector_fields = [
        ("facing_vector", "vector vector-facing", 10.0),
        ("gaze_vector", "vector vector-gaze", 12.0),
        ("aim_vector", "vector vector-aim", 16.0),
        ("trajectory_vector", "vector vector-trajectory", 18.0),
    ]
    for state in states.values():
        origin = preview_point(state)
        if not origin:
            continue
        for field, css_class, length in vector_fields:
            vector = vector2(state.get(field))
            if vector is None:
                continue
            end = preview_arrow_end(origin, vector, length)
            title = f"{state.get('id')} {field}={format_spatial_value(state.get(field))}"
            lines.append(render_preview_line(origin, end, css_class, title, marker=True))
    return lines


def render_spatial_preview_entities(
    contract: dict[str, Any],
    states: dict[str, dict[str, Any]],
) -> list[str]:
    elements: list[str] = []
    entities = {str(entity.get("id") or ""): entity for entity in contract.get("entities", [])}
    for entity_id, state in states.items():
        point = preview_point(state)
        if not point:
            continue
        entity = entities.get(entity_id, {"id": entity_id, "type": "entity", "role": ""})
        classes = preview_entity_classes(entity)
        title = preview_state_title(entity, state)
        label = escape_html(entity_id)
        x, y = point
        if str(entity.get("type") or "").lower() == "landmark":
            shape = (
                f'<polygon points="{x:.2f},{y - 4.8:.2f} {x + 4.8:.2f},{y:.2f} '
                f'{x:.2f},{y + 4.8:.2f} {x - 4.8:.2f},{y:.2f}" />'
            )
        elif "cover" in str(entity.get("role") or "").lower() or str(entity.get("type") or "").lower() in {"object", "prop"}:
            shape = f'<rect x="{x - 4.5:.2f}" y="{y - 4.5:.2f}" width="9" height="9" rx="1.5" />'
        else:
            shape = f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.7" />'
        elements.append(
            f'<g class="{classes}"><title>{escape_html(title)}</title>{shape}'
            f'<text class="entity-label" x="{preview_clamp(x + 6, 0, 100):.2f}" y="{preview_clamp(y + 2, 0, 100):.2f}">{label}</text></g>'
        )
    return elements


def render_spatial_preview_snapshot(page: dict[str, Any], snapshot: dict[str, Any]) -> str:
    contract = page.get("spatial_contract", {})
    panel = panel_key(snapshot.get("panel"))
    states = {
        str(state.get("id") or ""): state
        for state in snapshot.get("entities", [])
        if str(state.get("id") or "")
    }
    relation_lines = render_spatial_preview_relations(contract, snapshot, states)
    vector_lines = render_spatial_preview_vectors(states)
    entity_elements = render_spatial_preview_entities(contract, states)
    panel_title = f"{page.get('filename')} panel {panel}"
    body = "\n".join([*relation_lines, *vector_lines, *entity_elements])
    return f"""
<section class="panel-preview">
  <div class="panel-title">Panel {escape_html(panel)}</div>
  <svg class="spatial-svg" viewBox="0 0 100 100" role="img" aria-label="{escape_html(panel_title)}">
    <defs>
      <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
        <path d="M0,0 L6,3 L0,6 z" />
      </marker>
    </defs>
    <rect class="panel-bg" x="1" y="1" width="98" height="98" rx="3" />
    {body}
  </svg>
</section>"""


def render_spatial_preview_entity_legend(page: dict[str, Any]) -> str:
    contract = page.get("spatial_contract", {})
    rows = []
    for entity in contract.get("entities", []):
        blocking_symbol = entity.get("blocking_symbol")
        entity_id = str(entity.get("id") or "")
        targets_attr = preview_targets_attribute([entity_id])
        rows.append(
            f"<tr{targets_attr}>"
            f"<td><code>{escape_html(entity_id)}</code></td>"
            f"<td>{escape_html(entity.get('type') or '')}</td>"
            f"<td>{escape_html(entity.get('role') or '')}</td>"
            f"<td>{escape_html(format_spatial_value(blocking_symbol) if blocking_symbol else '')}</td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="4" class="empty">No entities.</td></tr>')
    return "\n".join(rows)


def render_spatial_preview_constraint_list(page: dict[str, Any]) -> str:
    contract = page.get("spatial_contract", {})
    items = []
    cross_panel_types = {
        "same_landmark_relation_as",
        "same_cover_as",
        "state_persists_from",
        "occlusion_persists_from",
        "allowed_transition",
        "requires_cause",
    }
    for constraint in contract.get("constraints", []):
        css_class = "constraint cross-panel" if constraint.get("type") in cross_panel_types else "constraint"
        targets_attr = preview_targets_attribute(preview_target_entities(constraint))
        items.append(
            f'<li class="{css_class}"{targets_attr}><code>{escape_html(constraint.get("id") or "")}</code> '
            f'<span>{escape_html(constraint.get("type") or "")}</span>'
            f'<small>{escape_html(preview_constraint_title(constraint))}</small></li>'
        )
    if not items:
        items.append('<li class="empty">No constraints.</li>')
    return "\n".join(items)


def render_spatial_preview_lock_list(page: dict[str, Any]) -> str:
    contract = page.get("spatial_contract", {})
    items = []
    for lock in contract.get("locks", []):
        lock_type = str(lock.get("type") or "")
        targets_attr = preview_targets_attribute(preview_target_entities(lock))
        items.append(
            f'<li class="lock lock-{escape_html(lock_type)}"{targets_attr}><code>{escape_html(lock.get("id") or "")}</code> '
            f'<span>{escape_html(lock_type)}</span>'
            f'<small>{escape_html(preview_constraint_title(lock))}</small></li>'
        )
    if not items:
        items.append('<li class="empty">No locks.</li>')
    return "\n".join(items)


def render_spatial_preview_transition_list(page: dict[str, Any]) -> str:
    contract = page.get("spatial_contract", {})
    items = []
    for transition in contract.get("transitions", []):
        targets_attr = preview_targets_attribute(preview_target_entities(transition))
        items.append(
            f'<li class="transition"{targets_attr}><code>{escape_html(transition.get("id") or "")}</code> '
            f'<small>{escape_html(preview_constraint_title(transition))}</small></li>'
        )
    if not items:
        items.append('<li class="empty">No transitions.</li>')
    return "\n".join(items)


def render_spatial_preview_annotation_list(page: dict[str, Any]) -> str:
    contract = page.get("spatial_contract", {})
    items = []
    for annotation in contract.get("annotations", []):
        targets_attr = preview_targets_attribute(preview_target_entities(annotation))
        text = annotation.get("text") or annotation.get("note") or annotation.get("value") or ""
        panel = panel_key(annotation.get("panel"))
        panel_label = f"panel {panel} | " if panel else ""
        items.append(
            f'<li class="annotation"{targets_attr}><code>{escape_html(annotation.get("id") or "")}</code> '
            f'<small>{escape_html(panel_label + str(text))}</small></li>'
        )
    if not items:
        items.append('<li class="empty">No annotations.</li>')
    return "\n".join(items)


PREVIEW_TARGET_FIELDS = (
    "actor",
    "anchor",
    "cover",
    "destination_entity",
    "entity",
    "object",
    "occluder",
    "origin_entity",
    "source",
    "subject",
    "target",
    "threat",
    "vector_entity",
    "viewpoint_entity",
    "line_from",
    "line_to",
)


def preview_target_entities(item: dict[str, Any]) -> list[str]:
    targets: set[str] = set()
    for field in PREVIEW_TARGET_FIELDS:
        value = item.get(field)
        if isinstance(value, str) and value:
            targets.add(value)
        elif isinstance(value, list):
            if field in {"line_from", "line_to"} and all(isinstance(entry, (int, float)) for entry in value):
                continue
            targets.update(str(entry) for entry in value if str(entry or ""))
    entities = item.get("entities")
    if isinstance(entities, list):
        targets.update(str(entry) for entry in entities if str(entry or ""))
    return sorted(targets)


def preview_targets_attribute(targets: list[str]) -> str:
    clean_targets = [target for target in targets if target]
    if not clean_targets:
        return ""
    target_text = escape_html(" ".join(clean_targets))
    return f' data-preview-targets="{target_text}" tabindex="0"'


def preview_compact_label(entity_id: str, entity: dict[str, Any] | None = None) -> str:
    entity = entity or {}
    explicit = entity.get("preview_label")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()[:10]
    tokens = [token for token in re.split(r"[^A-Za-z0-9]+", entity_id) if token]
    priority_tokens = {
        "apc",
        "car",
        "cover",
        "door",
        "mag",
        "magazine",
        "railing",
        "shield",
        "slab",
        "stair",
        "wall",
        "window",
    }
    for token in reversed(tokens):
        if token.lower() in priority_tokens:
            return token.upper()[:10]
    for token in tokens:
        if token.lower() not in {"the", "a", "an", "of", "left", "right", "front", "back", "floor", "level"}:
            return token.upper()[:10]
    return entity_id[:10].upper()


def scene_3d_level_for_position(scene: dict[str, Any] | None, position: Any) -> str:
    point = vector3(position)
    if point is None:
        return ""
    for level in (scene or {}).get("levels", []):
        if scene_3d_level_contains_z(level, point[2]):
            return str(level.get("id") or "")
    return ""


def render_scene_3d_status_strip(page: dict[str, Any], scene: dict[str, Any] | None) -> str:
    contract = page.get("spatial_contract", {})
    entity_defs = {str(entity.get("id") or ""): entity for entity in contract.get("entities", [])}
    first_snapshot = (contract.get("panel_snapshots") or [{}])[0] or {}
    level_items: list[str] = []
    seen_level_items: set[str] = set()
    for state in first_snapshot.get("entities", []):
        entity_id = str(state.get("id") or "")
        if not entity_id:
            continue
        entity = entity_defs.get(entity_id, {})
        entity_type = str(entity.get("type") or "").lower()
        role = str(entity.get("role") or "").lower()
        level_id = str(state.get("level_id") or "") or scene_3d_level_for_position(scene, state.get("position"))
        is_focus = entity_type == "character" or "cover" in role or bool(state.get("trajectory_vector")) or bool(level_id)
        if is_focus:
            label = preview_compact_label(entity_id, entity)
            item = f"{label} {level_id}".strip()
            if item not in seen_level_items:
                level_items.append(item)
                seen_level_items.add(item)
    transitions = contract.get("transitions") or []
    hard_locks = [lock for lock in contract.get("locks", []) if str(lock.get("type") or "") == "hard"]
    chips = []
    for item in level_items[:6]:
        chips.append(f'<span>{escape_html(item)}</span>')
    if transitions:
        chips.append(f'<span>{len(transitions)} transition path(s)</span>')
    if hard_locks:
        chips.append(f'<span>{len(hard_locks)} hard lock(s)</span>')
    if not chips:
        chips.append("<span>scene_3d validation focus</span>")
    return f'<div class="scene-3d-status-strip" data-scene3d-status-strip>{"".join(chips)}</div>'


def scene_3d_preview_payload(page: dict[str, Any], scene: dict[str, Any] | None) -> str:
    payload = {
        "page_id": page.get("id"),
        "filename": page.get("filename"),
        "scene": scene or {},
        "contract": page.get("spatial_contract") or {},
    }
    return escape_html(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def render_scene_3d_preview(page: dict[str, Any], scene: dict[str, Any] | None) -> str:
    contract = page.get("spatial_contract", {})
    if spatial_contract_coordinate_type(contract) != "scene_3d":
        return ""
    scene_id = (contract.get("coordinate_space") or {}).get("scene_id") or ""
    levels = ", ".join(
        str(level.get("id") or "")
        for level in (scene or {}).get("levels", [])
        if str(level.get("id") or "")
    )
    snapshots = ", ".join(panel_key(snapshot.get("panel")) for snapshot in contract.get("panel_snapshots", []))
    return f"""
<section class="scene-3d-preview">
  <div class="scene-3d-header">
    <div>
      <h3>Scene 3D Preview</h3>
      <p>scene_id: <code>{escape_html(scene_id)}</code> | levels: {escape_html(levels or 'none')} | panels: {escape_html(snapshots or 'none')}</p>
    </div>
    <span class="pill">validation-only provisional scene</span>
  </div>
  <div class="scene-3d-controls" data-scene3d-controls>
    <button type="button" data-scene3d-control="reset">Reset</button>
    <button type="button" data-scene3d-control="top">Top</button>
    <button type="button" data-scene3d-control="front">Front</button>
    <button type="button" data-scene3d-control="side">Side</button>
    <button type="button" data-scene3d-control="iso">Iso</button>
    <button type="button" data-scene3d-control="camera">Camera</button>
    <span class="scene-3d-label-mode" data-scene3d-label-controls>
      Labels:
      <button type="button" data-scene3d-label-mode="key">key</button>
      <button type="button" data-scene3d-label-mode="all">all</button>
      <button type="button" data-scene3d-label-mode="off">off</button>
    </span>
    <span class="scene-3d-layer-controls" data-scene3d-layer-controls>
      Layers:
      <button type="button" data-scene3d-layer="actors">Actors</button>
      <button type="button" data-scene3d-layer="obstacles">Obstacles</button>
      <button type="button" data-scene3d-layer="landmarks">Landmarks</button>
      <button type="button" data-scene3d-layer="relations">Relations</button>
      <button type="button" data-scene3d-layer="vectors">Vectors</button>
      <button type="button" data-scene3d-layer="levels">Levels</button>
      <button type="button" data-scene3d-layer="annotations">Annotations</button>
      <button type="button" data-scene3d-layer="camera">Camera</button>
      <button type="button" data-scene3d-layer="ghosts">Ghosts</button>
    </span>
    <label class="scene-3d-sync"><input type="checkbox" data-scene3d-control="sync"> Sync scene view</label>
    <span class="scene-3d-status" data-scene3d-status>yaw: -45deg | pitch: -35deg | zoom: 1.00 | panel: none</span>
    <span class="scene-3d-panel-buttons" data-scene3d-panels></span>
  </div>
  {render_scene_3d_status_strip(page, scene)}
  <canvas class="scene-3d-canvas" width="720" height="420" data-scene-id="{escape_html(scene_id)}" data-scene3d="{scene_3d_preview_payload(page, scene)}" tabindex="0" aria-label="Scene 3D orbit preview"></canvas>
  <div class="scene-3d-level-rail" data-scene3d-level-rail></div>
  <p class="scene-3d-note">Drag to orbit, shift-drag or middle-drag to pan, wheel to zoom. Hard locks are rerun criteria. Soft/inferred geometry may reconcile after approved storyboard inspection; the first panel can act as a calibration anchor when it has no prior continuity.</p>
</section>"""


def render_spatial_preview_page(page: dict[str, Any], issues: list[str], scenes_by_id: dict[str, dict[str, Any]] | None = None) -> str:
    contract = page.get("spatial_contract", {})
    issue_items = "\n".join(f"<li>{escape_html(issue)}</li>" for issue in issues)
    if not issue_items:
        issue_items = '<li class="empty">No spatial-check issues.</li>'
    if not spatial_contract_has_content(contract):
        snapshots = '<p class="empty">No structured spatial_contract supplied.</p>'
    elif not contract.get("panel_snapshots"):
        snapshots = '<p class="empty">No panel_snapshots supplied.</p>'
    else:
        snapshots = "\n".join(render_spatial_preview_snapshot(page, snapshot) for snapshot in contract.get("panel_snapshots", []))
    scene_id = str((contract.get("coordinate_space") or {}).get("scene_id") or "")
    scene_preview = render_scene_3d_preview(page, (scenes_by_id or {}).get(scene_id))
    snapshot_preview = "" if scene_preview else f'<div class="panel-grid">{snapshots}</div>'
    return f"""
<article class="page-card" id="page-{escape_html(page.get('id') or '')}" data-preview-page-id="{escape_html(page.get('id') or '')}">
  <header class="page-card-header">
    <div>
      <h2>{escape_html(page.get('filename') or page.get('id') or '')}</h2>
      <p>{escape_html(page.get('layout_brief') or '')}</p>
    </div>
    <span class="issue-badge {'has-issues' if issues else ''}">{len(issues)} issue(s)</span>
  </header>
  <div class="page-grid">
    <div>
      {scene_preview}
      {snapshot_preview}
    </div>
    <aside class="legend">
      <h3>Entities</h3>
      <table>
        <thead><tr><th>id</th><th>type</th><th>role</th><th>blocking_symbol</th></tr></thead>
        <tbody>{render_spatial_preview_entity_legend(page)}</tbody>
      </table>
      <h3>Locks</h3>
      <ul class="constraint-list">{render_spatial_preview_lock_list(page)}</ul>
      <h3>Transitions</h3>
      <ul class="constraint-list">{render_spatial_preview_transition_list(page)}</ul>
      <h3>Annotations</h3>
      <ul class="constraint-list">{render_spatial_preview_annotation_list(page)}</ul>
      <h3>Constraints</h3>
      <ul class="constraint-list">{render_spatial_preview_constraint_list(page)}</ul>
      <h3>Issues</h3>
      <ul class="issue-list">{issue_items}</ul>
    </aside>
  </div>
</article>"""


def render_spatial_preview_html(model: dict[str, Any]) -> str:
    pages = model.get("pages", [])
    issue_map = model.get("issue_map", {})
    scenes_by_id = scene_3d_scenes_by_id(model.get("spatial_continuity_plan"))
    page_nav = []
    page_cards = []
    for page in pages:
        page_id = str(page.get("id") or "")
        page_issues = issue_map.get(page_id, [])
        page_nav.append(
            f'<a href="#page-{escape_html(page_id)}"><span>{escape_html(page.get("filename") or page_id)}</span>'
            f'<strong class="{"has-issues" if page_issues else ""}">{len(page_issues)}</strong></a>'
        )
        page_cards.append(render_spatial_preview_page(page, page_issues, scenes_by_id))
    all_issues = "\n".join(f"<li>{escape_html(issue)}</li>" for issue in model.get("issues", []))
    if not all_issues:
        all_issues = '<li class="empty">No spatial-check issues.</li>'
    all_warnings = "\n".join(f"<li>{escape_html(warning)}</li>" for warning in model.get("warnings", []))
    if not all_warnings:
        all_warnings = '<li class="empty">No spatial-check warnings.</li>'
    nav = "\n".join(page_nav) or '<span class="empty">No pages.</span>'
    cards = "\n".join(page_cards) or '<p class="empty">No pages to preview.</p>'
    status_class = "status-fail" if model.get("status") == "fail" else "status-pass"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape_html(model.get('title') or 'Spatial contract preview')}</title>
  <style>
    :root {{ color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ margin: 0; background: #f5f6f8; color: #17202a; }}
    header.app-header {{ position: sticky; top: 0; z-index: 5; background: #ffffff; border-bottom: 1px solid #d8dee8; padding: 14px 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 20px; }}
    h2 {{ margin: 0; font-size: 17px; }}
    h3 {{ margin: 16px 0 8px; font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: #526071; }}
    p {{ margin: 4px 0 0; color: #526071; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }}
    .summary {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}
    .pill {{ border: 1px solid #cbd5e1; border-radius: 999px; padding: 4px 9px; font-size: 13px; background: #f8fafc; }}
    .status-pass {{ color: #166534; background: #ecfdf3; border-color: #bbf7d0; }}
    .status-fail {{ color: #991b1b; background: #fef2f2; border-color: #fecaca; }}
    .layout {{ display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 18px; padding: 18px; }}
    nav {{ position: sticky; top: 86px; align-self: start; background: #ffffff; border: 1px solid #d8dee8; border-radius: 8px; padding: 10px; }}
    nav a {{ display: flex; justify-content: space-between; gap: 8px; color: #17202a; text-decoration: none; padding: 8px; border-radius: 6px; font-size: 13px; }}
    nav a:hover {{ background: #f1f5f9; }}
    nav strong {{ min-width: 22px; text-align: center; border-radius: 999px; background: #e2e8f0; }}
    nav strong.has-issues, .issue-badge.has-issues {{ background: #fee2e2; color: #991b1b; }}
    .global-issues, .page-card {{ background: #ffffff; border: 1px solid #d8dee8; border-radius: 8px; margin-bottom: 18px; overflow: hidden; }}
    .global-issues {{ padding: 12px 14px; }}
    .page-card-header {{ display: flex; justify-content: space-between; gap: 12px; padding: 13px 14px; border-bottom: 1px solid #e5eaf1; }}
    .issue-badge {{ height: fit-content; border-radius: 999px; padding: 4px 9px; background: #e2e8f0; font-size: 13px; white-space: nowrap; }}
    .page-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) 390px; gap: 14px; padding: 14px; }}
    .panel-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; align-items: start; }}
    .panel-preview {{ border: 1px solid #d8dee8; border-radius: 8px; background: #fbfcfe; padding: 10px; }}
    .panel-title {{ font-weight: 700; font-size: 13px; margin-bottom: 8px; }}
    .spatial-svg {{ width: 100%; aspect-ratio: 1 / 1; border: 1px solid #e2e8f0; background: #ffffff; }}
    .panel-bg {{ fill: #fbfdff; stroke: #cbd5e1; stroke-width: .55; }}
    .relation {{ fill: none; stroke-width: .8; stroke-dasharray: 3 2; opacity: .85; }}
    .relation-aim {{ stroke: #dc2626; }}
    .relation-trajectory {{ stroke: #2563eb; }}
    .relation-cover-line {{ stroke: #475569; }}
    .relation-cover-anchor {{ stroke: #16a34a; stroke-dasharray: 1.5 1.5; }}
    .vector {{ stroke-width: 1.2; fill: none; }}
    .vector-facing {{ stroke: #64748b; }}
    .vector-gaze {{ stroke: #7c3aed; }}
    .vector-aim {{ stroke: #ef4444; }}
    .vector-trajectory {{ stroke: #0ea5e9; }}
    marker path {{ fill: #334155; }}
    .entity circle, .entity rect, .entity polygon {{ stroke: #111827; stroke-width: .65; fill: #fef08a; }}
    .entity-character circle {{ fill: #fde68a; }}
    .entity-object rect, .entity-cover rect {{ fill: #bbf7d0; }}
    .entity-landmark polygon {{ fill: #bfdbfe; }}
    .entity-label, .relation-label {{ font-size: 3.4px; paint-order: stroke; stroke: #ffffff; stroke-width: .8px; fill: #111827; }}
    .legend {{ border-left: 1px solid #e5eaf1; padding-left: 14px; min-width: 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border-bottom: 1px solid #e5eaf1; padding: 6px 5px; vertical-align: top; text-align: left; word-break: break-word; }}
    .constraint-list, .issue-list {{ margin: 0; padding-left: 18px; font-size: 13px; }}
    .constraint-list li {{ margin-bottom: 8px; }}
    .constraint-list small {{ display: block; color: #526071; word-break: break-word; }}
    [data-preview-targets] {{ border-radius: 4px; outline: none; }}
    [data-preview-targets]:hover, [data-preview-targets]:focus {{ background: #f8fafc; box-shadow: 0 0 0 2px rgba(14, 165, 233, .16); }}
    .cross-panel span {{ background: #ede9fe; color: #5b21b6; border-radius: 999px; padding: 1px 6px; }}
    .lock-hard span {{ background: #fee2e2; color: #991b1b; border-radius: 999px; padding: 1px 6px; }}
    .lock-soft span {{ background: #fef3c7; color: #92400e; border-radius: 999px; padding: 1px 6px; }}
    .lock-inferred span {{ background: #e0f2fe; color: #075985; border-radius: 999px; padding: 1px 6px; }}
    .scene-3d-preview {{ border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; margin-bottom: 12px; padding: 10px; }}
    .scene-3d-header {{ display: flex; align-items: start; justify-content: space-between; gap: 12px; }}
    .scene-3d-header h3 {{ margin-top: 0; }}
    .scene-3d-controls {{ display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
    .scene-3d-controls button {{ border: 1px solid #cbd5e1; border-radius: 6px; background: #ffffff; color: #17202a; padding: 4px 8px; font: inherit; font-size: 12px; cursor: pointer; }}
    .scene-3d-controls button:hover, .scene-3d-controls button.active {{ background: #e2e8f0; }}
    .scene-3d-label-mode {{ display: inline-flex; align-items: center; gap: 4px; border-left: 1px solid #cbd5e1; margin-left: 4px; padding-left: 10px; font-size: 12px; color: #334155; }}
    .scene-3d-layer-controls {{ display: inline-flex; align-items: center; flex-wrap: wrap; gap: 4px; border-left: 1px solid #cbd5e1; margin-left: 4px; padding-left: 10px; font-size: 12px; color: #334155; }}
    .scene-3d-layer-controls button:not(.active) {{ color: #64748b; background: #f8fafc; }}
    .scene-3d-status-strip {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
    .scene-3d-status-strip span {{ border: 1px solid #d8dee8; border-radius: 999px; background: #ffffff; color: #334155; padding: 3px 8px; font-size: 12px; }}
    .scene-3d-sync {{ display: inline-flex; align-items: center; gap: 4px; border-left: 1px solid #cbd5e1; margin-left: 4px; padding-left: 10px; font-size: 12px; color: #334155; }}
    .scene-3d-status {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; color: #475569; background: #ffffff; border: 1px solid #d8dee8; border-radius: 6px; padding: 4px 7px; }}
    .scene-3d-panel-buttons {{ display: inline-flex; flex-wrap: wrap; gap: 4px; }}
    .scene-3d-canvas {{ display: block; width: 100%; max-height: 420px; border: 1px solid #d8dee8; background: #ffffff; margin-top: 10px; cursor: grab; touch-action: none; outline: none; }}
    .scene-3d-canvas:focus {{ border-color: #64748b; box-shadow: 0 0 0 2px rgba(100, 116, 139, .16); }}
    .scene-3d-canvas.is-dragging {{ cursor: grabbing; }}
    .scene-3d-level-rail {{ display: grid; gap: 6px; margin-top: 8px; font-size: 12px; }}
    .scene-3d-level-row {{ display: grid; grid-template-columns: 120px minmax(0, 1fr); align-items: center; gap: 8px; color: #475569; }}
    .scene-3d-level-bar {{ min-height: 8px; border-radius: 999px; background: #e2e8f0; overflow: hidden; }}
    .scene-3d-level-fill {{ display: block; min-height: 8px; background: #bae6fd; }}
    .scene-3d-level-entities {{ color: #17202a; font-weight: 600; }}
    .scene-3d-note {{ font-size: 13px; }}
    .empty {{ color: #6b7280; font-size: 13px; }}
    @media (max-width: 980px) {{
      .layout {{ grid-template-columns: 1fr; }}
      nav {{ position: static; }}
      .page-grid {{ grid-template-columns: 1fr; }}
      .legend {{ border-left: 0; border-top: 1px solid #e5eaf1; padding: 12px 0 0; }}
    }}
  </style>
</head>
<body>
  <header class="app-header">
    <h1>{escape_html(model.get('title') or 'Spatial contract preview')}</h1>
    <div class="summary">
      <span class="pill">source: {escape_html(model.get('source') or 'unknown')}</span>
      <span class="pill">pages: {escape_html(model.get('page_count'))}</span>
      <span class="pill">structured pages: {escape_html(model.get('structured_page_count'))}</span>
      <span class="pill {status_class}">spatial-check: {escape_html(model.get('status'))}</span>
    </div>
  </header>
  <div class="layout">
    <nav aria-label="Pages">{nav}</nav>
    <main>
      <section class="global-issues">
        <h2>Spatial-check Issues</h2>
        <ul class="issue-list">{all_issues}</ul>
        <h2>Spatial-check Warnings</h2>
        <ul class="issue-list">{all_warnings}</ul>
      </section>
      {cards}
    </main>
  </div>
  <script>
    (function () {{
      const sceneViewers = [];
      const ISOMETRIC_YAW = -Math.PI / 4;
      const ISOMETRIC_PITCH = -Math.atan(1 / Math.sqrt(2));
      const DEFAULT_YAW = ISOMETRIC_YAW;
      const DEFAULT_PITCH = ISOMETRIC_PITCH;
      const MIN_PITCH = -1.45;
      const MAX_PITCH = 1.45;

      function clamp(value, minimum, maximum) {{
        return Math.max(minimum, Math.min(maximum, value));
      }}

      function numberAt(values, index, fallback) {{
        if (!Array.isArray(values) || values.length <= index) return fallback;
        const value = Number(values[index]);
        return Number.isFinite(value) ? value : fallback;
      }}

      function vec3(value) {{
        if (!Array.isArray(value) || value.length < 3) return null;
        return [numberAt(value, 0, 0), numberAt(value, 1, 0), numberAt(value, 2, 0)];
      }}

      function addVec(a, b) {{
        return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
      }}

      function subVec(a, b) {{
        return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
      }}

      function scaleVec(a, scale) {{
        return [a[0] * scale, a[1] * scale, a[2] * scale];
      }}

      function lengthVec(a) {{
        return Math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]);
      }}

      function normalizeVec(a) {{
        const length = lengthVec(a) || 1;
        return [a[0] / length, a[1] / length, a[2] / length];
      }}

      function panelKey(value) {{
        return value == null ? "" : String(value);
      }}

      function panelSnapshots(payload) {{
        return (((payload || {{}}).contract || {{}}).panel_snapshots || []);
      }}

      function activeSnapshot(viewer) {{
        const snapshots = panelSnapshots(viewer.payload);
        return snapshots.find(snapshot => panelKey(snapshot.panel) === viewer.state.activePanel) || snapshots[0] || null;
      }}

      function defaultViewState(payload) {{
        const firstSnapshot = panelSnapshots(payload)[0] || {{}};
        return {{
          yaw: DEFAULT_YAW,
          pitch: DEFAULT_PITCH,
          zoom: 1,
          panX: 0,
          panY: 0,
          activePanel: panelKey(firstSnapshot.panel),
          sync: false,
          labelMode: 'key',
          visibleLayers: {{
            actors: true,
            obstacles: true,
            landmarks: false,
            relations: true,
            vectors: false,
            camera: false,
            ghosts: false,
            levels: true,
            annotations: true
          }},
          highlightTargets: []
        }};
      }}

      function entityDefinitions(payload) {{
        const definitions = {{}};
        ((((payload || {{}}).contract || {{}}).entities) || []).forEach(entity => {{
          if (entity && entity.id) definitions[String(entity.id)] = entity;
        }});
        return definitions;
      }}

      function layerVisible(viewer, layer) {{
        return Boolean(viewer && viewer.state && viewer.state.visibleLayers && viewer.state.visibleLayers[layer]);
      }}

      function mergedEntityMeta(definitions, entity) {{
        const entityId = String((entity || {{}}).id || '');
        return Object.assign({{}}, definitions[entityId] || {{}}, entity || {{}});
      }}

      function entityLayer(meta, fixed) {{
        const type = String((meta || {{}}).type || '').toLowerCase();
        const role = String((meta || {{}}).role || '').toLowerCase();
        const id = String((meta || {{}}).id || '').toLowerCase();
        if (type === 'character' || role.indexOf('protagonist') !== -1 || role.indexOf('observer') !== -1) return 'actors';
        if (/building|wall|pillar|debris|slab|apc|vehicle|cover|railing|door|stair|ramp/.test(id + ' ' + role + ' ' + type)) return 'obstacles';
        if (type === 'landmark' && role.indexOf('cover') === -1) return 'landmarks';
        return 'obstacles';
      }}

      function entityStyle(meta) {{
        const geometry = ((meta || {{}}).preview_geometry || {{}});
        const explicit = String(geometry.style || '').toLowerCase();
        if (explicit) return explicit;
        const type = String((meta || {{}}).type || '').toLowerCase();
        const role = String((meta || {{}}).role || '').toLowerCase();
        const id = String((meta || {{}}).id || '').toLowerCase();
        if (/building|wall|pillar|breach/.test(id + ' ' + role + ' ' + type)) return 'building';
        if (/apc|vehicle|car/.test(id + ' ' + role + ' ' + type)) return 'vehicle';
        if (/slab|ramp|slope/.test(id + ' ' + role + ' ' + type)) return 'slab';
        if (/floor/.test(id + ' ' + role + ' ' + type)) return 'floor';
        if (/ceiling/.test(id + ' ' + role + ' ' + type)) return 'ceiling';
        if (/debris|server|cover|railing/.test(id + ' ' + role + ' ' + type)) return 'cover';
        if (/pillar|column/.test(id + ' ' + role + ' ' + type)) return 'pillar';
        if (type === 'character') return 'humanoid';
        return type || 'object';
      }}

      function defaultGeometryFor(meta) {{
        const style = entityStyle(meta);
        const descriptor = String(((meta || {{}}).id || '') + ' ' + ((meta || {{}}).role || '') + ' ' + ((meta || {{}}).type || '')).toLowerCase();
        if (style === 'humanoid') return {{ shape: 'humanoid_mannequin', size: [0.55, 0.35, 1.72], anchor: 'base_center', style }};
        if (style === 'building' && /shell|room|lobby|building/.test(descriptor)) return {{ shape: 'building_shell', size: [4.2, 3.2, 3.0], anchor: 'base_center', style }};
        if (style === 'building' && /floor2|floor_2|breach/.test(descriptor)) return {{ shape: 'box', size: [4.8, 2.4, 2.3], anchor: 'center', style }};
        if (style === 'building' && /wall/.test(descriptor)) return {{ shape: 'wall', size: [0.45, 2.4, 2.2], anchor: 'center', style }};
        if (style === 'building' && /pillar|column/.test(descriptor)) return {{ shape: 'pillar', size: [0.75, 0.75, 2.6], anchor: 'center', style }};
        if (style === 'building') return {{ shape: 'box', size: [1.2, 0.55, 3.8], anchor: 'base_center', style }};
        if (style === 'vehicle') return {{ shape: 'box', size: [3.4, 1.7, 1.35], anchor: 'base_center', style }};
        if (style === 'slab') return {{ shape: 'floor_slab', size: [3.6, 1.45, 0.35], anchor: 'base_center', style }};
        if (style === 'floor') return {{ shape: 'floor_slab', size: [3.2, 2.4, 0.08], anchor: 'base_center', style }};
        if (style === 'ceiling') return {{ shape: 'ceiling_slab', size: [3.2, 2.4, 0.08], anchor: 'base_center', style }};
        if (style === 'cover') return {{ shape: 'box', size: [2.0, 0.8, 1.0], anchor: 'base_center', style }};
        if (style === 'door') return {{ shape: 'box', size: [1.1, 0.22, 2.0], anchor: 'base_center', style }};
        if (style === 'landmark') return {{ shape: 'box', size: [1.0, 1.0, 0.45], anchor: 'base_center', style }};
        if (/cylinder|barrel|column/.test(descriptor)) return {{ shape: 'cylinder', size: [0.8, 0.8, 1.0], anchor: 'base_center', style }};
        return null;
      }}

      function normalizePreviewShape(shape) {{
        const requested = String(shape || 'box').toLowerCase();
        const aliases = {{
          floor: 'floor_slab',
          ceiling: 'ceiling_slab',
          object_box: 'box',
          room: 'building_shell'
        }};
        const normalized = aliases[requested] || requested;
        const supported = new Set(['humanoid_mannequin', 'building_shell', 'wall', 'pillar', 'floor_slab', 'ceiling_slab', 'box', 'cylinder', 'flat_plane']);
        return supported.has(normalized) ? normalized : 'box';
      }}

      function geometryForEntity(meta) {{
        const explicit = (meta || {{}}).preview_geometry;
        const fallback = defaultGeometryFor(meta);
        if (!explicit && !fallback) return null;
        const source = Object.assign({{}}, fallback || {{}}, explicit || {{}});
        const shape = normalizePreviewShape(source.shape || (fallback || {{}}).shape || 'box');
        const rawSize = Array.isArray(source.size) ? source.size : (fallback ? fallback.size : null);
        if (!rawSize) return null;
        const size = [
          Math.max(0.05, numberAt(rawSize, 0, 1)),
          Math.max(0.05, numberAt(rawSize, 1, 1)),
          Math.max(0.05, numberAt(rawSize, 2, 0.5))
        ];
        return {{
          shape,
          size,
          yaw: Number(source.yaw_degrees || source.yaw || 0) * Math.PI / 180,
          pitch: Number(source.pitch_degrees || source.pitch || 0) * Math.PI / 180,
          roll: Number(source.roll_degrees || source.roll || 0) * Math.PI / 180,
          anchor: String(source.anchor || 'base_center'),
          style: String(source.style || entityStyle(meta)),
          parts: Array.isArray(source.parts) ? source.parts : []
        }};
      }}

      function transformLocalPoint(point, geometry) {{
        let x = point[0];
        let y = point[1];
        let z = point[2];
        const roll = (geometry || {{}}).roll || 0;
        if (roll) {{
          const cosRoll = Math.cos(roll);
          const sinRoll = Math.sin(roll);
          const rolledX = x * cosRoll + z * sinRoll;
          const rolledZ = -x * sinRoll + z * cosRoll;
          x = rolledX;
          z = rolledZ;
        }}
        const pitch = (geometry || {{}}).pitch || 0;
        if (pitch) {{
          const cosPitch = Math.cos(pitch);
          const sinPitch = Math.sin(pitch);
          const pitchedY = y * cosPitch - z * sinPitch;
          const pitchedZ = y * sinPitch + z * cosPitch;
          y = pitchedY;
          z = pitchedZ;
        }}
        const yaw = (geometry || {{}}).yaw || 0;
        const cosYaw = Math.cos(yaw);
        const sinYaw = Math.sin(yaw);
        return [
          x * cosYaw - y * sinYaw,
          x * sinYaw + y * cosYaw,
          z
        ];
      }}

      function boxCorners(position, geometry) {{
        const base = vec3(position);
        if (!base || !geometry) return [];
        const sx = geometry.size[0] / 2;
        const sy = geometry.size[1] / 2;
        const sz = geometry.size[2] / 2;
        const centerZ = geometry.anchor === 'center' ? base[2] : base[2] + sz;
        const center = [base[0], base[1], centerZ];
        const local = [
          [-sx, -sy, -sz], [sx, -sy, -sz], [sx, sy, -sz], [-sx, sy, -sz],
          [-sx, -sy, sz], [sx, -sy, sz], [sx, sy, sz], [-sx, sy, sz]
        ];
        return local.map(point => {{
          const transformed = transformLocalPoint(point, geometry);
          return [
            center[0] + transformed[0],
            center[1] + transformed[1],
            center[2] + transformed[2]
          ];
        }});
      }}

      function snapshotPositions(snapshot, definitions) {{
        const positions = [];
        ((snapshot || {{}}).entities || []).forEach(entity => {{
          const position = vec3(entity.position);
          if (position) {{
            positions.push(position);
            const meta = mergedEntityMeta(definitions || {{}}, entity);
            boxCorners(position, geometryForEntity(meta)).forEach(corner => positions.push(corner));
            const trajectory = vec3(entity.trajectory_vector);
            if (trajectory) positions.push(addVec(position, trajectory));
          }}
        }});
        return positions;
      }}

      function referencedFixedIds(payload, snapshot) {{
        const ids = new Set();
        ((snapshot || {{}}).entities || []).forEach(entity => {{
          if (entity && entity.id) ids.add(String(entity.id));
        }});
        ((((payload || {{}}).contract || {{}}).constraints) || []).forEach(item => {{
          ['actor', 'anchor', 'cover', 'destination_entity', 'entity', 'object', 'occluder', 'origin_entity', 'source', 'subject', 'target', 'threat', 'vector_entity', 'viewpoint_entity'].forEach(field => {{
            if (item && item[field]) ids.add(String(item[field]));
          }});
        }});
        ((((payload || {{}}).contract || {{}}).transitions) || []).forEach(item => {{
          if (item && item.entity) ids.add(String(item.entity));
        }});
        return ids;
      }}

      function entityPositions(payload, state) {{
        const positions = [];
        const snapshots = panelSnapshots(payload);
        const active = snapshots.find(snapshot => panelKey(snapshot.panel) === state.activePanel) || snapshots[0] || null;
        const definitions = entityDefinitions(payload);
        if (active) positions.push.apply(positions, snapshotPositions(active, definitions));
        else snapshots.forEach(snapshot => positions.push.apply(positions, snapshotPositions(snapshot, definitions)));
        const fixedIds = referencedFixedIds(payload, active);
        const fixedEntities = ((payload.scene || {{}}).fixed_entities || []);
        fixedEntities.forEach((entity, index) => {{
          const entityId = String((entity || {{}}).id || '');
          if (fixedIds.has(entityId) || index < 8) {{
            const position = vec3(entity.position);
            if (position) {{
              positions.push(position);
              const meta = mergedEntityMeta(definitions, entity);
              boxCorners(position, geometryForEntity(meta)).forEach(corner => positions.push(corner));
            }}
          }}
        }});
        return positions;
      }}

      function contentBounds(payload, state) {{
        const positions = entityPositions(payload, state || defaultViewState(payload));
        const xs = positions.map(point => point[0]);
        const ys = positions.map(point => point[1]);
        const minX = xs.length ? Math.min.apply(null, xs) : -3;
        const maxX = xs.length ? Math.max.apply(null, xs) : 3;
        const minY = ys.length ? Math.min.apply(null, ys) : -3;
        const maxY = ys.length ? Math.max.apply(null, ys) : 3;
        const padX = Math.max(1.5, (maxX - minX) * 0.25);
        const padY = Math.max(1.5, (maxY - minY) * 0.25);
        return {{ minX: minX - padX, maxX: maxX + padX, minY: minY - padY, maxY: maxY + padY }};
      }}

      function levelFootprintPositions(payload, state, level) {{
        const positions = [];
        const levelId = String((level || {{}}).id || '');
        if (!levelId) return positions;
        const definitions = entityDefinitions(payload);
        const active = activeSnapshot({{ payload, state: state || defaultViewState(payload) }});
        const addEntity = entity => {{
          if (!entity || levelForEntity(payload, entity) !== levelId) return;
          const position = vec3(entity.position);
          if (!position) return;
          positions.push(position);
          const meta = mergedEntityMeta(definitions, entity);
          boxCorners(position, geometryForEntity(meta)).forEach(corner => positions.push(corner));
        }};
        ((active || {{}}).entities || []).forEach(addEntity);
        const fixedIds = referencedFixedIds(payload, active);
        (((payload || {{}}).scene || {{}}).fixed_entities || []).forEach((entity, index) => {{
          const entityId = String((entity || {{}}).id || '');
          if (!fixedIds.has(entityId) && index >= 8) return;
          addEntity(entity);
        }});
        return positions;
      }}

      function levelPlaneBounds(payload, state, level) {{
        const positions = levelFootprintPositions(payload, state, level);
        if (!positions.length) return null;
        const xs = positions.map(point => point[0]);
        const ys = positions.map(point => point[1]);
        const minX = Math.min.apply(null, xs);
        const maxX = Math.max.apply(null, xs);
        const minY = Math.min.apply(null, ys);
        const maxY = Math.max.apply(null, ys);
        const padX = Math.max(0.85, (maxX - minX) * 0.28);
        const padY = Math.max(0.85, (maxY - minY) * 0.28);
        return {{ minX: minX - padX, maxX: maxX + padX, minY: minY - padY, maxY: maxY + padY }};
      }}

      function levelPlaneCorners(payload, state) {{
        const levels = (((payload || {{}}).scene || {{}}).levels || []);
        const corners = [];
        levels.forEach(level => {{
          const bounds = levelPlaneBounds(payload, state, level);
          if (!bounds) return;
          const range = Array.isArray(level.z_range) ? level.z_range : [0, 0];
          const z = Number(range[0] || 0);
          corners.push([bounds.minX, bounds.minY, z]);
          corners.push([bounds.maxX, bounds.minY, z]);
          corners.push([bounds.maxX, bounds.maxY, z]);
          corners.push([bounds.minX, bounds.maxY, z]);
        }});
        return corners;
      }}

      function allPositions(payload, state) {{
        return entityPositions(payload, state).concat(levelPlaneCorners(payload, state));
      }}

      function fixedEntityPositions(payload, state) {{
        const positions = [];
        const snapshots = panelSnapshots(payload);
        const active = snapshots.find(snapshot => panelKey(snapshot.panel) === state.activePanel) || snapshots[0] || null;
        const fixedIds = referencedFixedIds(payload, active);
        const definitions = entityDefinitions(payload);
        ((payload.scene || {{}}).fixed_entities || []).forEach((entity, index) => {{
          const entityId = String((entity || {{}}).id || '');
          if (!fixedIds.has(entityId) && index >= 8) return;
          const position = vec3(entity.position);
          if (position) {{
            positions.push(position);
            const meta = mergedEntityMeta(definitions, entity);
            boxCorners(position, geometryForEntity(meta)).forEach(corner => positions.push(corner));
          }}
        }});
        return positions;
      }}

      function rotatePoint(point, state) {{
        const source = vec3(point) || [0, 0, 0];
        const cosYaw = Math.cos(state.yaw);
        const sinYaw = Math.sin(state.yaw);
        const x1 = source[0] * cosYaw - source[1] * sinYaw;
        const y1 = source[0] * sinYaw + source[1] * cosYaw;
        const z1 = source[2];
        const cosPitch = Math.cos(state.pitch);
        const sinPitch = Math.sin(state.pitch);
        const y2 = y1 * cosPitch - z1 * sinPitch;
        const z2 = y1 * sinPitch + z1 * cosPitch;
        return {{ x: x1, y: -z2, depth: y2 }};
      }}

      function makeProjector(canvas, payload, state) {{
        const width = canvas.width;
        const height = canvas.height;
        const rotated = allPositions(payload, state).map(point => rotatePoint(point, state));
        const xs = rotated.map(point => point.x);
        const ys = rotated.map(point => point.y);
        const minX = xs.length ? Math.min.apply(null, xs) : -3;
        const maxX = xs.length ? Math.max.apply(null, xs) : 3;
        const minY = ys.length ? Math.min.apply(null, ys) : -3;
        const maxY = ys.length ? Math.max.apply(null, ys) : 3;
        const rangeX = Math.max(1, maxX - minX);
        const rangeY = Math.max(1, maxY - minY);
        const scale = Math.min((width - 96) / rangeX, (height - 72) / rangeY) * state.zoom;
        const midX = (minX + maxX) / 2;
        const midY = (minY + maxY) / 2;
        return {{
          point(point) {{
            const rotatedPoint = rotatePoint(point, state);
            return {{
              x: width / 2 + (rotatedPoint.x - midX) * scale + state.panX,
              y: height / 2 + (rotatedPoint.y - midY) * scale + state.panY,
              depth: rotatedPoint.depth
            }};
          }},
          scale,
          state,
          bounds: contentBounds(payload, state)
        }};
      }}

      function drawLine(ctx, projector, startPoint, endPoint, color, alpha, width, dashed) {{
        const start = projector.point(startPoint);
        const end = projector.point(endPoint);
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.strokeStyle = color;
        ctx.lineWidth = width || 1.4;
        ctx.setLineDash(dashed ? [5, 4] : []);
        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(end.x, end.y);
        ctx.stroke();
        ctx.restore();
      }}

      function drawArrowHead(ctx, start, end, color, alpha, size) {{
        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        if (length < 0.1) return;
        const ux = dx / length;
        const uy = dy / length;
        const px = -uy;
        const py = ux;
        const arrowSize = size || 8;
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(end.x, end.y);
        ctx.lineTo(end.x - ux * arrowSize + px * arrowSize * 0.45, end.y - uy * arrowSize + py * arrowSize * 0.45);
        ctx.lineTo(end.x - ux * arrowSize - px * arrowSize * 0.45, end.y - uy * arrowSize - py * arrowSize * 0.45);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }}

      function drawArrowLine(ctx, projector, startPoint, endPoint, color, alpha, width, dashed) {{
        const start = projector.point(startPoint);
        const end = projector.point(endPoint);
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.strokeStyle = color;
        ctx.lineWidth = width || 1.4;
        ctx.setLineDash(dashed ? [6, 4] : []);
        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(end.x, end.y);
        ctx.stroke();
        ctx.restore();
        drawArrowHead(ctx, start, end, color, alpha, width && width > 1.5 ? 9 : 7);
      }}

      function drawBlockedMark(ctx, projector, startPoint, endPoint, color, alpha) {{
        const start = projector.point(startPoint);
        const end = projector.point(endPoint);
        const mid = {{ x: (start.x + end.x) / 2, y: (start.y + end.y) / 2 }};
        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const length = Math.sqrt(dx * dx + dy * dy) || 1;
        const px = -dy / length;
        const py = dx / length;
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(mid.x - px * 6, mid.y - py * 6);
        ctx.lineTo(mid.x + px * 6, mid.y + py * 6);
        ctx.stroke();
        ctx.restore();
      }}

      function geometryColors(style) {{
        const key = String(style || '').toLowerCase();
        if (key === 'building') return {{ stroke: '#475569', fill: 'rgba(148, 163, 184, .15)' }};
        if (key === 'vehicle') return {{ stroke: '#334155', fill: 'rgba(59, 130, 246, .14)' }};
        if (key === 'slab') return {{ stroke: '#7c2d12', fill: 'rgba(251, 146, 60, .14)' }};
        if (key === 'cover') return {{ stroke: '#166534', fill: 'rgba(34, 197, 94, .13)' }};
        if (key === 'door') return {{ stroke: '#92400e', fill: 'rgba(245, 158, 11, .14)' }};
        if (key === 'humanoid' || key === 'actor') return {{ stroke: '#92400e', fill: 'rgba(251, 191, 36, .18)' }};
        if (key === 'floor') return {{ stroke: '#0284c7', fill: 'rgba(186, 230, 253, .18)' }};
        if (key === 'ceiling') return {{ stroke: '#7c3aed', fill: 'rgba(221, 214, 254, .12)' }};
        if (key === 'pillar') return {{ stroke: '#475569', fill: 'rgba(100, 116, 139, .16)' }};
        if (key === 'annotation') return {{ stroke: '#db2777', fill: 'rgba(251, 207, 232, .28)' }};
        return {{ stroke: '#64748b', fill: 'rgba(203, 213, 225, .16)' }};
      }}

      function drawWireBox(ctx, projector, position, geometry, meta, viewer, entityId, alpha) {{
        const corners = boxCorners(position, geometry);
        if (!corners.length) return;
        const projected = corners.map(point => projector.point(point));
        const colors = geometryColors((geometry || {{}}).style || entityStyle(meta));
        const drawAlpha = viewer ? alphaForHighlight(viewer, entityId, alpha) : alpha;
        const faces = [
          [0, 1, 2, 3],
          [4, 5, 6, 7]
        ];
        const edges = [
          [0, 1], [1, 2], [2, 3], [3, 0],
          [4, 5], [5, 6], [6, 7], [7, 4],
          [0, 4], [1, 5], [2, 6], [3, 7]
        ];
        ctx.save();
        ctx.globalAlpha = drawAlpha;
        faces.forEach((face, index) => {{
          ctx.fillStyle = index === 1 ? colors.fill : 'rgba(255, 255, 255, .04)';
          ctx.beginPath();
          face.forEach((cornerIndex, pointIndex) => {{
            const point = projected[cornerIndex];
            if (pointIndex === 0) ctx.moveTo(point.x, point.y);
            else ctx.lineTo(point.x, point.y);
          }});
          ctx.closePath();
          ctx.fill();
        }});
        ctx.strokeStyle = colors.stroke;
        ctx.lineWidth = 1.25;
        ctx.setLineDash([5, 3]);
        edges.forEach(edge => {{
          const start = projected[edge[0]];
          const end = projected[edge[1]];
          ctx.beginPath();
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(end.x, end.y);
          ctx.stroke();
        }});
        ctx.restore();
      }}

      function rotateLocalYaw(point, yaw) {{
        const cosYaw = Math.cos(yaw || 0);
        const sinYaw = Math.sin(yaw || 0);
        return [
          point[0] * cosYaw - point[1] * sinYaw,
          point[0] * sinYaw + point[1] * cosYaw,
          point[2]
        ];
      }}

      function drawCylinder(ctx, projector, position, geometry, meta, viewer, entityId, alpha) {{
        const base = vec3(position);
        if (!base || !geometry) return;
        const radiusX = geometry.size[0] / 2;
        const radiusY = geometry.size[1] / 2;
        const height = geometry.size[2];
        const baseZ = geometry.anchor === 'center' ? base[2] - height / 2 : base[2];
        const center = [base[0], base[1], baseZ];
        const colors = geometryColors((geometry || {{}}).style || entityStyle(meta));
        const drawAlpha = viewer ? alphaForHighlight(viewer, entityId, alpha) : alpha;
        const bottom = [];
        const top = [];
        for (let index = 0; index < 16; index += 1) {{
          const angle = (Math.PI * 2 * index) / 16;
          const local = [Math.cos(angle) * radiusX, Math.sin(angle) * radiusY, 0];
          const rotated = rotateLocalYaw(local, geometry.yaw || 0);
          bottom.push([center[0] + rotated[0], center[1] + rotated[1], center[2]]);
          top.push([center[0] + rotated[0], center[1] + rotated[1], center[2] + height]);
        }}
        const drawLoop = points => {{
          const projected = points.map(point => projector.point(point));
          ctx.beginPath();
          projected.forEach((point, index) => {{
            if (index === 0) ctx.moveTo(point.x, point.y);
            else ctx.lineTo(point.x, point.y);
          }});
          ctx.closePath();
        }};
        ctx.save();
        ctx.globalAlpha = drawAlpha;
        ctx.fillStyle = colors.fill;
        ctx.strokeStyle = colors.stroke;
        ctx.lineWidth = 1.25;
        drawLoop(top);
        ctx.fill();
        ctx.stroke();
        drawLoop(bottom);
        ctx.stroke();
        [0, 4, 8, 12].forEach(index => drawLine(ctx, projector, bottom[index], top[index], colors.stroke, drawAlpha, 1, true));
        ctx.restore();
      }}

      function partGeometryFrom(parent, part, fallbackShape) {{
        const rawSize = Array.isArray(part.size) ? part.size : parent.size;
        return {{
          shape: normalizePreviewShape(part.shape || fallbackShape || 'box'),
          size: [
            Math.max(0.05, numberAt(rawSize, 0, parent.size[0])),
            Math.max(0.05, numberAt(rawSize, 1, parent.size[1])),
            Math.max(0.05, numberAt(rawSize, 2, parent.size[2]))
          ],
          yaw: (parent.yaw || 0) + Number(part.yaw_degrees || part.yaw || 0) * Math.PI / 180,
          pitch: (parent.pitch || 0) + Number(part.pitch_degrees || part.pitch || 0) * Math.PI / 180,
          roll: (parent.roll || 0) + Number(part.roll_degrees || part.roll || 0) * Math.PI / 180,
          anchor: String(part.anchor || 'base_center'),
          style: String(part.style || part.shape || parent.style || 'building'),
          parts: []
        }};
      }}

      function partPositionFrom(base, parent, part) {{
        const rawOffset = Array.isArray(part.offset) ? part.offset : [0, 0, 0];
        const offset = [
          numberAt(rawOffset, 0, 0),
          numberAt(rawOffset, 1, 0),
          numberAt(rawOffset, 2, 0)
        ];
        const transformed = transformLocalPoint(offset, parent || {{}});
        return [base[0] + transformed[0], base[1] + transformed[1], base[2] + transformed[2]];
      }}

      function defaultBuildingShellParts(geometry) {{
        const sx = geometry.size[0];
        const sy = geometry.size[1];
        const sz = geometry.size[2];
        const thin = Math.max(0.06, Math.min(sx, sy, sz) * 0.035);
        return [
          {{ shape: 'floor_slab', style: 'floor', size: [sx, sy, thin], offset: [0, 0, 0], anchor: 'base_center' }},
          {{ shape: 'ceiling_slab', style: 'ceiling', size: [sx, sy, thin], offset: [0, 0, sz - thin], anchor: 'base_center' }},
          {{ shape: 'wall', style: 'building', size: [sx, thin, sz], offset: [0, -sy / 2, 0], anchor: 'base_center' }},
          {{ shape: 'wall', style: 'building', size: [sx, thin, sz], offset: [0, sy / 2, 0], anchor: 'base_center' }},
          {{ shape: 'wall', style: 'building', size: [thin, sy, sz], offset: [-sx / 2, 0, 0], anchor: 'base_center' }},
          {{ shape: 'wall', style: 'building', size: [thin, sy, sz], offset: [sx / 2, 0, 0], anchor: 'base_center' }},
          {{ shape: 'pillar', style: 'pillar', size: [thin * 1.6, thin * 1.6, sz], offset: [-sx / 2, -sy / 2, 0], anchor: 'base_center' }},
          {{ shape: 'pillar', style: 'pillar', size: [thin * 1.6, thin * 1.6, sz], offset: [sx / 2, sy / 2, 0], anchor: 'base_center' }}
        ];
      }}

      function drawBuildingShell(ctx, projector, position, geometry, meta, viewer, entityId, alpha) {{
        const base = vec3(position);
        if (!base || !geometry) return;
        drawWireBox(ctx, projector, base, Object.assign({{}}, geometry, {{ shape: 'box', style: geometry.style || 'building' }}), meta, viewer, entityId, alpha * 0.18);
        const parts = geometry.parts.length ? geometry.parts : defaultBuildingShellParts(geometry);
        parts.forEach((part, index) => {{
          const partGeometry = partGeometryFrom(geometry, part, part.shape || 'box');
          const partPosition = partPositionFrom(base, geometry, part);
          const partMeta = Object.assign({{}}, meta || {{}}, {{ preview_geometry: partGeometry, id: entityId + '-part-' + index }});
          if (partGeometry.shape === 'cylinder') drawCylinder(ctx, projector, partPosition, partGeometry, partMeta, viewer, entityId, alpha * 0.48);
          else drawWireBox(ctx, projector, partPosition, partGeometry, partMeta, viewer, entityId, alpha * 0.48);
        }});
      }}

      function drawHumanoidMannequin(ctx, projector, position, geometry, entity, label, alpha, viewer, entityId, priority) {{
        const base = vec3(position);
        if (!base) return;
        const vector = directionVector(entity) || [0, 1, 0];
        const forward = normalizeVec([vector[0], vector[1], 0]);
        const right = normalizeVec([forward[1], -forward[0], 0]);
        const height = Math.max(0.8, geometry ? geometry.size[2] : 1.7);
        const shoulder = Math.max(0.22, geometry ? geometry.size[0] : 0.55);
        const hip = shoulder * 0.58;
        const crouch = /crouch|kneel|앉|무릎|웅크/.test(String((entity || {{}}).pose || '').toLowerCase()) ? 0.76 : 1;
        const footZ = base[2];
        const pelvis = [base[0], base[1], footZ + height * 0.48 * crouch];
        const chest = [base[0], base[1], footZ + height * 0.72 * crouch];
        const neck = [base[0], base[1], footZ + height * 0.84 * crouch];
        const head = [base[0], base[1], footZ + height * 0.93 * crouch];
        const leftShoulder = addVec(chest, scaleVec(right, shoulder / 2));
        const rightShoulder = addVec(chest, scaleVec(right, -shoulder / 2));
        const leftHip = addVec(pelvis, scaleVec(right, hip / 2));
        const rightHip = addVec(pelvis, scaleVec(right, -hip / 2));
        const leftHand = addVec(addVec(leftShoulder, scaleVec(right, shoulder * 0.25)), scaleVec(forward, shoulder * 0.35));
        leftHand[2] -= height * 0.24 * crouch;
        const rightHand = addVec(addVec(rightShoulder, scaleVec(right, -shoulder * 0.25)), scaleVec(forward, shoulder * 0.35));
        rightHand[2] -= height * 0.24 * crouch;
        const leftFoot = addVec(addVec(base, scaleVec(right, shoulder * 0.32)), scaleVec(forward, -shoulder * 0.12));
        const rightFoot = addVec(addVec(base, scaleVec(right, -shoulder * 0.32)), scaleVec(forward, shoulder * 0.12));
        const drawAlpha = viewer ? alphaForHighlight(viewer, entityId, alpha) : alpha;
        const color = '#92400e';
        ctx.save();
        ctx.globalAlpha = drawAlpha;
        ctx.strokeStyle = color;
        ctx.fillStyle = 'rgba(251, 191, 36, .22)';
        ctx.lineWidth = 1.8;
        [[head, neck], [neck, chest], [chest, pelvis], [leftShoulder, rightShoulder], [leftHip, rightHip], [leftShoulder, leftHand], [rightShoulder, rightHand], [leftHip, leftFoot], [rightHip, rightFoot]].forEach(pair => {{
          const start = projector.point(pair[0]);
          const end = projector.point(pair[1]);
          ctx.beginPath();
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(end.x, end.y);
          ctx.stroke();
        }});
        const headPoint = projector.point(head);
        ctx.beginPath();
        ctx.arc(headPoint.x, headPoint.y, Math.max(4, projector.scale * height * 0.035), 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.restore();
        drawArrowLine(ctx, projector, head, addVec(head, scaleVec(forward, shoulder * 0.65)), '#0f766e', drawAlpha * 0.75, 1.2, false);
        if (label) drawSceneLabel(ctx, viewer, headPoint, label, priority || 4, drawAlpha, entityId || label);
      }}

      function drawPreviewGeometry(ctx, projector, position, geometry, meta, viewer, entityId, alpha, label, priority, entity) {{
        if (!geometry) return false;
        if (geometry.shape === 'humanoid_mannequin') {{
          drawHumanoidMannequin(ctx, projector, position, geometry, entity || meta || {{}}, label, alpha, viewer, entityId, priority);
          return true;
        }}
        if (geometry.shape === 'building_shell') {{
          drawBuildingShell(ctx, projector, position, geometry, meta, viewer, entityId, alpha);
          return true;
        }}
        if (geometry.shape === 'cylinder') {{
          drawCylinder(ctx, projector, position, geometry, meta, viewer, entityId, alpha);
          return true;
        }}
        drawWireBox(ctx, projector, position, geometry, meta, viewer, entityId, alpha);
        return true;
      }}

      function directionVector(entity) {{
        return vec3((entity || {{}}).aim_vector) || vec3((entity || {{}}).trajectory_vector) || vec3((entity || {{}}).facing_vector) || vec3((entity || {{}}).gaze_vector);
      }}

      function drawDirectionShape(ctx, projector, position, direction, fill, stroke, alpha, size) {{
        const center = projector.point(position);
        let dx = 1;
        let dy = 0;
        const vector = vec3(direction);
        if (vector) {{
          const normalized = normalizeVec(vector);
          const end = projector.point(addVec(position, scaleVec(normalized, 0.8)));
          dx = end.x - center.x;
          dy = end.y - center.y;
          const length = Math.sqrt(dx * dx + dy * dy);
          if (length > 0.1) {{
            dx /= length;
            dy /= length;
          }} else {{
            dx = 1;
            dy = 0;
          }}
        }}
        const px = -dy;
        const py = dx;
        const length = size || 10;
        const width = length * 0.72;
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.fillStyle = fill;
        ctx.strokeStyle = stroke || '#111827';
        ctx.lineWidth = 1.1;
        ctx.beginPath();
        ctx.moveTo(center.x + dx * length, center.y + dy * length);
        ctx.lineTo(center.x - dx * length * 0.58 + px * width, center.y - dy * length * 0.58 + py * width);
        ctx.lineTo(center.x - dx * length * 0.28, center.y - dy * length * 0.28);
        ctx.lineTo(center.x - dx * length * 0.58 - px * width, center.y - dy * length * 0.58 - py * width);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        ctx.restore();
        return center;
      }}

      function drawOrientedEntity(ctx, projector, entity, meta, label, fill, alpha, viewer, entityId, priority, active) {{
        const position = vec3((entity || {{}}).position);
        if (!position) return;
        const vector = directionVector(entity);
        const drawAlpha = viewer ? alphaForHighlight(viewer, entityId, alpha) : alpha;
        const center = drawDirectionShape(ctx, projector, position, vector, fill, '#111827', drawAlpha, active ? 9.5 : 7.5);
        if (label) drawSceneLabel(ctx, viewer, center, label, priority || 1, drawAlpha, entityId || label);
        if (vector && layerVisible(viewer, 'vectors')) {{
          const vectorAlpha = viewer ? alphaForHighlight(viewer, entityId, active ? 0.86 : 0.24) : alpha;
          drawArrowLine(ctx, projector, position, addVec(position, scaleVec(normalizeVec(vector), active ? 1.0 : 0.72)), '#0f766e', vectorAlpha, active ? 1.8 : 1.1, !active);
        }}
      }}

      function compactEntityLabel(entityId, meta) {{
        const entity = meta || {{}};
        if (entity.preview_label) return String(entity.preview_label).slice(0, 10);
        const tokens = String(entityId || 'entity').split(/[^A-Za-z0-9]+/).filter(Boolean);
        const priority = new Set(['apc', 'car', 'cover', 'door', 'mag', 'magazine', 'railing', 'shield', 'slab', 'stair', 'wall', 'window']);
        for (let index = tokens.length - 1; index >= 0; index -= 1) {{
          if (priority.has(tokens[index].toLowerCase())) return tokens[index].toUpperCase().slice(0, 10);
        }}
        const stop = new Set(['the', 'a', 'an', 'of', 'left', 'right', 'front', 'back', 'floor', 'level']);
        const token = tokens.find(item => !stop.has(item.toLowerCase())) || tokens[0] || String(entityId || 'entity');
        return token.toUpperCase().slice(0, 10);
      }}

      function labelsOverlap(a, b) {{
        return !(a.x + a.width + 4 < b.x || b.x + b.width + 4 < a.x || a.y + a.height + 3 < b.y || b.y + b.height + 3 < a.y);
      }}

      function clampLabelBox(box, width, height) {{
        const x = clamp(box.x, 4, Math.max(4, width - box.width - 4));
        const y = clamp(box.y, 4, Math.max(4, height - box.height - 4));
        return {{ x, y, width: box.width, height: box.height, baseline: y + 12 }};
      }}

      function placeSceneLabel(ctx, viewer, anchor, label, priority, entityId) {{
        if (!viewer || !label || viewer.state.labelMode === 'off') return null;
        const targets = viewer.state.highlightTargets || [];
        if (viewer.state.labelMode === 'key' && priority < 2 && !(targets.length && isHighlighted(viewer, entityId))) return null;
        ctx.font = '12px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';
        const textWidth = Math.ceil(ctx.measureText(label).width);
        const labelWidth = textWidth + 6;
        const labelHeight = 16;
        const candidates = [
          {{ x: anchor.x + 9, y: anchor.y - 12, width: labelWidth, height: labelHeight }},
          {{ x: anchor.x - labelWidth - 9, y: anchor.y - 12, width: labelWidth, height: labelHeight }},
          {{ x: anchor.x + 9, y: anchor.y + 8, width: labelWidth, height: labelHeight }},
          {{ x: anchor.x - labelWidth - 9, y: anchor.y + 8, width: labelWidth, height: labelHeight }},
          {{ x: anchor.x - labelWidth / 2, y: anchor.y - 24, width: labelWidth, height: labelHeight }},
          {{ x: anchor.x - labelWidth / 2, y: anchor.y + 14, width: labelWidth, height: labelHeight }}
        ].map(box => clampLabelBox(box, viewer.canvas.width, viewer.canvas.height));
        let best = null;
        let bestScore = Number.POSITIVE_INFINITY;
        candidates.forEach(candidate => {{
          const overlaps = viewer.labelBoxes.filter(box => labelsOverlap(candidate, box)).length;
          const distance = Math.abs(candidate.x - anchor.x) + Math.abs(candidate.baseline - anchor.y);
          const score = overlaps * 1000 + distance;
          if (score < bestScore) {{
            best = candidate;
            bestScore = score;
          }}
        }});
        if (!best) return null;
        if (viewer.state.labelMode === 'key' && bestScore >= 1000 && priority < 4) return null;
        viewer.labelBoxes.push(best);
        return best;
      }}

      function drawSceneLabel(ctx, viewer, anchor, label, priority, alpha, entityId) {{
        const box = placeSceneLabel(ctx, viewer, anchor, label, priority, entityId);
        if (!box) return;
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.strokeStyle = 'rgba(71, 85, 105, .55)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(anchor.x, anchor.y);
        ctx.lineTo(box.x + 3, box.baseline - 8);
        ctx.stroke();
        ctx.fillStyle = 'rgba(255, 255, 255, .86)';
        ctx.strokeStyle = 'rgba(203, 213, 225, .92)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        if (typeof ctx.roundRect === 'function') {{
          ctx.roundRect(box.x, box.y, box.width, box.height, 4);
        }} else {{
          ctx.rect(box.x, box.y, box.width, box.height);
        }}
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = '#111827';
        ctx.font = '12px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';
        ctx.fillText(label, box.x + 3, box.baseline);
        ctx.restore();
      }}

      function isHighlighted(viewer, entityId) {{
        const targets = (viewer.state.highlightTargets || []);
        if (!targets.length) return true;
        return targets.indexOf(String(entityId || '')) !== -1;
      }}

      function alphaForHighlight(viewer, entityId, alpha) {{
        const targets = (viewer.state.highlightTargets || []);
        if (!targets.length) return alpha;
        return isHighlighted(viewer, entityId) ? Math.max(alpha, 0.92) : alpha * 0.18;
      }}

      function alphaForTargets(viewer, entityIds, alpha) {{
        const targets = (viewer.state.highlightTargets || []);
        if (!targets.length) return alpha;
        const ids = (entityIds || []).map(value => String(value || '')).filter(Boolean);
        return ids.some(id => targets.indexOf(id) !== -1) ? Math.max(alpha, 0.88) : alpha * 0.16;
      }}

      function pointLabelFor(viewer, entityId, meta, panel, active, fixed) {{
        if (viewer.state.labelMode === 'off') return '';
        if (viewer.state.labelMode === 'all') {{
          if (fixed) return 'fixed:' + (entityId || 'entity');
          return (active ? '' : 'ghost ') + panelKey(panel) + ':' + (entityId || 'entity');
        }}
        return compactEntityLabel(entityId, meta);
      }}

      function pointPriority(entityId, meta, state, active, fixed) {{
        const entityType = String((meta || {{}}).type || '').toLowerCase();
        const role = String((meta || {{}}).role || '').toLowerCase();
        if (active && entityType === 'character') return 5;
        if (active && (state.trajectory_vector || role.indexOf('cover') !== -1 || role.indexOf('moving') !== -1)) return 4;
        if (active) return 3;
        if (fixed) return 1;
        return 1;
      }}

      function drawPoint(ctx, projector, point, label, fill, alpha, radius, viewer, entityId, priority) {{
        const canvasPoint = projector.point(point);
        const drawAlpha = viewer ? alphaForHighlight(viewer, entityId || label, alpha) : alpha;
        ctx.save();
        ctx.globalAlpha = drawAlpha;
        ctx.fillStyle = fill;
        ctx.strokeStyle = '#111827';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(canvasPoint.x, canvasPoint.y, radius || 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.restore();
        if (label) drawSceneLabel(ctx, viewer, canvasPoint, label, priority || 1, drawAlpha, entityId || label);
      }}

      function levelColors(level, index) {{
        const descriptor = String(((level || {{}}).id || '') + ' ' + ((level || {{}}).label || '')).toLowerCase();
        if (/floor_2|floor2|2층|upper/.test(descriptor)) return {{ fill: 'rgba(196, 181, 253, .46)', stroke: '#7c3aed', text: '#4c1d95', emphasis: true }};
        if (/slope|rubble|slab|ramp|경사/.test(descriptor)) return {{ fill: 'rgba(254, 240, 138, .42)', stroke: '#d97706', text: '#92400e', emphasis: true }};
        if (/street|road|도로|ground/.test(descriptor)) return {{ fill: 'rgba(224, 242, 254, .36)', stroke: '#38bdf8', text: '#075985', emphasis: false }};
        const palette = [
          {{ fill: 'rgba(224, 242, 254, .34)', stroke: '#38bdf8', text: '#075985', emphasis: false }},
          {{ fill: 'rgba(196, 181, 253, .38)', stroke: '#7c3aed', text: '#4c1d95', emphasis: true }},
          {{ fill: 'rgba(254, 240, 138, .36)', stroke: '#d97706', text: '#92400e', emphasis: true }}
        ];
        return palette[index % palette.length];
      }}

      function drawLevelPlanes(ctx, projector, viewer) {{
        const payload = (viewer || {{}}).payload || {{}};
        const levels = (((payload || {{}}).scene || {{}}).levels || []);
        levels.forEach((level, index) => {{
          const bounds = levelPlaneBounds(payload, projector.state, level);
          if (!bounds) return;
          const range = Array.isArray(level.z_range) ? level.z_range : [0, 0];
          const z = Number(range[0] || 0);
          const colors = levelColors(level, index);
          const corners = [
            [bounds.minX, bounds.minY, z],
            [bounds.maxX, bounds.minY, z],
            [bounds.maxX, bounds.maxY, z],
            [bounds.minX, bounds.maxY, z]
          ];
          const canvasCorners = corners.map(point => projector.point(point));
          ctx.save();
          ctx.fillStyle = colors.fill;
          ctx.strokeStyle = colors.stroke;
          ctx.lineWidth = colors.emphasis ? 2.2 : 1;
          ctx.globalAlpha = colors.emphasis ? 0.9 : 0.7;
          ctx.setLineDash(colors.emphasis ? [8, 4] : []);
          ctx.beginPath();
          canvasCorners.forEach((point, index) => {{
            if (index === 0) ctx.moveTo(point.x, point.y);
            else ctx.lineTo(point.x, point.y);
          }});
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
          if (!viewer || viewer.state.labelMode !== 'off') {{
            const labelPoint = projector.point([(bounds.minX + bounds.maxX) / 2, (bounds.minY + bounds.maxY) / 2, z]);
            ctx.fillStyle = colors.text;
            ctx.font = colors.emphasis ? '12px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' : '10px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';
            ctx.fillText(String(level.id || level.label || 'level'), labelPoint.x + 5, labelPoint.y - 5);
          }}
          ctx.restore();
        }});
      }}

      function drawCamera(ctx, projector, snapshot, alpha, viewer) {{
        const camera = (snapshot || {{}}).camera || {{}};
        const position = vec3(camera.position);
        const lookAt = vec3(camera.look_at);
        if (!position || !lookAt) return;
        const label = viewer && viewer.state.labelMode === 'all' ? 'camera' : '';
        drawPoint(ctx, projector, position, label, '#a78bfa', alpha, 5, viewer, 'camera', 1);
        drawLine(ctx, projector, position, lookAt, '#7c3aed', alpha, 1.5, false);
        const direction = normalizeVec(subVec(lookAt, position));
        const side = normalizeVec([-direction[1], direction[0], 0]);
        const up = [0, 0, 1];
        const distance = Math.max(0.8, Math.min(3.5, lengthVec(subVec(lookAt, position)) * 0.55));
        const fov = clamp(Number(camera.fov || 45), 18, 100) * Math.PI / 180;
        const spread = Math.tan(fov / 2) * distance;
        const center = addVec(position, scaleVec(direction, distance));
        const left = addVec(center, scaleVec(side, spread));
        const right = addVec(center, scaleVec(side, -spread));
        const top = addVec(center, scaleVec(up, spread * 0.5));
        drawLine(ctx, projector, position, left, '#7c3aed', alpha * 0.65, 1, true);
        drawLine(ctx, projector, position, right, '#7c3aed', alpha * 0.65, 1, true);
        drawLine(ctx, projector, position, top, '#7c3aed', alpha * 0.65, 1, true);
        drawLine(ctx, projector, left, right, '#7c3aed', alpha * 0.5, 1, true);
        drawLine(ctx, projector, right, top, '#7c3aed', alpha * 0.45, 1, true);
        drawLine(ctx, projector, top, left, '#7c3aed', alpha * 0.45, 1, true);
      }}

      function drawTransitionPaths(ctx, projector, payload, viewer) {{
        const snapshots = panelSnapshots(payload);
        const transitions = (((payload || {{}}).contract || {{}}).transitions || []);
        transitions.forEach(transition => {{
          const fromPanel = panelKey(transition.from_panel);
          const toPanel = panelKey(transition.to_panel);
          const entityId = transition.entity;
          const fromSnapshot = snapshots.find(snapshot => panelKey(snapshot.panel) === fromPanel);
          const toSnapshot = snapshots.find(snapshot => panelKey(snapshot.panel) === toPanel);
          const fromEntity = ((fromSnapshot || {{}}).entities || []).find(entity => entity.id === entityId);
          const toEntity = ((toSnapshot || {{}}).entities || []).find(entity => entity.id === entityId);
          const fromPosition = vec3((fromEntity || {{}}).position);
          const toPosition = vec3((toEntity || {{}}).position);
          const alpha = viewer ? alphaForHighlight(viewer, entityId, 0.58) : 0.58;
          if (fromPosition && toPosition) drawLine(ctx, projector, fromPosition, toPosition, '#475569', alpha, 1.2, true);
        }});
      }}

      function itemMatchesActivePanel(item, activePanel) {{
        const panel = panelKey((item || {{}}).panel);
        if (panel) return panel === activePanel;
        if (Array.isArray((item || {{}}).panels) && item.panels.length) {{
          return item.panels.map(panelKey).indexOf(activePanel) !== -1;
        }}
        return true;
      }}

      function entityPositionMap(payload, snapshot) {{
        const positions = {{}};
        (((payload || {{}}).scene || {{}}).fixed_entities || []).forEach(entity => {{
          if (!entity || !entity.id) return;
          const position = vec3(entity.position);
          if (position) positions[String(entity.id)] = position;
        }});
        ((snapshot || {{}}).entities || []).forEach(entity => {{
          if (!entity || !entity.id) return;
          const position = vec3(entity.position);
          if (position) positions[String(entity.id)] = position;
        }});
        return positions;
      }}

      function relationTargetIds(item) {{
        const ids = [];
        ['actor', 'anchor', 'as', 'comparison', 'cover', 'destination', 'destination_entity', 'entity', 'from', 'object', 'occluder', 'origin', 'origin_entity', 'recipient', 'reference', 'reference_object', 'same_as', 'sender', 'source', 'subject', 'target', 'threat', 'to', 'vector_entity', 'via', 'viewpoint_entity', 'waypoint', 'line_from', 'line_to'].forEach(field => {{
          const value = (item || {{}})[field];
          if (typeof value === 'string' && value) ids.push(value);
          else if (Array.isArray(value) && !value.every(entry => typeof entry === 'number')) value.forEach(entry => {{ if (entry) ids.push(String(entry)); }});
        }});
        if (Array.isArray((item || {{}}).entities)) item.entities.forEach(entry => {{ if (entry) ids.push(String(entry)); }});
        return Array.from(new Set(ids));
      }}

      function firstPosition(positions, ids) {{
        for (const id of ids || []) {{
          const key = String(id || '');
          if (key && positions[key]) return positions[key];
        }}
        return null;
      }}

      function drawRelationOverlay(ctx, projector, payload, viewer) {{
        if (!layerVisible(viewer, 'relations')) return;
        const snapshot = activeSnapshot(viewer);
        if (!snapshot) return;
        const positions = entityPositionMap(payload, snapshot);
        const activePanel = viewer.state.activePanel;
        const constraints = ((((payload || {{}}).contract || {{}}).constraints) || []);
        constraints.forEach(constraint => {{
          if (!itemMatchesActivePanel(constraint, activePanel)) return;
          const type = String(constraint.type || '').toLowerCase();
          const targets = relationTargetIds(constraint);
          const alpha = alphaForTargets(viewer, targets, 0.68);
          if (type === 'trajectory_to') {{
            const start = firstPosition(positions, [constraint.object, constraint.entity, constraint.actor, constraint.source, constraint.origin_entity]);
            const end = firstPosition(positions, [constraint.target, constraint.destination_entity, constraint.anchor]);
            if (start && end) drawArrowLine(ctx, projector, start, end, '#2563eb', alpha, 1.55, true);
            return;
          }}
          if (type === 'max_transfer_distance') {{
            const start = firstPosition(positions, [constraint.origin, constraint.from, constraint.source, constraint.sender, constraint.actor]);
            const end = firstPosition(positions, [constraint.destination, constraint.target, constraint.to, constraint.recipient]);
            if (start && end) drawArrowLine(ctx, projector, start, end, '#2563eb', alpha, 1.45, true);
            return;
          }}
          if (type === 'path_via') {{
            const start = firstPosition(positions, [constraint.object, constraint.entity, constraint.subject, constraint.source, constraint.from]);
            const via = firstPosition(positions, [constraint.via, constraint.waypoint, constraint.through]);
            const end = firstPosition(positions, [constraint.destination, constraint.target, constraint.to]);
            if (start && via) drawLine(ctx, projector, start, via, '#0ea5e9', alpha, 1.35, true);
            if (via && end) drawArrowLine(ctx, projector, via, end, '#0ea5e9', alpha, 1.35, true);
            return;
          }}
          if (type === 'cover_between' || type === 'behind_cover_from' || type === 'line_of_sight_blocked' || type === 'occluder_between_3d') {{
            const actor = firstPosition(positions, [constraint.actor, constraint.subject, constraint.entity, constraint.target]);
            const cover = firstPosition(positions, [constraint.cover, constraint.occluder, constraint.anchor]);
            const threat = firstPosition(positions, [constraint.threat, constraint.source, constraint.viewpoint_entity]);
            if (threat && cover) drawLine(ctx, projector, threat, cover, '#64748b', alpha, 1.25, true);
            if (cover && actor) drawLine(ctx, projector, cover, actor, '#16a34a', alpha, 1.45, true);
            return;
          }}
          if (type === 'no_line_of_fire' || type === 'not_aims_at') {{
            const source = firstPosition(positions, [constraint.actor, constraint.source, constraint.entity, constraint.vector_entity]);
            const target = firstPosition(positions, [constraint.target, constraint.subject, constraint.threat]);
            if (source && target) {{
              drawLine(ctx, projector, source, target, '#dc2626', alpha, 1.35, true);
              drawBlockedMark(ctx, projector, source, target, '#dc2626', alpha);
            }}
            return;
          }}
          if (type === 'above' || type === 'below' || type === 'vertical_separation' || type === 'on_level') {{
            const subject = firstPosition(positions, [constraint.subject, constraint.entity, constraint.actor]);
            const anchor = firstPosition(positions, [constraint.anchor, constraint.target]);
            if (subject && anchor) drawLine(ctx, projector, anchor, subject, '#7c3aed', alpha, 1.25, true);
            else if (subject) {{
              const levelTarget = [subject[0], subject[1], subject[2] + (type === 'on_level' ? 0.65 : 1.0)];
              drawLine(ctx, projector, subject, levelTarget, '#7c3aed', alpha, 1.1, true);
            }}
            return;
          }}
          if (type === 'distance_less_than' || type === 'distance_at_least') {{
            const subject = firstPosition(positions, [constraint.subject, constraint.entity, constraint.actor, constraint.a]);
            const target = firstPosition(positions, [constraint.target, constraint.to, constraint.anchor, constraint.b]);
            const comparison = firstPosition(positions, [constraint.comparison, constraint.other, constraint.reference, constraint.c, constraint.farther_than]);
            if (subject && target) drawLine(ctx, projector, subject, target, '#9333ea', alpha, 1.25, true);
            if (comparison && target) drawLine(ctx, projector, comparison, target, '#a855f7', alpha * 0.78, 1.05, true);
            return;
          }}
          if (type === 'same_side_as' || type === 'opposite_side_from') {{
            const subject = firstPosition(positions, [constraint.subject, constraint.entity, constraint.actor]);
            const reference = firstPosition(positions, [constraint.reference_object, constraint.reference, constraint.anchor, constraint.object]);
            const comparison = firstPosition(positions, [constraint.same_as, constraint.as, constraint.target, constraint.comparison, constraint.other]);
            if (reference && subject) drawLine(ctx, projector, reference, subject, '#f97316', alpha, 1.25, true);
            if (reference && comparison) drawLine(ctx, projector, reference, comparison, '#fb923c', alpha * 0.82, 1.1, true);
          }}
        }});
      }}

      function annotationEndpoint(value, positions) {{
        const direct = vec3(value);
        if (direct) return direct;
        const key = String(value || '');
        return key && positions[key] ? positions[key] : null;
      }}

      function drawAnnotation(ctx, projector, annotation, positions, viewer) {{
        const targets = relationTargetIds(annotation);
        const alpha = alphaForTargets(viewer, targets, 0.82);
        const from = annotationEndpoint(annotation.line_from, positions) || firstPosition(positions, targets);
        const to = annotationEndpoint(annotation.line_to, positions);
        const notePoint = vec3(annotation.position) || to || from;
        if (!notePoint) return;
        const color = '#db2777';
        if (from && to) drawArrowLine(ctx, projector, from, to, color, alpha, 1.25, true);
        else if (from && notePoint) drawLine(ctx, projector, from, notePoint, color, alpha, 1.15, true);
        const canvasPoint = projector.point(notePoint);
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.fillStyle = 'rgba(251, 207, 232, .82)';
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(canvasPoint.x, canvasPoint.y - 5);
        ctx.lineTo(canvasPoint.x + 5, canvasPoint.y);
        ctx.lineTo(canvasPoint.x, canvasPoint.y + 5);
        ctx.lineTo(canvasPoint.x - 5, canvasPoint.y);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        ctx.restore();
        const text = String(annotation.text || annotation.note || annotation.id || 'note').slice(0, 14);
        drawSceneLabel(ctx, viewer, canvasPoint, text, 4, alpha, String(annotation.id || text));
      }}

      function drawAnnotations(ctx, projector, payload, viewer) {{
        if (!layerVisible(viewer, 'annotations')) return;
        const snapshot = activeSnapshot(viewer);
        if (!snapshot) return;
        const positions = entityPositionMap(payload, snapshot);
        const activePanel = viewer.state.activePanel;
        const annotations = ((((payload || {{}}).contract || {{}}).annotations) || []);
        annotations.forEach(annotation => {{
          if (!itemMatchesActivePanel(annotation, activePanel)) return;
          drawAnnotation(ctx, projector, annotation, positions, viewer);
        }});
      }}

      function drawSnapshotEntities(ctx, projector, snapshot, active, viewer) {{
        if (!active && !layerVisible(viewer, 'ghosts')) return;
        const alpha = active ? 1 : 0.28;
        const pointFill = active ? '#fbbf24' : '#fde68a';
        const definitions = entityDefinitions(viewer.payload);
        (snapshot.entities || []).forEach(entity => {{
          const position = vec3(entity.position);
          if (!position) return;
          const entityId = String(entity.id || 'entity');
          const meta = mergedEntityMeta(definitions, entity);
          const layer = entityLayer(meta, false);
          if (!layerVisible(viewer, layer)) return;
          const label = pointLabelFor(viewer, entityId, meta, snapshot.panel, active, false);
          const priority = pointPriority(entityId, meta, entity, active, false);
          const geometry = geometryForEntity(meta);
          if (geometry && geometry.shape === 'humanoid_mannequin') {{
            drawPreviewGeometry(ctx, projector, position, geometry, meta, viewer, entityId, active ? 0.88 : 0.26, label, priority, entity);
            if (directionVector(entity) && layerVisible(viewer, 'vectors')) {{
              const vector = directionVector(entity);
              const vectorAlpha = viewer ? alphaForHighlight(viewer, entityId, active ? 0.86 : 0.24) : alpha;
              drawArrowLine(ctx, projector, position, addVec(position, scaleVec(normalizeVec(vector), active ? 1.0 : 0.72)), '#0f766e', vectorAlpha, active ? 1.8 : 1.1, !active);
            }}
            return;
          }}
          if (geometry && layer !== 'actors') drawPreviewGeometry(ctx, projector, position, geometry, meta, viewer, entityId, active ? 0.58 : 0.18, '', priority, entity);
          if (layer === 'actors' || directionVector(entity)) {{
            const fill = layer === 'actors' ? pointFill : (active ? '#67e8f9' : '#bae6fd');
            drawOrientedEntity(ctx, projector, entity, meta, label, fill, alpha, viewer, entityId, priority, active);
          }} else {{
            drawPoint(ctx, projector, position, label, pointFill, alpha, active ? 5.4 : 4.2, viewer, entityId, priority);
          }}
        }});
      }}

      function drawSceneViewer(viewer, shouldSync) {{
        const canvas = viewer.canvas;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        const width = canvas.width;
        const height = canvas.height;
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);
        viewer.labelBoxes = [];
        const projector = makeProjector(canvas, viewer.payload, viewer.state);
        if (layerVisible(viewer, 'levels')) drawLevelPlanes(ctx, projector, viewer);
        const scene = viewer.payload.scene || {{}};
        const definitions = entityDefinitions(viewer.payload);
        const active = activeSnapshot(viewer);
        const fixedIds = referencedFixedIds(viewer.payload, active);
        (scene.fixed_entities || []).forEach((entity, index) => {{
          const position = vec3(entity.position);
          if (!position) return;
          const entityId = String(entity.id || 'fixed');
          if (!fixedIds.has(entityId) && index >= 8) return;
          const meta = mergedEntityMeta(definitions, entity);
          const layer = entityLayer(meta, true);
          if (!layerVisible(viewer, layer)) return;
          const geometry = geometryForEntity(meta);
          const alpha = fixedIds.has(entityId) ? 0.48 : 0.24;
          if (geometry) drawPreviewGeometry(ctx, projector, position, geometry, meta, viewer, entityId, alpha, '', pointPriority(entityId, meta, entity, false, true), entity);
          const label = pointLabelFor(viewer, entityId, meta, '', false, true);
          const priority = pointPriority(entityId, meta, entity, false, true);
          drawPoint(ctx, projector, position, label, '#93c5fd', geometry ? alpha * 0.88 : alpha, geometry ? 3.2 : 4.6, viewer, entityId, priority);
        }});
        if (layerVisible(viewer, 'relations')) {{
          drawTransitionPaths(ctx, projector, viewer.payload, viewer);
          drawRelationOverlay(ctx, projector, viewer.payload, viewer);
        }}
        drawAnnotations(ctx, projector, viewer.payload, viewer);
        const snapshots = panelSnapshots(viewer.payload);
        snapshots.forEach(snapshot => {{
          if (panelKey(snapshot.panel) !== viewer.state.activePanel) drawSnapshotEntities(ctx, projector, snapshot, false, viewer);
        }});
        snapshots.forEach(snapshot => {{
          if (panelKey(snapshot.panel) === viewer.state.activePanel) {{
            drawSnapshotEntities(ctx, projector, snapshot, true, viewer);
            if (layerVisible(viewer, 'camera')) drawCamera(ctx, projector, snapshot, 0.9, viewer);
          }}
        }});
        updateSceneStatus(viewer);
        updatePanelButtons(viewer);
        updateLabelButtons(viewer);
        updateLayerButtons(viewer);
        updateLevelRail(viewer);
        if (shouldSync) propagateSceneSync(viewer);
      }}

      function updateSceneStatus(viewer) {{
        if (!viewer.status) return;
        viewer.status.textContent =
          'yaw: ' + Math.round(viewer.state.yaw * 180 / Math.PI) + 'deg | ' +
          'pitch: ' + Math.round(viewer.state.pitch * 180 / Math.PI) + 'deg | ' +
          'zoom: ' + viewer.state.zoom.toFixed(2) + ' | ' +
          'panel: ' + (viewer.state.activePanel || 'none');
      }}

      function updatePanelButtons(viewer) {{
        if (!viewer.panelHost) return;
        Array.from(viewer.panelHost.querySelectorAll('button[data-scene3d-panel]')).forEach(button => {{
          button.classList.toggle('active', button.dataset.scene3dPanel === viewer.state.activePanel);
        }});
      }}

      function updateLabelButtons(viewer) {{
        if (!viewer.labelHost) return;
        Array.from(viewer.labelHost.querySelectorAll('button[data-scene3d-label-mode]')).forEach(button => {{
          button.classList.toggle('active', button.dataset.scene3dLabelMode === viewer.state.labelMode);
        }});
      }}

      function updateLayerButtons(viewer) {{
        if (!viewer.layerHost) return;
        Array.from(viewer.layerHost.querySelectorAll('button[data-scene3d-layer]')).forEach(button => {{
          const layer = button.dataset.scene3dLayer;
          button.classList.toggle('active', layerVisible(viewer, layer));
        }});
      }}

      function levelForEntity(payload, entity) {{
        if (entity.level_id) return String(entity.level_id);
        const position = vec3(entity.position);
        if (!position) return '';
        const levels = (((payload || {{}}).scene || {{}}).levels || []);
        const z = position[2];
        for (const level of levels) {{
          const range = Array.isArray(level.z_range) ? level.z_range : [0, 0];
          const minZ = Number(range[0] || 0);
          const maxZ = Number(range[1] || minZ);
          if (z >= minZ && z <= maxZ) return String(level.id || '');
        }}
        return '';
      }}

      function updateLevelRail(viewer) {{
        if (!viewer.levelRail) return;
        if (!layerVisible(viewer, 'levels')) {{
          viewer.levelRail.innerHTML = '';
          viewer.levelRail.style.display = 'none';
          return;
        }}
        viewer.levelRail.style.display = '';
        const levels = (((viewer.payload || {{}}).scene || {{}}).levels || []);
        const snapshot = activeSnapshot(viewer);
        const definitions = entityDefinitions(viewer.payload);
        const entitiesByLevel = {{}};
        ((snapshot || {{}}).entities || []).forEach(entity => {{
          const levelId = levelForEntity(viewer.payload, entity);
          if (!levelId) return;
          const entityId = String(entity.id || 'entity');
          const label = compactEntityLabel(entityId, definitions[entityId] || {{}});
          if (!entitiesByLevel[levelId]) entitiesByLevel[levelId] = [];
          if (entitiesByLevel[levelId].indexOf(label) === -1) entitiesByLevel[levelId].push(label);
        }});
        viewer.levelRail.innerHTML = '';
        if (!levels.length) return;
        levels.forEach(level => {{
          const range = Array.isArray(level.z_range) ? level.z_range : [0, 0];
          const label = document.createElement('div');
          label.className = 'scene-3d-level-row';
          const name = document.createElement('span');
          const activeLabels = entitiesByLevel[String(level.id || '')] || [];
          name.textContent = (level.label || level.id || 'level') + ' z=' + String(range[0] || 0) + (activeLabels.length ? ' | ' + activeLabels.join(', ') : '');
          const bar = document.createElement('span');
          bar.className = 'scene-3d-level-bar';
          const fill = document.createElement('span');
          fill.className = 'scene-3d-level-fill';
          fill.style.width = activeLabels.length ? '100%' : '18%';
          bar.appendChild(fill);
          label.appendChild(name);
          label.appendChild(bar);
          viewer.levelRail.appendChild(label);
        }});
      }}

      function setupPanelButtons(viewer) {{
        if (!viewer.panelHost) return;
        const seen = [];
        panelSnapshots(viewer.payload).forEach(snapshot => {{
          const panel = panelKey(snapshot.panel);
          if (panel && seen.indexOf(panel) === -1) seen.push(panel);
        }});
        viewer.panelHost.innerHTML = '';
        seen.forEach(panel => {{
          const button = document.createElement('button');
          button.type = 'button';
          button.dataset.scene3dPanel = panel;
          button.textContent = 'Panel ' + panel;
          button.addEventListener('click', () => {{
            viewer.state.activePanel = panel;
            drawSceneViewer(viewer, true);
          }});
          viewer.panelHost.appendChild(button);
        }});
      }}

      function copyViewState(source, target) {{
        target.yaw = source.yaw;
        target.pitch = source.pitch;
        target.zoom = source.zoom;
        target.panX = source.panX;
        target.panY = source.panY;
      }}

      function propagateSceneSync(source) {{
        if (!source.state.sync) return;
        sceneViewers.forEach(viewer => {{
          if (viewer === source) return;
          if (!viewer.state.sync) return;
          if (viewer.sceneId !== source.sceneId) return;
          copyViewState(source.state, viewer.state);
          drawSceneViewer(viewer, false);
        }});
      }}

      function resetViewer(viewer) {{
        const activePanel = viewer.state.activePanel;
        const sync = viewer.state.sync;
        const labelMode = viewer.state.labelMode;
        const visibleLayers = Object.assign({{}}, viewer.state.visibleLayers || {{}});
        const highlightTargets = viewer.state.highlightTargets || [];
        viewer.state = defaultViewState(viewer.payload);
        viewer.state.activePanel = activePanel || viewer.state.activePanel;
        viewer.state.sync = sync;
        viewer.state.labelMode = labelMode || viewer.state.labelMode;
        viewer.state.visibleLayers = Object.assign(viewer.state.visibleLayers || {{}}, visibleLayers);
        viewer.state.highlightTargets = highlightTargets;
      }}

      function applyPreset(viewer, action) {{
        if (action === 'reset') {{
          resetViewer(viewer);
        }} else if (action === 'top') {{
          viewer.state.yaw = 0;
          viewer.state.pitch = -Math.PI / 2;
          viewer.state.zoom = 1;
          viewer.state.panX = 0;
          viewer.state.panY = 0;
        }} else if (action === 'front') {{
          viewer.state.yaw = 0;
          viewer.state.pitch = 0;
          viewer.state.zoom = 1;
          viewer.state.panX = 0;
          viewer.state.panY = 0;
        }} else if (action === 'side') {{
          viewer.state.yaw = Math.PI / 2;
          viewer.state.pitch = 0;
          viewer.state.zoom = 1;
          viewer.state.panX = 0;
          viewer.state.panY = 0;
        }} else if (action === 'iso') {{
          viewer.state.yaw = ISOMETRIC_YAW;
          viewer.state.pitch = ISOMETRIC_PITCH;
          viewer.state.zoom = 1;
          viewer.state.panX = 0;
          viewer.state.panY = 0;
        }} else if (action === 'camera') {{
          const snapshot = activeSnapshot(viewer);
          const camera = (snapshot || {{}}).camera || {{}};
          const position = vec3(camera.position);
          const lookAt = vec3(camera.look_at);
          if (position && lookAt) {{
            const direction = subVec(lookAt, position);
            const horizontal = Math.sqrt(direction[0] * direction[0] + direction[1] * direction[1]) || 1;
            viewer.state.yaw = Math.atan2(direction[0], direction[1]);
            viewer.state.pitch = clamp(-Math.atan2(direction[2], horizontal), MIN_PITCH, MAX_PITCH);
          }} else {{
            viewer.state.yaw = DEFAULT_YAW;
            viewer.state.pitch = DEFAULT_PITCH;
          }}
          viewer.state.zoom = 1;
          viewer.state.panX = 0;
          viewer.state.panY = 0;
        }}
        drawSceneViewer(viewer, true);
      }}

      function setupControls(viewer) {{
        if (!viewer.container) return;
        Array.from(viewer.container.querySelectorAll('button[data-scene3d-control]')).forEach(button => {{
          button.addEventListener('click', () => applyPreset(viewer, button.dataset.scene3dControl));
        }});
        Array.from(viewer.container.querySelectorAll('button[data-scene3d-label-mode]')).forEach(button => {{
          button.addEventListener('click', () => {{
            viewer.state.labelMode = button.dataset.scene3dLabelMode || 'key';
            drawSceneViewer(viewer, true);
          }});
        }});
        Array.from(viewer.container.querySelectorAll('button[data-scene3d-layer]')).forEach(button => {{
          button.addEventListener('click', () => {{
            const layer = button.dataset.scene3dLayer;
            viewer.state.visibleLayers[layer] = !layerVisible(viewer, layer);
            drawSceneViewer(viewer, true);
          }});
        }});
        if (viewer.syncControl) {{
          viewer.syncControl.addEventListener('change', () => {{
            viewer.state.sync = viewer.syncControl.checked;
            drawSceneViewer(viewer, true);
          }});
        }}
      }}

      function bindCanvasInput(viewer) {{
        const canvas = viewer.canvas;
        canvas.addEventListener('pointerdown', event => {{
          canvas.focus();
          viewer.drag = {{
            pointerId: event.pointerId,
            lastX: event.clientX,
            lastY: event.clientY,
            mode: (event.shiftKey || event.button === 1) ? 'pan' : 'rotate'
          }};
          canvas.classList.add('is-dragging');
          try {{ canvas.setPointerCapture(event.pointerId); }} catch (error) {{}}
        }});
        canvas.addEventListener('pointermove', event => {{
          if (!viewer.drag || viewer.drag.pointerId !== event.pointerId) return;
          const dx = event.clientX - viewer.drag.lastX;
          const dy = event.clientY - viewer.drag.lastY;
          viewer.drag.lastX = event.clientX;
          viewer.drag.lastY = event.clientY;
          const panMode = viewer.drag.mode === 'pan' || event.shiftKey || event.buttons === 4;
          if (panMode) {{
            viewer.state.panX += dx;
            viewer.state.panY += dy;
          }} else {{
            viewer.state.yaw += dx * 0.01;
            viewer.state.pitch = clamp(viewer.state.pitch + dy * 0.01, MIN_PITCH, MAX_PITCH);
          }}
          drawSceneViewer(viewer, true);
        }});
        function endDrag(event) {{
          if (!viewer.drag || viewer.drag.pointerId !== event.pointerId) return;
          viewer.drag = null;
          canvas.classList.remove('is-dragging');
          try {{ canvas.releasePointerCapture(event.pointerId); }} catch (error) {{}}
        }}
        canvas.addEventListener('pointerup', endDrag);
        canvas.addEventListener('pointercancel', endDrag);
        canvas.addEventListener('wheel', event => {{
          event.preventDefault();
          const direction = event.deltaY > 0 ? 0.9 : 1.1;
          viewer.state.zoom = clamp(viewer.state.zoom * direction, 0.25, 8);
          drawSceneViewer(viewer, true);
        }}, {{ passive: false }});
        canvas.addEventListener('dblclick', () => {{
          resetViewer(viewer);
          drawSceneViewer(viewer, true);
        }});
        canvas.addEventListener('keydown', event => {{
          let handled = true;
          if (event.key === 'ArrowLeft') viewer.state.yaw -= 0.08;
          else if (event.key === 'ArrowRight') viewer.state.yaw += 0.08;
          else if (event.key === 'ArrowUp') viewer.state.pitch = clamp(viewer.state.pitch - 0.08, MIN_PITCH, MAX_PITCH);
          else if (event.key === 'ArrowDown') viewer.state.pitch = clamp(viewer.state.pitch + 0.08, MIN_PITCH, MAX_PITCH);
          else if (event.key === '+' || event.key === '=') viewer.state.zoom = clamp(viewer.state.zoom * 1.1, 0.25, 8);
          else if (event.key === '-' || event.key === '_') viewer.state.zoom = clamp(viewer.state.zoom * 0.9, 0.25, 8);
          else if (event.key === '0') resetViewer(viewer);
          else handled = false;
          if (handled) {{
            event.preventDefault();
            drawSceneViewer(viewer, true);
          }}
        }});
      }}

      function createSceneViewer(canvas) {{
        let payload = {{}};
        try {{
          payload = JSON.parse(canvas.dataset.scene3d || '{{}}');
        }} catch (error) {{
          const ctx = canvas.getContext('2d');
          if (ctx) ctx.fillText('Scene 3D preview data could not be parsed.', 16, 24);
          return null;
        }}
        const container = canvas.closest('.scene-3d-preview');
        const viewer = {{
          canvas,
          payload,
          container,
          sceneId: canvas.dataset.sceneId || (((payload.contract || {{}}).coordinate_space || {{}}).scene_id || ''),
          state: defaultViewState(payload),
          status: container ? container.querySelector('[data-scene3d-status]') : null,
          panelHost: container ? container.querySelector('[data-scene3d-panels]') : null,
          labelHost: container ? container.querySelector('[data-scene3d-label-controls]') : null,
          layerHost: container ? container.querySelector('[data-scene3d-layer-controls]') : null,
          levelRail: container ? container.querySelector('[data-scene3d-level-rail]') : null,
          syncControl: container ? container.querySelector('input[data-scene3d-control="sync"]') : null,
          drag: null,
          labelBoxes: []
        }};
        canvas._scene3dViewer = viewer;
        setupPanelButtons(viewer);
        setupControls(viewer);
        bindCanvasInput(viewer);
        sceneViewers.push(viewer);
        drawSceneViewer(viewer, false);
        return viewer;
      }}

      document.querySelectorAll('canvas[data-scene3d]').forEach(canvas => {{
        createSceneViewer(canvas);
      }});

      function findSceneViewerForPage(pageId) {{
        const pageSelector = pageId ? '[data-preview-page-id="' + String(pageId).replace(/"/g, '\\"') + '"]' : '.page-card';
        const pageCard = document.querySelector(pageSelector);
        const canvas = pageCard ? pageCard.querySelector('canvas[data-scene3d]') : document.querySelector('canvas[data-scene3d]');
        return canvas ? canvas._scene3dViewer : null;
      }}

      window.__spatialPreviewRender = {{
        apply(options) {{
          const request = options || {{}};
          const viewer = findSceneViewerForPage(request.pageId || request.page_id || '');
          if (!viewer) return {{ ok: false, error: 'scene viewer not found' }};
          if (request.panel != null) viewer.state.activePanel = panelKey(request.panel);
          if (request.labelMode) viewer.state.labelMode = String(request.labelMode);
          if (Array.isArray(request.highlightTargets)) viewer.state.highlightTargets = request.highlightTargets.map(String);
          if (request.layers && typeof request.layers === 'object') {{
            Object.keys(request.layers).forEach(layer => {{
              viewer.state.visibleLayers[layer] = Boolean(request.layers[layer]);
            }});
          }}
          const view = String(request.view || request.preset || '').toLowerCase();
          if (view) applyPreset(viewer, view);
          else drawSceneViewer(viewer, true);
          const pageCard = viewer.canvas.closest('.page-card');
          return {{
            ok: true,
            pageId: pageCard ? pageCard.dataset.previewPageId : '',
            panel: viewer.state.activePanel,
            view: view || 'current',
            canvasSelector: '[data-preview-page-id="' + (pageCard ? pageCard.dataset.previewPageId : '') + '"] canvas[data-scene3d]'
          }};
        }}
      }};

      function setPageHighlight(element, targets) {{
        const pageCard = element.closest('.page-card');
        if (!pageCard) return;
        pageCard.querySelectorAll('canvas[data-scene3d]').forEach(canvas => {{
          const viewer = canvas._scene3dViewer;
          if (!viewer) return;
          viewer.state.highlightTargets = targets;
          drawSceneViewer(viewer, false);
        }});
      }}

      document.querySelectorAll('[data-preview-targets]').forEach(element => {{
        const targets = String(element.dataset.previewTargets || '').split(/\\s+/).filter(Boolean);
        element.addEventListener('pointerenter', () => setPageHighlight(element, targets));
        element.addEventListener('pointerleave', () => setPageHighlight(element, []));
        element.addEventListener('focus', () => setPageHighlight(element, targets));
        element.addEventListener('blur', () => setPageHighlight(element, []));
      }});
    }})();
  </script>
</body>
</html>"""


def spatial_preview_title(args: argparse.Namespace) -> str:
    if getattr(args, "plan_json", ""):
        try:
            plan = json.loads(args.plan_json)
        except json.JSONDecodeError:
            return "Spatial contract preview"
        return str(plan.get("scenario_title") or plan.get("story_title") or "Spatial contract preview")
    if getattr(args, "plan_file", ""):
        plan = load_json(Path(args.plan_file))
        return str(plan.get("scenario_title") or plan.get("story_title") or Path(args.plan_file).stem)
    if getattr(args, "run_dir", ""):
        state = load_state(Path(args.run_dir))
        return str(state.get("title") or "Spatial contract preview")
    return "Spatial contract preview"


def spatial_preview_source(args: argparse.Namespace) -> str:
    if getattr(args, "plan_json", ""):
        return "inline plan-json"
    if getattr(args, "plan_file", ""):
        return str(Path(args.plan_file))
    if getattr(args, "run_dir", ""):
        return str(Path(args.run_dir))
    return ""


def spatial_preview_output_path(args: argparse.Namespace) -> Path:
    if getattr(args, "output", ""):
        return Path(args.output)
    if getattr(args, "plan_json", ""):
        raise SystemExit("spatial-preview with --plan-json requires --output <html>.")
    if getattr(args, "plan_file", ""):
        plan_path = Path(args.plan_file)
        return plan_path.with_name(f"{plan_path.stem}_spatial_preview.html")
    if getattr(args, "run_dir", ""):
        return Path(args.run_dir) / "spatial_contract_preview.html"
    raise SystemExit("Use --plan-file, --plan-json, or --run-dir.")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Missing file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def stage_meta(stage_id: str) -> dict[str, str]:
    for stage in STAGES:
        if stage["id"] == stage_id:
            return stage
    raise SystemExit(f"Unknown stage: {stage_id}")


def blank_stage_state() -> dict[str, Any]:
    return {
        "status": "pending",
        "attempts": 0,
        "rerun_pending": False,
        "batch_id": "",
        "prompt_file": "",
        "subagent_prompt_file": "",
        "output_path": "",
        "description_path": "",
        "description_source": "",
        "description_imported_at": "",
        "generated_source": "",
        "external_prior_stage": False,
        "worker_status": "",
        "worker_note": "",
        "parent_note": "",
        "spatial_verdict": "",
        "spatial_note": "",
        "spatial_checked_at": "",
        "current_rerun_correction": "",
        "user_revision_overlays": [],
        "visual_reference_paths": [],
    }


def build_stage_states() -> dict[str, dict[str, Any]]:
    return {stage_id: blank_stage_state() for stage_id in STAGE_IDS}


def blank_stage_review() -> dict[str, Any]:
    return {
        "status": "pending",
        "note": "",
        "issues": [],
        "reviewed_at": "",
    }


def build_stage_reviews() -> dict[str, dict[str, Any]]:
    return {stage_id: blank_stage_review() for stage_id in STAGE_IDS}


def blank_stage_anchor_review() -> dict[str, Any]:
    return {
        "status": "pending",
        "anchor_item": "",
        "output_path": "",
        "note": "",
        "issues": [],
        "reviewed_at": "",
        "anchor_level_note": "",
    }


def build_stage_anchor_reviews() -> dict[str, dict[str, Any]]:
    return {stage_id: blank_stage_anchor_review() for stage_id in STAGE_IDS}


def stage_gate_key(from_stage: str, to_stage: str) -> str:
    return f"{from_stage}_to_{to_stage}"


def stage_transition(from_stage: str, to_stage: str) -> dict[str, Any] | None:
    for transition in TRANSITIONS:
        if transition["from_stage"] == from_stage and transition["to_stage"] == to_stage:
            return transition
    return None


def transition_after_stage(stage_id: str) -> dict[str, Any] | None:
    for transition in TRANSITIONS:
        if transition["from_stage"] == stage_id:
            return transition
    return None


def transition_before_stage(stage_id: str) -> dict[str, Any] | None:
    for transition in TRANSITIONS:
        if transition["to_stage"] == stage_id:
            return transition
    return None


def transition_gate_key(transition: dict[str, Any]) -> str:
    return stage_gate_key(transition["from_stage"], transition["to_stage"])


def transition_feedback_choices_text(transition: dict[str, Any]) -> str:
    return f"{transition['approve_choice']} | {FEEDBACK_CHOICE_OPEN_OVERLAY_UI} | {FEEDBACK_CHOICE_STOP_AFTER_STAGE}"


def transition_required_before_stage(state: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    transition = transition_before_stage(stage_id)
    if transition is None:
        return None
    if transition["from_stage"] in target_stages(state):
        return transition
    if stage_id == FINISH_STAGE:
        return transition
    return None


def blank_stage_gate() -> dict[str, Any]:
    return {
        "status": "pending",
        "note": "",
        "updated_at": "",
        "feedback_request": "",
        "feedback_request_created_at": "",
        "feedback_choice": "",
        "feedback_approved_at": "",
    }


def build_stage_gates() -> dict[str, dict[str, Any]]:
    return {transition_gate_key(transition): blank_stage_gate() for transition in TRANSITIONS}


def normalize_stage_gates(state: dict[str, Any]) -> None:
    gates = state.setdefault("stage_gates", {})
    for key, value in build_stage_gates().items():
        gate = gates.setdefault(key, value)
        for field, default in blank_stage_gate().items():
            gate.setdefault(field, default)
        if gate["status"] not in STAGE_GATE_STATUSES:
            raise SystemExit(f"Invalid stage gate status for {key}: {gate['status']}")


def normalize_target_stages(state: dict[str, Any]) -> None:
    raw = state.get("target_stages") or STAGE_IDS
    target_stages = as_list(raw)
    if not target_stages:
        target_stages = list(STAGE_IDS)
    for stage_id in target_stages:
        if stage_id not in STAGE_IDS:
            raise SystemExit(f"Invalid target stage: {stage_id}")
    ordered = [stage_id for stage_id in STAGE_IDS if stage_id in target_stages]
    if not ordered:
        ordered = list(STAGE_IDS)
    state["target_stages"] = ordered


def normalize_page_generation_mode(state: dict[str, Any]) -> None:
    mode = str(state.get("page_generation_mode") or "").strip()
    if not mode:
        mode = (
            PAGE_GENERATION_MODE_PARALLEL_BATCH
            if state.get("plan_approved")
            else PAGE_GENERATION_MODE_SEQUENTIAL_PRIOR_PAGES
        )
    if mode not in PAGE_GENERATION_MODE_VALUES:
        raise SystemExit(f"Invalid page_generation_mode: {mode}")
    state["page_generation_mode"] = mode


def normalize_stage_review(review: dict[str, Any], stage_id: str) -> None:
    for key, value in blank_stage_review().items():
        review.setdefault(key, value)
    review["issues"] = as_list(review.get("issues"))
    if review["status"] not in REVIEW_STATUSES:
        raise SystemExit(f"Invalid stage review status for {stage_id}: {review['status']}")


def normalize_stage_anchor_review(review: dict[str, Any], stage_id: str) -> None:
    for key, value in blank_stage_anchor_review().items():
        review.setdefault(key, value)
    review["issues"] = as_list(review.get("issues"))
    if review["status"] not in ANCHOR_REVIEW_STATUSES:
        raise SystemExit(f"Invalid stage anchor review status for {stage_id}: {review['status']}")


def normalize_stage_record(stage: dict[str, Any], page_id: str, stage_id: str) -> None:
    for key, value in blank_stage_state().items():
        stage.setdefault(key, value)
    if not isinstance(stage.get("user_revision_overlays"), list):
        stage["user_revision_overlays"] = as_list(stage.get("user_revision_overlays"))
    stage["visual_reference_paths"] = [str(path) for path in as_list(stage.get("visual_reference_paths"))]
    if stage["status"] not in VALID_STATUSES:
        raise SystemExit(f"Invalid stage status for {page_id}:{stage_id}: {stage['status']}")


def migrate_legacy_stage_records(stages: dict[str, Any]) -> None:
    if STORYBOARD_CONTI_SKETCH_INK_STAGE not in stages:
        stages[STORYBOARD_CONTI_SKETCH_INK_STAGE] = blank_stage_state()
    if FINISH_STAGE not in stages:
        stages[FINISH_STAGE] = blank_stage_state()
    for stage_id in list(stages.keys()):
        if stage_id not in STAGE_IDS:
            del stages[stage_id]


def normalize_state(state: dict[str, Any]) -> None:
    if "pages" not in state and "panels" in state:
        state["pages"] = legacy_panels_to_pages({"panels": state.get("panels", [])})
    state.setdefault("source_root", str(DEFAULT_SOURCE_ROOT))
    state.setdefault("excluded_source_roots", [str(DEFAULT_OUTPUT_ROOT)])
    state["text_policy"] = normalize_text_policy(state.get("text_policy"))
    state["character_locks"] = merge_unique(state.get("character_locks"))
    state["visual_text_guard"] = merge_unique(state.get("visual_text_guard"))
    state["spatial_continuity_plan"] = normalize_spatial_continuity_plan(
        state.get("spatial_continuity_plan")
        or state.get("setting_continuity_plan")
        or state.get("location_plan")
    )
    state["stage_order"] = STAGE_IDS
    normalize_target_stages(state)
    normalize_page_generation_mode(state)
    normalize_stage_gates(state)
    state["source_references"] = validate_reference_paths(state.get("source_references", []))
    stage_reviews = state.setdefault("stage_reviews", {})
    for stage_id in list(stage_reviews.keys()):
        if stage_id not in STAGE_IDS:
            del stage_reviews[stage_id]
    for stage_id in STAGE_IDS:
        review = stage_reviews.setdefault(stage_id, {})
        normalize_stage_review(review, stage_id)
    stage_anchor_reviews = state.setdefault("stage_anchor_reviews", {})
    for stage_id in list(stage_anchor_reviews.keys()):
        if stage_id not in STAGE_IDS:
            del stage_anchor_reviews[stage_id]
    for stage_id in STAGE_IDS:
        review = stage_anchor_reviews.setdefault(stage_id, {})
        normalize_stage_anchor_review(review, stage_id)
    state.setdefault("pages", [])
    for page in state.get("pages", []):
        page.setdefault("dependencies", [])
        page["references"] = validate_reference_paths(page.get("references", []))
        page.setdefault("panels", [])
        page["text_policy"] = normalize_text_policy(page.get("text_policy") or state["text_policy"])
        page["character_locks"] = merge_unique(page.get("character_locks"))
        page["visual_text_guard"] = merge_unique(page.get("visual_text_guard"))
        page.setdefault("page_dialogue_notes", "")
        page.setdefault("pacing_notes", DEFAULT_PACING_NOTES)
        page.setdefault("panel_shape_notes", DEFAULT_PANEL_SHAPE_NOTES)
        page.setdefault("negative_space_notes", DEFAULT_NEGATIVE_SPACE_NOTES)
        page.setdefault("detail_density_notes", DEFAULT_DETAIL_DENSITY_NOTES)
        page.setdefault("visual_emphasis_notes", DEFAULT_VISUAL_EMPHASIS_NOTES)
        page.setdefault("comic_effects_notes", DEFAULT_COMIC_EFFECTS_NOTES)
        page["narrative_plan"] = normalize_optional_object(page.get("narrative_plan"), "narrative_plan")
        page["location_continuity"] = normalize_location_continuity(
            page.get("location_continuity") or page.get("setting_continuity")
        )
        page["location_id"] = str(
            page.get("location_id") or page["location_continuity"].get("location_id") or ""
        ).strip()
        if page["location_id"] and not page["location_continuity"].get("location_id"):
            page["location_continuity"]["location_id"] = page["location_id"]
        page["spatial_contract_extraction"] = normalize_optional_object(
            page.get("spatial_contract_extraction"), "spatial_contract_extraction"
        )
        page.setdefault("spatial_logic_notes", "")
        page.setdefault("motion_checks", [])
        page.setdefault("must_match", [])
        page["spatial_contract"] = normalize_spatial_contract(page.get("spatial_contract"))
        stages = page.setdefault("stages", {})
        migrate_legacy_stage_records(stages)
        for stage_id in STAGE_IDS:
            stage = stages.setdefault(stage_id, {})
            normalize_stage_record(stage, page.get("id"), stage_id)


def load_state(run_dir: Path) -> dict[str, Any]:
    state = load_json(run_dir / "state.json")
    if state.get("workflow") != WORKFLOW:
        raise SystemExit(f"Unexpected workflow in state.json: {state.get('workflow')}")
    normalize_state(state)
    return state


def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    state["complete"] = workflow_complete(state)
    write_json(run_dir / "state.json", state)


def stage_state(page: dict[str, Any], stage_id: str) -> dict[str, Any]:
    if stage_id not in STAGE_IDS:
        raise SystemExit(f"Unknown stage: {stage_id}")
    return page["stages"][stage_id]


def page_complete_for_stage(page: dict[str, Any], stage_id: str) -> bool:
    return stage_state(page, stage_id).get("status") in PASS_STATUSES


def pages_complete_for_stage(state: dict[str, Any], stage_id: str) -> bool:
    pages = state.get("pages", [])
    return bool(pages) and all(page_complete_for_stage(page, stage_id) for page in pages)


def stage_review_passed(state: dict[str, Any], stage_id: str) -> bool:
    return state.get("stage_reviews", {}).get(stage_id, {}).get("status") == "passed"


def stage_anchor_review_passed(state: dict[str, Any], stage_id: str) -> bool:
    if not sequential_prior_pages_mode(state):
        return True
    return state.get("stage_anchor_reviews", {}).get(stage_id, {}).get("status") == "passed"


def stage_complete(state: dict[str, Any], stage_id: str) -> bool:
    return pages_complete_for_stage(state, stage_id) and stage_review_passed(state, stage_id)


def target_stages(state: dict[str, Any]) -> list[str]:
    normalize_target_stages(state)
    return state["target_stages"]


def workflow_complete(state: dict[str, Any]) -> bool:
    return all(stage_complete(state, stage_id) for stage_id in target_stages(state))


def current_stage_id(state: dict[str, Any]) -> str | None:
    for stage_id in target_stages(state):
        if not stage_complete(state, stage_id):
            return stage_id
    return None


def resolve_page(state: dict[str, Any], page_ref: str) -> dict[str, Any]:
    ref_slug = slugify(str(Path(page_ref).stem), str(page_ref))
    matches = []
    for page in state.get("pages", []):
        aliases = {
            page.get("id", ""),
            page.get("filename", ""),
            Path(page.get("filename", "")).stem,
            slugify(page.get("id", "")),
            slugify(Path(page.get("filename", "")).stem),
        }
        if page_ref in aliases or ref_slug in aliases:
            matches.append(page)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SystemExit(f"Ambiguous page reference: {page_ref}")
    raise SystemExit(f"Unknown page: {page_ref}")


def stage_output_path(run_dir: Path, page: dict[str, Any], stage_id: str, prefer_recorded: bool = False) -> Path:
    if prefer_recorded:
        stage = page.get("stages", {}).get(stage_id, {})
        recorded = str(stage.get("output_path") or "").strip()
        if recorded:
            return Path(recorded)
    return run_dir / stage_meta(stage_id)["dir"] / page["filename"]


def stage_description_path(run_dir: Path, page: dict[str, Any], stage_id: str) -> Path:
    stem = Path(page["filename"]).stem
    return run_dir / stage_meta(stage_id)["dir"] / f"{stem}_desc.md"


def recorded_stage_description_path(run_dir: Path, page: dict[str, Any], stage_id: str) -> Path:
    recorded = str(stage_state(page, stage_id).get("description_path") or "").strip()
    return Path(recorded) if recorded else stage_description_path(run_dir, page, stage_id)


def stage_prompt_path(run_dir: Path, page: dict[str, Any], stage_id: str) -> Path:
    stem = Path(page["filename"]).stem
    return run_dir / "prompts" / stage_id / f"{stem}.prompt.txt"


def subagent_prompt_path(run_dir: Path, page: dict[str, Any], stage_id: str) -> Path:
    stem = Path(page["filename"]).stem
    return run_dir / "subagent_prompts" / stage_id / f"{stem}.subagent.txt"


def previous_stage_id(stage_id: str) -> str:
    index = STAGE_IDS.index(stage_id)
    if index == 0:
        return ""
    return STAGE_IDS[index - 1]


def prior_stage_reference(
    run_dir: Path,
    page: dict[str, Any],
    stage_id: str,
    state: dict[str, Any] | None = None,
) -> str:
    prior = previous_stage_id(stage_id)
    if not prior:
        return "none"
    if state is not None and prior not in target_stages(state) and not page_complete_for_stage(page, prior):
        return f"none ({prior} skipped by target_stages)"
    path = stage_output_path(run_dir, page, prior, prefer_recorded=True)
    if stage_id == FINISH_STAGE:
        conti_desc = recorded_stage_description_path(run_dir, page, STORYBOARD_CONTI_SKETCH_INK_STAGE)
        marker = "required visual input / structure reference from storyboard_conti_sketch_ink"
        image_part = f"{path} ({marker})" if path.exists() else f"{path} ({marker}; not found yet)"
        if conti_desc.exists():
            return f"{image_part}; conti/sketch/ink spatial/temporal source: {conti_desc}"
        return image_part
    return str(path) if path.exists() else f"{path} (not found yet)"


def page_generation_mode(state: dict[str, Any]) -> str:
    normalize_page_generation_mode(state)
    return state["page_generation_mode"]


def sequential_prior_pages_mode(state: dict[str, Any]) -> bool:
    return page_generation_mode(state) == PAGE_GENERATION_MODE_SEQUENTIAL_PRIOR_PAGES


def ordered_pages(state: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(state.get("pages", []), key=lambda page: (int(page.get("order", 9999)), page.get("id", "")))


def previous_pages_for_page(state: dict[str, Any], page: dict[str, Any]) -> list[dict[str, Any]]:
    pages = ordered_pages(state)
    for index, candidate in enumerate(pages):
        if candidate.get("id") == page.get("id"):
            return pages[:index]
    return []


def stage_anchor_page(state: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    pages = ordered_pages(state)
    return pages[0] if pages and stage_id in STAGE_IDS else None


def is_stage_anchor_page(state: dict[str, Any], page: dict[str, Any], stage_id: str) -> bool:
    anchor_page = stage_anchor_page(state, stage_id)
    return bool(anchor_page and anchor_page.get("id") == page.get("id"))


def prior_pages_ready_for_stage(state: dict[str, Any], page: dict[str, Any], stage_id: str) -> bool:
    if not sequential_prior_pages_mode(state):
        return True
    return all(page_complete_for_stage(prior_page, stage_id) for prior_page in previous_pages_for_page(state, page))


def stage_anchor_allows_page_reservation(state: dict[str, Any], page: dict[str, Any], stage_id: str) -> bool:
    if not sequential_prior_pages_mode(state):
        return True
    if is_stage_anchor_page(state, page, stage_id):
        return True
    return stage_anchor_review_passed(state, stage_id)


def stage_anchor_review_required_page(state: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    if not sequential_prior_pages_mode(state):
        return None
    anchor_page = stage_anchor_page(state, stage_id)
    if not anchor_page:
        return None
    if not page_complete_for_stage(anchor_page, stage_id):
        return None
    if stage_anchor_review_passed(state, stage_id):
        return None
    return anchor_page


def stage_image_reference_path(run_dir: Path, page: dict[str, Any], stage_id: str) -> Path | None:
    if not page_complete_for_stage(page, stage_id):
        return None
    path = stage_output_path(run_dir, page, stage_id, prefer_recorded=True)
    return path if path.exists() else None


def visual_reference_paths(run_dir: Path, page: dict[str, Any], stage_id: str, state: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    prior_stage = previous_stage_id(stage_id)
    if prior_stage:
        current_prior = stage_image_reference_path(run_dir, page, prior_stage)
        if current_prior is not None:
            paths.append(str(current_prior))
    if sequential_prior_pages_mode(state):
        for prior_page in reversed(previous_pages_for_page(state, page)):
            prior_page_path = stage_image_reference_path(run_dir, prior_page, stage_id)
            if prior_page_path is not None:
                paths.append(str(prior_page_path))
    return merge_unique(paths)


def visual_reference_prompt_text(paths: list[str]) -> str:
    if not paths:
        return "- none"
    return "\n".join(f"- {path}" for path in paths)


def prior_page_continuity_reference_text(
    run_dir: Path,
    page: dict[str, Any],
    stage_id: str,
    state: dict[str, Any],
) -> str:
    if not sequential_prior_pages_mode(state):
        return "- none (legacy parallel_batch mode)"
    prior_pages = previous_pages_for_page(state, page)
    if not prior_pages:
        return "- none"
    lines: list[str] = []
    for priority, prior_page in enumerate(reversed(prior_pages), start=1):
        path = stage_image_reference_path(run_dir, prior_page, stage_id)
        if path is None:
            continue
        if priority == 1:
            role = "highest priority immediate previous page for action, pose, layout rhythm, and continuity"
        else:
            role = "supporting earlier page for style, character, prop, landmark, and setting continuity"
        line = f"- priority {priority}: {prior_page['filename']} -> {path} ({role})"
        if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE:
            desc_path = recorded_stage_description_path(run_dir, prior_page, stage_id)
            if desc_path.exists():
                line += f"; conti/sketch/ink description={desc_path}"
        lines.append(line)
    return "\n".join(lines) if lines else "- none"


def stage_anchor_review_checklist(stage_id: str) -> str:
    common = (
        "Common anchor checks: text_policy, character_locks, character appearance/anatomy lock, "
        "visual_text_guard, structured spatial_contract, panel/page continuity, page-to-page continuity, "
        "and technical quality must all fit the approved plan."
    )
    if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE:
        return (
            "storyboard_conti_sketch_ink anchor: preserve page composition, scene rhythm, reader eye flow, and "
            "spatial relations first; important entities must be recognizable as rough sketch forms with light clean "
            "line/ink structure; use arrows, relation lines, visibility/occlusion marks, and motion-path marks only "
            "where needed; reject meaningless pure-symbol conti, tone/color, lighting, glossy finish, or final polish. "
            + common
        )
    return (
        "finish anchor: preserve the inspected conti/sketch/ink layout, panel shapes, negative space, line rhythm, effect lines, "
        "text policy, and character structure while adding tone/color/final polish; reject redraws, layout changes, "
        "weakened effect-line direction, or changed eye/face/hand/limb/silhouette/body-proportion/posture structure. "
        + common
    )


def stage_anchor_reference_text(
    run_dir: Path,
    page: dict[str, Any],
    stage_id: str,
    state: dict[str, Any],
) -> str:
    if not sequential_prior_pages_mode(state):
        return "- none (legacy parallel_batch mode)"
    anchor_page = stage_anchor_page(state, stage_id)
    if not anchor_page:
        return "- none"
    if is_stage_anchor_page(state, page, stage_id):
        return "\n".join(
            [
                "- Stage level anchor: this page will define the stage level for later pages in this stage.",
                "- After import and parent inspect-pass, run anchor-review before reserving page 2 or later.",
                f"- Anchor checklist: {stage_anchor_review_checklist(stage_id)}",
            ]
        )
    review = state.get("stage_anchor_reviews", {}).get(stage_id, blank_stage_anchor_review())
    path = stage_image_reference_path(run_dir, anchor_page, stage_id)
    if review.get("status") == "passed" and path is not None:
        note = review.get("anchor_level_note") or review.get("note") or "stage level anchor passed"
        return "\n".join(
            [
                f"- anchor page: {anchor_page['filename']} -> {path}",
                "- role: highest-priority stage-level quality benchmark for roughness/detail/polish, line rhythm, "
                "visual intensity, text policy, and continuity consistency.",
                f"- anchor_level_note: {note}",
                f"- Anchor checklist: {stage_anchor_review_checklist(stage_id)}",
            ]
        )
    return "\n".join(
        [
            f"- anchor page: {anchor_page['filename']} is not available as a passed stage-level anchor yet.",
            "- Do not reserve later pages in this stage until anchor-review passes.",
            f"- Anchor checklist: {stage_anchor_review_checklist(stage_id)}",
        ]
    )


def assert_required_prior_stage_outputs_exist(state: dict[str, Any], run_dir: Path, pages: list[dict[str, Any]], stage_id: str) -> None:
    prior = previous_stage_id(stage_id)
    if not prior:
        return
    missing = []
    for page in pages:
        if not page_complete_for_stage(page, prior):
            missing.append(f"{page['filename']} needs parent-inspected {prior} before {stage_id}")
            continue
        path = stage_output_path(run_dir, page, prior, prefer_recorded=True)
        if not path.exists():
            missing.append(f"{page['filename']} requires {path}")
        if prior == STORYBOARD_CONTI_SKETCH_INK_STAGE:
            desc_path = recorded_stage_description_path(run_dir, page, prior)
            if not desc_path.exists():
                missing.append(f"{page['filename']} requires conti/sketch/ink description {desc_path}")
    if missing:
        details = "; ".join(missing)
        if stage_id == FINISH_STAGE:
            raise SystemExit(
                "Finish stage requires the parent-inspected storyboard_conti_sketch_ink image as input before reservation: "
                f"{details}"
            )
        raise SystemExit(
            f"{stage_id} stage requires the parent-inspected {prior} image"
            + (" and description" if prior == STORYBOARD_CONTI_SKETCH_INK_STAGE else "")
            + " as input before reservation: "
            f"{details}"
        )
    if not stage_review_passed(state, prior):
        if stage_id == FINISH_STAGE:
            raise SystemExit("Finish stage requires storyboard_conti_sketch_ink stage-review pass before reservation.")
        raise SystemExit(f"{stage_id} stage requires {prior} stage-review pass before reservation.")


def validate_stage_description(path: Path, page: dict[str, Any]) -> None:
    if not path.exists():
        raise SystemExit(f"Conti/sketch/ink description file not found: {path}")
    text = path.read_text(encoding="utf-8")
    stem_heading = f"# {Path(page['filename']).stem}_desc"
    issues = []
    if stem_heading not in text:
        issues.append(f"missing heading {stem_heading}")
    for heading in BLOCKING_DESCRIPTION_HEADINGS:
        if heading not in text:
            issues.append(f"missing heading {heading}")
    contract = page.get("spatial_contract", {})
    if spatial_contract_has_content(contract):
        for entity in contract.get("entities", []):
            entity_id = str(entity.get("id") or "").strip()
            if entity_id and entity_id not in text:
                issues.append(f"missing spatial_contract entity id {entity_id}")
        for constraint in contract.get("constraints", []):
            constraint_id = str(constraint.get("id") or "").strip()
            if constraint_id and constraint_id not in text:
                issues.append(f"missing spatial_contract constraint id {constraint_id}")
    if issues:
        details = "; ".join(issues)
        raise SystemExit(f"Invalid conti/sketch/ink description {path}: {details}")


def current_blockers(state: dict[str, Any]) -> list[tuple[dict[str, Any], str, dict[str, Any]]]:
    blockers: list[tuple[dict[str, Any], str, dict[str, Any]]] = []
    for page in state.get("pages", []):
        for stage_id in STAGE_IDS:
            stage = stage_state(page, stage_id)
            if stage.get("status") in CURRENT_STATUSES:
                blockers.append((page, stage_id, stage))
    return blockers


def dependency_passed_for_stage(state: dict[str, Any], page_id: str, stage_id: str) -> bool:
    for page in state.get("pages", []):
        if page.get("id") == page_id:
            return page_complete_for_stage(page, stage_id)
    return False


def dependencies_ready(state: dict[str, Any], page: dict[str, Any], stage_id: str) -> bool:
    return all(dependency_passed_for_stage(state, dep, stage_id) for dep in page.get("dependencies", []))


def page_sort_key(page: dict[str, Any], stage_id: str) -> tuple[int, int, str]:
    stage = stage_state(page, stage_id)
    return (0 if stage.get("rerun_pending") else 1, int(page.get("order", 9999)), page.get("id", ""))


def reset_stage_review(state: dict[str, Any], stage_id: str, note: str) -> None:
    review = state.setdefault("stage_reviews", {}).setdefault(stage_id, blank_stage_review())
    review["status"] = "pending"
    review["note"] = note
    review["issues"] = []
    review["reviewed_at"] = ""


def reset_stage_anchor_review(state: dict[str, Any], stage_id: str, note: str) -> None:
    review = state.setdefault("stage_anchor_reviews", {}).setdefault(stage_id, blank_stage_anchor_review())
    review["status"] = "pending"
    review["anchor_item"] = ""
    review["output_path"] = ""
    review["note"] = note
    review["issues"] = []
    review["reviewed_at"] = ""
    review["anchor_level_note"] = ""


def reset_following_stage_gates(state: dict[str, Any], stage_id: str, note: str) -> None:
    stage_index = STAGE_IDS.index(stage_id)
    for transition in TRANSITIONS:
        if STAGE_IDS.index(transition["from_stage"]) < stage_index:
            continue
        gate = state.setdefault("stage_gates", {}).setdefault(transition_gate_key(transition), blank_stage_gate())
        gate["status"] = "pending"
        gate["note"] = note
        gate["updated_at"] = now_iso()
        gate["feedback_request"] = ""
        gate["feedback_request_created_at"] = ""
        gate["feedback_choice"] = ""
        gate["feedback_approved_at"] = ""


def feedback_request_path(run_dir: Path, from_stage: str, to_stage: str) -> Path:
    return run_dir / "feedback_requests" / f"{stage_gate_key(from_stage, to_stage)}.json"


def feedback_request_markdown_path(run_dir: Path, from_stage: str, to_stage: str) -> Path:
    return feedback_request_path(run_dir, from_stage, to_stage).with_suffix(".md")


def resolved_path_string(path: Path) -> str:
    return str(path.resolve(strict=False))


def transition_feedback_outputs(state: dict[str, Any], run_dir: Path, stage_id: str) -> list[dict[str, Any]]:
    outputs = []
    for page in state.get("pages", []):
        stage = stage_state(page, stage_id)
        output_path = stage.get("output_path") or str(stage_output_path(run_dir, page, stage_id))
        outputs.append(
            {
                "page_id": page.get("id", ""),
                "filename": page.get("filename", ""),
                "page_no": page.get("page_no", ""),
                "stage": stage_id,
                "output_path": output_path,
                "description_path": stage.get("description_path", ""),
                "parent_note": stage.get("parent_note", ""),
                "spatial_verdict": stage.get("spatial_verdict", ""),
                "spatial_note": stage.get("spatial_note", ""),
            }
        )
    return outputs


def build_feedback_request(
    state: dict[str, Any],
    run_dir: Path,
    from_stage: str,
    to_stage: str,
    created_at: str,
) -> dict[str, Any]:
    gate_key = stage_gate_key(from_stage, to_stage)
    transition = stage_transition(from_stage, to_stage)
    if transition is None:
        raise SystemExit(f"Unsupported stage transition: {from_stage} -> {to_stage}")
    review = state.get("stage_reviews", {}).get(from_stage, blank_stage_review())
    return {
        "workflow": WORKFLOW,
        "type": "stage_transition_feedback_request",
        "run_dir": str(run_dir),
        "from_stage": from_stage,
        "to_stage": to_stage,
        "gate_key": gate_key,
        "created_at": created_at,
        "stage_review": {
            "status": review.get("status", "pending"),
            "note": review.get("note", ""),
            "issues": as_list(review.get("issues")),
            "reviewed_at": review.get("reviewed_at", ""),
        },
        "outputs": transition_feedback_outputs(state, run_dir, from_stage),
        "choices": [
            {
                "id": transition["approve_choice"],
                "label": transition["approve_label"],
                "next_command": (
                    "comic_storyboard_runner.py approve-next-stage "
                    f"--run-dir {run_dir} --from-stage {from_stage} --to-stage {to_stage} "
                    f"--feedback-request {feedback_request_path(run_dir, from_stage, to_stage)} "
                    f"--feedback-choice {transition['approve_choice']} --note \"{transition['approve_note_placeholder']}\""
                ),
            },
            {
                "id": FEEDBACK_CHOICE_OPEN_OVERLAY_UI,
                "label": "Open revision UI or create agent markup",
                "next_command": (
                    "review_overlay_server.py serve "
                    f"--run-dir {run_dir} --stage {from_stage}"
                ),
            },
            {
                "id": FEEDBACK_CHOICE_STOP_AFTER_STAGE,
                "label": "Stop after current stage",
                "next_command": (
                    "comic_storyboard_runner.py stop-after-stage "
                    f"--run-dir {run_dir} --stage {from_stage} --note \"<user stops after {from_stage}>\""
                ),
            },
        ],
    }


def feedback_request_markdown(request: dict[str, Any]) -> str:
    outputs = request.get("outputs", [])
    lines = [
        "# Comic Storyboard Stage Feedback Request",
        "",
        f"Run folder: {request.get('run_dir', '')}",
        f"Transition: {request.get('from_stage', '')} -> {request.get('to_stage', '')}",
        f"Gate: {request.get('gate_key', '')}",
        f"Created at: {request.get('created_at', '')}",
        "",
        "Stage review:",
        f"- status: {request.get('stage_review', {}).get('status', '')}",
        f"- note: {request.get('stage_review', {}).get('note', '')}",
        f"- issues: {'; '.join(as_list(request.get('stage_review', {}).get('issues'))) or 'none'}",
        "",
        "Stage outputs:",
    ]
    for output in outputs:
        lines.append(f"- {output.get('filename', '')}: {output.get('output_path', '')}")
    lines.extend(["", "User feedback choices:"])
    for choice in request.get("choices", []):
        lines.append(f"- {choice.get('id', '')}: {choice.get('label', '')}")
        lines.append(f"  command: {choice.get('next_command', '')}")
    lines.append("")
    return "\n".join(lines)


def write_transition_feedback_request(
    state: dict[str, Any],
    run_dir: Path,
    from_stage: str,
    to_stage: str,
    created_at: str,
) -> Path:
    request = build_feedback_request(state, run_dir, from_stage, to_stage, created_at)
    path = feedback_request_path(run_dir, from_stage, to_stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, request)
    feedback_request_markdown_path(run_dir, from_stage, to_stage).write_text(
        feedback_request_markdown(request),
        encoding="utf-8",
    )
    return path


def mark_transition_waiting_for_feedback(
    state: dict[str, Any],
    run_dir: Path,
    from_stage: str,
    to_stage: str,
    note: str,
) -> Path | None:
    if to_stage not in target_stages(state):
        return None
    gate = state.setdefault("stage_gates", {}).setdefault(stage_gate_key(from_stage, to_stage), blank_stage_gate())
    if gate.get("status") != "approved":
        created_at = now_iso()
        gate["status"] = "pending_user_feedback"
        gate["note"] = note
        gate["updated_at"] = created_at
        gate["feedback_choice"] = ""
        gate["feedback_approved_at"] = ""
        request_path = write_transition_feedback_request(state, run_dir, from_stage, to_stage, created_at)
        gate["feedback_request"] = resolved_path_string(request_path)
        gate["feedback_request_created_at"] = created_at
        return Path(gate["feedback_request"])
    return None


def transition_gate_allows(state: dict[str, Any], from_stage: str, to_stage: str) -> bool:
    gate = state.setdefault("stage_gates", {}).setdefault(stage_gate_key(from_stage, to_stage), blank_stage_gate())
    return gate.get("status") == "approved"


def assert_valid_feedback_approval(
    args: argparse.Namespace,
    state: dict[str, Any],
    run_dir: Path,
    gate: dict[str, Any],
) -> Path:
    transition = stage_transition(args.from_stage, args.to_stage)
    if transition is None:
        raise SystemExit(f"Unsupported stage transition: {args.from_stage} -> {args.to_stage}")
    approve_choice = transition["approve_choice"]
    if args.feedback_choice != approve_choice:
        raise SystemExit(f"approve-next-stage requires --feedback-choice {approve_choice}.")
    if gate.get("status") != "pending_user_feedback":
        raise SystemExit(
            "approve-next-stage requires the stage gate to be pending_user_feedback. "
            f"Current gate status: {gate.get('status', 'pending')}"
        )
    request_path = Path(args.feedback_request)
    request = load_json(request_path)
    gate_key = stage_gate_key(args.from_stage, args.to_stage)
    if request.get("workflow") != WORKFLOW or request.get("type") != "stage_transition_feedback_request":
        raise SystemExit("Invalid feedback request: not a comic storyboard transition feedback request.")
    if request.get("from_stage") != args.from_stage or request.get("to_stage") != args.to_stage:
        raise SystemExit("Invalid feedback request: stage transition does not match approve-next-stage arguments.")
    if request.get("gate_key") != gate_key:
        raise SystemExit("Invalid feedback request: gate key does not match approve-next-stage arguments.")
    if resolved_path_string(Path(request.get("run_dir", ""))) != resolved_path_string(run_dir):
        raise SystemExit("Invalid feedback request: run_dir does not match this run.")
    expected_request = gate.get("feedback_request", "")
    if expected_request and resolved_path_string(request_path) != resolved_path_string(Path(expected_request)):
        raise SystemExit("Invalid feedback request: path does not match the active stage gate request.")
    expected_created_at = gate.get("feedback_request_created_at", "")
    if expected_created_at and request.get("created_at") != expected_created_at:
        raise SystemExit("Invalid feedback request: created_at does not match the active stage gate request.")
    choices = {choice.get("id") for choice in request.get("choices", [])}
    if approve_choice not in choices:
        raise SystemExit(f"Invalid feedback request: {approve_choice} choice is missing.")
    return request_path


def archive_existing_stage_artifacts(
    run_dir: Path | None,
    page: dict[str, Any],
    stage_id: str,
    stage: dict[str, Any],
) -> dict[str, str]:
    if run_dir is None:
        return {}
    archive: dict[str, str] = {}
    timestamp = now_iso().replace("-", "").replace(":", "").replace("+", "")
    archive_index = len(stage.get("rerun_history", [])) + 1
    archive_dir = run_dir / "rerun_archive" / stage_id / Path(page["filename"]).stem
    output_value = str(stage.get("output_path") or "").strip()
    if output_value:
        output_path = Path(output_value)
        if output_path.exists():
            archive_dir.mkdir(parents=True, exist_ok=True)
            archived_output = archive_dir / f"{timestamp}-{archive_index:03d}-output{output_path.suffix}"
            shutil.copy2(output_path, archived_output)
            archive["archived_output_path"] = str(archived_output)
    description_value = str(stage.get("description_path") or "").strip()
    if description_value:
        description_path = Path(description_value)
        if description_path.exists():
            archive_dir.mkdir(parents=True, exist_ok=True)
            archived_description = archive_dir / f"{timestamp}-{archive_index:03d}-desc{description_path.suffix}"
            shutil.copy2(description_path, archived_description)
            archive["archived_description_path"] = str(archived_description)
    return archive


def mark_page_stage_for_rerun(
    page: dict[str, Any],
    stage_id: str,
    note: str,
    run_dir: Path | None = None,
) -> None:
    stage = stage_state(page, stage_id)
    if stage.get("status") not in {"pending", "generation_requested", "imported", "inspected_pass", "complete"}:
        raise SystemExit(f"Cannot rerun page stage in status {stage.get('status')}: {page['filename']} {stage_id}")
    archived_artifacts = archive_existing_stage_artifacts(run_dir, page, stage_id, stage)
    history = stage.setdefault("rerun_history", [])
    history_entry = {
        "at": now_iso(),
        "from_status": stage.get("status"),
        "note": note,
        "output_path": stage.get("output_path", ""),
        "worker_status": stage.get("worker_status", ""),
        "worker_note": stage.get("worker_note", ""),
        "spatial_verdict": stage.get("spatial_verdict", ""),
        "spatial_note": stage.get("spatial_note", ""),
        "user_revision_overlays": stage.get("user_revision_overlays", []),
        "visual_reference_paths": stage.get("visual_reference_paths", []),
    }
    history_entry.update(archived_artifacts)
    history.append(history_entry)
    stage["status"] = "pending"
    stage["rerun_pending"] = True
    stage["batch_id"] = ""
    stage["requested_at"] = ""
    stage["worker_status"] = ""
    stage["worker_note"] = ""
    stage["parent_note"] = note
    stage["spatial_verdict"] = ""
    stage["spatial_note"] = ""
    stage["spatial_checked_at"] = ""
    stage["current_rerun_correction"] = note
    stage["user_revision_overlays"] = []
    stage["visual_reference_paths"] = []


def downstream_prior_page_dependents(
    state: dict[str, Any],
    source_page: dict[str, Any],
    stage_id: str,
) -> list[dict[str, Any]]:
    if not sequential_prior_pages_mode(state):
        return []
    pages = ordered_pages(state)
    source_index = next(
        (index for index, page in enumerate(pages) if page.get("id") == source_page.get("id")),
        None,
    )
    if source_index is None:
        return []
    return [
        downstream_page
        for downstream_page in pages[source_index + 1 :]
        if stage_state(downstream_page, stage_id).get("status") != "pending"
    ]


def mark_downstream_prior_page_dependents_for_rerun(
    state: dict[str, Any],
    source_page: dict[str, Any],
    stage_id: str,
    note: str,
    run_dir: Path | None = None,
) -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for downstream_page in downstream_prior_page_dependents(state, source_page, stage_id):
        mark_page_stage_for_rerun(downstream_page, stage_id, note, run_dir)
        updated.append(downstream_page)
    return updated


def append_unique_page(pages: list[dict[str, Any]], page: dict[str, Any]) -> None:
    if page.get("id") not in {entry.get("id") for entry in pages}:
        pages.append(page)


def pages_excluding(pages: list[dict[str, Any]], excluded: list[dict[str, Any]]) -> list[dict[str, Any]]:
    excluded_ids = {page.get("id") for page in excluded}
    return [page for page in pages if page.get("id") not in excluded_ids]


def print_downstream_unchanged_hint(pages: list[dict[str, Any]]) -> None:
    if not pages:
        return
    for page in pages:
        print(f"DOWNSTREAM_UNCHANGED_ITEM: {page['filename']}")
    print("DOWNSTREAM_SCOPE_HINT: pass --cascade-downstream to rerun later pages in the same stage.")


def record_revision_scope_history(
    state: dict[str, Any],
    *,
    command: str,
    stage_id: str,
    requested_pages: list[dict[str, Any]],
    cascade_downstream: bool,
    downstream_rerun_pages: list[dict[str, Any]],
    downstream_unchanged_pages: list[dict[str, Any]],
    manifest: str = "",
    note: str = "",
) -> None:
    state.setdefault("revision_scope_history", []).append(
        {
            "at": now_iso(),
            "command": command,
            "stage": stage_id,
            "requested_pages": [page["filename"] for page in requested_pages],
            "cascade_downstream": bool(cascade_downstream),
            "downstream_rerun_pages": [page["filename"] for page in downstream_rerun_pages],
            "downstream_unchanged_pages": [page["filename"] for page in downstream_unchanged_pages],
            "manifest": manifest,
            "note": note,
        }
    )


def stage_instruction(stage_id: str) -> str:
    if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE:
        return (
            "Create the comic-page conti/sketch/light-ink pass from the approved narrative page design. Preserve panel "
            "composition, story rhythm, reader eye flow, character action, emotional beat, and spatial/cause-effect logic first. "
            "Draw every important character, object, and environment element with readable rough sketch forms and light clean "
            "line structure: clear enough to identify the entity category, pose, action, occluder, path, and panel role, but "
            "not final ink. Add arrows, vectors, sight/direction lines, movement-path marks, visibility/occlusion marks, and "
            "relation lines only where needed to inspect the spatial validation overlay. "
            "Simplify or omit unimportant props/background elements when they are not needed for story readability, "
            "action readability, visibility/occlusion, landmark continuity, or page composition. Do not render tone/color, "
            "lighting, texture, dialogue, SFX, typography, glossy finish, or final polish. "
            "The image should remain readable as a comic conti/sketch page rather than a spatial validation diagram, while still making "
            "entity positions, facing, gaze/direction/movement vectors, visibility, occlusion, and panel-to-panel "
            "state continuity easy to inspect. "
            "Also write the required *_desc.md beside the image with symbol legend, panel spatial map, "
            "constraint check, and temporal continuity check sections. Keep the required section headings "
            "exactly as specified, but write the description body text in Korean."
        )
    if stage_id == FINISH_STAGE:
        return (
            "Create the final Korean comic-book page using the required parent-inspected "
            "storyboard_conti_sketch_ink image as the visual input and structure reference. Add tones, color "
            "if requested, lighting, shadows, policy-approved lettering/SFX or required text absence, "
            "and cleanup without changing page layout, panel count, freeform panel shapes, negative "
            "space, text placement or text absence, comic effect lines, visual emphasis, line-weight rhythm, "
            "character/object blocking, motion direction, or action logic. Finish must preserve the inspected "
            "storyboard_conti_sketch_ink eye, face, hand, limb, silhouette, body proportion, and posture structure."
        )
    raise SystemExit(f"Unknown stage: {stage_id}")


def ordered_sfx(page: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for panel in page.get("panels", []):
        values = merge_unique(values, panel.get("sfx"))
    return values


def text_policy_instruction_lines(policy: str, page: dict[str, Any]) -> list[str]:
    policy = normalize_text_policy(policy)
    if policy == TEXT_POLICY_DIALOGUE_SFX_CAPTIONS:
        return [
            "Text policy: dialogue_sfx_captions",
            "Use adapted_dialogue, approved SFX, and approved captions inside the page image. Keep lettering short, legible, and placed so it does not cover key faces, hands, props, or action.",
        ]
    if policy == TEXT_POLICY_SFX_ONLY:
        allowed_sfx = ", ".join(ordered_sfx(page)) or "none listed"
        return [
            "Text policy: sfx_only",
            f"Only approved SFX may appear in the generated image: {allowed_sfx}.",
            "Do not render any other text: no spoken dialogue, no speech balloons, no captions, no narration, no signage, no environmental text, no labels, no page or panel numbers, no random typography, and no corner labels.",
        ]
    if policy == TEXT_POLICY_TEXT_FREE:
        return [
            "Text policy: text_free",
            "No text of any kind may appear in the generated image.",
            "Do not render SFX, dialogue, speech balloons, captions, signage, labels, page or panel numbers, logos, environmental text, random glyphs, or corner labels.",
            "Absolute ban: no dialogue, no speech balloons, no captions, no signage, no labels, no page or panel numbers, no SFX, no environmental text, no random glyphs.",
        ]
    raise SystemExit(f"Unknown text_policy: {policy}")


def text_policy_worker_check_lines(policy: str) -> list[str]:
    policy = normalize_text_policy(policy)
    if policy == TEXT_POLICY_DIALOGUE_SFX_CAPTIONS:
        return [
            "- Uses adapted dialogue/SFX/captions from the approved plan, not raw source dialogue by default",
            "- Speech balloons, SFX, and captions are legible and do not cover key art",
        ]
    if policy == TEXT_POLICY_SFX_ONLY:
        return [
            "- Rejects spoken dialogue, speech balloons, captions/narration, signage, labels, page/panel numbers, random typography, environmental text, or corner labels",
            "- Allows only approved SFX from the panel metadata and verifies SFX placement does not cover key art",
        ]
    if policy == TEXT_POLICY_TEXT_FREE:
        return [
            "- Rejects all rendered text/glyphs, including SFX, dialogue, captions, signage, labels, panel/page numbers, logos, environmental text, random typography, and corner labels",
            "- Treats dialogue, caption, and SFX fields as planning metadata only; none may appear in the image",
        ]
    raise SystemExit(f"Unknown text_policy: {policy}")


def text_policy_negative_terms(policy: str) -> str:
    policy = normalize_text_policy(policy)
    if policy == TEXT_POLICY_SFX_ONLY:
        return (
            "spoken dialogue, speech balloons, captions, narration, signage, environmental text, labels, "
            "page numbers, panel numbers, random typography, corner labels, unapproved text"
        )
    if policy == TEXT_POLICY_TEXT_FREE:
        return (
            "any text, SFX letters, speech balloons, captions, narration, signage, environmental text, "
            "labels, page numbers, panel numbers, logos, random glyphs, random typography, corner labels"
        )
    return ""


def text_policy_batch_summary(policy: str) -> str:
    policy = normalize_text_policy(policy)
    if policy == TEXT_POLICY_SFX_ONLY:
        return (
            "Only approved SFX may be rendered; speech balloons, dialogue, captions, signage, labels, "
            "environmental text, and page/panel numbers are forbidden."
        )
    if policy == TEXT_POLICY_TEXT_FREE:
        return "All rendered text is forbidden, including SFX, dialogue, captions, signage, labels, and page/panel numbers."
    return "Approved adapted dialogue, SFX, and short captions are included in the page image."


def bullet_text(items: list[str], empty: str = "- none") -> str:
    return "\n".join(f"- {item}" for item in items) or empty


def format_spatial_value(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(f"{item:g}" if isinstance(item, float) else str(item) for item in value) + "]"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def spatial_entity_summary(entity: dict[str, Any]) -> str:
    detail = f"{entity.get('id')}"
    extra = []
    if entity.get("type"):
        extra.append(f"type={entity.get('type')}")
    if entity.get("role"):
        extra.append(f"role={entity.get('role')}")
    if entity.get("blocking_symbol"):
        extra.append(f"blocking_symbol={format_spatial_value(entity.get('blocking_symbol'))}")
    if extra:
        detail += " (" + ", ".join(extra) + ")"
    return detail


def constraint_prompt_guard_lines(constraint: dict[str, Any]) -> list[str]:
    constraint_id = str(constraint.get("id") or "")
    constraint_type = str(constraint.get("type") or "")
    lines: list[str] = []
    if constraint_type in {"behind_cover_from", "line_of_sight_blocked"} or constraint.get("viewpoint_entity"):
        actor = str(spatial_constraint_value(constraint, "actor", "subject", "protected", "target") or "actor")
        threat = str(spatial_constraint_value(constraint, "threat", "source", "from", "enemy") or "")
        viewpoint = str(spatial_constraint_value(constraint, "viewpoint_entity", "viewpoint", "from_viewpoint") or threat or "threat")
        cover = str(spatial_constraint_value(constraint, "cover", "blocker", "object") or "cover")
        relation = "line of fire"
        if constraint_type == "line_of_sight_blocked":
            relation = "line of sight"
        lines.append(
            f"- cover viewpoint guard {constraint_id}: {actor} must be behind {cover} "
            f"from {viewpoint}'s {relation} / threat viewpoint; reader POV is insufficient."
        )
        if constraint.get("allowed_exposure"):
            lines.append(
                f"- cover exposure guard {constraint_id}: "
                f"allowed_exposure={format_spatial_value(constraint.get('allowed_exposure'))}."
            )
        if constraint.get("forbidden_exposure"):
            lines.append(
                f"- cover exposure guard {constraint_id}: "
                f"forbidden_exposure={format_spatial_value(constraint.get('forbidden_exposure'))}; "
                "reject the page if any forbidden exposure is visible."
            )
    if constraint_type == "no_line_of_fire":
        source = str(spatial_constraint_value(constraint, "source", "actor", "from", "entity") or "source")
        target = str(spatial_constraint_value(constraint, "target", "to") or "target")
        lines.append(
            f"- no-line guard {constraint_id}: {source} must not fire at {target}; "
            "do not draw dashed/aim/pressure line, projectile, sight line, or firing vector "
            f"from {source} to {target}. Use placement, occlusion, reaction, or cover silhouette instead."
        )
    if constraint_type == "not_aims_at":
        actor = str(spatial_constraint_value(constraint, "actor", "source", "from", "entity") or "actor")
        target = str(spatial_constraint_value(constraint, "target", "to") or "target")
        lines.append(
            f"- negative aim guard {constraint_id}: {actor} must not aim, gaze, or point a weapon/vector "
            f"at {target}; reject target-facing vectors."
        )
    if constraint_type == "trajectory_to":
        origin_entity = spatial_constraint_value(constraint, "origin_entity", "from_entity")
        destination_entity = spatial_constraint_value(constraint, "destination_entity", "to_entity")
        if origin_entity or destination_entity:
            lines.append(
                f"- trajectory endpoint guard {constraint_id}: "
                f"origin_entity={format_spatial_value(origin_entity or 'unspecified')}, "
                f"destination_entity={format_spatial_value(destination_entity or 'unspecified')}; "
                "the path must visibly read from origin to destination."
            )
    return lines


def exposure_terms(value: Any) -> set[str]:
    terms: set[str] = set()
    for item in as_list(value):
        normalized = re.sub(r"[^a-z0-9]+", "_", item.lower()).strip("_")
        if normalized:
            terms.add(normalized)
    return terms


def is_visual_occlusion_constraint(constraint: dict[str, Any]) -> bool:
    constraint_type = str(constraint.get("type") or "")
    return bool(
        constraint_type in {"cover_between", "behind_cover_from", "line_of_sight_blocked"}
        or constraint.get("allowed_exposure")
        or constraint.get("forbidden_exposure")
    )


def constraint_mentions_intentional_exposure(constraint: dict[str, Any]) -> bool:
    haystack = json.dumps(constraint, ensure_ascii=False).lower()
    return any(
        marker in haystack
        for marker in [
            "intentional_exposure",
            "deliberate_exposure",
            "body_exposed",
            "firing",
            "fires",
            "shoot",
            "shot",
            "aims_at",
            "사격",
            "발사",
            "쏘",
        ]
    )


def visual_occlusion_prompt_text(page: dict[str, Any]) -> str:
    contract = page.get("spatial_contract", {})
    if not spatial_contract_has_content(contract):
        return "- no structured visual occlusion translation needed; preserve ordinary readable foreground/background separation."
    constraints = [
        constraint
        for constraint in contract.get("constraints", [])
        if is_visual_occlusion_constraint(constraint)
    ]
    if not constraints:
        return "- no cover/line-of-sight exposure constraint supplied; still keep characters visually separated from walls, pillars, and occluding props."

    lines = [
        "- Translate spatial_contract cover and visibility terms into visual occlusion staging before rendering; do not render allowed_exposure as a literal label or pasted feature.",
        "- For any occluded character, separate the actor from the wall, pillar, vehicle, furniture, or cover with a clean border, shadow gap, or negative-space sliver so the actor never fuses with the occluder.",
        "- Use no shared contour/hatching or continuous texture between the character silhouette and the cover surface; cover texture must stop at the cover edge.",
    ]
    for constraint in constraints:
        constraint_id = str(constraint.get("id") or "")
        constraint_type = str(constraint.get("type") or "")
        actor = str(spatial_constraint_value(constraint, "actor", "subject", "protected", "target") or "actor")
        viewpoint = str(
            spatial_constraint_value(constraint, "viewpoint_entity", "viewpoint", "from_viewpoint", "threat", "source", "from")
            or "threat/viewpoint"
        )
        cover = str(spatial_constraint_value(constraint, "cover", "blocker", "object") or "cover")
        lines.append(
            f"- visual occlusion guard {constraint_id}: draw {cover} as a distinct foreground occluder and "
            f"{actor} as a separate recessed silhouette/pocket behind it from {viewpoint}; "
            "the cover edge and actor edge must not merge."
        )
        if constraint_type == "line_of_sight_blocked":
            lines.append(
                f"- blocked-sight guard {constraint_id}: the direct sight/hit line from {viewpoint} to {actor} "
                f"must be visibly interrupted by {cover}, not merely hidden by the reader camera angle."
            )
        allowed_terms = exposure_terms(constraint.get("allowed_exposure"))
        if constraint.get("allowed_exposure"):
            lines.append(
                f"- allowed exposure visual guard {constraint_id}: "
                f"allowed_exposure={format_spatial_value(constraint.get('allowed_exposure'))} means a tiny, readable peek from behind {cover}, "
                "not a face, eye, hand, or weapon pasted onto the cover edge."
            )
        if allowed_terms & TINY_COVER_EXPOSURE_TERMS:
            lines.append(
                f"- tiny exposure guard {constraint_id}: full concealment is acceptable and preferred when "
                "eyes/hand/weapon-edge exposure would become ambiguous, unreadable, or fused with the cover; "
                "if shown, keep the peek detached inside a recessed pocket or shadow gap, and do not paste eye/weapon on cover edge."
            )
        if constraint_mentions_intentional_exposure(constraint):
            lines.append(
                f"- intentional exposure exception {constraint_id}: if the approved beat requires firing, aiming, or a deliberate body peek, "
                "show only that required exposure while preserving a separated silhouette and clean occlusion edge."
            )
        if constraint.get("forbidden_exposure"):
            lines.append(
                f"- forbidden exposure visual guard {constraint_id}: "
                f"forbidden_exposure={format_spatial_value(constraint.get('forbidden_exposure'))}; "
                "reject torso-visible, above-cover, open-field, or merged cover/actor readings."
            )
    return "\n".join(lines)


def spatial_contract_prompt_text(page: dict[str, Any]) -> str:
    contract = page.get("spatial_contract", {})
    if not spatial_contract_has_content(contract):
        return "- no structured spatial_contract supplied; use spatial_logic_notes, motion_checks, and must_match."
    lines = [
        f"- structured spatial_contract is active; {SPATIAL_VALIDATION_OVERLAY_NOTE}",
        "- Treat entries as validation constraints unless they contradict the approved narrative/page design.",
        f"- coordinate_space default policy: {SPATIAL_SCENE_3D_DEFAULT_POLICY}",
    ]
    coordinate_space = contract.get("coordinate_space") or {}
    if coordinate_space:
        lines.append(f"- coordinate_space: {json.dumps(coordinate_space, ensure_ascii=False, sort_keys=True)}")
    if spatial_contract_coordinate_type(contract) == "scene_3d":
        lines.extend(
            [
                "- scene_3d validation-only mode: use this as a provisional validation model, not as a composition driver or automatic rendered reference.",
                "- Preserve the approved narrative/page design first; hard locks are rerun criteria, while soft/inferred geometry may reconcile after parent inspection if the page design and prior continuity remain intact.",
                "- If this is the first page/panel with no prior spatial continuity, the first panel is a calibration anchor for soft/inferred scene geometry.",
                "- Camera-direction and auxiliary scene_3d render PNGs are inspection aids only: use them to sanity-check the contract before approval and parent inspection, but do not attach them as generation references or imitate them as final comic composition.",
            ]
        )
    for lock in contract.get("locks", []):
        fields = []
        for key, value in lock.items():
            if key == "id" or value is None or value == "":
                continue
            fields.append(f"{key}={format_spatial_value(value)}")
        lines.append(f"- lock {lock.get('id')}: " + (", ".join(fields) if fields else "no extra fields"))
    for transition in contract.get("transitions", []):
        fields = []
        for key, value in transition.items():
            if key == "id" or value is None or value == "":
                continue
            fields.append(f"{key}={format_spatial_value(value)}")
        lines.append(f"- transition {transition.get('id')}: " + (", ".join(fields) if fields else "no extra fields"))
    for annotation in contract.get("annotations", []):
        fields = []
        for key, value in annotation.items():
            if key == "id" or value is None or value == "":
                continue
            fields.append(f"{key}={format_spatial_value(value)}")
        lines.append(f"- annotation {annotation.get('id')}: " + (", ".join(fields) if fields else "no extra fields"))
    if contract.get("entities"):
        lines.append("- entities: " + "; ".join(spatial_entity_summary(entity) for entity in contract.get("entities", [])))
    for snapshot in contract.get("panel_snapshots", []):
        entity_parts = []
        for state in snapshot.get("entities", []):
            parts = [str(state.get("id"))]
            for field in [
                "position",
                "facing_vector",
                "gaze_vector",
                "aim_vector",
                "trajectory_vector",
                "pose",
                "cover",
                "level_id",
                "screen_box",
                "location_anchor",
                "held_props",
                "state_tags",
            ]:
                if field in state:
                    parts.append(f"{field}={format_spatial_value(state[field])}")
            if state.get("visibility"):
                parts.append(f"visibility={state.get('visibility')}")
            if state.get("occlusion"):
                parts.append(f"occlusion={state.get('occlusion')}")
            entity_parts.append(" ".join(parts))
        panel_parts = []
        if snapshot.get("location_id"):
            panel_parts.append(f"location_id={snapshot.get('location_id')}")
        if snapshot.get("camera"):
            panel_parts.append(f"camera={format_spatial_value(snapshot.get('camera'))}")
        panel_prefix = f"- panel {snapshot.get('panel')}"
        if panel_parts:
            panel_prefix += " " + " ".join(panel_parts)
        lines.append(f"{panel_prefix}: " + "; ".join(entity_parts))
    for constraint in contract.get("constraints", []):
        fields = []
        for key, value in constraint.items():
            if key in {"id", "type"} or value is None or value == "":
                continue
            fields.append(f"{key}={format_spatial_value(value)}")
        lines.append(
            f"- constraint {constraint.get('id')} type={constraint.get('type')}: "
            + (", ".join(fields) if fields else "no extra fields")
        )
        lines.extend(constraint_prompt_guard_lines(constraint))
    return "\n".join(lines)


def location_summary(location: dict[str, Any]) -> str:
    parts = [str(location.get("id") or "")]
    if location.get("name"):
        parts.append(f"name={location.get('name')}")
    for key in ["layout_summary", "camera_axis", "lighting", "entrances_exits", "offscreen_zones"]:
        if location.get(key):
            parts.append(f"{key}={format_spatial_value(location.get(key))}")
    landmark_summaries = []
    for landmark in location.get("fixed_landmarks", []):
        landmark_parts = [str(landmark.get("id") or "")]
        for key in ["description", "relative_position", "screen_region", "must_persist"]:
            if landmark.get(key) not in (None, ""):
                landmark_parts.append(f"{key}={format_spatial_value(landmark.get(key))}")
        landmark_summaries.append(" ".join(landmark_parts))
    if landmark_summaries:
        parts.append("fixed_landmarks=[" + "; ".join(landmark_summaries) + "]")
    return "; ".join(part for part in parts if part)


def spatial_continuity_prompt_text(state: dict[str, Any], page: dict[str, Any]) -> str:
    plan = normalize_spatial_continuity_plan(state.get("spatial_continuity_plan"))
    continuity = page_location_continuity(page)
    if not spatial_continuity_plan_has_content(plan):
        return "\n".join(
            [
                "- no top-level spatial_continuity_plan supplied.",
                "- If adjacent pages imply the same place, do not invent a new room, corridor, street, furniture layout, entrance, exit, or landmark arrangement without an explicit transition.",
            ]
        )
    lines = [
        f"- {SPATIAL_CONTINUITY_PLAN_NOTE}",
        "- Decide and preserve the physical set before drawing individual page compositions; page layout may crop or simplify the set, but must not relocate fixed landmarks.",
    ]
    if plan.get("scope"):
        lines.append(f"- scope: {plan.get('scope')}")
    for key in ["layout_summary", "camera_axis", "lighting", "movement_path", "temporal_state"]:
        if plan.get(key):
            lines.append(f"- {key}: {format_spatial_value(plan.get(key))}")
    for location in plan.get("locations", []):
        lines.append(f"- location: {location_summary(location)}")
    if plan.get("page_sequence"):
        lines.append(f"- page_sequence: {format_spatial_value(plan.get('page_sequence'))}")
    if plan.get("continuity_rules"):
        lines.append("- continuity_rules: " + "; ".join(plan.get("continuity_rules", [])))
    if plan.get("allowed_changes"):
        lines.append("- allowed_changes: " + "; ".join(plan.get("allowed_changes", [])))
    if page:
        if continuity:
            lines.append(f"- this_page_location_continuity: {json.dumps(continuity, ensure_ascii=False, sort_keys=True)}")
        else:
            lines.append("- this_page_location_continuity: missing; parent plan approval should reject this when the top-level plan is active.")
    return "\n".join(lines)


def narrative_plan_prompt_text(page: dict[str, Any]) -> str:
    narrative_plan = normalize_optional_object(page.get("narrative_plan"), "narrative_plan")
    if narrative_plan:
        lines = [
            "- Build and preserve the comic page from scenario, emotion, action rhythm, reader eye flow, panel density, negative space, and visual emphasis before applying spatial validation."
        ]
        for key in ["story_function", "reader_experience", "pacing_intent", "composition_intent"]:
            value = narrative_plan.get(key)
            if value not in (None, ""):
                lines.append(f"- {key}: {format_spatial_value(value)}")
        for key, value in narrative_plan.items():
            if key in {"story_function", "reader_experience", "pacing_intent", "composition_intent"} or value in (None, ""):
                continue
            lines.append(f"- {key}: {format_spatial_value(value)}")
        return "\n".join(lines)
    return "\n".join(
        [
            "- No explicit narrative_plan supplied; derive narrative-first page design from layout_brief, panel beats, pacing notes, panel shape notes, negative space, detail density, visual emphasis, comic effects, and prompt.",
            "- Compose the page as a comic scene first, then use spatial validation only to catch contradictions inside that approved design.",
        ]
    )


def spatial_contract_extraction_prompt_text(page: dict[str, Any]) -> str:
    extraction = normalize_optional_object(page.get("spatial_contract_extraction"), "spatial_contract_extraction")
    lines = [
        f"- {SPATIAL_VALIDATION_OVERLAY_NOTE}",
        "- Extract spatial_contract only after page/panel narrative design is chosen.",
        f"- coordinate_space default policy: {SPATIAL_SCENE_3D_DEFAULT_POLICY}",
    ]
    if not extraction:
        lines.extend(
            [
                "- derived_from: narrative_plan_and_panels",
                "- verification_purpose: validate spatial, temporal, direction, visibility/occlusion, line-of-sight, movement-path, landmark, and state continuity contradictions inside the approved page design.",
                "- must_not_override_page_design: true",
            ]
        )
        return "\n".join(lines)
    for key in ["derived_from", "verification_purpose", "must_not_override_page_design", "focus"]:
        if key in extraction:
            lines.append(f"- {key}: {format_spatial_value(extraction[key])}")
    for key, value in extraction.items():
        if key in {"derived_from", "verification_purpose", "must_not_override_page_design", "focus"} or value in (None, ""):
            continue
        lines.append(f"- {key}: {format_spatial_value(value)}")
    return "\n".join(lines)


def page_policy_items(state: dict[str, Any], page: dict[str, Any], key: str) -> list[str]:
    return merge_unique(state.get(key), page.get(key))


def current_rerun_correction(stage: dict[str, Any], require_pending: bool = False) -> str:
    if require_pending and not stage.get("rerun_pending"):
        return ""
    notes: list[str] = []
    notes = merge_unique(notes, stage.get("current_rerun_correction"))
    history = stage.get("rerun_history")
    if isinstance(history, list) and history:
        latest = history[-1]
        if isinstance(latest, dict):
            notes = merge_unique(notes, latest.get("note"))
    notes = merge_unique(notes, stage.get("parent_note"))
    return bullet_text(notes, "")


def user_revision_overlay_lines(stage: dict[str, Any]) -> list[str]:
    overlays = stage.get("user_revision_overlays") or []
    if not isinstance(overlays, list):
        return []
    lines: list[str] = []
    for overlay in overlays:
        if not isinstance(overlay, dict):
            continue
        color_id = str(overlay.get("color_id") or overlay.get("color") or "overlay")
        color = str(overlay.get("color") or "")
        overlay_path = str(overlay.get("overlay_path") or "")
        request_path = str(overlay.get("request_path") or "")
        request = str(overlay.get("request") or overlay.get("note") or "").strip()
        detail = f"- {color_id}"
        if color:
            detail += f" ({color})"
        if overlay_path:
            detail += f": overlay={overlay_path}"
        if request_path:
            detail += f"; request_file={request_path}"
        if request:
            detail += f"; request={request}"
        lines.append(detail)
    return lines


def user_revision_overlay_prompt_text(stage: dict[str, Any]) -> str:
    lines = user_revision_overlay_lines(stage)
    if not lines:
        return "- none"
    return "\n".join(
        [
            "- User-painted transparent overlays are active for this rerun.",
            "- Treat each overlay PNG as a location mask; edit only the marked area unless the matching request text says broader continuity changes are required.",
            "- Use the color-specific request text as the correction instruction for the matching overlay color.",
            *lines,
        ]
    )


def panel_line(panel: dict[str, Any]) -> str:
    source_dialogue = "; ".join(as_list(panel.get("source_dialogue") or panel.get("dialogue"))) or "none"
    adapted_dialogue = "; ".join(as_list(panel.get("adapted_dialogue"))) or "none"
    sfx = "; ".join(as_list(panel.get("sfx"))) or "none"
    captions = "; ".join(as_list(panel.get("caption") or panel.get("narration"))) or "none"
    checks = "; ".join(as_list(panel.get("motion_checks"))) or "none"
    must_match = "; ".join(as_list(panel.get("must_match"))) or "none"
    detail_density = panel.get("detail_density_notes") or "use selective detail; simplify non-focal areas"
    visual_emphasis = panel.get("visual_emphasis_notes") or "clear focal point and line-weight emphasis"
    comic_effects = panel.get("comic_effects_notes") or "use effect lines only when they match motion or mood"
    return (
        f"- panel {panel.get('panel_no', panel.get('order', ''))}: "
        f"beat={panel.get('beat') or panel.get('purpose') or ''}; "
        f"view={panel.get('composition') or panel.get('camera') or ''}; "
        f"characters={', '.join(as_list(panel.get('characters'))) or 'unspecified'}; "
        f"action={panel.get('action') or 'unspecified'}; "
        f"source_dialogue={source_dialogue}; adapted_dialogue={adapted_dialogue}; "
        f"sfx={sfx}; captions={captions}; "
        f"speech_balloon={panel.get('speech_balloon') or 'place naturally without covering faces/action'}; "
        f"sfx_placement={panel.get('sfx_placement') or 'near the sound source'}; "
        f"detail_density={detail_density}; visual_emphasis={visual_emphasis}; "
        f"comic_effects={comic_effects}; "
        f"spatial_logic={panel.get('spatial_logic_notes') or panel.get('continuity_notes') or 'keep positions and directions plausible'}; "
        f"motion_checks={checks}; must_match={must_match}"
    )


def prompt_text(run_dir: Path, page: dict[str, Any], stage_id: str, state: dict[str, Any]) -> str:
    meta = stage_meta(stage_id)
    references = validate_reference_paths(as_list(state.get("source_references")) + as_list(page.get("references")))
    reference_text = "\n".join(f"- {ref}" for ref in references) or "- none"
    source_root = state.get("source_root") or str(DEFAULT_SOURCE_ROOT)
    excluded_roots = ", ".join(state.get("excluded_source_roots") or [str(DEFAULT_OUTPUT_ROOT)])
    panels = page.get("panels", [])
    text_policy = normalize_text_policy(page.get("text_policy") or state.get("text_policy"))
    render_text_policy = TEXT_POLICY_TEXT_FREE if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE else text_policy
    text_policy_lines = text_policy_instruction_lines(render_text_policy, page)
    if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE:
        text_policy_lines = [
            "Text policy: storyboard_conti_sketch_ink_text_free",
            f"Approved final-page text_policy is {text_policy}, but storyboard_conti_sketch_ink must render no text.",
            "Do not render dialogue, SFX, speech balloons, captions, signage, labels, page or panel numbers, symbols with text, or arbitrary typography; put semantic meanings only in the *_desc.md.",
        ]
    text_policy_worker_checks = text_policy_worker_check_lines(render_text_policy)
    character_locks = page_policy_items(state, page, "character_locks")
    visual_text_guard = page_policy_items(state, page, "visual_text_guard")
    appearance_anatomy_lock = DEFAULT_APPEARANCE_ANATOMY_LOCK_NOTES
    stage = stage_state(page, stage_id)
    attachment_paths = as_list(stage.get("visual_reference_paths")) or visual_reference_paths(run_dir, page, stage_id, state)
    attachment_text = visual_reference_prompt_text(attachment_paths)
    prior_page_references = prior_page_continuity_reference_text(run_dir, page, stage_id, state)
    stage_anchor_reference = stage_anchor_reference_text(run_dir, page, stage_id, state)
    rerun_correction = current_rerun_correction(stage)
    revision_overlays = user_revision_overlay_prompt_text(stage)
    panel_text = "\n".join(panel_line(panel) for panel in panels) or "- no panel details supplied"
    page_dialogue_notes = page.get("page_dialogue_notes") or (
        "Adapt source dialogue to fit comic timing, mood, panel rhythm, and balloon space. "
        "Do not copy source dialogue verbatim unless the approved plan explicitly says to preserve it."
    )
    pacing_notes = page.get("pacing_notes") or DEFAULT_PACING_NOTES
    panel_shape_notes = page.get("panel_shape_notes") or DEFAULT_PANEL_SHAPE_NOTES
    negative_space_notes = page.get("negative_space_notes") or DEFAULT_NEGATIVE_SPACE_NOTES
    detail_density_notes = page.get("detail_density_notes") or DEFAULT_DETAIL_DENSITY_NOTES
    visual_emphasis_notes = page.get("visual_emphasis_notes") or DEFAULT_VISUAL_EMPHASIS_NOTES
    comic_effects_notes = page.get("comic_effects_notes") or DEFAULT_COMIC_EFFECTS_NOTES
    spatial_logic_notes = page.get("spatial_logic_notes") or "Keep character, object, prop, and environment positions physically plausible."
    motion_checks = "\n".join(f"- {entry}" for entry in as_list(page.get("motion_checks"))) or "- no impossible motion: thrown, kicked, or shot objects move in the direction implied by body pose and panel action"
    must_match = "\n".join(f"- {entry}" for entry in as_list(page.get("must_match"))) or "- preserve approved page layout, panel count, action direction, and character/object continuity"
    spatial_continuity = spatial_continuity_prompt_text(state, page)
    narrative_plan = narrative_plan_prompt_text(page)
    spatial_validation_overlay = spatial_contract_extraction_prompt_text(page)
    visual_occlusion = visual_occlusion_prompt_text(page)
    spatial_contract = spatial_contract_prompt_text(page)
    conti_desc_path = recorded_stage_description_path(run_dir, page, STORYBOARD_CONTI_SKETCH_INK_STAGE)
    assigned_description = (
        f"Assigned conti/sketch/ink description: {stage_description_path(run_dir, page, stage_id)}"
        if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE
        else f"Conti/sketch/ink description reference: {conti_desc_path if conti_desc_path.exists() else 'not available'}"
    )
    if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE:
        prior_stage_use_requirement = (
            "No prior-stage image is used for storyboard_conti_sketch_ink. Generate a text-free comic-page "
            "conti/sketch/light-ink image from the approved narrative-first page design and write the required *_desc.md beside it. "
            "Keep required headings exactly as specified, but write the description body text in Korean."
        )
        page_format_instruction = (
            "Generate one complete comic-page conti/sketch/light-ink image with the approved panel count and reading order. "
            "Preserve the page's scenario beat, panel composition, pacing, reader eye flow, and comic readability first. "
            "For each important character, object, and environment element, draw readable rough sketch forms plus light clean lines, "
            "recognizable enough to identify the entity and action: e.g. crouching person, "
            "standing person, held object, moving object, destination landmark, occluding element, wall, doorway, vehicle, table, tree, or landmark. "
            "Use gesture poses, clear object contours, environmental silhouettes, shadow masses, and landmark outlines. "
            "Add validation marks only where needed: arrows, sight/direction lines, movement-path "
            "arrows, visibility/occlusion markers, and relation lines. Simplify or omit unimportant props/background elements "
            "when they are not needed for story readability, action readability, visibility/occlusion, landmark continuity, "
            "or page composition. "
            "Light line cleanup is allowed, but do not render tone/color, lighting, texture, dialogue, "
            "SFX, captions, labels, typography, glossy finish, or final polish. Semantic labels belong only in the *_desc.md."
        )
    else:
        prior_stage_use_requirement = (
            "Use the prior-stage image above as the required visual input / structure reference and keep the "
            "conti/sketch/ink *_desc.md as the spatial validation overlay for the approved comic page design. Do not redraw "
            "the page from scratch or change the approved panel layout."
        )
        page_format_instruction = (
            "Generate one complete Korean comic-book page image with 3-5 panels by default and measured cinematic "
            "pacing. Preserve the inspected storyboard_conti_sketch_ink panel layout, freeform shapes, negative space, "
            "visual emphasis, effect-line direction, and ink rhythm."
        )
    negative = page.get("negative_prompt") or (
        "low resolution, watermark, random logo, unrelated captions, garbled lettering, unreadable "
        "speech balloons, duplicated limbs, broken perspective, impossible object motion, moving object traveling "
        "opposite the approved or implied path, inconsistent character design, inconsistent setting, wrong costume, "
        "cropped key action, blurry subject, over-smoothed AI texture."
    )
    negative_terms = merge_unique(
        negative,
        text_policy_negative_terms(render_text_policy),
        visual_text_guard,
        DEFAULT_APPEARANCE_ANATOMY_NEGATIVE_TERMS,
    )
    negative_prompt_text = ", ".join(negative_terms)
    return "\n".join(
        [
            f"Workflow: {WORKFLOW}",
            f"Scenario title: {state.get('title', '')}",
            f"Stage: {stage_id} ({meta['purpose']})",
            f"Assigned output: {stage_output_path(run_dir, page, stage_id)}",
            assigned_description,
            f"Page id: {page['id']}",
            f"Page number: {page.get('page_no', page.get('order', ''))}",
            f"Reading order: {page.get('reading_order') or state.get('reading_order') or 'right-to-left or top-to-bottom as approved'}",
            f"Scene refs: {', '.join(page.get('scene_refs', [])) or 'unspecified'}",
            f"Prior stage reference: {prior_stage_reference(run_dir, page, stage_id, state)}",
            "",
            "Required image attachments:",
            attachment_text,
            "",
            "Prior page continuity references:",
            prior_page_references,
            "",
            "Stage level anchor reference:",
            stage_anchor_reference,
            "",
            "Stage instruction:",
            stage_instruction(stage_id),
            "",
            "Prior-stage use requirement:",
            prior_stage_use_requirement,
            "",
            "Page format:",
            page_format_instruction,
            "",
            "Page layout brief:",
            page.get("layout_brief") or page.get("visual_brief") or page.get("prompt") or "",
            "",
            "Pre-page spatial continuity plan:",
            spatial_continuity,
            "",
            "Narrative-first page design:",
            narrative_plan,
            "",
            "Page pacing and panel shape policy:",
            pacing_notes,
            panel_shape_notes,
            negative_space_notes,
            "",
            "Panels on this page:",
            panel_text,
            "",
            "Comic visual direction:",
            detail_density_notes,
            visual_emphasis_notes,
            comic_effects_notes,
            "For storyboard_conti_sketch_ink, draw planned speed lines, focus lines, impact bursts, emotion lines, motion streaks, line-weight contrast, and light ink emphasis directly when they serve the beat.",
            "For finish, preserve the inspected storyboard_conti_sketch_ink visual emphasis, effect-line direction, and ink rhythm; tone/color must not weaken or cover them.",
            "",
            "Spatial validation overlay:",
            spatial_validation_overlay,
            "",
            "Visual occlusion rendering rules:",
            visual_occlusion,
            "",
            "Structured spatial contract:",
            spatial_contract,
            "",
            "Page text policy:",
            *text_policy_lines,
            "",
            "Page dialogue notes:",
            page_dialogue_notes
            if render_text_policy == TEXT_POLICY_DIALOGUE_SFX_CAPTIONS
            else "Dialogue and caption fields remain plan metadata only under this text_policy unless the policy above explicitly permits them.",
            "",
            "Character locks:",
            bullet_text(character_locks),
            "",
            "Character appearance/anatomy lock:",
            appearance_anatomy_lock,
            "",
            "Visual text guard:",
            bullet_text(visual_text_guard),
            "",
            "Current rerun correction:",
            rerun_correction or "- none",
            "",
            "User revision overlays:",
            revision_overlays,
            "",
            "Spatial and motion sanity rules:",
            spatial_logic_notes,
            motion_checks,
            "",
            "Source consistency checklist:",
            "- Keep character faces, age impression, body shape, hair, outfit, accessories, props, profile details, setting, and landmarks consistent with the approved plan and allowed sources/ references.",
            "- Preserve approved character appearance/anatomy: species/body structure, face structure, eye count and placement, hand/finger/arm/leg count, silhouette, body proportions, and posture.",
            "- Unless explicitly approved by the plan or source, reject missing/extra/merged eyes, one-eyed appearance for a two-eyed character, one-eyed face unless explicitly approved, missing/extra limbs or fingers, changed species/body type, broken joints, or broken body proportions.",
            "- Do not introduce source-data drift between panels or pages.",
            "",
            "Panel and page continuity checklist:",
            "- Keep same-page panel continuity coherent for positions, gaze, action direction, object movement, time flow, speech/SFX placement, and cause-effect motion.",
            "- Keep adjacent-page continuity coherent for recurring characters, props, locations, landmarks, and ongoing actions.",
            "",
            "Must match:",
            must_match,
            "",
            "Default source data folder:",
            f"- {source_root}",
            "- If no explicit reference paths are listed, inspect/search this folder for relevant story, character, location, style, and page-layout source files before generation.",
            "",
            "Output source exclusion:",
            f"- Do not use {excluded_roots} or any output/ subtree as source/reference data; it may contain unrelated generated files or failed cases.",
            "- Only the current run's parent-inspected prior-stage reference listed above may be used as workflow structure input.",
            "",
            "Reference paths:",
            reference_text,
            "",
            "Generation prompt:",
            page.get("prompt") or page.get("layout_brief") or "",
            "",
            "Worker inspection checklist:",
            "- Matches this exact page and stage",
            "- For storyboard_conti_sketch_ink, preserves comic-page readability, panel composition, story rhythm, reader eye flow, spatial relation, occlusion, movement path, and cause-effect logic first; draws recognizable rough sketch forms plus light clean ink lines for important characters, objects, environment elements, and occluders; adds arrows/vector/relation marks only where needed for validation; simplifies or omits unimportant props/background elements; rejects meaningless pure-symbol conti, spatial validation diagrams, dialogue, SFX, typography, tone/color, texture, glossy finish, final polish, or finished inking",
            "- For storyboard_conti_sketch_ink, writes the required *_desc.md with Symbol Legend, Panel Spatial Map, Constraint Check, and Temporal Continuity Check sections; heading text stays exact, and body explanation is Korean",
            "- For finish, uses the parent-inspected storyboard_conti_sketch_ink image and *_desc.md as the locked comic-page structure and spatial/temporal source",
            "- Uses 3-5 panels by default with measured cinematic pacing",
            "- Accepts and encourages 1-2 panels for special staging such as full-page emotion, silence, stillness, or decisive action moments",
            "- Requires explicit story justification for six or more panels",
            "- Uses experimental freeform panel design; do not reject diagonal, asymmetric, open, borderless, inset, overlapping, or negative-space layouts when reading order and continuity are clear",
            "- Rejects overcrowded pages, unjustified dense panel packing, unintentional uniform rectangular grids, or pages packed with dialogue/SFX without breathing room",
            "- Executes and verifies the approved comic visual direction: detail density, focal-point emphasis, closeup intensity, line weight, black-ink weight, and background simplification/emphasis",
            "- Verifies planned speed lines, focus lines, impact bursts, emotion lines, and motion streaks; effect-line direction must match action direction, impact, mood, or eye guidance",
            "- Rejects missing planned visual effects, effect lines that contradict motion, and pages where every panel has the same flat visual intensity",
            *text_policy_worker_checks,
            "- Preserves every Character locks item listed above; reject forbidden marker/accessory/silhouette drift",
            "- Verifies the Character appearance/anatomy lock: species/body structure, face structure, eye count and placement, hand/finger/arm/leg count, silhouette, body proportions, and posture",
            "- Rejects missing/extra/merged eyes, one-eyed appearance for a two-eyed character, one-eyed face unless explicitly approved, missing/extra limbs or fingers, changed species/body type, broken joints, or broken body proportions",
            "- During finish, preserve the inspected storyboard_conti_sketch_ink panel layout, light clean-line structure, eye, face, hand, limb, silhouette, body proportion, and posture structure",
            "- Enforces every Visual text guard item listed above; reject arbitrary environmental text, labels, signs, or corner text when forbidden",
            "- Preserves story beat, reading order, composition, and continuity",
            "- Preserves source-data consistency for characters, props, profiles, locations, and page-layout references",
            "- Preserves the pre-page spatial_continuity_plan: same location_id means the same physical set, fixed landmarks, entrances/exits, camera axis, lighting sources, and allowed state changes unless an explicit transition is listed",
            "- Preserves panel-to-panel and adjacent-page continuity for character/object placement, gaze, action direction, time flow, and lettering placement",
            "- Keeps prior-stage structure unchanged when a prior-stage reference exists, especially during finish",
            "- Character/object positions, action direction, moving-object path, and cause-effect motion are physically plausible",
            "- Enforces every Structured spatial contract entity, panel snapshot, vector, visibility, occlusion, and constraint listed above as validation constraints unless they contradict the approved narrative/page design",
            "- For scene_3d pages, parent inspection should use spatial-render-manifest camera PNGs and any selected top/side/iso auxiliary PNGs as visual sanity-check aids; these render PNGs are not generation references and must not replace the approved comic page design",
            "- For behind_cover_from and line_of_sight_blocked, cover must read from the named threat/viewpoint line of fire or line of sight; reader-side behind is not sufficient",
            "- Reject forbidden_exposure violations such as torso_visible, above_roofline, or open_field when listed; only allowed_exposure may peek past cover",
            "- Reject wall/cover fusion: character edges must not share a contour, hatching, texture, or unreadable silhouette with walls, pillars, vehicles, furniture, or any cover object",
            "- Reject eyes, faces, hands, or weapon tips pasted onto a wall/cover edge; for tiny allowed exposure, clear full concealment is acceptable when it prevents fused or unreadable staging",
            "- For no_line_of_fire and not_aims_at, reject firing vectors, dashed pressure/aim lines, projectiles, sight lines, gaze, or weapon direction that points from source/actor to target",
            "- Rejects target-opposite direction vectors, impossible moving-object paths, broken visibility/occlusion or line-of-sight blocking, fixed landmark relation drift, and temporal state drift without an allowed_transition cause",
            "- No impossible staging such as a moving object traveling away from its approved destination or implied path",
            "- Has no obvious anatomy, perspective, crop, object, or continuity defects",
            "",
            "Negative prompt:",
            negative_prompt_text,
            "",
            "Return only: generated file path, description path for storyboard_conti_sketch_ink, worker_status, worker_note.",
        ]
    )


def subagent_prompt_text(run_dir: Path, page: dict[str, Any], stage_id: str, state: dict[str, Any]) -> str:
    stage = stage_state(page, stage_id)
    references = validate_reference_paths(as_list(state.get("source_references")) + as_list(page.get("references")))
    reference_text = "\n".join(f"- {ref}" for ref in references) or "- none"
    attachment_paths = as_list(stage.get("visual_reference_paths")) or visual_reference_paths(run_dir, page, stage_id, state)
    attachment_text = visual_reference_prompt_text(attachment_paths)
    prior_page_references = prior_page_continuity_reference_text(run_dir, page, stage_id, state)
    stage_anchor_reference = stage_anchor_reference_text(run_dir, page, stage_id, state)
    skill_name = STAGE_SKILL_NAMES[stage_id]
    text_policy = normalize_text_policy(page.get("text_policy") or state.get("text_policy"))
    character_locks = page_policy_items(state, page, "character_locks")
    visual_text_guard = page_policy_items(state, page, "visual_text_guard")
    appearance_anatomy_lock = DEFAULT_APPEARANCE_ANATOMY_LOCK_NOTES
    spatial_continuity = spatial_continuity_prompt_text(state, page)
    narrative_plan = narrative_plan_prompt_text(page)
    spatial_validation_overlay = spatial_contract_extraction_prompt_text(page)
    visual_occlusion = visual_occlusion_prompt_text(page)
    spatial_contract = spatial_contract_prompt_text(page)
    revision_overlays = user_revision_overlay_prompt_text(stage)
    conti_desc_path = recorded_stage_description_path(run_dir, page, STORYBOARD_CONTI_SKETCH_INK_STAGE)
    if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE:
        description_line = f"Assigned description path: {stage_description_path(run_dir, page, stage_id)}"
    else:
        description_line = f"Conti/sketch/ink description reference: {conti_desc_path if conti_desc_path.exists() else 'not available'}"
    return "\n".join(
        [
            f"Use ${skill_name}.",
            "You are generating exactly one image for create-comic-storyboard-pack.",
            "Do not edit state.json or any runner state files.",
            f"Run folder: {run_dir}",
            f"Story/scenario file: {run_dir / 'scenario.md'}",
            f"Approved plan: {run_dir / 'approved_storyboard_plan.json'}",
            f"Assigned page: {page['filename']}",
            f"Page id: {page['id']}",
            f"Stage: {stage_id}",
            f"Prompt file: {stage.get('prompt_file')}",
            f"Output path: {stage.get('output_path')}",
            description_line,
            f"Batch id: {stage.get('batch_id')}",
            f"Default source folder: {state.get('source_root') or DEFAULT_SOURCE_ROOT}",
            f"Excluded source folder: {', '.join(state.get('excluded_source_roots') or [str(DEFAULT_OUTPUT_ROOT)])}",
            f"Prior-stage reference: {prior_stage_reference(run_dir, page, stage_id, state)}",
            "Required image attachments:",
            attachment_text,
            "Prior page continuity references:",
            prior_page_references,
            "Stage level anchor reference:",
            stage_anchor_reference,
            "Relevant references:",
            reference_text,
            f"Page text policy: {text_policy}",
            "Stage render text policy: storyboard_conti_sketch_ink_text_free; render no text in the conti/sketch/ink image"
            if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE
            else f"Stage render text policy: {text_policy}",
            "Character locks:",
            bullet_text(character_locks),
            "Character appearance/anatomy lock:",
            appearance_anatomy_lock,
            "Visual text guard:",
            bullet_text(visual_text_guard),
            "Pre-page spatial continuity plan:",
            spatial_continuity,
            "Narrative-first page design:",
            narrative_plan,
            "Spatial validation overlay:",
            spatial_validation_overlay,
            "Visual occlusion rendering rules:",
            visual_occlusion,
            "Structured spatial contract:",
            spatial_contract,
            "Current rerun correction:",
            current_rerun_correction(stage) or "- none",
            "User revision overlays:",
            revision_overlays,
            "Agent-driven overlay option:",
            f"- Review overlay runner: {REPO_ROOT / '.agents' / 'skills' / 'review-image-overlays' / 'scripts' / 'review_overlay_server.py'}",
            "- If self-inspection finds a localized defect that should be rerun, you may create a rect/polygon coordinate markup spec and run `create-markup` to save a revision_requests.json manifest under this run folder.",
            "- Do not call `request-revisions` or edit runner state yourself; return `worker_status: needs_rerun` and include the manifest path in `worker_note` so the parent can import it.",
            "",
            "Use image_gen with the assigned prompt file and attach every Required image attachments path as a local image visual reference. Include any User revision overlays. For storyboard_conti_sketch_ink, use image_gen exactly once, preserve comic-page readability, panel composition, story rhythm, reader eye flow, spatial relations, occlusion, movement paths, and cause-effect logic first; draw recognizable rough sketch forms plus light clean ink lines for important entities; add arrows/vector/relation marks only where needed for validation; simplify or omit unimportant props/background elements; and write the *_desc.md beside the image. For finish, do not redraw or reinterpret the page: preserve the inspected storyboard_conti_sketch_ink layout, light clean-line structure, spatial relationships, and description source while adding tone/color/final polish. Keep the required *_desc.md headings exactly as specified, and write the description body text in Korean while preserving entity ids and constraint ids verbatim. Inspect the output for stage fit, page/story fit, multi-panel layout, active text_policy compliance, character_locks, character appearance/anatomy lock, visual_text_guard, the pre-page spatial_continuity_plan, every Structured spatial contract constraint as a validation overlay, the Visual occlusion rendering rules, threat/viewpoint-based cover, forbidden_exposure, wall/cover fusion, pasted eye/face/hand/weapon-edge artifacts, no_line_of_fire/not_aims_at negative constraints, temporal continuity, user revision requests, spatial continuity, motion plausibility, technical quality, and obvious defects.",
            "Return only:",
            "- generated file path",
            "- description path when stage is storyboard_conti_sketch_ink",
            "- worker_status: pass or needs_rerun",
            "- worker_note: concise inspection note",
        ]
    )


def write_batch_plan(run_dir: Path, state: dict[str, Any]) -> None:
    text_policy = normalize_text_policy(state.get("text_policy"))
    lines = [
        "# Approved Comic Storyboard Page Plan",
        "",
        f"Run folder: {run_dir}",
        f"Scenario title: {state.get('title', '')}",
        f"Plan approved: {state.get('plan_approved', False)}",
        f"Target stages: {', '.join(target_stages(state))}",
        f"Page generation mode: {page_generation_mode(state)}",
        "",
        "Generation policy:",
        "- Use Codex built-in image_gen only through one subagent per reserved page.",
        "- Do not reserve images before approve-plan.",
        f"- Use {state.get('source_root') or DEFAULT_SOURCE_ROOT} as the default source data folder when the user did not specify source/reference paths.",
        f"- Do not use {', '.join(state.get('excluded_source_roots') or [str(DEFAULT_OUTPUT_ROOT)])} or any output/ subtree as source/reference data.",
        f"- {SPATIAL_CONTINUITY_PLAN_NOTE}",
        "- Generate stages in order: storyboard_conti_sketch_ink, finish.",
        "- Plan page/panel composition from scenario, emotion, action rhythm, reader eye flow, pacing, negative space, detail density, visual emphasis, and comic effects before extracting spatial_contract.",
        f"- {SPATIAL_VALIDATION_OVERLAY_NOTE}",
        "- storyboard_conti_sketch_ink is the combined conti, rough sketch, and light clean-line pass; it must preserve page readability, panel composition, story rhythm, reader eye flow, spatial relations, occlusion, movement paths, and cause-effect logic first, draw recognizable rough sketch forms plus light clean ink lines for important entities, add arrows/vector/relation marks only where needed for validation, and write a sibling *_desc.md.",
        "- Do not reserve finish until every targeted page has passed storyboard_conti_sketch_ink parent inspection and storyboard_conti_sketch_ink stage-review.",
        "- Do not reserve finish until storyboard_conti_sketch_ink stage-review has passed and the user has approved the next stage with approve-next-stage plus the active feedback request.",
        "- Finish must use the parent-inspected storyboard_conti_sketch_ink image and *_desc.md as the required visual input / structure reference; it must add tone/color/final polish without redrawing or reinterpreting the stage-1 composition, line structure, spatial relationships, or cause-effect logic.",
        "- Use 3-5 panels by default with measured cinematic pacing; use 1-2 panels for special staging; six or more panels need clear story justification.",
        "- Use experimental freeform panel design by default and avoid unintentional uniform rectangular grids.",
        "- Plan and verify comic visual direction: detail density, visual emphasis, line-weight rhythm, and speed/focus/impact/emotion lines when the beat calls for them.",
        "- Plan and verify character appearance/anatomy locks: species/body structure, face structure, eye count and placement, hand/finger/arm/leg count, silhouette, body proportions, and posture.",
        "- Unless explicitly approved by the plan or source, reject missing/extra/merged eyes, one-eyed appearance for a two-eyed character, one-eyed face unless explicitly approved, missing/extra limbs or fingers, changed species/body type, broken joints, or broken body proportions.",
        f"- Text policy: {text_policy}. {text_policy_batch_summary(text_policy)}",
        "- In sequential_prior_pages mode, reserve one page per batch and use parent-inspected earlier pages from the same stage as visual continuity references.",
        "- In sequential_prior_pages mode, the first page in each stage is the stage-level anchor; page 2 or later waits for anchor-review pass.",
        "- In legacy parallel_batch mode, reserve at most four eligible pages per batch.",
        "- Parent inspection is required before a page stage counts as passed.",
        "- Stage finish review is required after all page stages pass; next stage opens only after stage-review pass.",
        "- Stage finish review checks source consistency against characters, props, profiles, sources/ references, character appearance/anatomy locks, and panel/page continuity.",
        "- Worker and parent inspection must reject implausible spatial layout, object motion, or cause-effect direction inside the approved comic page design.",
        "- Structured spatial_contract entries are validation constraints unless they contradict the approved narrative/page design: runner validates plan-time entity/vector/visibility/landmark/temporal constraints, and parent inspection must record spatial pass or rerun.",
        "",
    ]
    for lock in state.get("character_locks", []):
        lines.append(f"- Character lock: {lock}")
    for guard in state.get("visual_text_guard", []):
        lines.append(f"- Visual text guard: {guard}")
    spatial_continuity = normalize_spatial_continuity_plan(state.get("spatial_continuity_plan"))
    if spatial_continuity_plan_has_content(spatial_continuity):
        lines.extend(["", "Pre-page spatial continuity plan:"])
        for line in spatial_continuity_prompt_text(state, {}).splitlines():
            lines.append(f"- {line}" if not line.startswith("- ") else line)
    lines.append("")
    lines.extend(["Stage gates:", ""])
    for key, gate in state.get("stage_gates", {}).items():
        lines.extend(
            [
                f"- {key}: {gate.get('status', 'pending')}",
                f"  note: {gate.get('note', '')}",
                f"  updated_at: {gate.get('updated_at', '')}",
                f"  feedback_request: {gate.get('feedback_request', '')}",
                f"  feedback_choice: {gate.get('feedback_choice', '')}",
                "",
            ]
        )
    lines.extend(["Stage reviews:", ""])
    for stage_id in STAGE_IDS:
        review = state.get("stage_reviews", {}).get(stage_id, blank_stage_review())
        issues = "; ".join(as_list(review.get("issues"))) or "none"
        lines.extend(
            [
                f"- {stage_id}: {review.get('status', 'pending')}",
                f"  note: {review.get('note', '')}",
                f"  issues: {issues}",
                f"  reviewed_at: {review.get('reviewed_at', '')}",
                "",
            ]
        )
    lines.extend(["Stage anchor reviews:", ""])
    for stage_id in STAGE_IDS:
        review = state.get("stage_anchor_reviews", {}).get(stage_id, blank_stage_anchor_review())
        issues = "; ".join(as_list(review.get("issues"))) or "none"
        lines.extend(
            [
                f"- {stage_id}: {review.get('status', 'pending')}",
                f"  anchor_item: {review.get('anchor_item', '')}",
                f"  output_path: {review.get('output_path', '')}",
                f"  note: {review.get('note', '')}",
                f"  anchor_level_note: {review.get('anchor_level_note', '')}",
                f"  issues: {issues}",
                f"  reviewed_at: {review.get('reviewed_at', '')}",
                "",
            ]
        )
    lines.extend(["Pages:", ""])
    for page in state.get("pages", []):
        stage_summary = ", ".join(
            f"{stage_id}={stage_state(page, stage_id).get('status')}" for stage_id in STAGE_IDS
        )
        lines.extend(
            [
                f"- page: {page['id']}",
                f"  filename: {page['filename']}",
                f"  order: {page.get('order')}",
                f"  page_no: {page.get('page_no')}",
                f"  scenes: {', '.join(page.get('scene_refs', [])) or 'unspecified'}",
                f"  layout: {page.get('layout_brief') or ''}",
                f"  reading_order: {page.get('reading_order') or state.get('reading_order') or 'unspecified'}",
                f"  text_policy: {normalize_text_policy(page.get('text_policy') or text_policy)}",
                f"  character_locks: {'; '.join(page_policy_items(state, page, 'character_locks')) or 'none'}",
                f"  appearance_anatomy_lock: {DEFAULT_APPEARANCE_ANATOMY_LOCK_NOTES}",
                f"  visual_text_guard: {'; '.join(page_policy_items(state, page, 'visual_text_guard')) or 'none'}",
                f"  panel_count: {len(page.get('panels', []))}",
                f"  pacing: {page.get('pacing_notes') or DEFAULT_PACING_NOTES}",
                f"  panel_shapes: {page.get('panel_shape_notes') or DEFAULT_PANEL_SHAPE_NOTES}",
                f"  negative_space: {page.get('negative_space_notes') or DEFAULT_NEGATIVE_SPACE_NOTES}",
                f"  detail_density: {page.get('detail_density_notes') or DEFAULT_DETAIL_DENSITY_NOTES}",
                f"  visual_emphasis: {page.get('visual_emphasis_notes') or DEFAULT_VISUAL_EMPHASIS_NOTES}",
                f"  comic_effects: {page.get('comic_effects_notes') or DEFAULT_COMIC_EFFECTS_NOTES}",
                f"  location_id: {page.get('location_id') or ''}",
                f"  location_continuity: {json.dumps(page.get('location_continuity') or {}, ensure_ascii=False, sort_keys=True)}",
                f"  narrative_plan: {json.dumps(page.get('narrative_plan') or {}, ensure_ascii=False, sort_keys=True)}",
                f"  spatial_contract_extraction: {json.dumps(page.get('spatial_contract_extraction') or {}, ensure_ascii=False, sort_keys=True)}",
                f"  dialogue_notes: {page.get('page_dialogue_notes') or ''}",
                f"  spatial_logic: {page.get('spatial_logic_notes') or ''}",
                f"  spatial_contract: {'present' if spatial_contract_has_content(page.get('spatial_contract')) else 'none'}",
                f"  dependencies: {', '.join(page.get('dependencies', [])) or 'none'}",
                f"  stages: {stage_summary}",
                "",
            ]
        )
        for stage_id in STAGE_IDS:
            visual_refs = stage_state(page, stage_id).get("visual_reference_paths") or []
            if visual_refs:
                lines.append(f"  {stage_id}_visual_reference_paths:")
                for ref_path in visual_refs:
                    lines.append(f"    - {ref_path}")
                lines.append("")
        if spatial_contract_has_content(page.get("spatial_contract")):
            lines.append("  Structured spatial contract:")
            for contract_line in spatial_contract_prompt_text(page).splitlines():
                lines.append(f"    {contract_line}")
            lines.append("")
    (run_dir / "batch_plan.md").write_text("\n".join(lines), encoding="utf-8")


def command_init(args: argparse.Namespace) -> None:
    title = args.title or (Path(args.scenario).stem if args.scenario else "comic-storyboard")
    slug = slugify(title, WORKFLOW)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_root = Path(args.output_root) if args.output_root else DEFAULT_OUTPUT_ROOT
    run_dir = output_root / f"{slug}-comic-storyboard-pack-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "prompts").mkdir()
    (run_dir / "subagent_prompts").mkdir()
    for stage in STAGES:
        (run_dir / "prompts" / stage["id"]).mkdir()
        (run_dir / "subagent_prompts" / stage["id"]).mkdir()
        (run_dir / stage["dir"]).mkdir()

    scenario_path = run_dir / "scenario.md"
    if args.scenario:
        source = Path(args.scenario)
        if not source.exists():
            raise SystemExit(f"Story/scenario file not found: {source}")
        shutil.copy2(source, scenario_path)
    else:
        scenario_path.write_text(args.scenario_summary or "", encoding="utf-8")

    state = {
        "workflow": WORKFLOW,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "title": title,
        "run_dir": str(run_dir),
        "scenario_file": str(scenario_path),
        "source_root": str(DEFAULT_SOURCE_ROOT),
        "excluded_source_roots": [str(DEFAULT_OUTPUT_ROOT)],
        "source_references": [],
        "text_policy": TEXT_POLICY_DIALOGUE_SFX_CAPTIONS,
        "character_locks": [],
        "visual_text_guard": [],
        "spatial_continuity_plan": normalize_spatial_continuity_plan({}),
        "stage_order": STAGE_IDS,
        "target_stages": STAGE_IDS,
        "page_generation_mode": PAGE_GENERATION_MODE_SEQUENTIAL_PRIOR_PAGES,
        "stage_reviews": build_stage_reviews(),
        "stage_anchor_reviews": build_stage_anchor_reviews(),
        "stage_gates": build_stage_gates(),
        "plan_approved": False,
        "complete": False,
        "pages": [],
        "batches": [],
        "notes": ["Generation is blocked until approve-plan is run after explicit user approval."],
    }
    save_state(run_dir, state)
    print(f"RUN_DIR: {run_dir}")
    print(f"STATE: {run_dir / 'state.json'}")
    print(f"STORY_INPUT: {scenario_path}")
    print("NEXT: Present the Korean page plan approval request, then run approve-plan after user approval.")


def normalize_panel(raw: dict[str, Any], index: int) -> dict[str, Any]:
    base = raw.get("id") or raw.get("filename") or raw.get("beat") or raw.get("visual_brief") or f"panel-{index}"
    panel_id = slugify(str(base), f"panel-{index}")[:80]
    return {
        "id": panel_id,
        "panel_no": raw.get("panel_no") or raw.get("order") or index,
        "order": int(raw.get("panel_no") or raw.get("order") or index),
        "scene_refs": as_list(raw.get("scene_refs") or raw.get("scenes")),
        "beat": str(raw.get("beat") or raw.get("purpose") or ""),
        "purpose": str(raw.get("purpose") or raw.get("beat") or ""),
        "visual_brief": str(raw.get("visual_brief") or raw.get("brief") or ""),
        "setting": str(raw.get("setting") or ""),
        "characters": as_list(raw.get("characters")),
        "action": str(raw.get("action") or ""),
        "camera": str(raw.get("camera") or ""),
        "composition": str(raw.get("composition") or ""),
        "mood": str(raw.get("mood") or ""),
        "source_dialogue": as_list(raw.get("source_dialogue") or raw.get("dialogue")),
        "adapted_dialogue": as_list(raw.get("adapted_dialogue")),
        "sfx": as_list(raw.get("sfx")),
        "caption": as_list(raw.get("caption") or raw.get("narration")),
        "speech_balloon": str(raw.get("speech_balloon") or raw.get("speech_balloon_placement") or ""),
        "sfx_placement": str(raw.get("sfx_placement") or ""),
        "detail_density_notes": str(raw.get("detail_density_notes") or ""),
        "visual_emphasis_notes": str(raw.get("visual_emphasis_notes") or ""),
        "comic_effects_notes": str(raw.get("comic_effects_notes") or ""),
        "continuity_notes": str(raw.get("continuity_notes") or ""),
        "spatial_logic_notes": str(raw.get("spatial_logic_notes") or ""),
        "motion_checks": as_list(raw.get("motion_checks")),
        "must_match": as_list(raw.get("must_match")),
        "prompt": str(raw.get("prompt") or raw.get("visual_brief") or raw.get("brief") or ""),
        "notes": str(raw.get("notes") or ""),
    }


def page_from_raw(raw: dict[str, Any], index: int) -> dict[str, Any]:
    base = raw.get("id") or raw.get("filename") or raw.get("layout_brief") or raw.get("title") or f"page-{index}"
    page_id = slugify(str(base), f"page-{index}")[:80]
    filename = raw.get("filename")
    if filename:
        filename = slugify(Path(str(filename)).stem, page_id) + ".png"
    else:
        filename = f"{index:03d}_{page_id}.png"
    raw_panels = raw.get("panels")
    if not isinstance(raw_panels, list) or not raw_panels:
        raw_panels = [
            {
                "id": f"{page_id}-panel-1",
                "panel_no": 1,
                "scene_refs": raw.get("scene_refs") or raw.get("scenes"),
                "beat": raw.get("beat") or raw.get("purpose") or "",
                "visual_brief": raw.get("visual_brief") or raw.get("layout_brief") or raw.get("prompt") or "",
                "setting": raw.get("setting") or "",
                "characters": raw.get("characters") or [],
                "action": raw.get("action") or "",
                "camera": raw.get("camera") or "",
                "composition": raw.get("composition") or "",
                "mood": raw.get("mood") or "",
                "source_dialogue": raw.get("source_dialogue") or raw.get("dialogue") or [],
                "adapted_dialogue": raw.get("adapted_dialogue") or [],
                "sfx": raw.get("sfx") or [],
                "caption": raw.get("caption") or raw.get("narration") or [],
                "text_policy": raw.get("text_policy") or "",
                "character_locks": raw.get("character_locks") or [],
                "visual_text_guard": raw.get("visual_text_guard") or [],
                "detail_density_notes": raw.get("detail_density_notes") or "",
                "visual_emphasis_notes": raw.get("visual_emphasis_notes") or "",
                "comic_effects_notes": raw.get("comic_effects_notes") or "",
                "continuity_notes": raw.get("continuity_notes") or "",
                "spatial_logic_notes": raw.get("spatial_logic_notes") or "",
                "motion_checks": raw.get("motion_checks") or [],
                "must_match": raw.get("must_match") or [],
                "prompt": raw.get("prompt") or raw.get("visual_brief") or raw.get("layout_brief") or "",
            }
        ]
    panels = [normalize_panel(panel, panel_index) for panel_index, panel in enumerate(raw_panels, start=1)]
    if not any(panel.get("visual_brief") or panel.get("prompt") for panel in panels):
        raise SystemExit(f"Page {page_id} needs at least one panel with visual_brief or prompt.")
    location_continuity = normalize_location_continuity(
        raw.get("location_continuity") or raw.get("setting_continuity")
    )
    location_id = str(raw.get("location_id") or location_continuity.get("location_id") or "").strip()
    if location_id and not location_continuity.get("location_id"):
        location_continuity["location_id"] = location_id

    return {
        "id": page_id,
        "filename": filename,
        "order": int(raw.get("page_no") or raw.get("order") or index),
        "page_no": raw.get("page_no") or index,
        "scene_refs": as_list(raw.get("scene_refs") or raw.get("scenes")),
        "layout_brief": str(raw.get("layout_brief") or raw.get("visual_brief") or ""),
        "reading_order": str(raw.get("reading_order") or ""),
        "text_policy": normalize_text_policy(raw.get("text_policy")) if raw.get("text_policy") else "",
        "character_locks": merge_unique(raw.get("character_locks")),
        "visual_text_guard": merge_unique(raw.get("visual_text_guard")),
        "page_dialogue_notes": str(raw.get("page_dialogue_notes") or ""),
        "pacing_notes": str(raw.get("pacing_notes") or DEFAULT_PACING_NOTES),
        "panel_shape_notes": str(raw.get("panel_shape_notes") or DEFAULT_PANEL_SHAPE_NOTES),
        "negative_space_notes": str(raw.get("negative_space_notes") or DEFAULT_NEGATIVE_SPACE_NOTES),
        "detail_density_notes": str(raw.get("detail_density_notes") or DEFAULT_DETAIL_DENSITY_NOTES),
        "visual_emphasis_notes": str(raw.get("visual_emphasis_notes") or DEFAULT_VISUAL_EMPHASIS_NOTES),
        "comic_effects_notes": str(raw.get("comic_effects_notes") or DEFAULT_COMIC_EFFECTS_NOTES),
        "location_id": location_id,
        "location_continuity": location_continuity,
        "narrative_plan": normalize_optional_object(raw.get("narrative_plan"), "narrative_plan"),
        "spatial_contract_extraction": normalize_optional_object(
            raw.get("spatial_contract_extraction"), "spatial_contract_extraction"
        ),
        "spatial_logic_notes": str(raw.get("spatial_logic_notes") or ""),
        "motion_checks": as_list(raw.get("motion_checks")),
        "must_match": as_list(raw.get("must_match")),
        "references": validate_reference_paths(raw.get("references") or raw.get("reference_paths")),
        "prompt": str(raw.get("prompt") or raw.get("layout_brief") or raw.get("visual_brief") or ""),
        "negative_prompt": str(raw.get("negative_prompt") or ""),
        "dependencies": as_list(raw.get("dependencies")),
        "notes": str(raw.get("notes") or ""),
        "spatial_contract": normalize_spatial_contract(raw.get("spatial_contract")),
        "panels": panels,
        "stages": build_stage_states(),
    }


def legacy_panels_to_pages(plan: dict[str, Any]) -> list[dict[str, Any]]:
    pages = []
    for index, raw_panel in enumerate(plan.get("panels", []), start=1):
        if not isinstance(raw_panel, dict):
            raise SystemExit(f"Panel {index} is not an object.")
        page_seed = dict(raw_panel)
        page_seed.setdefault("id", raw_panel.get("id") or f"page-{index}")
        page_seed.setdefault("filename", raw_panel.get("filename") or f"{index:03d}_page-{index}.png")
        page_seed.setdefault("page_no", raw_panel.get("panel_no") or index)
        page_seed.setdefault("layout_brief", raw_panel.get("visual_brief") or raw_panel.get("prompt") or "")
        page_seed["panels"] = [raw_panel]
        pages.append(page_from_raw(page_seed, index))
    return pages


def normalize_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(plan.get("pages"), list) and plan["pages"]:
        pages = []
        for index, raw_page in enumerate(plan["pages"], start=1):
            if not isinstance(raw_page, dict):
                raise SystemExit(f"Page {index} is not an object.")
            pages.append(page_from_raw(raw_page, index))
    elif isinstance(plan.get("panels"), list) and plan["panels"]:
        pages = legacy_panels_to_pages(plan)
    else:
        raise SystemExit("Plan must contain a non-empty pages list, or a legacy non-empty panels list.")

    seen_ids: set[str] = set()
    seen_files: set[str] = set()
    for index, page in enumerate(pages, start=1):
        if page["id"] in seen_ids:
            page["id"] = f"{index:03d}-{page['id']}"
        seen_ids.add(page["id"])
        if page["filename"] in seen_files:
            page["filename"] = f"{index:03d}_{page['filename']}"
        seen_files.add(page["filename"])

    id_aliases: dict[str, str] = {}
    for page in pages:
        id_aliases[page["id"]] = page["id"]
        id_aliases[slugify(page["id"])] = page["id"]
        id_aliases[page["filename"]] = page["id"]
        id_aliases[Path(page["filename"]).stem] = page["id"]
        id_aliases[slugify(Path(page["filename"]).stem)] = page["id"]

    for page in pages:
        normalized_deps = []
        for dep in page.get("dependencies", []):
            dep_key = slugify(Path(str(dep)).stem, str(dep))
            dep_id = id_aliases.get(str(dep)) or id_aliases.get(dep_key)
            if not dep_id:
                raise SystemExit(f"Page {page['id']} has unknown dependency: {dep}")
            if dep_id != page["id"] and dep_id not in normalized_deps:
                normalized_deps.append(dep_id)
        page["dependencies"] = normalized_deps
    pages.sort(key=lambda page: (page["order"], page["id"]))
    return pages


def plan_and_pages_for_spatial_check(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if getattr(args, "plan_json", ""):
        try:
            plan = json.loads(args.plan_json)
            return plan, normalize_plan(plan)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid --plan-json: {exc}") from exc
    if getattr(args, "plan_file", ""):
        plan = load_json(Path(args.plan_file))
        return plan, normalize_plan(plan)
    if getattr(args, "run_dir", ""):
        state = load_state(Path(args.run_dir))
        return state, state.get("pages", [])
    raise SystemExit("Use --plan-file, --plan-json, or --run-dir.")


def pages_for_spatial_check(args: argparse.Namespace) -> list[dict[str, Any]]:
    return plan_and_pages_for_spatial_check(args)[1]


def spatial_continuity_plan_from_context(plan_context: dict[str, Any]) -> dict[str, Any]:
    return normalize_spatial_continuity_plan(
        plan_context.get("spatial_continuity_plan")
        or plan_context.get("setting_continuity_plan")
        or plan_context.get("location_plan")
    )


def command_spatial_check(args: argparse.Namespace) -> None:
    plan_context, pages = plan_and_pages_for_spatial_check(args)
    spatial_continuity_plan = spatial_continuity_plan_from_context(plan_context)
    issues = spatial_plan_issues(pages, spatial_continuity_plan)
    warnings = spatial_plan_warnings(pages, spatial_continuity_plan)
    if issues:
        print("SPATIAL_CHECK: fail")
        for issue in issues:
            print(f"- {issue}")
        print(f"SPATIAL_WARNINGS: {len(warnings)}")
        for warning in warnings:
            print(f"- warning: {warning}")
        raise SystemExit(1)
    print("SPATIAL_CHECK: pass")
    print(f"STRUCTURED_PAGES: {spatial_contract_page_count(pages)}")
    print(f"SPATIAL_WARNINGS: {len(warnings)}")
    for warning in warnings:
        print(f"- warning: {warning}")


def command_spatial_preview(args: argparse.Namespace) -> None:
    plan_context, pages = plan_and_pages_for_spatial_check(args)
    spatial_continuity_plan = spatial_continuity_plan_from_context(plan_context)
    issues = spatial_plan_issues(pages, spatial_continuity_plan)
    warnings = spatial_plan_warnings(pages, spatial_continuity_plan)
    model = build_spatial_preview_model(pages, issues, warnings)
    model["spatial_continuity_plan"] = spatial_continuity_plan
    model["title"] = spatial_preview_title(args)
    model["source"] = spatial_preview_source(args)
    output_path = spatial_preview_output_path(args)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_spatial_preview_html(model), encoding="utf-8")
    print(f"SPATIAL_PREVIEW: {output_path}")
    print(f"SPATIAL_CHECK: {model['status']}")
    print(f"STRUCTURED_PAGES: {model['structured_page_count']}")
    print(f"ISSUES: {len(issues)}")
    print(f"SPATIAL_WARNINGS: {len(warnings)}")


def phase_for_spatial_render_manifest(args: argparse.Namespace) -> str:
    if getattr(args, "stage", ""):
        return str(args.stage)
    if getattr(args, "plan_file", ""):
        return "proposed"
    return "approved"


def spatial_render_output_dir(args: argparse.Namespace) -> Path:
    if getattr(args, "output_dir", ""):
        return Path(args.output_dir)
    phase = phase_for_spatial_render_manifest(args)
    if getattr(args, "run_dir", ""):
        return Path(args.run_dir) / "spatial_renders" / phase
    if getattr(args, "plan_file", ""):
        return Path(args.plan_file).parent / "spatial_renders" / phase
    raise SystemExit("spatial-render-manifest requires --run-dir or --plan-file.")


def snapshot_has_camera(snapshot: dict[str, Any]) -> bool:
    camera = snapshot.get("camera") or {}
    return vector3(camera.get("position")) is not None and vector3(camera.get("look_at")) is not None


def scene_3d_text_haystack(page: dict[str, Any], scene: dict[str, Any] | None, contract: dict[str, Any]) -> str:
    return json.dumps({"page": page, "scene": scene or {}, "contract": contract}, ensure_ascii=False).lower()


def scene_3d_has_level_cues(page: dict[str, Any], scene: dict[str, Any] | None, contract: dict[str, Any]) -> bool:
    haystack = scene_3d_text_haystack(page, scene, contract)
    if len((scene or {}).get("levels", [])) > 1:
        return True
    if any(str(constraint.get("type") or "") in {"on_level", "above", "below", "vertical_separation"} for constraint in contract.get("constraints", [])):
        return True
    return bool(re.search(r"floor_2|floor2|2층|upper|above|below|stair|railing|balcony|level|층|계단|난간|발코니|고도", haystack))


def scene_3d_has_cover_or_sight_cues(contract: dict[str, Any]) -> bool:
    cover_types = {"cover_between", "behind_cover_from", "line_of_sight_blocked", "no_line_of_fire", "not_aims_at", "occluder_between_3d"}
    return any(str(constraint.get("type") or "") in cover_types for constraint in contract.get("constraints", []))


def scene_3d_has_trajectory_cues(snapshot: dict[str, Any], contract: dict[str, Any]) -> bool:
    if any(str(constraint.get("type") or "") in {"trajectory_to", "max_transfer_distance", "path_via"} for constraint in contract.get("constraints", [])):
        return True
    return any(
        vector3(entity.get("trajectory_vector") or entity.get("motion_vector") or entity.get("velocity_vector")) is not None
        for entity in snapshot.get("entities", [])
    )


def normalize3(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = vector3_length(vector) or 1.0
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def dot3(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross3(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def camera_overlap_risk(snapshot: dict[str, Any]) -> bool:
    camera = snapshot.get("camera") or {}
    camera_position = vector3(camera.get("position"))
    look_at = vector3(camera.get("look_at"))
    if camera_position is None or look_at is None:
        return True
    forward = normalize3((
        look_at[0] - camera_position[0],
        look_at[1] - camera_position[1],
        look_at[2] - camera_position[2],
    ))
    world_up = (0.0, 0.0, 1.0)
    right = cross3(forward, world_up)
    if vector3_length(right) < 0.001:
        right = (1.0, 0.0, 0.0)
    else:
        right = normalize3(right)
    up = normalize3(cross3(right, forward))
    projected: list[tuple[float, float]] = []
    for entity in snapshot.get("entities", []):
        position = vector3(entity.get("position"))
        if position is None:
            continue
        relative = (
            position[0] - camera_position[0],
            position[1] - camera_position[1],
            position[2] - camera_position[2],
        )
        depth = abs(dot3(relative, forward)) or 1.0
        projected.append((dot3(relative, right) / depth, dot3(relative, up) / depth))
    for index, first in enumerate(projected):
        for second in projected[index + 1 :]:
            if math.hypot(first[0] - second[0], first[1] - second[1]) < 0.08:
                return True
    return False


def render_views_for_snapshot(
    page: dict[str, Any],
    scene: dict[str, Any] | None,
    contract: dict[str, Any],
    snapshot: dict[str, Any],
) -> list[tuple[str, str, bool]]:
    views: dict[str, tuple[str, bool]] = {}

    def add(view: str, reason: str, required: bool = True) -> None:
        current = views.get(view)
        if current:
            views[view] = (f"{current[0]}; {reason}", current[1] or required)
        else:
            views[view] = (reason, required)

    if snapshot_has_camera(snapshot):
        add("camera", "camera direction baseline")
    else:
        add("iso", "camera missing; iso view required for spatial sanity check")
    if scene_3d_has_level_cues(page, scene, contract):
        add("iso", "level/height/stair/railing/balcony relationship")
        add("side", "vertical separation readability")
    if scene_3d_has_cover_or_sight_cues(contract):
        add("top", "cover/line-of-sight relationship")
        if snapshot_has_camera(snapshot):
            add("camera", "cover/line-of-sight from panel camera")
    if scene_3d_has_trajectory_cues(snapshot, contract):
        add("top", "trajectory/movement path readability")
    if camera_overlap_risk(snapshot):
        add("iso", "camera view overlap risk")
    return [(view, reason, required) for view, (reason, required) in views.items()]


def scene_3d_canvas_selector(page_id: str) -> str:
    safe_page_id = page_id.replace("\\", "\\\\").replace('"', '\\"')
    return f'[data-preview-page-id="{safe_page_id}"] canvas[data-scene3d]'


def command_spatial_render_manifest(args: argparse.Namespace) -> None:
    plan_context, pages = plan_and_pages_for_spatial_check(args)
    spatial_continuity_plan = spatial_continuity_plan_from_context(plan_context)
    issues = spatial_plan_issues(pages, spatial_continuity_plan)
    warnings = spatial_plan_warnings(pages, spatial_continuity_plan)
    model = build_spatial_preview_model(pages, issues, warnings)
    model["spatial_continuity_plan"] = spatial_continuity_plan
    model["title"] = spatial_preview_title(args)
    model["source"] = spatial_preview_source(args)
    html_path = spatial_preview_output_path(args)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_spatial_preview_html(model), encoding="utf-8")

    output_dir = spatial_render_output_dir(args)
    output_dir.mkdir(parents=True, exist_ok=True)
    scenes_by_id = scene_3d_scenes_by_id(spatial_continuity_plan)
    items: list[dict[str, Any]] = []
    for page in pages:
        contract = page.get("spatial_contract", {})
        if spatial_contract_coordinate_type(contract) != "scene_3d":
            continue
        scene_id = str((contract.get("coordinate_space") or {}).get("scene_id") or "")
        scene = scenes_by_id.get(scene_id)
        page_id = str(page.get("id") or Path(str(page.get("filename") or "page")).stem)
        for snapshot in contract.get("panel_snapshots", []):
            panel = panel_key(snapshot.get("panel")) or "1"
            for view, reason, required in render_views_for_snapshot(page, scene, contract, snapshot):
                stem = slugify(f"{page_id}-panel-{panel}-{view}", "scene-3d-render")
                items.append(
                    {
                        "id": stem,
                        "page_id": page_id,
                        "page_filename": page.get("filename", ""),
                        "panel": panel,
                        "view": view,
                        "reason": reason,
                        "html_path": str(html_path),
                        "canvas_selector": scene_3d_canvas_selector(page_id),
                        "output_png": str(output_dir / f"{stem}.png"),
                        "required_for_review": bool(required),
                    }
                )
    manifest_path = output_dir / "render_manifest.json"
    write_json(
        manifest_path,
        {
            "workflow": WORKFLOW,
            "type": "spatial_render_manifest",
            "created_at": now_iso(),
            "source": spatial_preview_source(args),
            "stage": getattr(args, "stage", ""),
            "phase": phase_for_spatial_render_manifest(args),
            "html_path": str(html_path),
            "output_dir": str(output_dir),
            "spatial_check": "fail" if issues else "pass",
            "issues": issues,
            "warnings": warnings,
            "items": items,
        },
    )
    print(f"SPATIAL_RENDER_MANIFEST: {manifest_path}")
    print(f"SPATIAL_PREVIEW: {html_path}")
    print(f"SPATIAL_CHECK: {'fail' if issues else 'pass'}")
    print(f"RENDER_ITEMS: {len(items)}")
    print(f"REQUIRED_RENDER_ITEMS: {sum(1 for item in items if item.get('required_for_review'))}")


def command_approve_plan(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    if args.plan_json:
        try:
            plan = json.loads(args.plan_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid --plan-json: {exc}") from exc
    elif args.plan_file:
        plan = load_json(Path(args.plan_file))
    else:
        raise SystemExit("Use --plan-file or --plan-json.")

    pages = normalize_plan(plan)
    spatial_continuity_plan = spatial_continuity_plan_from_context(plan)
    assert_spatial_contracts_pass(pages, spatial_continuity_plan)
    state["title"] = plan.get("scenario_title") or plan.get("story_title") or state.get("title")
    state["style_brief"] = str(plan.get("style_brief") or "")
    state["reading_order"] = str(plan.get("reading_order") or "right-to-left or top-to-bottom as approved")
    state["source_root"] = str(DEFAULT_SOURCE_ROOT)
    state["excluded_source_roots"] = [str(DEFAULT_OUTPUT_ROOT)]
    state["source_references"] = validate_reference_paths(plan.get("references") or plan.get("reference_paths"))
    state["text_policy"] = normalize_text_policy(plan.get("text_policy"))
    state["character_locks"] = merge_unique(plan.get("character_locks"))
    state["visual_text_guard"] = merge_unique(plan.get("visual_text_guard"))
    state["spatial_continuity_plan"] = spatial_continuity_plan
    state["plan_approved"] = True
    state["approved_at"] = now_iso()
    state["target_stages"] = [args.target_stage] if args.target_stage else list(STAGE_IDS)
    state["page_generation_mode"] = PAGE_GENERATION_MODE_SEQUENTIAL_PRIOR_PAGES
    state["pages"] = pages
    state.pop("panels", None)
    state["batches"] = []
    state["stage_reviews"] = build_stage_reviews()
    state["stage_anchor_reviews"] = build_stage_anchor_reviews()
    state["stage_gates"] = build_stage_gates()
    state.setdefault("notes", []).append(f"Approved {len(pages)} comic pages at {state['approved_at']}.")
    normalize_state(state)

    write_json(
        run_dir / "approved_storyboard_plan.json",
        {
            "scenario_title": state["title"],
            "style_brief": state.get("style_brief", ""),
            "reading_order": state.get("reading_order", ""),
            "source_root": state.get("source_root", ""),
            "excluded_source_roots": state.get("excluded_source_roots", []),
            "source_references": state.get("source_references", []),
            "text_policy": state.get("text_policy", TEXT_POLICY_DIALOGUE_SFX_CAPTIONS),
            "character_locks": state.get("character_locks", []),
            "visual_text_guard": state.get("visual_text_guard", []),
            "spatial_continuity_plan": state.get("spatial_continuity_plan", normalize_spatial_continuity_plan({})),
            "target_stages": state.get("target_stages", STAGE_IDS),
            "page_generation_mode": state.get("page_generation_mode", PAGE_GENERATION_MODE_SEQUENTIAL_PRIOR_PAGES),
            "stage_anchor_reviews": state.get("stage_anchor_reviews", {}),
            "pages": state.get("pages", []),
        },
    )
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"APPROVED_PAGES: {len(pages)}")
    print(f"SPATIAL_CHECK: pass ({spatial_contract_page_count(pages)} structured pages)")
    print(f"PLAN: {run_dir / 'approved_storyboard_plan.json'}")
    print("NEXT: comic_storyboard_runner.py next-batch --run-dir <run-dir> --limit 1")


def command_next_batch(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    if not state.get("plan_approved"):
        raise SystemExit("Plan is not approved. Present the Korean page approval request, then run approve-plan.")

    blockers = current_blockers(state)
    if blockers:
        names = ", ".join(
            f"{page['filename']}:{stage_id}({stage.get('status')})" for page, stage_id, stage in blockers
        )
        raise SystemExit(f"Resolve current batch before reserving another: {names}")

    stage_id = current_stage_id(state)
    if not stage_id:
        print("COMPLETE: true")
        return

    candidates = []
    for page in state.get("pages", []):
        stage = stage_state(page, stage_id)
        if stage.get("status") != "pending":
            continue
        if not dependencies_ready(state, page, stage_id):
            continue
        if not prior_pages_ready_for_stage(state, page, stage_id):
            continue
        if not stage_anchor_allows_page_reservation(state, page, stage_id):
            continue
        candidates.append(page)
    candidates.sort(key=lambda page: page_sort_key(page, stage_id))

    if not candidates:
        anchor_page = stage_anchor_review_required_page(state, stage_id)
        if anchor_page:
            print(f"STAGE_ANCHOR_REVIEW_REQUIRED: {stage_id}")
            print(f"ANCHOR_ITEM: {anchor_page['filename']}")
            print(f"ANCHOR_OUTPUT: {stage_output_path(run_dir, anchor_page, stage_id, prefer_recorded=True)}")
            print(
                "ANCHOR_REVIEW_COMMAND: comic_storyboard_runner.py anchor-review "
                f"--run-dir <run-dir> --stage {stage_id} --item {anchor_page['filename']} "
                '--status pass --note "<stage level anchor pass>"'
            )
            print(
                "ANCHOR_RERUN_COMMAND: comic_storyboard_runner.py anchor-review "
                f"--run-dir <run-dir> --stage {stage_id} --item {anchor_page['filename']} "
                '--status needs_rerun --note "<reason>"'
            )
        if pages_complete_for_stage(state, stage_id) and not stage_review_passed(state, stage_id):
            print(f"STAGE_REVIEW_REQUIRED: {stage_id}")
        print("NO_ELIGIBLE_ITEMS")
        command_status(args)
        return

    limit = min(max(args.limit, 1), 4)
    if sequential_prior_pages_mode(state):
        limit = 1
    selected = candidates[:limit]
    assert_required_prior_stage_outputs_exist(state, run_dir, selected, stage_id)
    required_transition = transition_required_before_stage(state, stage_id)
    if required_transition and not transition_gate_allows(
        state,
        required_transition["from_stage"],
        required_transition["to_stage"],
    ):
        gate = state.get("stage_gates", {}).get(transition_gate_key(required_transition), blank_stage_gate())
        request_path = gate.get("feedback_request", "")
        if gate.get("status") == "pending":
            written_request_path = mark_transition_waiting_for_feedback(
                state,
                run_dir,
                required_transition["from_stage"],
                required_transition["to_stage"],
                required_transition["pending_note"],
            )
            write_batch_plan(run_dir, state)
            save_state(run_dir, state)
            gate = state.get("stage_gates", {}).get(transition_gate_key(required_transition), blank_stage_gate())
            request_path = str(written_request_path or gate.get("feedback_request", ""))
        print(f"USER_FEEDBACK_REQUIRED: {required_transition['from_stage']} -> {required_transition['to_stage']}")
        print(f"GATE_STATUS: {gate.get('status', 'pending_user_feedback')}")
        print(f"FEEDBACK_REQUEST: {request_path or gate.get('feedback_request', '')}")
        print(f"FEEDBACK_CHOICES: {transition_feedback_choices_text(required_transition)}")
        command_status(args)
        return
    batch_id = f"batch-{len(state.get('batches', [])) + 1:03d}"
    for page in selected:
        stage = stage_state(page, stage_id)
        rerun_correction = current_rerun_correction(stage, require_pending=True)
        stage["status"] = "generation_requested"
        stage["batch_id"] = batch_id
        stage["attempts"] = int(stage.get("attempts", 0)) + 1
        stage["requested_at"] = now_iso()
        stage["rerun_pending"] = False
        stage["worker_status"] = ""
        stage["worker_note"] = ""
        stage["parent_note"] = ""
        stage["spatial_verdict"] = ""
        stage["spatial_note"] = ""
        stage["spatial_checked_at"] = ""
        stage["current_rerun_correction"] = rerun_correction
        stage["visual_reference_paths"] = visual_reference_paths(run_dir, page, stage_id, state)
        prompt_path = stage_prompt_path(run_dir, page, stage_id)
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text(run_dir, page, stage_id, state), encoding="utf-8")
        stage["prompt_file"] = str(prompt_path)
        stage["output_path"] = str(stage_output_path(run_dir, page, stage_id))
        if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE:
            stage["description_path"] = str(stage_description_path(run_dir, page, stage_id))
        subagent_path = subagent_prompt_path(run_dir, page, stage_id)
        subagent_path.parent.mkdir(parents=True, exist_ok=True)
        stage["subagent_prompt_file"] = str(subagent_path)
        subagent_path.write_text(subagent_prompt_text(run_dir, page, stage_id, state), encoding="utf-8")

    state.setdefault("batches", []).append(
        {
            "id": batch_id,
            "stage": stage_id,
            "created_at": now_iso(),
            "pages": [page["id"] for page in selected],
            "limit": limit,
            "page_generation_mode": page_generation_mode(state),
        }
    )
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)

    print(f"BATCH_ID: {batch_id}")
    print(f"STAGE: {stage_id}")
    print(f"RUN_DIR: {run_dir}")
    for page in selected:
        stage = stage_state(page, stage_id)
        print(f"ITEM: {page['filename']}")
        print(f"ITEM_ID: {page['id']}")
        print(f"PROMPT_FILE: {stage['prompt_file']}")
        print(f"SUBAGENT_PROMPT_FILE: {stage['subagent_prompt_file']}")
        print(f"OUTPUT: {stage['output_path']}")
        for path in stage.get("visual_reference_paths", []):
            print(f"VISUAL_REFERENCE_IMAGE: {path}")


def command_import(args: argparse.Namespace) -> None:
    if args.worker_status not in WORKER_STATUS_VALUES:
        raise SystemExit(f"Invalid worker-status: {args.worker_status}")
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    page = resolve_page(state, args.item)
    stage_id = args.stage
    stage = stage_state(page, stage_id)
    if stage.get("status") not in {"generation_requested", "imported"}:
        raise SystemExit(f"Page stage is not waiting for import: {page['filename']} {stage_id} ({stage.get('status')})")
    generated = Path(args.generated)
    if not generated.exists():
        raise SystemExit(f"Generated file not found: {generated}")

    destination = stage_output_path(run_dir, page, stage_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if generated.resolve(strict=False) != destination.resolve(strict=False):
        shutil.copy2(generated, destination)
    description_destination = None
    if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE:
        if not args.description:
            raise SystemExit("storyboard_conti_sketch_ink import requires --description <desc.md>.")
        description_source = Path(args.description)
        if not description_source.exists():
            raise SystemExit(f"Conti/sketch/ink description file not found: {description_source}")
        description_destination = stage_description_path(run_dir, page, stage_id)
        description_destination.parent.mkdir(parents=True, exist_ok=True)
        if description_source.resolve(strict=False) != description_destination.resolve(strict=False):
            shutil.copy2(description_source, description_destination)
        validate_stage_description(description_destination, page)
    stage["status"] = "imported"
    stage["generated_source"] = str(generated)
    stage["output_path"] = str(destination)
    if description_destination is not None:
        stage["description_path"] = str(description_destination)
        stage["description_source"] = str(args.description)
        stage["description_imported_at"] = now_iso()
    stage["worker_status"] = args.worker_status
    stage["worker_note"] = args.worker_note
    stage["imported_at"] = now_iso()
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"IMPORTED: {destination}")
    print(f"WORKER_STATUS: {args.worker_status}")
    print("NEXT: Parent must inspect, then run inspect-pass or rerun.")


def command_inspect_pass(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    page = resolve_page(state, args.item)
    stage_id = args.stage
    stage = stage_state(page, stage_id)
    if stage.get("status") not in {"imported", "inspected_pass", "complete"}:
        raise SystemExit(f"Page stage is not imported for inspection: {page['filename']} {stage_id} ({stage.get('status')})")
    output = stage_output_path(run_dir, page, stage_id, prefer_recorded=True)
    if not output.exists():
        raise SystemExit(f"Output file does not exist: {output}")
    if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE:
        validate_stage_description(recorded_stage_description_path(run_dir, page, stage_id), page)
    spatial_note = args.spatial_note or (
        "parent spatial contract inspection passed"
        if spatial_contract_has_content(page.get("spatial_contract"))
        else ""
    )
    if args.spatial_verdict == "needs_rerun":
        note = args.spatial_note or args.note
        stage["spatial_verdict"] = "needs_rerun"
        stage["spatial_note"] = note
        stage["spatial_checked_at"] = now_iso()
        mark_page_stage_for_rerun(page, stage_id, f"Spatial inspection needs rerun: {note}", run_dir)
        downstream_pages = mark_downstream_prior_page_dependents_for_rerun(
            state,
            page,
            stage_id,
            f"Prior page {page['filename']} rerun invalidated this {stage_id} continuity reference.",
            run_dir,
        )
        if is_stage_anchor_page(state, page, stage_id):
            reset_stage_anchor_review(state, stage_id, f"Stage anchor review reset because {page['filename']} failed spatial inspection.")
        reset_stage_review(state, stage_id, f"Stage review reset because {page['filename']} failed spatial inspection.")
        reset_following_stage_gates(state, stage_id, f"Stage gate reset because {page['filename']} failed spatial inspection.")
        write_batch_plan(run_dir, state)
        save_state(run_dir, state)
        print(f"SPATIAL_RERUN_REQUIRED: {page['filename']} {stage_id}")
        for downstream_page in downstream_pages:
            print(f"DOWNSTREAM_RERUN_ITEM: {downstream_page['filename']}")
        print("NEXT: Resolve any other current items, then run next-batch.")
        return
    stage["status"] = "inspected_pass"
    stage["parent_note"] = args.note
    stage["spatial_verdict"] = args.spatial_verdict
    stage["spatial_note"] = spatial_note
    if args.spatial_verdict == "reconciled":
        reconciliation = {
            "page": page["filename"],
            "stage": stage_id,
            "note": args.reconciliation_note or spatial_note or args.note,
            "recorded_at": now_iso(),
        }
        stage["reconciliation_note"] = reconciliation["note"]
        state.setdefault("spatial_reconciliations", []).append(reconciliation)
    stage["spatial_checked_at"] = now_iso()
    stage["inspected_at"] = now_iso()
    stage["output_path"] = str(output)
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"INSPECTED_PASS: {page['filename']} {stage_id}")


def command_anchor_review(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    stage_id = args.stage
    page = resolve_page(state, args.item)
    if not sequential_prior_pages_mode(state):
        raise SystemExit("anchor-review is only required for sequential_prior_pages mode.")
    if not is_stage_anchor_page(state, page, stage_id):
        anchor_page = stage_anchor_page(state, stage_id)
        anchor_name = anchor_page["filename"] if anchor_page else "<none>"
        raise SystemExit(f"Stage anchor review must target the first page in stage order: {anchor_name}")
    stage = stage_state(page, stage_id)
    if not page_complete_for_stage(page, stage_id):
        raise SystemExit(
            f"Stage anchor review requires parent-inspected pass first: {page['filename']} {stage_id} ({stage.get('status')})"
        )
    output = stage_output_path(run_dir, page, stage_id, prefer_recorded=True)
    if not output.exists():
        raise SystemExit(f"Output file does not exist: {output}")
    if stage_id == STORYBOARD_CONTI_SKETCH_INK_STAGE:
        validate_stage_description(recorded_stage_description_path(run_dir, page, stage_id), page)

    review = state.setdefault("stage_anchor_reviews", {}).setdefault(stage_id, blank_stage_anchor_review())
    issues = as_list(args.issue)
    reviewed_at = now_iso()
    review["anchor_item"] = page["filename"]
    review["output_path"] = str(output)
    review["note"] = args.note
    review["issues"] = issues
    review["reviewed_at"] = reviewed_at

    downstream_pages: list[dict[str, Any]] = []
    if args.status == "pass":
        review["status"] = "passed"
        review["anchor_level_note"] = args.note
    elif args.status == "needs_rerun":
        review["status"] = "needs_rerun"
        review["anchor_level_note"] = ""
        mark_page_stage_for_rerun(page, stage_id, f"Stage anchor review needs rerun: {args.note}", run_dir)
        downstream_pages = mark_downstream_prior_page_dependents_for_rerun(
            state,
            page,
            stage_id,
            f"Prior page {page['filename']} anchor rerun invalidated this {stage_id} continuity reference.",
            run_dir,
        )
        reset_stage_review(state, stage_id, f"Stage review reset because {page['filename']} failed stage anchor review.")
        reset_following_stage_gates(state, stage_id, f"Stage gate reset because {page['filename']} failed stage anchor review.")
    else:
        raise SystemExit(f"Invalid stage anchor review status: {args.status}")

    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"STAGE_ANCHOR_REVIEW: {stage_id}")
    print(f"ANCHOR_ITEM: {page['filename']}")
    print(f"STATUS: {review['status']}")
    if args.status == "needs_rerun":
        print(f"RERUN_ITEM: {page['filename']}")
        for downstream_page in downstream_pages:
            print(f"DOWNSTREAM_RERUN_ITEM: {downstream_page['filename']}")


def command_rerun(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    page = resolve_page(state, args.item)
    stage_id = args.stage
    mark_page_stage_for_rerun(page, stage_id, args.note, run_dir)
    downstream_candidates = downstream_prior_page_dependents(state, page, stage_id)
    downstream_pages: list[dict[str, Any]] = []
    if args.cascade_downstream:
        downstream_pages = mark_downstream_prior_page_dependents_for_rerun(
            state,
            page,
            stage_id,
            f"Prior page {page['filename']} rerun invalidated this {stage_id} continuity reference.",
            run_dir,
        )
    if is_stage_anchor_page(state, page, stage_id):
        reset_stage_anchor_review(state, stage_id, f"Stage anchor review reset because {page['filename']} was marked for rerun.")
    reset_stage_review(state, stage_id, f"Stage review reset because {page['filename']} was marked for rerun.")
    reset_following_stage_gates(state, stage_id, f"Stage gate reset because {page['filename']} was marked for rerun.")
    record_revision_scope_history(
        state,
        command="rerun",
        stage_id=stage_id,
        requested_pages=[page],
        cascade_downstream=args.cascade_downstream,
        downstream_rerun_pages=downstream_pages,
        downstream_unchanged_pages=[] if args.cascade_downstream else downstream_candidates,
        note=args.note,
    )
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"RERUN_PENDING: {page['filename']} {stage_id}")
    for downstream_page in downstream_pages:
        print(f"DOWNSTREAM_RERUN_ITEM: {downstream_page['filename']}")
    if not args.cascade_downstream:
        print_downstream_unchanged_hint(downstream_candidates)
    print("NEXT: Resolve any other current items, then run next-batch.")


def review_manifest_path(value: Any, manifest_dir: Path) -> Path:
    raw = str(value or "").strip()
    if not raw:
        raise SystemExit("Review manifest overlay entry is missing a path.")
    path = Path(raw)
    if not path.is_absolute():
        path = manifest_dir / path
    return path.resolve(strict=False)


def require_review_artifact_under_run(path: Path, run_dir: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"{label} does not exist: {path}")
    if not path_is_under(path, run_dir):
        raise SystemExit(f"{label} must be under the run folder: {path}")


def revision_overlays_from_manifest_item(item: dict[str, Any], run_dir: Path, manifest_dir: Path) -> list[dict[str, str]]:
    overlays = item.get("overlays") or []
    if not isinstance(overlays, list):
        raise SystemExit("Review manifest item overlays must be a list.")
    normalized: list[dict[str, str]] = []
    for overlay in overlays:
        if not isinstance(overlay, dict):
            raise SystemExit("Review manifest overlay entries must be objects.")
        request = str(overlay.get("request") or overlay.get("note") or "").strip()
        request_path_value = overlay.get("request_path")
        request_path = review_manifest_path(request_path_value, manifest_dir) if request_path_value else None
        if request_path is not None:
            require_review_artifact_under_run(request_path, run_dir, "Review request text file")
            if not request:
                request = request_path.read_text(encoding="utf-8").strip()
        if not request:
            raise SystemExit("Every review overlay must include non-empty request text.")
        overlay_path = review_manifest_path(overlay.get("overlay_path"), manifest_dir)
        require_review_artifact_under_run(overlay_path, run_dir, "Review overlay image")
        normalized.append(
            {
                "color_id": str(overlay.get("color_id") or "overlay"),
                "color": str(overlay.get("color") or ""),
                "overlay_path": str(overlay_path),
                "request_path": str(request_path) if request_path else "",
                "request": request,
            }
        )
    return normalized


def command_request_revisions(args: argparse.Namespace) -> None:
    manifest_path = Path(args.review_manifest).resolve(strict=False)
    manifest = load_json(manifest_path)
    run_dir_value = args.run_dir or manifest.get("run_dir")
    if not run_dir_value:
        raise SystemExit("Use --run-dir or provide run_dir in the review manifest.")
    run_dir = Path(run_dir_value)
    run_dir = run_dir.resolve(strict=False)
    state = load_state(run_dir)
    manifest_run_dir = manifest.get("run_dir")
    if manifest_run_dir and Path(manifest_run_dir).resolve(strict=False) != run_dir:
        raise SystemExit(f"Review manifest run_dir does not match --run-dir: {manifest_run_dir}")
    stage_id = args.stage or str(manifest.get("stage") or "")
    if stage_id not in STAGE_IDS:
        raise SystemExit(f"Review manifest stage must be one of: {', '.join(STAGE_IDS)}")
    items = manifest.get("items") or []
    if not isinstance(items, list) or not items:
        raise SystemExit("Review manifest must contain at least one item.")

    requested_pages: list[dict[str, Any]] = []
    updated_pages: list[dict[str, Any]] = []
    downstream_rerun_pages: list[dict[str, Any]] = []
    downstream_unchanged_pages: list[dict[str, Any]] = []
    revision_notes: list[str] = []
    manifest_dir = manifest_path.parent
    for item in items:
        if not isinstance(item, dict):
            raise SystemExit("Review manifest items must be objects.")
        page_ref = item.get("filename") or item.get("page_id") or item.get("item") or ""
        page = resolve_page(state, str(page_ref))
        overlays = revision_overlays_from_manifest_item(item, run_dir, manifest_dir)
        if not overlays:
            continue
        note_parts = []
        for overlay in overlays:
            note_parts.append(
                f"{overlay['color_id']} overlay={overlay['overlay_path']} request={overlay['request']}"
            )
        note = f"User revision overlays from {manifest_path}: " + "; ".join(note_parts)
        mark_page_stage_for_rerun(page, stage_id, note, run_dir)
        stage = stage_state(page, stage_id)
        stage["user_revision_overlays"] = overlays
        if is_stage_anchor_page(state, page, stage_id):
            reset_stage_anchor_review(
                state,
                stage_id,
                f"Stage anchor review reset because {page['filename']} received user revision overlays.",
            )
        append_unique_page(requested_pages, page)
        append_unique_page(updated_pages, page)
        revision_notes.append(note)
        downstream_candidates = downstream_prior_page_dependents(state, page, stage_id)
        if args.cascade_downstream:
            for downstream_page in mark_downstream_prior_page_dependents_for_rerun(
                state,
                page,
                stage_id,
                f"Prior page {page['filename']} revision invalidated this {stage_id} continuity reference.",
                run_dir,
            ):
                append_unique_page(updated_pages, downstream_page)
                append_unique_page(downstream_rerun_pages, downstream_page)
        else:
            for downstream_page in downstream_candidates:
                append_unique_page(downstream_unchanged_pages, downstream_page)

    if not updated_pages:
        raise SystemExit("Review manifest did not contain any overlay revision requests.")
    downstream_rerun_pages = pages_excluding(downstream_rerun_pages, requested_pages)
    downstream_unchanged_pages = pages_excluding(downstream_unchanged_pages, requested_pages)
    reset_stage_review(state, stage_id, "Stage review reset because user revision overlays requested reruns.")
    reset_following_stage_gates(state, stage_id, "Stage gate reset because user revision overlays requested reruns.")
    state.setdefault("notes", []).append(
        f"Requested revisions for {len(updated_pages)} page(s) in {stage_id} from {manifest_path}."
    )
    record_revision_scope_history(
        state,
        command="request-revisions",
        stage_id=stage_id,
        requested_pages=requested_pages,
        cascade_downstream=args.cascade_downstream,
        downstream_rerun_pages=downstream_rerun_pages,
        downstream_unchanged_pages=downstream_unchanged_pages,
        manifest=str(manifest_path),
        note=" | ".join(revision_notes),
    )
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"REVISION_REQUESTED: {stage_id}")
    print(f"MANIFEST: {manifest_path}")
    for page in requested_pages:
        print(f"RERUN_ITEM: {page['filename']}")
    if not args.cascade_downstream:
        print_downstream_unchanged_hint(downstream_unchanged_pages)
    else:
        for page in downstream_rerun_pages:
            print(f"DOWNSTREAM_RERUN_ITEM: {page['filename']}")
    print("NEXT: Resolve any other current items, then run next-batch.")


def command_stage_review(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    stage_id = args.stage
    if args.status != "needs_rerun" and args.cascade_downstream:
        raise SystemExit("--cascade-downstream is only valid when stage-review status is needs_rerun.")
    if not pages_complete_for_stage(state, stage_id):
        raise SystemExit(
            f"Stage review requires every page in {stage_id} to be parent-inspected pass or complete first."
        )

    review = state.setdefault("stage_reviews", {}).setdefault(stage_id, blank_stage_review())
    issues = as_list(args.issue)
    rerun_items = as_list(args.rerun_item)
    feedback_request = None
    transition = None

    if args.status == "pass":
        if rerun_items:
            raise SystemExit("Do not pass a stage review while rerun items are specified.")
        review["status"] = "passed"
        review["note"] = args.note
        review["issues"] = issues
        review["reviewed_at"] = now_iso()
        transition = transition_after_stage(stage_id)
        if transition and transition["to_stage"] in target_stages(state):
            feedback_request = mark_transition_waiting_for_feedback(
                state,
                run_dir,
                transition["from_stage"],
                transition["to_stage"],
                transition["pending_note"],
            )
    elif args.status == "needs_rerun":
        if not rerun_items:
            raise SystemExit("Use --rerun-item at least once when stage-review status is needs_rerun.")
        resolved_pages = []
        for item in rerun_items:
            page = resolve_page(state, item)
            append_unique_page(resolved_pages, page)
        rerun_pages = list(resolved_pages)
        downstream_rerun_pages: list[dict[str, Any]] = []
        downstream_unchanged_pages: list[dict[str, Any]] = []
        for page in rerun_pages:
            mark_page_stage_for_rerun(page, stage_id, args.note, run_dir)
            if is_stage_anchor_page(state, page, stage_id):
                reset_stage_anchor_review(
                    state,
                    stage_id,
                    f"Stage anchor review reset because {page['filename']} stage-review requested rerun.",
                )
            downstream_candidates = downstream_prior_page_dependents(state, page, stage_id)
            if args.cascade_downstream:
                for downstream_page in mark_downstream_prior_page_dependents_for_rerun(
                    state,
                    page,
                    stage_id,
                    f"Prior page {page['filename']} stage-review rerun invalidated this {stage_id} continuity reference.",
                    run_dir,
                ):
                    append_unique_page(resolved_pages, downstream_page)
                    append_unique_page(downstream_rerun_pages, downstream_page)
            else:
                for downstream_page in downstream_candidates:
                    append_unique_page(downstream_unchanged_pages, downstream_page)
        downstream_rerun_pages = pages_excluding(downstream_rerun_pages, rerun_pages)
        downstream_unchanged_pages = pages_excluding(downstream_unchanged_pages, rerun_pages)
        review["status"] = "needs_rerun"
        review["note"] = args.note
        review["issues"] = issues + [f"rerun_item={page['filename']}" for page in resolved_pages]
        review["reviewed_at"] = now_iso()
        reset_following_stage_gates(state, stage_id, f"Stage review needs rerun for {stage_id}.")
        record_revision_scope_history(
            state,
            command="stage-review",
            stage_id=stage_id,
            requested_pages=rerun_pages,
            cascade_downstream=args.cascade_downstream,
            downstream_rerun_pages=downstream_rerun_pages,
            downstream_unchanged_pages=downstream_unchanged_pages,
            note=args.note,
        )
    else:
        raise SystemExit(f"Invalid stage review status: {args.status}")

    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"STAGE_REVIEW: {stage_id}")
    print(f"STATUS: {review['status']}")
    if feedback_request and transition:
        print(f"USER_FEEDBACK_REQUIRED: {transition['from_stage']} -> {transition['to_stage']}")
        print(f"FEEDBACK_REQUEST: {feedback_request}")
        print(f"FEEDBACK_CHOICES: {transition_feedback_choices_text(transition)}")
    if rerun_items:
        for item in rerun_items:
            print(f"RERUN_ITEM: {item}")
        if args.status == "needs_rerun":
            for page in downstream_rerun_pages:
                print(f"DOWNSTREAM_RERUN_ITEM: {page['filename']}")
            if not args.cascade_downstream:
                print_downstream_unchanged_hint(downstream_unchanged_pages)


def command_approve_next_stage(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    if args.from_stage not in STAGE_IDS or args.to_stage not in STAGE_IDS:
        raise SystemExit("Unknown stage transition.")
    if previous_stage_id(args.to_stage) != args.from_stage:
        raise SystemExit(f"Unsupported stage transition: {args.from_stage} -> {args.to_stage}")
    if not stage_complete(state, args.from_stage):
        raise SystemExit(f"Cannot approve next stage until {args.from_stage} is complete.")
    if args.to_stage not in target_stages(state):
        state["target_stages"] = [stage_id for stage_id in STAGE_IDS if stage_id in set(target_stages(state) + [args.to_stage])]
    gate = state.setdefault("stage_gates", {}).setdefault(stage_gate_key(args.from_stage, args.to_stage), blank_stage_gate())
    feedback_request = assert_valid_feedback_approval(args, state, run_dir, gate)
    approved_at = now_iso()
    gate["status"] = "approved"
    gate["note"] = args.note
    gate["updated_at"] = approved_at
    gate["feedback_request"] = resolved_path_string(feedback_request)
    gate["feedback_choice"] = args.feedback_choice
    gate["feedback_approved_at"] = approved_at
    state.setdefault("notes", []).append(
        f"Approved next stage {args.from_stage}->{args.to_stage} from {feedback_request}: {args.note}"
    )
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"NEXT_STAGE_APPROVED: {args.from_stage} -> {args.to_stage}")
    next_limit = 1 if sequential_prior_pages_mode(state) else 4
    print(f"NEXT: comic_storyboard_runner.py next-batch --run-dir <run-dir> --limit {next_limit}")


def command_stop_after_stage(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    if not stage_complete(state, args.stage):
        raise SystemExit(f"Cannot stop after {args.stage} until that stage is complete.")
    stop_index = STAGE_IDS.index(args.stage)
    state["target_stages"] = STAGE_IDS[: stop_index + 1]
    transition = transition_after_stage(args.stage)
    if transition:
        gate = state.setdefault("stage_gates", {}).setdefault(transition_gate_key(transition), blank_stage_gate())
        gate["status"] = "stopped"
        gate["note"] = args.note
        gate["updated_at"] = now_iso()
        gate["feedback_choice"] = FEEDBACK_CHOICE_STOP_AFTER_STAGE
    state.setdefault("notes", []).append(f"Stopped after {args.stage}: {args.note}")
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"STOPPED_AFTER_STAGE: {args.stage}")
    print(f"TARGET_STAGES: {', '.join(state['target_stages'])}")


def command_import_prior_stage(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    if args.stage == FINISH_STAGE:
        raise SystemExit("import-prior-stage is for stages before finish, not finish itself.")
    page = resolve_page(state, args.item)
    generated = Path(args.generated)
    if not generated.exists():
        raise SystemExit(f"Generated file not found: {generated}")
    destination = stage_output_path(run_dir, page, args.stage)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if generated.resolve(strict=False) != destination.resolve(strict=False):
        shutil.copy2(generated, destination)
    stage = stage_state(page, args.stage)
    if args.stage == STORYBOARD_CONTI_SKETCH_INK_STAGE:
        if not args.description:
            raise SystemExit("import-prior-stage for storyboard_conti_sketch_ink requires --description <desc.md>.")
        description_source = Path(args.description)
        if not description_source.exists():
            raise SystemExit(f"Conti/sketch/ink description file not found: {description_source}")
        description_destination = stage_description_path(run_dir, page, args.stage)
        description_destination.parent.mkdir(parents=True, exist_ok=True)
        if description_source.resolve(strict=False) != description_destination.resolve(strict=False):
            shutil.copy2(description_source, description_destination)
        validate_stage_description(description_destination, page)
        stage["description_path"] = str(description_destination)
        stage["description_source"] = str(description_source)
        stage["description_imported_at"] = now_iso()
    stage["status"] = "inspected_pass"
    stage["generated_source"] = str(generated)
    stage["output_path"] = str(destination)
    stage["external_prior_stage"] = True
    stage["parent_note"] = args.note
    stage["imported_at"] = now_iso()
    stage["inspected_at"] = now_iso()
    state.setdefault("notes", []).append(f"Imported external prior-stage reference for {page['filename']}:{args.stage}.")
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"IMPORTED_PRIOR_STAGE: {page['filename']} {args.stage}")
    print(f"OUTPUT: {destination}")


def command_batch_status(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    batch = next((entry for entry in state.get("batches", []) if entry.get("id") == args.batch_id), None)
    if not batch:
        raise SystemExit(f"Unknown batch: {args.batch_id}")
    stage_id = batch.get("stage")
    print(f"BATCH_ID: {args.batch_id}")
    print(f"STAGE: {stage_id}")
    for page_id in batch.get("pages", []):
        page = resolve_page(state, page_id)
        stage = stage_state(page, stage_id)
        print(f"- {page['filename']}: {stage.get('status')} worker={stage.get('worker_status', '')}")


def command_status(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    print(f"RUN_DIR: {run_dir}")
    print(f"PLAN_APPROVED: {state.get('plan_approved')}")
    print(f"PAGES: {len(state.get('pages', []))}")
    print(f"TARGET_STAGES: {', '.join(target_stages(state))}")
    print(f"PAGE_GENERATION_MODE: {page_generation_mode(state)}")
    print(f"CURRENT_STAGE: {current_stage_id(state) or 'complete'}")
    for stage_id in STAGE_IDS:
        counts: dict[str, int] = {}
        for page in state.get("pages", []):
            status = stage_state(page, stage_id).get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        parts = ", ".join(f"{status}={counts[status]}" for status in sorted(counts)) or "none"
        print(f"{stage_id}: {parts}")
        review = state.get("stage_reviews", {}).get(stage_id, blank_stage_review())
        print(f"{stage_id}_review: {review.get('status', 'pending')}")
        anchor_review = state.get("stage_anchor_reviews", {}).get(stage_id, blank_stage_anchor_review())
        print(f"{stage_id}_anchor_review: {anchor_review.get('status', 'pending')}")
        if anchor_review.get("anchor_item"):
            print(f"{stage_id}_anchor_item: {anchor_review.get('anchor_item')}")
    for key, gate in state.get("stage_gates", {}).items():
        print(f"{key}_gate: {gate.get('status', 'pending')}")
        if gate.get("feedback_request"):
            print(f"{key}_feedback_request: {gate.get('feedback_request')}")
        if gate.get("feedback_choice"):
            print(f"{key}_feedback_choice: {gate.get('feedback_choice')}")
    blockers = current_blockers(state)
    if blockers:
        print("CURRENT_BLOCKERS:")
        for page, stage_id, stage in blockers:
            print(f"- {page['filename']}:{stage_id}: {stage.get('status')}")
    print(f"COMPLETE: {str(workflow_complete(state)).lower()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage create-comic-storyboard-pack state.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--title", default="")
    init.add_argument("--scenario", default="")
    init.add_argument("--scenario-summary", default="")
    init.add_argument("--output-root", default="")
    init.set_defaults(func=command_init)

    spatial_check = subparsers.add_parser("spatial-check")
    spatial_check.add_argument("--run-dir", default="")
    spatial_check.add_argument("--plan-file", default="")
    spatial_check.add_argument("--plan-json", default="")
    spatial_check.set_defaults(func=command_spatial_check)

    spatial_preview = subparsers.add_parser("spatial-preview")
    spatial_preview.add_argument("--run-dir", default="")
    spatial_preview.add_argument("--plan-file", default="")
    spatial_preview.add_argument("--plan-json", default="")
    spatial_preview.add_argument("--output", default="")
    spatial_preview.set_defaults(func=command_spatial_preview)

    spatial_render_manifest = subparsers.add_parser("spatial-render-manifest")
    spatial_render_manifest.add_argument("--run-dir", default="")
    spatial_render_manifest.add_argument("--plan-file", default="")
    spatial_render_manifest.add_argument("--stage", choices=STAGE_IDS, default="")
    spatial_render_manifest.add_argument("--output-dir", default="")
    spatial_render_manifest.set_defaults(func=command_spatial_render_manifest)

    approve = subparsers.add_parser("approve-plan")
    approve.add_argument("--run-dir", required=True)
    approve.add_argument("--plan-file", default="")
    approve.add_argument("--plan-json", default="")
    approve.add_argument("--target-stage", choices=STAGE_IDS, default="")
    approve.set_defaults(func=command_approve_plan)

    next_batch = subparsers.add_parser("next-batch")
    next_batch.add_argument("--run-dir", required=True)
    next_batch.add_argument("--limit", type=int, default=4)
    next_batch.set_defaults(func=command_next_batch)

    import_cmd = subparsers.add_parser("import")
    import_cmd.add_argument("--run-dir", required=True)
    import_cmd.add_argument("--item", required=True)
    import_cmd.add_argument("--stage", choices=STAGE_IDS, required=True)
    import_cmd.add_argument("--generated", required=True)
    import_cmd.add_argument("--description", default="")
    import_cmd.add_argument("--worker-status", choices=sorted(WORKER_STATUS_VALUES), required=True)
    import_cmd.add_argument("--worker-note", required=True)
    import_cmd.set_defaults(func=command_import)

    inspect_pass = subparsers.add_parser("inspect-pass")
    inspect_pass.add_argument("--run-dir", required=True)
    inspect_pass.add_argument("--item", required=True)
    inspect_pass.add_argument("--stage", choices=STAGE_IDS, required=True)
    inspect_pass.add_argument("--note", required=True)
    inspect_pass.add_argument("--spatial-verdict", choices=sorted(SPATIAL_VERDICT_VALUES), default="pass")
    inspect_pass.add_argument("--spatial-note", default="")
    inspect_pass.add_argument("--reconciliation-note", default="")
    inspect_pass.set_defaults(func=command_inspect_pass)

    anchor_review = subparsers.add_parser("anchor-review")
    anchor_review.add_argument("--run-dir", required=True)
    anchor_review.add_argument("--stage", choices=STAGE_IDS, required=True)
    anchor_review.add_argument("--item", required=True)
    anchor_review.add_argument("--status", choices=sorted(ANCHOR_REVIEW_CLI_STATUSES), required=True)
    anchor_review.add_argument("--note", required=True)
    anchor_review.add_argument("--issue", action="append", default=[])
    anchor_review.set_defaults(func=command_anchor_review)

    rerun = subparsers.add_parser("rerun")
    rerun.add_argument("--run-dir", required=True)
    rerun.add_argument("--item", required=True)
    rerun.add_argument("--stage", choices=STAGE_IDS, required=True)
    rerun.add_argument("--note", required=True)
    rerun.add_argument("--cascade-downstream", action="store_true")
    rerun.set_defaults(func=command_rerun)

    request_revisions = subparsers.add_parser("request-revisions")
    request_revisions.add_argument("--run-dir", default="")
    request_revisions.add_argument("--stage", choices=STAGE_IDS, default="")
    request_revisions.add_argument("--review-manifest", required=True)
    request_revisions.add_argument("--cascade-downstream", action="store_true")
    request_revisions.set_defaults(func=command_request_revisions)

    stage_review = subparsers.add_parser("stage-review")
    stage_review.add_argument("--run-dir", required=True)
    stage_review.add_argument("--stage", choices=STAGE_IDS, required=True)
    stage_review.add_argument("--status", choices=sorted(REVIEW_CLI_STATUSES), required=True)
    stage_review.add_argument("--note", required=True)
    stage_review.add_argument("--issue", action="append", default=[])
    stage_review.add_argument("--rerun-item", action="append", default=[])
    stage_review.add_argument("--cascade-downstream", action="store_true")
    stage_review.set_defaults(func=command_stage_review)

    approve_next = subparsers.add_parser("approve-next-stage")
    approve_next.add_argument("--run-dir", required=True)
    approve_next.add_argument("--from-stage", choices=STAGE_IDS, required=True)
    approve_next.add_argument("--to-stage", choices=STAGE_IDS, required=True)
    approve_next.add_argument("--feedback-request", required=True)
    approve_next.add_argument(
        "--feedback-choice",
        choices=[transition["approve_choice"] for transition in TRANSITIONS],
        required=True,
    )
    approve_next.add_argument("--note", required=True)
    approve_next.set_defaults(func=command_approve_next_stage)

    stop_after = subparsers.add_parser("stop-after-stage")
    stop_after.add_argument("--run-dir", required=True)
    stop_after.add_argument("--stage", choices=STAGE_IDS, required=True)
    stop_after.add_argument("--note", required=True)
    stop_after.set_defaults(func=command_stop_after_stage)

    import_prior = subparsers.add_parser("import-prior-stage")
    import_prior.add_argument("--run-dir", required=True)
    import_prior.add_argument("--item", required=True)
    import_prior.add_argument("--stage", choices=STAGE_IDS, required=True)
    import_prior.add_argument("--generated", required=True)
    import_prior.add_argument("--description", default="")
    import_prior.add_argument("--note", required=True)
    import_prior.set_defaults(func=command_import_prior_stage)

    batch_status = subparsers.add_parser("batch-status")
    batch_status.add_argument("--run-dir", required=True)
    batch_status.add_argument("--batch-id", required=True)
    batch_status.set_defaults(func=command_batch_status)

    status = subparsers.add_parser("status")
    status.add_argument("--run-dir", required=True)
    status.set_defaults(func=command_status)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
