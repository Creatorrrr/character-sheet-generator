#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
STORYBOARD_SKETCH_INK_STAGE = "storyboard_sketch_ink"
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
        "id": STORYBOARD_SKETCH_INK_STAGE,
        "label": "storyboard/sketch/ink",
        "dir": "01_storyboard_sketch_ink",
        "purpose": "comic page storyboard, panel layout, policy-approved text/SFX placement or text absence, sketch, and ink line pass",
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
    STORYBOARD_SKETCH_INK_STAGE: "create-comic-storyboard-sketch-ink",
    FINISH_STAGE: "create-comic-storyboard-finish",
}
STAGE_GATE_STATUSES = {"pending", "pending_user_feedback", "approved", "stopped"}
PASS_STATUSES = {"inspected_pass", "complete"}
CURRENT_STATUSES = {"generation_requested", "imported"}
VALID_STATUSES = {"pending", "generation_requested", "imported", "inspected_pass", "complete"}
WORKER_STATUS_VALUES = {"pass", "needs_rerun"}
REVIEW_STATUSES = {"pending", "passed", "needs_rerun"}
REVIEW_CLI_STATUSES = {"pass", "needs_rerun"}
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


def merge_unique(*values: Any) -> list[str]:
    merged: list[str] = []
    for value in values:
        for item in as_list(value):
            item = item.strip()
            if item and item not in merged:
                merged.append(item)
    return merged


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
        "generated_source": "",
        "external_prior_stage": False,
        "worker_status": "",
        "worker_note": "",
        "parent_note": "",
        "current_rerun_correction": "",
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


def stage_gate_key(from_stage: str, to_stage: str) -> str:
    return f"{from_stage}_to_{to_stage}"


def blank_stage_gate() -> dict[str, Any]:
    return {
        "status": "pending",
        "note": "",
        "updated_at": "",
    }


def build_stage_gates() -> dict[str, dict[str, Any]]:
    return {stage_gate_key(STORYBOARD_SKETCH_INK_STAGE, FINISH_STAGE): blank_stage_gate()}


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


def normalize_stage_review(review: dict[str, Any], stage_id: str) -> None:
    for key, value in blank_stage_review().items():
        review.setdefault(key, value)
    review["issues"] = as_list(review.get("issues"))
    if review["status"] not in REVIEW_STATUSES:
        raise SystemExit(f"Invalid stage review status for {stage_id}: {review['status']}")


def normalize_stage_record(stage: dict[str, Any], page_id: str, stage_id: str) -> None:
    for key, value in blank_stage_state().items():
        stage.setdefault(key, value)
    if stage["status"] not in VALID_STATUSES:
        raise SystemExit(f"Invalid stage status for {page_id}:{stage_id}: {stage['status']}")


def migrate_legacy_stage_records(stages: dict[str, Any]) -> None:
    if STORYBOARD_SKETCH_INK_STAGE not in stages:
        legacy_sketch = stages.get("sketch_ink")
        if isinstance(legacy_sketch, dict) and legacy_sketch.get("status") in PASS_STATUSES:
            stages[STORYBOARD_SKETCH_INK_STAGE] = dict(legacy_sketch)
        else:
            stages[STORYBOARD_SKETCH_INK_STAGE] = blank_stage_state()

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
    state["stage_order"] = STAGE_IDS
    normalize_target_stages(state)
    normalize_stage_gates(state)
    state["source_references"] = validate_reference_paths(state.get("source_references", []))
    stage_reviews = state.setdefault("stage_reviews", {})
    for stage_id in list(stage_reviews.keys()):
        if stage_id not in STAGE_IDS:
            del stage_reviews[stage_id]
    for stage_id in STAGE_IDS:
        review = stage_reviews.setdefault(stage_id, {})
        normalize_stage_review(review, stage_id)
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
        page.setdefault("spatial_logic_notes", "")
        page.setdefault("motion_checks", [])
        page.setdefault("must_match", [])
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


def stage_output_path(run_dir: Path, page: dict[str, Any], stage_id: str) -> Path:
    return run_dir / stage_meta(stage_id)["dir"] / page["filename"]


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


