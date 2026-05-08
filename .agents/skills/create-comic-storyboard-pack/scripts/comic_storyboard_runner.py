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
STAGES = [
    {
        "id": STORYBOARD_SKETCH_INK_STAGE,
        "label": "storyboard/sketch/ink",
        "dir": "01_storyboard_sketch_ink",
        "purpose": "comic page storyboard, panel layout, dialogue/SFX placement, sketch, and ink line pass",
    },
    {
        "id": FINISH_STAGE,
        "label": "tone/color/finish",
        "dir": "02_finish",
        "purpose": "tone, color, lettering, and final polish pass",
    },
]
STAGE_IDS = [stage["id"] for stage in STAGES]
PASS_STATUSES = {"inspected_pass", "complete"}
CURRENT_STATUSES = {"generation_requested", "imported"}
VALID_STATUSES = {"pending", "generation_requested", "imported", "inspected_pass", "complete"}
WORKER_STATUS_VALUES = {"pass", "needs_rerun"}
REVIEW_STATUSES = {"pending", "passed", "needs_rerun"}
REVIEW_CLI_STATUSES = {"pass", "needs_rerun"}


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
        "output_path": "",
        "generated_source": "",
        "worker_status": "",
        "worker_note": "",
        "parent_note": "",
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
    state["stage_order"] = STAGE_IDS
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
        page.setdefault("page_dialogue_notes", "")
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


def workflow_complete(state: dict[str, Any]) -> bool:
    return all(stage_complete(state, stage_id) for stage_id in STAGE_IDS)


def current_stage_id(state: dict[str, Any]) -> str | None:
    for stage_id in STAGE_IDS:
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


def assert_required_prior_stage_outputs_exist(run_dir: Path, pages: list[dict[str, Any]], stage_id: str) -> None:
    if stage_id != FINISH_STAGE:
        return
    missing = []
    for page in pages:
        path = stage_output_path(run_dir, page, STORYBOARD_SKETCH_INK_STAGE)
        if not path.exists():
            missing.append(f"{page['filename']} requires {path}")
    if missing:
        details = "; ".join(missing)
        raise SystemExit(
            "Finish stage requires the parent-inspected storyboard_sketch_ink image as input before reservation: "
            f"{details}"
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


def stage_instruction(stage_id: str) -> str:
    if stage_id == STORYBOARD_SKETCH_INK_STAGE:
        return (
            "Create the combined Korean comic-book page storyboard, sketch, and ink pass. Show a full "
            "page with multiple panels, gutters, varied panel sizes, reading order, speech balloon "
            "placement, SFX placement, captions where useful, clear action blocking, and clean ink lines."
        )
    if stage_id == FINISH_STAGE:
        return (
            "Create the final Korean comic-book page using the required parent-inspected "
            "storyboard_sketch_ink image as the visual input and structure reference. Add tones, color "
            "if requested, lighting, shadows, final lettering, speech balloons, SFX, short captions, "
            "and cleanup without changing page layout, panel count, text placement, character/object "
            "blocking, motion direction, or action logic."
        )
    raise SystemExit(f"Unknown stage: {stage_id}")


def panel_line(panel: dict[str, Any]) -> str:
    source_dialogue = "; ".join(as_list(panel.get("source_dialogue") or panel.get("dialogue"))) or "none"
    adapted_dialogue = "; ".join(as_list(panel.get("adapted_dialogue"))) or "none"
    sfx = "; ".join(as_list(panel.get("sfx"))) or "none"
    captions = "; ".join(as_list(panel.get("caption") or panel.get("narration"))) or "none"
    checks = "; ".join(as_list(panel.get("motion_checks"))) or "none"
    must_match = "; ".join(as_list(panel.get("must_match"))) or "none"
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
    panel_text = "\n".join(panel_line(panel) for panel in panels) or "- no panel details supplied"
    page_dialogue_notes = page.get("page_dialogue_notes") or (
        "Adapt source dialogue to fit comic timing, mood, panel rhythm, and balloon space. "
        "Do not copy source dialogue verbatim unless the approved plan explicitly says to preserve it."
    )
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
            "Generate one complete Korean comic-book page image with multiple panels on the same page. Use panel gutters, varied panel sizes, clear reading flow, speech balloons, SFX lettering, and short captions where approved.",
            "",
            "Page layout brief:",
            page.get("layout_brief") or page.get("visual_brief") or page.get("prompt") or "",
            "",
            "Page dialogue and lettering policy:",
            page_dialogue_notes,
            "Use adapted_dialogue, approved SFX, and approved captions inside the page image. Keep lettering short, legible, and placed so it does not cover key faces, hands, props, or action.",
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
            "- Contains multiple panels on one page with clear Korean comic-book layout",
            "- Uses adapted dialogue/SFX/captions from the approved plan, not raw source dialogue by default",
            "- Speech balloons, SFX, and captions are legible and do not cover key art",
            "- Preserves story beat, reading order, composition, and continuity",
            "- Preserves source-data consistency for characters, props, profiles, locations, and page-layout references",
            "- Preserves panel-to-panel and adjacent-page continuity for character/object placement, gaze, action direction, time flow, and lettering placement",
            "- Keeps prior-stage structure unchanged when a prior-stage reference exists, especially during finish",
            "- Character/object positions, action direction, object trajectory, and cause-effect motion are physically plausible",
            "- No examples of impossible staging such as a basketball shot where the ball travels behind the shooter",
            "- Has no obvious anatomy, perspective, crop, object, or continuity defects",
            "",
            "Negative prompt:",
            negative,
            "",
            "Return only: generated file path, worker_status, worker_note.",
        ]
    )


