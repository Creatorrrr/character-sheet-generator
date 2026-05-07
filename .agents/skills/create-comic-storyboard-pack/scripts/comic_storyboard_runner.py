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
DEFAULT_OUTPUT_ROOT = Path("/Users/chasoik/Projects/character-sheet-generator/output")
STAGES = [
    {
        "id": "storyboard",
        "label": "storyboard",
        "dir": "01_storyboard",
        "purpose": "comic storyboard thumbnail and composition pass",
    },
    {
        "id": "sketch_ink",
        "label": "sketch/ink",
        "dir": "02_sketch_ink",
        "purpose": "clean sketch and ink line pass",
    },
    {
        "id": "finish",
        "label": "tone/color/finish",
        "dir": "03_finish",
        "purpose": "tone, color, and final polish pass",
    },
]
STAGE_IDS = [stage["id"] for stage in STAGES]
PASS_STATUSES = {"inspected_pass", "complete"}
CURRENT_STATUSES = {"generation_requested", "imported"}
VALID_STATUSES = {"pending", "generation_requested", "imported", "inspected_pass", "complete"}
WORKER_STATUS_VALUES = {"pass", "needs_rerun"}


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


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Missing file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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


def normalize_state(state: dict[str, Any]) -> None:
    for panel in state.get("panels", []):
        panel.setdefault("dependencies", [])
        panel.setdefault("references", [])
        stages = panel.setdefault("stages", {})
        for stage_id in STAGE_IDS:
            stage = stages.setdefault(stage_id, {})
            stage.setdefault("status", "pending")
            stage.setdefault("attempts", 0)
            stage.setdefault("rerun_pending", False)
            stage.setdefault("batch_id", "")
            stage.setdefault("prompt_file", "")
            stage.setdefault("output_path", "")
            stage.setdefault("generated_source", "")
            stage.setdefault("worker_status", "")
            stage.setdefault("worker_note", "")
            stage.setdefault("parent_note", "")
            if stage["status"] not in VALID_STATUSES:
                raise SystemExit(f"Invalid stage status for {panel.get('id')}:{stage_id}: {stage['status']}")


def stage_meta(stage_id: str) -> dict[str, str]:
    for stage in STAGES:
        if stage["id"] == stage_id:
            return stage
    raise SystemExit(f"Unknown stage: {stage_id}")


def stage_state(panel: dict[str, Any], stage_id: str) -> dict[str, Any]:
    if stage_id not in STAGE_IDS:
        raise SystemExit(f"Unknown stage: {stage_id}")
    return panel["stages"][stage_id]


def panel_complete_for_stage(panel: dict[str, Any], stage_id: str) -> bool:
    return stage_state(panel, stage_id).get("status") in PASS_STATUSES


def stage_complete(state: dict[str, Any], stage_id: str) -> bool:
    panels = state.get("panels", [])
    return bool(panels) and all(panel_complete_for_stage(panel, stage_id) for panel in panels)


def workflow_complete(state: dict[str, Any]) -> bool:
    panels = state.get("panels", [])
    return bool(panels) and all(
        panel_complete_for_stage(panel, stage_id) for panel in panels for stage_id in STAGE_IDS
    )


def current_stage_id(state: dict[str, Any]) -> str | None:
    for stage_id in STAGE_IDS:
        if not stage_complete(state, stage_id):
            return stage_id
    return None


def resolve_panel(state: dict[str, Any], panel_ref: str) -> dict[str, Any]:
    ref_slug = slugify(str(Path(panel_ref).stem), str(panel_ref))
    matches = []
    for panel in state.get("panels", []):
        aliases = {
            panel.get("id", ""),
            panel.get("filename", ""),
            Path(panel.get("filename", "")).stem,
            slugify(panel.get("id", "")),
            slugify(Path(panel.get("filename", "")).stem),
        }
        if panel_ref in aliases or ref_slug in aliases:
            matches.append(panel)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SystemExit(f"Ambiguous panel reference: {panel_ref}")
    raise SystemExit(f"Unknown panel: {panel_ref}")