def prior_stage_reference(run_dir: Path, page: dict[str, Any], stage_id: str) -> str:
    prior = previous_stage_id(stage_id)
    if not prior:
        return "none"
    path = stage_output_path(run_dir, page, prior)
    if stage_id == FINISH_STAGE:
        marker = "required visual input / structure reference from storyboard_sketch_ink"
        return f"{path} ({marker})" if path.exists() else f"{path} ({marker}; not found yet)"
    return str(path) if path.exists() else f"{path} (not found yet)"


def assert_required_prior_stage_outputs_exist(state: dict[str, Any], run_dir: Path, pages: list[dict[str, Any]], stage_id: str) -> None:
    if stage_id != FINISH_STAGE:
        return
    missing = []
    for page in pages:
        if not page_complete_for_stage(page, STORYBOARD_SKETCH_INK_STAGE):
            missing.append(f"{page['filename']} needs parent-inspected storyboard_sketch_ink before finish")
            continue
        path = stage_output_path(run_dir, page, STORYBOARD_SKETCH_INK_STAGE)
        if not path.exists():
            missing.append(f"{page['filename']} requires {path}")
    if missing:
        details = "; ".join(missing)
        raise SystemExit(
            "Finish stage requires the parent-inspected storyboard_sketch_ink image as input before reservation: "
            f"{details}"
        )
    if not stage_review_passed(state, STORYBOARD_SKETCH_INK_STAGE):
        raise SystemExit(
            "Finish stage requires storyboard_sketch_ink stage-review pass before reservation."
        )


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


def reset_following_stage_gates(state: dict[str, Any], stage_id: str, note: str) -> None:
    if stage_id == STORYBOARD_SKETCH_INK_STAGE:
        gate = state.setdefault("stage_gates", {}).setdefault(
            stage_gate_key(STORYBOARD_SKETCH_INK_STAGE, FINISH_STAGE),
            blank_stage_gate(),
        )
        gate["status"] = "pending"
        gate["note"] = note
        gate["updated_at"] = now_iso()


def mark_transition_waiting_for_feedback(state: dict[str, Any], from_stage: str, to_stage: str, note: str) -> None:
    if to_stage not in target_stages(state):
        return
    gate = state.setdefault("stage_gates", {}).setdefault(stage_gate_key(from_stage, to_stage), blank_stage_gate())
    if gate.get("status") != "approved":
        gate["status"] = "pending_user_feedback"
        gate["note"] = note
        gate["updated_at"] = now_iso()


def transition_gate_allows(state: dict[str, Any], from_stage: str, to_stage: str) -> bool:
    gate = state.setdefault("stage_gates", {}).setdefault(stage_gate_key(from_stage, to_stage), blank_stage_gate())
    return gate.get("status") == "approved"


def mark_page_stage_for_rerun(page: dict[str, Any], stage_id: str, note: str) -> None:
    stage = stage_state(page, stage_id)
    if stage.get("status") not in {"pending", "generation_requested", "imported", "inspected_pass", "complete"}:
        raise SystemExit(f"Cannot rerun page stage in status {stage.get('status')}: {page['filename']} {stage_id}")
    history = stage.setdefault("rerun_history", [])
    history.append(
        {
            "at": now_iso(),
            "from_status": stage.get("status"),
            "note": note,
            "output_path": stage.get("output_path", ""),
            "worker_status": stage.get("worker_status", ""),
            "worker_note": stage.get("worker_note", ""),
        }
    )
    stage["status"] = "pending"
    stage["rerun_pending"] = True
    stage["batch_id"] = ""
    stage["requested_at"] = ""
    stage["worker_status"] = ""
    stage["worker_note"] = ""
    stage["parent_note"] = note
    stage["current_rerun_correction"] = note