def write_batch_plan(run_dir: Path, state: dict[str, Any]) -> None:
    lines = [
        "# Approved Comic Storyboard Page Plan",
        "",
        f"Run folder: {run_dir}",
        f"Scenario title: {state.get('title', '')}",
        f"Plan approved: {state.get('plan_approved', False)}",
        "",
        "Generation policy:",
        "- Use Codex built-in image_gen only through one subagent per reserved page.",
        "- Do not reserve images before approve-plan.",
        f"- Use {state.get('source_root') or DEFAULT_SOURCE_ROOT} as the default source data folder when the user did not specify source/reference paths.",
        f"- Do not use {', '.join(state.get('excluded_source_roots') or [str(DEFAULT_OUTPUT_ROOT)])} or any output/ subtree as source/reference data.",
        "- Generate stages in order: storyboard_sketch_ink, finish.",
        "- Do not reserve finish until every page has passed storyboard_sketch_ink parent inspection.",
        "- Finish must use the parent-inspected storyboard_sketch_ink image as the required visual input / structure reference.",
        "- Reserve at most four pages per batch.",
        "- Parent inspection is required before a page stage counts as passed.",
        "- Stage finish review is required after all page stages pass; next stage opens only after stage-review pass.",
        "- Stage finish review checks source consistency against characters, props, profiles, sources/ references, and panel/page continuity.",
        "- Approved adapted dialogue, SFX, and short captions are included in the page image.",
        "- Worker and parent inspection must reject implausible spatial layout, object motion, or cause-effect direction.",
        "",
    ]
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
                f"  panel_count: {len(page.get('panels', []))}",
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
    for stage in STAGES:
        (run_dir / "prompts" / stage["id"]).mkdir()
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
        "stage_order": STAGE_IDS,
        "stage_reviews": build_stage_reviews(),
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
        "page_dialogue_notes": str(raw.get("page_dialogue_notes") or ""),
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
    state["plan_approved"] = True
    state["approved_at"] = now_iso()
    state["pages"] = pages
    state.pop("panels", None)
    state["batches"] = []
    state["stage_reviews"] = build_stage_reviews()
    state.setdefault("notes", []).append(f"Approved {len(pages)} comic pages at {state['approved_at']}.")

    write_json(
        run_dir / "approved_storyboard_plan.json",
        {
            "scenario_title": state["title"],
            "style_brief": state.get("style_brief", ""),
            "reading_order": state.get("reading_order", ""),
            "source_root": state.get("source_root", ""),
            "excluded_source_roots": state.get("excluded_source_roots", []),
            "source_references": state.get("source_references", []),
            "pages": pages,
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
    assert_required_prior_stage_outputs_exist(run_dir, selected, stage_id)
    batch_id = f"batch-{len(state.get('batches', [])) + 1:03d}"
    for page in selected:
        stage = stage_state(page, stage_id)
        stage["status"] = "generation_requested"
        stage["batch_id"] = batch_id
        stage["attempts"] = int(stage.get("attempts", 0)) + 1
        stage["requested_at"] = now_iso()
        stage["rerun_pending"] = False
        stage["worker_status"] = ""
        stage["worker_note"] = ""
        stage["parent_note"] = ""
        prompt_path = stage_prompt_path(run_dir, page, stage_id)
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text(run_dir, page, stage_id, state), encoding="utf-8")
        stage["prompt_file"] = str(prompt_path)
        stage["output_path"] = str(stage_output_path(run_dir, page, stage_id))

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
    else:
        raise SystemExit(f"Invalid stage review status: {args.status}")

    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"STAGE_REVIEW: {stage_id}")
    print(f"STATUS: {review['status']}")
    if rerun_items:
        for item in rerun_items:
            print(f"RERUN_ITEM: {item}")


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