def stage_output_path(run_dir: Path, panel: dict[str, Any], stage_id: str) -> Path:
    return run_dir / stage_meta(stage_id)["dir"] / panel["filename"]


def stage_prompt_path(run_dir: Path, panel: dict[str, Any], stage_id: str) -> Path:
    stem = Path(panel["filename"]).stem
    return run_dir / "prompts" / stage_id / f"{stem}.prompt.txt"


def previous_stage_id(stage_id: str) -> str:
    index = STAGE_IDS.index(stage_id)
    if index == 0:
        return ""
    return STAGE_IDS[index - 1]


def current_blockers(state: dict[str, Any]) -> list[tuple[dict[str, Any], str, dict[str, Any]]]:
    blockers: list[tuple[dict[str, Any], str, dict[str, Any]]] = []
    for panel in state.get("panels", []):
        for stage_id in STAGE_IDS:
            stage = stage_state(panel, stage_id)
            if stage.get("status") in CURRENT_STATUSES:
                blockers.append((panel, stage_id, stage))
    return blockers


def dependency_passed_for_stage(state: dict[str, Any], panel_id: str, stage_id: str) -> bool:
    for panel in state.get("panels", []):
        if panel.get("id") == panel_id:
            return panel_complete_for_stage(panel, stage_id)
    return False


def dependencies_ready(state: dict[str, Any], panel: dict[str, Any], stage_id: str) -> bool:
    return all(dependency_passed_for_stage(state, dep, stage_id) for dep in panel.get("dependencies", []))


def panel_sort_key(panel: dict[str, Any], stage_id: str) -> tuple[int, int, str]:
    stage = stage_state(panel, stage_id)
    return (0 if stage.get("rerun_pending") else 1, int(panel.get("order", 9999)), panel.get("id", ""))


def stage_instruction(stage_id: str) -> str:
    if stage_id == "storyboard":
        return (
            "Create a rough but readable comic storyboard panel. Prioritize shot composition, panel "
            "framing, character blocking, camera angle, action clarity, and story beat readability. "
            "Use simple grayscale thumbnail rendering; do not polish details."
        )
    if stage_id == "sketch_ink":
        return (
            "Create the clean sketch and ink line pass for the approved storyboard panel. Preserve the "
            "same composition, camera, character blocking, props, and continuity. Use crisp comic line "
            "art, clear silhouettes, clean facial/action readability, and no final color yet unless the "
            "approved style requires a minimal guide."
        )
    if stage_id == "finish":
        return (
            "Create the final comic panel finish using the approved sketch/ink image as the structure. "
            "Add tones, color, lighting, shadows, material treatment, and final cleanup consistent with "
            "the approved style. Keep composition and story beat unchanged."
        )
    raise SystemExit(f"Unknown stage: {stage_id}")


def prior_stage_reference(run_dir: Path, panel: dict[str, Any], stage_id: str) -> str:
    prior = previous_stage_id(stage_id)
    if not prior:
        return "none"
    path = stage_output_path(run_dir, panel, prior)
    return str(path) if path.exists() else f"{path} (not found yet)"