def stage_instruction(stage_id: str) -> str:
    if stage_id == STORYBOARD_SKETCH_INK_STAGE:
        return (
            "Create the combined Korean comic-book page storyboard, sketch, and ink pass. Show a full "
            "page with 3-5 panels by default, measured cinematic pacing, experimental freeform panel "
            "design, gutters or open borders where appropriate, clear reading order, active-text-policy "
            "placement or required text absence, clear action blocking, planned detail "
            "density, visual emphasis, comic effect lines, line-weight contrast, and clean ink lines. "
            "Use 1-2 panels for special staging such as a full-page emotion beat, silence, stillness, "
            "or a decisive action moment."
        )
    if stage_id == FINISH_STAGE:
        return (
            "Create the final Korean comic-book page using the required parent-inspected "
            "storyboard_sketch_ink image as the visual input and structure reference. Add tones, color "
            "if requested, lighting, shadows, policy-approved lettering/SFX or required text absence, "
            "and cleanup without changing page layout, panel count, freeform panel shapes, negative "
            "space, text placement or text absence, comic effect lines, visual emphasis, line-weight rhythm, "
            "character/object blocking, motion direction, or action logic. Finish must preserve the inspected "
            "storyboard_sketch_ink eye, face, hand, limb, silhouette, body proportion, and posture structure."
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
    text_policy_lines = text_policy_instruction_lines(text_policy, page)
    text_policy_worker_checks = text_policy_worker_check_lines(text_policy)
    character_locks = page_policy_items(state, page, "character_locks")
    visual_text_guard = page_policy_items(state, page, "visual_text_guard")
    appearance_anatomy_lock = DEFAULT_APPEARANCE_ANATOMY_LOCK_NOTES
    stage = stage_state(page, stage_id)
    rerun_correction = current_rerun_correction(stage)
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
    prior_stage_use_requirement = (
        "Use the prior-stage image above as the required visual input / structure reference. "
        "Do not redraw the page from scratch or change the approved panel layout."
        if stage_id == FINISH_STAGE
        else "No prior-stage image is used for storyboard_sketch_ink; generate the approved page structure, sketch, and ink pass from the approved plan and allowed source references."
    )
    negative = page.get("negative_prompt") or (
        "low resolution, watermark, random logo, unrelated captions, garbled lettering, unreadable "
        "speech balloons, duplicated limbs, broken perspective, impossible object motion, ball moving "
        "opposite the throw or shot, inconsistent character design, inconsistent setting, wrong costume, "
        "cropped key action, blurry subject, over-smoothed AI texture."
    )
    negative_terms = merge_unique(
        negative,
        text_policy_negative_terms(text_policy),
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
            f"Page id: {page['id']}",
            f"Page number: {page.get('page_no', page.get('order', ''))}",
            f"Reading order: {page.get('reading_order') or state.get('reading_order') or 'right-to-left or top-to-bottom as approved'}",
            f"Scene refs: {', '.join(page.get('scene_refs', [])) or 'unspecified'}",
            f"Prior stage reference: {prior_stage_reference(run_dir, page, stage_id)}",
            "",
            "Stage instruction:",
            stage_instruction(stage_id),
            "",
            "Prior-stage use requirement:",
            prior_stage_use_requirement,
            "",
            "Page format:",
            "Generate one complete Korean comic-book page image with 3-5 panels by default and measured cinematic pacing. Use 1-2 panels for special staging such as full-page emotional beats, silence, stillness, or decisive action moments. Use experimental freeform panel design by default: diagonal panels, asymmetry, tall vertical panels, open or borderless panels, inset panels, partial overlaps, and wide negative space are allowed when reading order and continuity stay clear. Avoid a uniform rectangular grid unless the user requested it or the scene clearly benefits from it.",
            "",
            "Page layout brief:",
            page.get("layout_brief") or page.get("visual_brief") or page.get("prompt") or "",
            "",
            "Page pacing and panel shape policy:",
            pacing_notes,
            panel_shape_notes,
            negative_space_notes,
            "",
            "Comic visual direction:",
            detail_density_notes,
            visual_emphasis_notes,
            comic_effects_notes,
            "For storyboard_sketch_ink, draw planned speed lines, focus lines, impact bursts, emotion lines, motion streaks, line-weight contrast, and ink emphasis directly in the sketch/ink pass when they serve the beat.",
            "For finish, preserve the inspected storyboard_sketch_ink visual emphasis, effect-line direction, and ink rhythm; tone/color must not weaken or cover them.",
            "",
            "Page text policy:",
            *text_policy_lines,
            "",
            "Page dialogue notes:",
            page_dialogue_notes
            if text_policy == TEXT_POLICY_DIALOGUE_SFX_CAPTIONS
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
            "Panels on this page:",
            panel_text,
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
            "- During finish, preserve the inspected storyboard_sketch_ink eye, face, hand, limb, silhouette, body proportion, and posture structure",
            "- Enforces every Visual text guard item listed above; reject arbitrary environmental text, labels, signs, or corner text when forbidden",
            "- Preserves story beat, reading order, composition, and continuity",
            "- Preserves source-data consistency for characters, props, profiles, locations, and page-layout references",
            "- Preserves panel-to-panel and adjacent-page continuity for character/object placement, gaze, action direction, time flow, and lettering placement",
            "- Keeps prior-stage structure unchanged when a prior-stage reference exists, especially during finish",
            "- Character/object positions, action direction, object trajectory, and cause-effect motion are physically plausible",
            "- No examples of impossible staging such as a basketball shot where the ball travels behind the shooter",
            "- Has no obvious anatomy, perspective, crop, object, or continuity defects",
            "",
            "Negative prompt:",
            negative_prompt_text,
            "",
            "Return only: generated file path, worker_status, worker_note.",
        ]
    )


def subagent_prompt_text(run_dir: Path, page: dict[str, Any], stage_id: str, state: dict[str, Any]) -> str:
    stage = stage_state(page, stage_id)
    references = validate_reference_paths(as_list(state.get("source_references")) + as_list(page.get("references")))
    reference_text = "\n".join(f"- {ref}" for ref in references) or "- none"
    skill_name = STAGE_SKILL_NAMES[stage_id]
    text_policy = normalize_text_policy(page.get("text_policy") or state.get("text_policy"))
    character_locks = page_policy_items(state, page, "character_locks")
    visual_text_guard = page_policy_items(state, page, "visual_text_guard")
    appearance_anatomy_lock = DEFAULT_APPEARANCE_ANATOMY_LOCK_NOTES
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
            f"Batch id: {stage.get('batch_id')}",
            f"Default source folder: {state.get('source_root') or DEFAULT_SOURCE_ROOT}",
            f"Excluded source folder: {', '.join(state.get('excluded_source_roots') or [str(DEFAULT_OUTPUT_ROOT)])}",
            f"Prior-stage reference: {prior_stage_reference(run_dir, page, stage_id)}",
            "Relevant references:",
            reference_text,
            f"Page text policy: {text_policy}",
            "Character locks:",
            bullet_text(character_locks),
            "Character appearance/anatomy lock:",
            appearance_anatomy_lock,
            "Visual text guard:",
            bullet_text(visual_text_guard),
            "Current rerun correction:",
            current_rerun_correction(stage) or "- none",
            "",
            "Use image_gen with the assigned prompt file and visual references. Inspect the output for stage fit, page/story fit, multi-panel layout, active text_policy compliance, character_locks, character appearance/anatomy lock, visual_text_guard, spatial continuity, motion plausibility, technical quality, and obvious defects.",
            "Return only:",
            "- generated file path",
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
        "",
        "Generation policy:",
        "- Use Codex built-in image_gen only through one subagent per reserved page.",
        "- Do not reserve images before approve-plan.",
        f"- Use {state.get('source_root') or DEFAULT_SOURCE_ROOT} as the default source data folder when the user did not specify source/reference paths.",
        f"- Do not use {', '.join(state.get('excluded_source_roots') or [str(DEFAULT_OUTPUT_ROOT)])} or any output/ subtree as source/reference data.",
        "- Generate stages in order: storyboard_sketch_ink, finish.",
        "- Do not reserve finish until every page has passed storyboard_sketch_ink parent inspection.",
        "- Do not reserve finish until storyboard_sketch_ink stage-review has passed and the user has approved the next stage with approve-next-stage.",
        "- Finish must use the parent-inspected storyboard_sketch_ink image as the required visual input / structure reference.",
        "- Use 3-5 panels by default with measured cinematic pacing; use 1-2 panels for special staging; six or more panels need clear story justification.",
        "- Use experimental freeform panel design by default and avoid unintentional uniform rectangular grids.",
        "- Plan and verify comic visual direction: detail density, visual emphasis, line-weight rhythm, and speed/focus/impact/emotion lines when the beat calls for them.",
        "- Plan and verify character appearance/anatomy locks: species/body structure, face structure, eye count and placement, hand/finger/arm/leg count, silhouette, body proportions, and posture.",
        "- Unless explicitly approved by the plan or source, reject missing/extra/merged eyes, one-eyed appearance for a two-eyed character, one-eyed face unless explicitly approved, missing/extra limbs or fingers, changed species/body type, broken joints, or broken body proportions.",
        f"- Text policy: {text_policy}. {text_policy_batch_summary(text_policy)}",
        "- Reserve at most four pages per batch.",
        "- Parent inspection is required before a page stage counts as passed.",
        "- Stage finish review is required after all page stages pass; next stage opens only after stage-review pass.",
        "- Stage finish review checks source consistency against characters, props, profiles, sources/ references, character appearance/anatomy locks, and panel/page continuity.",
        "- Worker and parent inspection must reject implausible spatial layout, object motion, or cause-effect direction.",
        "",
    ]
    for lock in state.get("character_locks", []):
        lines.append(f"- Character lock: {lock}")
    for guard in state.get("visual_text_guard", []):
        lines.append(f"- Visual text guard: {guard}")
    lines.append("")
    lines.extend(["Stage gates:", ""])
    for key, gate in state.get("stage_gates", {}).items():
        lines.extend(
            [
                f"- {key}: {gate.get('status', 'pending')}",
                f"  note: {gate.get('note', '')}",
                f"  updated_at: {gate.get('updated_at', '')}",
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
                f"  dialogue_notes: {page.get('page_dialogue_notes') or ''}",
                f"  spatial_logic: {page.get('spatial_logic_notes') or ''}",
                f"  dependencies: {', '.join(page.get('dependencies', [])) or 'none'}",
                f"  stages: {stage_summary}",
                "",
            ]
        )
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
        "stage_order": STAGE_IDS,
        "target_stages": STAGE_IDS,
        "stage_reviews": build_stage_reviews(),
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
        "spatial_logic_notes": str(raw.get("spatial_logic_notes") or ""),
        "motion_checks": as_list(raw.get("motion_checks")),
        "must_match": as_list(raw.get("must_match")),
        "references": validate_reference_paths(raw.get("references") or raw.get("reference_paths")),
        "prompt": str(raw.get("prompt") or raw.get("layout_brief") or raw.get("visual_brief") or ""),
        "negative_prompt": str(raw.get("negative_prompt") or ""),
        "dependencies": as_list(raw.get("dependencies")),
        "notes": str(raw.get("notes") or ""),
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
    state["title"] = plan.get("scenario_title") or plan.get("story_title") or state.get("title")
    state["style_brief"] = str(plan.get("style_brief") or "")
    state["reading_order"] = str(plan.get("reading_order") or "right-to-left or top-to-bottom as approved")
    state["source_root"] = str(DEFAULT_SOURCE_ROOT)
    state["excluded_source_roots"] = [str(DEFAULT_OUTPUT_ROOT)]
    state["source_references"] = validate_reference_paths(plan.get("references") or plan.get("reference_paths"))
    state["text_policy"] = normalize_text_policy(plan.get("text_policy"))
    state["character_locks"] = merge_unique(plan.get("character_locks"))
    state["visual_text_guard"] = merge_unique(plan.get("visual_text_guard"))
    state["plan_approved"] = True
    state["approved_at"] = now_iso()
    state["target_stages"] = [args.target_stage] if args.target_stage else list(STAGE_IDS)
    state["pages"] = pages
    state.pop("panels", None)
    state["batches"] = []
    state["stage_reviews"] = build_stage_reviews()
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
            "target_stages": state.get("target_stages", STAGE_IDS),
            "pages": state.get("pages", []),
        },
    )
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"APPROVED_PAGES: {len(pages)}")
    print(f"PLAN: {run_dir / 'approved_storyboard_plan.json'}")
    print("NEXT: comic_storyboard_runner.py next-batch --run-dir <run-dir> --limit 4")


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
        candidates.append(page)
    candidates.sort(key=lambda page: page_sort_key(page, stage_id))

    if not candidates:
        if pages_complete_for_stage(state, stage_id) and not stage_review_passed(state, stage_id):
            print(f"STAGE_REVIEW_REQUIRED: {stage_id}")
        print("NO_ELIGIBLE_ITEMS")
        command_status(args)
        return

    limit = min(max(args.limit, 1), 4)
    selected = candidates[:limit]
    assert_required_prior_stage_outputs_exist(state, run_dir, selected, stage_id)
    if stage_id == FINISH_STAGE and not transition_gate_allows(state, STORYBOARD_SKETCH_INK_STAGE, FINISH_STAGE):
        gate = state.get("stage_gates", {}).get(
            stage_gate_key(STORYBOARD_SKETCH_INK_STAGE, FINISH_STAGE),
            blank_stage_gate(),
        )
        if gate.get("status") == "pending":
            mark_transition_waiting_for_feedback(
                state,
                STORYBOARD_SKETCH_INK_STAGE,
                FINISH_STAGE,
                "storyboard_sketch_ink passed; user feedback is required before finish.",
            )
            write_batch_plan(run_dir, state)
            save_state(run_dir, state)
        print("USER_FEEDBACK_REQUIRED: storyboard_sketch_ink -> finish")
        print(f"GATE_STATUS: {gate.get('status', 'pending_user_feedback')}")
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
        stage["current_rerun_correction"] = rerun_correction
        prompt_path = stage_prompt_path(run_dir, page, stage_id)
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text(run_dir, page, stage_id, state), encoding="utf-8")
        stage["prompt_file"] = str(prompt_path)
        stage["output_path"] = str(stage_output_path(run_dir, page, stage_id))
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
    stage["status"] = "imported"
    stage["generated_source"] = str(generated)
    stage["output_path"] = str(destination)
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
    output = stage_output_path(run_dir, page, stage_id)
    if not output.exists():
        raise SystemExit(f"Output file does not exist: {output}")
    stage["status"] = "inspected_pass"
    stage["parent_note"] = args.note
    stage["inspected_at"] = now_iso()
    stage["output_path"] = str(output)
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"INSPECTED_PASS: {page['filename']} {stage_id}")