def prompt_text(run_dir: Path, panel: dict[str, Any], stage_id: str, state: dict[str, Any]) -> str:
    meta = stage_meta(stage_id)
    references = as_list(panel.get("references"))
    reference_text = "\n".join(f"- {ref}" for ref in references) or "- none"
    dialogue = "\n".join(f"- {line}" for line in as_list(panel.get("dialogue"))) or "- none"
    sfx = "\n".join(f"- {line}" for line in as_list(panel.get("sfx"))) or "- none"
    narration = "\n".join(f"- {line}" for line in as_list(panel.get("narration"))) or "- none"
    characters = ", ".join(as_list(panel.get("characters"))) or "unspecified"
    negative = panel.get("negative_prompt") or (
        "low resolution, watermark, logo, caption text, speech bubble text, subtitles, panel number, "
        "handwritten labels, random typography, unreadable text, malformed hands, distorted faces, "
        "duplicated limbs, broken perspective, inconsistent character design, inconsistent setting, "
        "wrong costume, cropped key action, blurry subject, over-smoothed AI texture."
    )
    return "\n".join(
        [
            f"Workflow: {WORKFLOW}",
            f"Scenario title: {state.get('title', '')}",
            f"Stage: {stage_id} ({meta['purpose']})",
            f"Assigned output: {stage_output_path(run_dir, panel, stage_id)}",
            f"Panel id: {panel['id']}",
            f"Panel number: {panel.get('panel_no', panel.get('order', ''))}",
            f"Scene refs: {', '.join(panel.get('scene_refs', [])) or 'unspecified'}",
            f"Prior stage reference: {prior_stage_reference(run_dir, panel, stage_id)}",
            "",
            "Stage instruction:",
            stage_instruction(stage_id),
            "",
            "Panel story beat:",
            panel.get("beat") or panel.get("purpose") or "",
            "",
            "Visual brief:",
            panel.get("visual_brief") or panel.get("prompt") or "",
            "",
            "Composition and camera:",
            panel.get("composition") or panel.get("camera") or "unspecified",
            "",
            "Setting:",
            panel.get("setting") or "unspecified",
            "",
            "Characters:",
            characters,
            "",
            "Action:",
            panel.get("action") or "unspecified",
            "",
            "Mood and tone:",
            panel.get("mood") or state.get("style_brief") or "unspecified",
            "",
            "Continuity notes:",
            panel.get("continuity_notes") or "none",
            "",
            "Reference paths:",
            reference_text,
            "",
            "Dialogue notes, not image text:",
            dialogue,
            "",
            "Sound effect notes, not image text:",
            sfx,
            "",
            "Caption/narration notes, not image text:",
            narration,
            "",
            "Image text policy:",
            "Do not draw speech bubbles, subtitles, panel numbers, handwritten labels, captions, or any readable text inside the panel image. Keep dialogue, SFX, and captions as metadata only unless the user explicitly approved visible text.",
            "",
            "Generation prompt:",
            panel.get("prompt") or panel.get("visual_brief") or "",
            "",
            "Worker inspection checklist:",
            "- Matches this exact panel and stage",
            "- Preserves story beat, camera, composition, and continuity",
            "- Keeps prior-stage structure unchanged when a prior-stage reference exists",
            "- Contains no unapproved image text, labels, subtitles, watermarks, or random typography",
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
        "# Approved Comic Storyboard Plan",
        "",
        f"Run folder: {run_dir}",
        f"Scenario title: {state.get('title', '')}",
        f"Plan approved: {state.get('plan_approved', False)}",
        "",
        "Generation policy:",
        "- Use Codex built-in image_gen only through one subagent per reserved panel.",
        "- Do not reserve images before approve-plan.",
        "- Generate stages in order: storyboard, sketch_ink, finish.",
        "- Reserve at most four panels per batch.",
        "- Parent inspection is required before a panel stage counts as passed.",
        "- Dialogue, SFX, captions, and panel numbers stay in metadata unless visible text is explicitly approved.",
        "",
        "Panels:",
        "",
    ]
    for panel in state.get("panels", []):
        stage_summary = ", ".join(
            f"{stage_id}={stage_state(panel, stage_id).get('status')}" for stage_id in STAGE_IDS
        )
        lines.extend(
            [
                f"- panel: {panel['id']}",
                f"  filename: {panel['filename']}",
                f"  order: {panel.get('order')}",
                f"  scenes: {', '.join(panel.get('scene_refs', [])) or 'unspecified'}",
                f"  beat: {panel.get('beat') or panel.get('purpose') or ''}",
                f"  camera: {panel.get('camera') or panel.get('composition') or 'unspecified'}",
                f"  characters: {', '.join(as_list(panel.get('characters'))) or 'unspecified'}",
                f"  dependencies: {', '.join(panel.get('dependencies', [])) or 'none'}",
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
        "stage_order": STAGE_IDS,
        "plan_approved": False,
        "complete": False,
        "panels": [],
        "batches": [],
        "notes": ["Generation is blocked until approve-plan is run after explicit user approval."],
    }
    save_state(run_dir, state)
    print(f"RUN_DIR: {run_dir}")
    print(f"STATE: {run_dir / 'state.json'}")
    print(f"STORY_INPUT: {scenario_path}")
    print("NEXT: Present the Korean storyboard approval request, then run approve-plan after user approval.")


def build_stage_states() -> dict[str, dict[str, Any]]:
    return {
        stage_id: {
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
        for stage_id in STAGE_IDS
    }


def normalize_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    raw_panels = plan.get("panels") or plan.get("items")
    if not isinstance(raw_panels, list) or not raw_panels:
        raise SystemExit("Plan must contain a non-empty panels list.")

    panels: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_files: set[str] = set()
    for index, raw in enumerate(raw_panels, start=1):
        if not isinstance(raw, dict):
            raise SystemExit(f"Panel {index} is not an object.")
        base = raw.get("id") or raw.get("filename") or raw.get("visual_brief") or f"panel-{index}"
        panel_id = slugify(str(base), f"panel-{index}")[:80]
        if panel_id in seen_ids:
            panel_id = f"{index:03d}-{panel_id}"
        seen_ids.add(panel_id)

        filename = raw.get("filename")
        if filename:
            filename = slugify(Path(str(filename)).stem, panel_id) + ".png"
        else:
            filename = f"{index:03d}_{panel_id}.png"
        if filename in seen_files:
            filename = f"{index:03d}_{filename}"
        seen_files.add(filename)

        visual_brief = str(raw.get("visual_brief") or raw.get("brief") or "").strip()
        prompt = str(raw.get("prompt") or visual_brief).strip()
        if not visual_brief and not prompt:
            raise SystemExit(f"Panel {panel_id} needs visual_brief or prompt.")

        panels.append(
            {
                "id": panel_id,
                "filename": filename,
                "order": int(raw.get("panel_no") or raw.get("order") or index),
                "panel_no": raw.get("panel_no") or index,
                "scene_refs": as_list(raw.get("scene_refs") or raw.get("scenes")),
                "beat": str(raw.get("beat") or raw.get("purpose") or ""),
                "purpose": str(raw.get("purpose") or raw.get("beat") or ""),
                "visual_brief": visual_brief,
                "setting": str(raw.get("setting") or ""),
                "characters": as_list(raw.get("characters")),
                "action": str(raw.get("action") or ""),
                "camera": str(raw.get("camera") or ""),
                "composition": str(raw.get("composition") or ""),
                "mood": str(raw.get("mood") or ""),
                "dialogue": as_list(raw.get("dialogue")),
                "sfx": as_list(raw.get("sfx")),
                "narration": as_list(raw.get("narration") or raw.get("caption")),
                "continuity_notes": str(raw.get("continuity_notes") or ""),
                "references": as_list(raw.get("references") or raw.get("reference_paths")),
                "prompt": prompt,
                "negative_prompt": str(raw.get("negative_prompt") or ""),
                "dependencies": as_list(raw.get("dependencies")),
                "notes": str(raw.get("notes") or ""),
                "stages": build_stage_states(),
            }
        )

    id_aliases: dict[str, str] = {}
    for panel in panels:
        id_aliases[panel["id"]] = panel["id"]
        id_aliases[slugify(panel["id"])] = panel["id"]
        id_aliases[panel["filename"]] = panel["id"]
        id_aliases[Path(panel["filename"]).stem] = panel["id"]
        id_aliases[slugify(Path(panel["filename"]).stem)] = panel["id"]

    for panel in panels:
        normalized_deps = []
        for dep in panel.get("dependencies", []):
            dep_key = slugify(Path(str(dep)).stem, str(dep))
            dep_id = id_aliases.get(str(dep)) or id_aliases.get(dep_key)
            if not dep_id:
                raise SystemExit(f"Panel {panel['id']} has unknown dependency: {dep}")
            if dep_id != panel["id"] and dep_id not in normalized_deps:
                normalized_deps.append(dep_id)
        panel["dependencies"] = normalized_deps
    panels.sort(key=lambda panel: (panel["order"], panel["id"]))
    return panels


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

    panels = normalize_plan(plan)
    state["title"] = plan.get("scenario_title") or state.get("title")
    state["style_brief"] = str(plan.get("style_brief") or "")
    state["reading_order"] = str(plan.get("reading_order") or "left-to-right")
    state["plan_approved"] = True
    state["approved_at"] = now_iso()
    state["panels"] = panels
    state["batches"] = []
    state.setdefault("notes", []).append(f"Approved {len(panels)} storyboard panels at {state['approved_at']}.")

    write_json(
        run_dir / "approved_storyboard_plan.json",
        {
            "scenario_title": state["title"],
            "style_brief": state.get("style_brief", ""),
            "reading_order": state.get("reading_order", "left-to-right"),
            "panels": panels,
        },
    )
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"APPROVED_PANELS: {len(panels)}")
    print(f"PLAN: {run_dir / 'approved_storyboard_plan.json'}")
    print("NEXT: comic_storyboard_runner.py next-batch --run-dir <run-dir> --limit 4")


def command_next_batch(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    if not state.get("plan_approved"):
        raise SystemExit("Plan is not approved. Present the Korean approval request, then run approve-plan.")

    blockers = current_blockers(state)
    if blockers:
        names = ", ".join(
            f"{panel['filename']}:{stage_id}({stage.get('status')})" for panel, stage_id, stage in blockers
        )
        raise SystemExit(f"Resolve current batch before reserving another: {names}")

    stage_id = current_stage_id(state)
    if not stage_id:
        print("COMPLETE: true")
        return

    candidates = []
    for panel in state.get("panels", []):
        stage = stage_state(panel, stage_id)
        if stage.get("status") != "pending":
            continue
        if not dependencies_ready(state, panel, stage_id):
            continue
        candidates.append(panel)
    candidates.sort(key=lambda panel: panel_sort_key(panel, stage_id))

    if not candidates:
        print("NO_ELIGIBLE_ITEMS")
        command_status(args)
        return

    limit = min(max(args.limit, 1), 4)
    selected = candidates[:limit]
    batch_id = f"batch-{len(state.get('batches', [])) + 1:03d}"
    for panel in selected:
        stage = stage_state(panel, stage_id)
        stage["status"] = "generation_requested"
        stage["batch_id"] = batch_id
        stage["attempts"] = int(stage.get("attempts", 0)) + 1
        stage["requested_at"] = now_iso()
        stage["rerun_pending"] = False
        stage["worker_status"] = ""
        stage["worker_note"] = ""
        stage["parent_note"] = ""
        prompt_path = stage_prompt_path(run_dir, panel, stage_id)
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text(run_dir, panel, stage_id, state), encoding="utf-8")
        stage["prompt_file"] = str(prompt_path)
        stage["output_path"] = str(stage_output_path(run_dir, panel, stage_id))

    state.setdefault("batches", []).append(
        {
            "id": batch_id,
            "stage": stage_id,
            "created_at": now_iso(),
            "panels": [panel["id"] for panel in selected],
            "limit": limit,
        }
    )
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)

    print(f"BATCH_ID: {batch_id}")
    print(f"STAGE: {stage_id}")
    print(f"RUN_DIR: {run_dir}")
    for panel in selected:
        stage = stage_state(panel, stage_id)
        print(f"ITEM: {panel['filename']}")
        print(f"ITEM_ID: {panel['id']}")
        print(f"PROMPT_FILE: {stage['prompt_file']}")
        print(f"OUTPUT: {stage['output_path']}")


def command_import(args: argparse.Namespace) -> None:
    if args.worker_status not in WORKER_STATUS_VALUES:
        raise SystemExit(f"Invalid worker-status: {args.worker_status}")
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    panel = resolve_panel(state, args.item)
    stage_id = args.stage
    stage = stage_state(panel, stage_id)
    if stage.get("status") not in {"generation_requested", "imported"}:
        raise SystemExit(f"Panel stage is not waiting for import: {panel['filename']} {stage_id} ({stage.get('status')})")
    generated = Path(args.generated)
    if not generated.exists():
        raise SystemExit(f"Generated file not found: {generated}")

    destination = stage_output_path(run_dir, panel, stage_id)
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
    panel = resolve_panel(state, args.item)
    stage_id = args.stage
    stage = stage_state(panel, stage_id)
    if stage.get("status") not in {"imported", "inspected_pass", "complete"}:
        raise SystemExit(f"Panel stage is not imported for inspection: {panel['filename']} {stage_id} ({stage.get('status')})")
    output = stage_output_path(run_dir, panel, stage_id)
    if not output.exists():
        raise SystemExit(f"Output file does not exist: {output}")
    stage["status"] = "inspected_pass"
    stage["parent_note"] = args.note
    stage["inspected_at"] = now_iso()
    stage["output_path"] = str(output)
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"INSPECTED_PASS: {panel['filename']} {stage_id}")


def command_rerun(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    panel = resolve_panel(state, args.item)
    stage_id = args.stage
    stage = stage_state(panel, stage_id)
    if stage.get("status") not in {"pending", "generation_requested", "imported", "inspected_pass", "complete"}:
        raise SystemExit(f"Cannot rerun panel stage in status {stage.get('status')}: {panel['filename']} {stage_id}")
    history = stage.setdefault("rerun_history", [])
    history.append(
        {
            "at": now_iso(),
            "from_status": stage.get("status"),
            "note": args.note,
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
    stage["parent_note"] = args.note
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"RERUN_PENDING: {panel['filename']} {stage_id}")
    print("NEXT: Resolve any other current items, then run next-batch.")


def command_batch_status(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    batch = next((entry for entry in state.get("batches", []) if entry.get("id") == args.batch_id), None)
    if not batch:
        raise SystemExit(f"Unknown batch: {args.batch_id}")
    stage_id = batch.get("stage")
    print(f"BATCH_ID: {args.batch_id}")
    print(f"STAGE: {stage_id}")
    for panel_id in batch.get("panels", []):
        panel = resolve_panel(state, panel_id)
        stage = stage_state(panel, stage_id)
        print(f"- {panel['filename']}: {stage.get('status')} worker={stage.get('worker_status', '')}")


def command_status(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    print(f"RUN_DIR: {run_dir}")
    print(f"PLAN_APPROVED: {state.get('plan_approved')}")
    print(f"PANELS: {len(state.get('panels', []))}")
    print(f"CURRENT_STAGE: {current_stage_id(state) or 'complete'}")
    for stage_id in STAGE_IDS:
        counts: dict[str, int] = {}
        for panel in state.get("panels", []):
            status = stage_state(panel, stage_id).get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        parts = ", ".join(f"{status}={counts[status]}" for status in sorted(counts)) or "none"
        print(f"{stage_id}: {parts}")
    blockers = current_blockers(state)
    if blockers:
        print("CURRENT_BLOCKERS:")
        for panel, stage_id, stage in blockers:
            print(f"- {panel['filename']}:{stage_id}: {stage.get('status')}")
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