def command_rerun(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    page = resolve_page(state, args.item)
    stage_id = args.stage
    mark_page_stage_for_rerun(page, stage_id, args.note)
    reset_stage_review(state, stage_id, f"Stage review reset because {page['filename']} was marked for rerun.")
    reset_following_stage_gates(state, stage_id, f"Stage gate reset because {page['filename']} was marked for rerun.")
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"RERUN_PENDING: {page['filename']} {stage_id}")
    print("NEXT: Resolve any other current items, then run next-batch.")


def command_stage_review(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    stage_id = args.stage
    if not pages_complete_for_stage(state, stage_id):
        raise SystemExit(
            f"Stage review requires every page in {stage_id} to be parent-inspected pass or complete first."
        )

    review = state.setdefault("stage_reviews", {}).setdefault(stage_id, blank_stage_review())
    issues = as_list(args.issue)
    rerun_items = as_list(args.rerun_item)

    if args.status == "pass":
        if rerun_items:
            raise SystemExit("Do not pass a stage review while rerun items are specified.")
        review["status"] = "passed"
        review["note"] = args.note
        review["issues"] = issues
        review["reviewed_at"] = now_iso()
        if stage_id == STORYBOARD_SKETCH_INK_STAGE:
            mark_transition_waiting_for_feedback(
                state,
                STORYBOARD_SKETCH_INK_STAGE,
                FINISH_STAGE,
                "storyboard_sketch_ink stage-review passed; user feedback is required before finish.",
            )
    elif args.status == "needs_rerun":
        if not rerun_items:
            raise SystemExit("Use --rerun-item at least once when stage-review status is needs_rerun.")
        resolved_pages = []
        for item in rerun_items:
            page = resolve_page(state, item)
            resolved_pages.append(page)
        for page in resolved_pages:
            mark_page_stage_for_rerun(page, stage_id, args.note)
        review["status"] = "needs_rerun"
        review["note"] = args.note
        review["issues"] = issues + [f"rerun_item={page['filename']}" for page in resolved_pages]
        review["reviewed_at"] = now_iso()
        reset_following_stage_gates(state, stage_id, f"Stage review needs rerun for {stage_id}.")
    else:
        raise SystemExit(f"Invalid stage review status: {args.status}")

    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"STAGE_REVIEW: {stage_id}")
    print(f"STATUS: {review['status']}")
    if rerun_items:
        for item in rerun_items:
            print(f"RERUN_ITEM: {item}")


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
    gate["status"] = "approved"
    gate["note"] = args.note
    gate["updated_at"] = now_iso()
    state.setdefault("notes", []).append(f"Approved next stage {args.from_stage}->{args.to_stage}: {args.note}")
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"NEXT_STAGE_APPROVED: {args.from_stage} -> {args.to_stage}")
    print("NEXT: comic_storyboard_runner.py next-batch --run-dir <run-dir> --limit 4")


def command_stop_after_stage(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    if not stage_complete(state, args.stage):
        raise SystemExit(f"Cannot stop after {args.stage} until that stage is complete.")
    stop_index = STAGE_IDS.index(args.stage)
    state["target_stages"] = STAGE_IDS[: stop_index + 1]
    if args.stage == STORYBOARD_SKETCH_INK_STAGE:
        gate = state.setdefault("stage_gates", {}).setdefault(
            stage_gate_key(STORYBOARD_SKETCH_INK_STAGE, FINISH_STAGE),
            blank_stage_gate(),
        )
        gate["status"] = "stopped"
        gate["note"] = args.note
        gate["updated_at"] = now_iso()
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
    for key, gate in state.get("stage_gates", {}).items():
        print(f"{key}_gate: {gate.get('status', 'pending')}")
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
    import_cmd.add_argument("--worker-status", choices=sorted(WORKER_STATUS_VALUES), required=True)
    import_cmd.add_argument("--worker-note", required=True)
    import_cmd.set_defaults(func=command_import)

    inspect_pass = subparsers.add_parser("inspect-pass")
    inspect_pass.add_argument("--run-dir", required=True)
    inspect_pass.add_argument("--item", required=True)
    inspect_pass.add_argument("--stage", choices=STAGE_IDS, required=True)
    inspect_pass.add_argument("--note", required=True)
    inspect_pass.set_defaults(func=command_inspect_pass)

    rerun = subparsers.add_parser("rerun")
    rerun.add_argument("--run-dir", required=True)
    rerun.add_argument("--item", required=True)
    rerun.add_argument("--stage", choices=STAGE_IDS, required=True)
    rerun.add_argument("--note", required=True)
    rerun.set_defaults(func=command_rerun)

    stage_review = subparsers.add_parser("stage-review")
    stage_review.add_argument("--run-dir", required=True)
    stage_review.add_argument("--stage", choices=STAGE_IDS, required=True)
    stage_review.add_argument("--status", choices=sorted(REVIEW_CLI_STATUSES), required=True)
    stage_review.add_argument("--note", required=True)
    stage_review.add_argument("--issue", action="append", default=[])
    stage_review.add_argument("--rerun-item", action="append", default=[])
    stage_review.set_defaults(func=command_stage_review)

    approve_next = subparsers.add_parser("approve-next-stage")
    approve_next.add_argument("--run-dir", required=True)
    approve_next.add_argument("--from-stage", choices=STAGE_IDS, required=True)
    approve_next.add_argument("--to-stage", choices=STAGE_IDS, required=True)
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
