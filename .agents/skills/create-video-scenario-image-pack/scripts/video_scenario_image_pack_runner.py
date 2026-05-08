#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


WORKFLOW = "create-video-scenario-image-pack"
DEFAULT_OUTPUT_ROOT = Path("/Users/chasoik/Projects/character-sheet-generator/output")
CURRENT_STATUSES = {"generation_requested", "imported"}
PASS_STATUSES = {"inspected_pass", "complete"}
CHARACTER_CATEGORIES = {"character", "action_pose", "performance_pose", "player_action"}
WEB_REFERENCE_RECOMMENDED_MIN = 3
NO_CHARACTER_ARTIFACT_LOCK = (
    "No-character artifact lock: reject people, pedestrians, players, performers, body parts, hands, faces, "
    "silhouettes, crowds, vehicle silhouettes, poster/window figures, human-like reflections, tiny human-like "
    "marks, and background street activity anywhere in the frame, including the far background."
)
SPATIAL_CONTINUITY_LOCK = (
    "Spatial continuity lock: preserve fixed landmarks and their relative positions from fixed_layout_notes, "
    "must_match, continuity anchors, and parent-inspected references. Reject moved landmarks, swapped building "
    "positions, wrong hoop side, wrong entrance side, wrong bench/wall/gate relationship, and fixed landmark "
    "relative-position drift."
)
PROP_ENVIRONMENT_STATE_LOCK = (
    "Prop/environment state lock: preserve approved prop shape/material/scale, damage state, time of day, "
    "weather, set dressing, and camera-critical insert details. Reject changed prop shape/material/scale, wrong "
    "damage state, wrong time of day/weather, unapproved set dressing drift, unrelated props, and cropped key subject."
)
WEB_REFERENCE_POLICY = (
    "Web reference policy: use only web_references explicitly registered for this current run. Treat them as factual "
    "references for shape, spatial layout, material, landmarks, mood, prop state, weather, and time of day. Do not copy "
    "the source image composition, watermark, logo, people, artist-specific style, brand styling, or copyrighted visual expression."
)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def slugify(value: str, fallback: str = "item") -> str:
    value = value.lower().encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or fallback


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "contains_character"}
    return bool(value)


def as_list(value: Any) -> list[str]:
    if value is None:
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


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Missing file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def load_state(run_dir: Path) -> dict[str, Any]:
    state = load_json(run_dir / "state.json")
    if state.get("workflow") != WORKFLOW:
        raise SystemExit(f"Unexpected workflow in state.json: {state.get('workflow')}")
    normalize_state(state)
    return state


def normalize_state(state: dict[str, Any]) -> None:
    state.setdefault("items", [])
    state.setdefault("batches", [])
    state.setdefault("notes", [])
    state.setdefault("anchor_facts", {})
    for item in state["items"]:
        item.setdefault("attempts", 0)
        item.setdefault("rerun_pending", False)
        item.setdefault("rerun_history", [])
        item.setdefault("rerun_prompt_hints", [])
        item.setdefault("worker_result", {})
        item.setdefault("parent_inspection", {})
        item.setdefault("artifact_paths", {})
        item.setdefault("batch_id", "")
        item.setdefault("prompt_file", "")
        item.setdefault("web_references", [])
        item.setdefault("web_reference_search_note", "")
        item.setdefault("worker_status", item.get("worker_result", {}).get("status", ""))
        item.setdefault("worker_note", item.get("worker_result", {}).get("note", ""))
        item.setdefault("parent_note", item.get("parent_inspection", {}).get("note", ""))


def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    normalize_state(state)
    state["updated_at"] = now_iso()
    state["complete"] = bool(state["items"]) and all(
        item.get("status") in PASS_STATUSES for item in state["items"]
    )
    write_json_atomic(run_dir / "state.json", state)


def resolve_item(state: dict[str, Any], item_ref: str) -> dict[str, Any]:
    for item in state.get("items", []):
        if item.get("id") == item_ref or item.get("filename") == item_ref:
            return item
    stem = slugify(Path(item_ref).stem, item_ref)
    for item in state.get("items", []):
        if slugify(Path(item.get("filename", "")).stem, "") == stem:
            return item
    raise SystemExit(f"Unknown item: {item_ref}")


def strict_empty_environment_negative(contains_character: bool) -> str:
    base = (
        "low resolution, watermark, random logo, caption text, storyboard panel labels, "
        "unreadable text, accidental subtitles, distorted anatomy, extra fingers, duplicated limbs, "
        "broken reflections, over-smoothed AI texture, waxy skin, plastic objects, "
        "inconsistent location layout, moved landmarks, swapped building positions, wrong hoop side, "
        "wrong entrance side, fixed landmark relative-position drift, wrong time of day/weather, "
        "wrong damage state, changed prop shape/material/scale, unapproved set dressing drift, "
        "unrelated props, cropped key subject"
    )
    if contains_character:
        return base
    strict = (
        "people, person, pedestrian, player, performer, character, body, hands, face, silhouette, "
        "crowd, cars, vehicles, bicycles, scooters, posters, signs, window figures, reflections, "
        "human-shaped marks, tiny vertical marks shaped like people, tiny human-like marks, "
        "human-like reflections, poster/window figures, vehicle silhouettes, background street activity"
    )
    return f"{strict}, {base}"


def production_source_verification_lock(contains_character: bool) -> str:
    lines = ["Production source verification lock:"]
    if not contains_character:
        lines.append(NO_CHARACTER_ARTIFACT_LOCK)
    lines.append(SPATIAL_CONTINUITY_LOCK)
    lines.append(PROP_ENVIRONMENT_STATE_LOCK)
    return "\n".join(lines)


def normalize_web_references(raw_refs: Any, run_dir: Path, item_id: str) -> list[dict[str, Any]]:
    if raw_refs in (None, ""):
        return []
    if not isinstance(raw_refs, list):
        raise SystemExit(f"Item {item_id} web_references must be a list.")
    normalized = []
    allowed_root = run_dir / "web_references"
    for index, raw in enumerate(raw_refs, start=1):
        if not isinstance(raw, dict):
            raise SystemExit(f"Item {item_id} web reference {index} is not an object.")
        ref_id = str(raw.get("id") or f"web-reference-{index}").strip()
        local_path = str(raw.get("local_path") or "").strip()
        if not local_path:
            raise SystemExit(f"Item {item_id} web reference {ref_id} needs local_path.")
        ref_path = Path(local_path).expanduser()
        if not ref_path.is_absolute():
            ref_path = run_dir / ref_path
        if not path_is_under(ref_path, allowed_root):
            raise SystemExit(
                f"Web reference {ref_id} for item {item_id} must be under the current run web_references folder: {ref_path}"
            )
        if not ref_path.exists():
            raise SystemExit(f"Web reference file not found for item {item_id}: {ref_path}")
        normalized.append(
            {
                "id": ref_id,
                "local_path": str(ref_path),
                "source_url": str(raw.get("source_url") or ""),
                "page_url": str(raw.get("page_url") or ""),
                "source_title": str(raw.get("source_title") or ""),
                "reference_purpose": str(raw.get("reference_purpose") or ""),
                "observed_facts": as_list(raw.get("observed_facts")),
                "usage_note": str(raw.get("usage_note") or ""),
            }
        )
    return normalized


def web_reference_prompt_lines(item: dict[str, Any]) -> str:
    lines = [WEB_REFERENCE_POLICY]
    refs = item.get("web_references") or []
    search_note = str(item.get("web_reference_search_note") or "").strip()
    lines.append(f"Web reference count: {len(refs)}")
    lines.append(f"Web reference search note: {search_note or 'none'}")
    if not refs:
        lines.append("- none registered")
        return "\n".join(lines)
    for ref in refs:
        facts = "; ".join(as_list(ref.get("observed_facts"))) or "none"
        lines.append(
            "- "
            f"id={ref.get('id', '')}; "
            f"local_path={ref.get('local_path', '')}; "
            f"source_url={ref.get('source_url', '')}; "
            f"page_url={ref.get('page_url', '')}; "
            f"source_title={ref.get('source_title', '')}; "
            f"reference_purpose={ref.get('reference_purpose', '')}; "
            f"observed_facts={facts}; "
            f"usage_note={ref.get('usage_note', '')}"
        )
    return "\n".join(lines)


def write_web_reference_manifest(run_dir: Path, state: dict[str, Any]) -> None:
    write_json_atomic(
        run_dir / "web_reference_manifest.json",
        {
            "scenario_title": state.get("title", ""),
            "items": [
                {
                    "id": item.get("id", ""),
                    "filename": item.get("filename", ""),
                    "web_reference_count": len(item.get("web_references", [])),
                    "web_reference_search_note": item.get("web_reference_search_note", ""),
                    "web_references": item.get("web_references", []),
                }
                for item in state.get("items", [])
            ],
        },
    )


def item_prompt_path(run_dir: Path, item: dict[str, Any]) -> Path:
    return run_dir / "prompts" / f"{Path(item['filename']).stem}.prompt.txt"


def item_subagent_prompt_path(run_dir: Path, item: dict[str, Any]) -> Path:
    return run_dir / "subagent_prompts" / f"{Path(item['filename']).stem}.subagent.txt"


def worker_note_path(run_dir: Path, item: dict[str, Any]) -> Path:
    return run_dir / "worker_notes" / f"{Path(item['filename']).stem}.txt"


def parent_note_path(run_dir: Path, item: dict[str, Any]) -> Path:
    return run_dir / "parent_notes" / f"{Path(item['filename']).stem}.txt"


def matching_reference_paths(run_dir: Path, item: dict[str, Any], state: dict[str, Any]) -> list[str]:
    refs = []
    for dep in item.get("dependencies", []):
        try:
            dep_item = resolve_item(state, dep)
        except SystemExit:
            continue
        output = run_dir / dep_item["filename"]
        if output.exists():
            refs.append(str(output))
    for ref in item.get("web_references", []):
        local_path = ref.get("local_path")
        if not local_path:
            continue
        path = Path(local_path)
        if not path.exists():
            raise SystemExit(f"Web reference file not found for item {item.get('id', '')}: {path}")
        refs.append(str(path))
    return refs


def prompt_text(item: dict[str, Any], state: dict[str, Any], run_dir: Path) -> str:
    contains_character = as_bool(item.get("contains_character"))
    character_policy = "explicit_character_allowed" if contains_character else "no_character"
    negative = item.get("negative_prompt") or strict_empty_environment_negative(contains_character)
    if item.get("negative_prompt") and not contains_character:
        negative = f"{strict_empty_environment_negative(False)}, {item['negative_prompt']}"
    must_match = as_list(item.get("must_match"))
    hints = as_list(item.get("rerun_prompt_hints"))
    anchor_facts = []
    for dep in item.get("dependencies", []):
        fact = state.get("anchor_facts", {}).get(dep)
        if fact:
            anchor_facts.append(f"{dep}: {fact}")
    return "\n".join(
        [
            f"Workflow: {WORKFLOW}",
            f"Scenario title: {state.get('title', '')}",
            f"Assigned output: {item['filename']}",
            f"Item id: {item['id']}",
            f"Scene refs: {', '.join(item.get('scene_refs', [])) or 'unspecified'}",
            f"Category: {item.get('category', 'unspecified')}",
            f"Character policy: {character_policy}",
            f"Spatial group: {item.get('spatial_group') or 'none'}",
            f"Continuity anchor: {item.get('continuity_anchor') or 'none'}",
            f"Camera view: {item.get('camera_view') or 'unspecified'}",
            f"Purpose: {item.get('purpose', '')}",
            "",
            "Visual brief:",
            item.get("visual_brief", ""),
            "",
            "Fixed layout notes:",
            item.get("fixed_layout_notes") or "none",
            "",
            "Known anchor facts from parent inspection:",
            "\n".join(f"- {fact}" for fact in anchor_facts) or "- none",
            "",
            production_source_verification_lock(contains_character),
            "",
            "Web references:",
            web_reference_prompt_lines(item),
            "",
            "Must match across related shots:",
            "\n".join(f"- {entry}" for entry in must_match) or "- none",
            "",
            "Rerun prompt hints:",
            "\n".join(f"- {entry}" for entry in hints) or "- none",
            "",
            "Generation prompt:",
            item.get("prompt") or item.get("visual_brief", ""),
            "",
            "Strict empty-environment rule:",
            (
                "Do not include people, pedestrians, players, performers, body parts, hands, faces, silhouettes, "
                "cars, bicycles, scooters, posters, signs, window figures, reflections, or tiny human-like marks anywhere, including the far background."
                if not contains_character
                else "Character-bearing content was explicitly approved for this item."
            ),
            "",
            "Negative prompt:",
            negative,
            "",
            "Reference paths:",
            "\n".join(f"- {path}" for path in matching_reference_paths(run_dir, item, state)) or "- none",
        ]
    )


def subagent_prompt_text(item: dict[str, Any], state: dict[str, Any], run_dir: Path) -> str:
    references = matching_reference_paths(run_dir, item, state)
    character_policy = "explicit_character_allowed" if as_bool(item.get("contains_character")) else "no_character"
    return "\n".join(
        [
            "You are generating exactly one image for create-video-scenario-image-pack.",
            "You are not alone in the codebase; do not revert or edit files made by others. Do not edit state.json.",
            "",
            f"Run folder: {run_dir}",
            f"Scenario file: {state.get('scenario_file')}",
            f"Approved plan: {run_dir / 'approved_image_plan.json'}",
            f"Assigned output: {item['filename']}",
            f"Prompt file: {item.get('prompt_file')}",
            f"Batch id: {item.get('batch_id')}",
            f"Relevant references: {', '.join(references) if references else 'none'}",
            f"Character policy: {character_policy}",
            f"Spatial group: {item.get('spatial_group') or 'none'}",
            f"Continuity anchor: {item.get('continuity_anchor') or 'none'}",
            f"Fixed layout notes: {item.get('fixed_layout_notes') or 'none'}",
            "",
            production_source_verification_lock(as_bool(item.get("contains_character"))),
            "",
            "Web references:",
            web_reference_prompt_lines(item),
            "",
            "Use image_gen with the assigned prompt and any provided visual references. If character policy is no_character, do not include people, players, performers, body parts, hands, faces, silhouettes, cars, bicycles, scooters, posters, signs, window figures, reflections, or tiny human-like background marks anywhere.",
            "Preserve spatial layout facts from the continuity anchor: fixed landmarks must stay in the same relative positions across shots.",
            "After generation, inspect the output for scenario fit, prompt fit, no-character artifact lock when active, spatial continuity lock, prop/environment state lock, technical quality, text policy, and obvious defects.",
            "Return only:",
            "- generated file path",
            "- worker_status: pass or needs_rerun",
            "- worker_note: concise inspection note",
        ]
    )


def write_item_artifacts(run_dir: Path, item: dict[str, Any], state: dict[str, Any]) -> None:
    prompt_path = item_prompt_path(run_dir, item)
    subagent_path = item_subagent_prompt_path(run_dir, item)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    subagent_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt_text(item, state, run_dir), encoding="utf-8")
    item["prompt_file"] = str(prompt_path)
    item.setdefault("artifact_paths", {})["prompt"] = str(prompt_path)
    subagent_path.write_text(subagent_prompt_text(item, state, run_dir), encoding="utf-8")
    item["artifact_paths"]["subagent_prompt"] = str(subagent_path)


def write_batch_plan(run_dir: Path, state: dict[str, Any]) -> None:
    lines = ["# Approved Video Scenario Image Plan", ""]
    for item in state.get("items", []):
        deps = ", ".join(item.get("dependencies", [])) or "none"
        scenes = ", ".join(item.get("scene_refs", [])) or "unspecified"
        must_match = "; ".join(as_list(item.get("must_match"))) or "none"
        lines.extend(
            [
                f"- output: {run_dir / item['filename']}",
                f"  id: {item['id']}",
                f"  scenes: {scenes}",
                f"  category: {item.get('category', 'unspecified')}",
                f"  contains_character: {item.get('contains_character', False)}",
                f"  spatial_group: {item.get('spatial_group') or 'none'}",
                f"  continuity_anchor: {item.get('continuity_anchor') or 'none'}",
                f"  camera_view: {item.get('camera_view') or 'unspecified'}",
                f"  must_match: {must_match}",
                f"  web_references: {len(item.get('web_references', []))}",
                f"  web_reference_search_note: {item.get('web_reference_search_note') or 'none'}",
                f"  purpose: {item.get('purpose', '')}",
                f"  dependencies: {deps}",
                f"  status: {item.get('status', 'pending')}",
                f"  attempts: {item.get('attempts', 0)}",
                "",
            ]
        )
    (run_dir / "batch_plan.md").write_text("\n".join(lines), encoding="utf-8")


def command_init(args: argparse.Namespace) -> None:
    title = args.title or (Path(args.scenario).stem if args.scenario else "video-scenario")
    slug = slugify(title, WORKFLOW)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_root = Path(args.output_root) if args.output_root else DEFAULT_OUTPUT_ROOT
    run_dir = Path(args.run_dir) if args.run_dir else output_root / f"{slug}-video-scenario-image-pack-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    for child in ("prompts", "subagent_prompts", "worker_notes", "parent_notes", "web_references"):
        (run_dir / child).mkdir()

    scenario_path = run_dir / "scenario.md"
    if args.scenario:
        source = Path(args.scenario)
        if not source.exists():
            raise SystemExit(f"Scenario file not found: {source}")
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
        "plan_approved": False,
        "items": [],
        "batches": [],
        "anchor_facts": {},
        "complete": False,
        "notes": ["Generation is blocked until approve-plan is run after user approval."],
    }
    save_state(run_dir, state)
    write_web_reference_manifest(run_dir, state)
    print(f"RUN_DIR: {run_dir}")
    print(f"STATE: {run_dir / 'state.json'}")
    print(f"SCENARIO: {scenario_path}")
    print("NEXT: Ask the user to approve the extracted image-source list, then run approve-plan.")


def normalize_plan(plan: dict[str, Any], run_dir: Path) -> list[dict[str, Any]]:
    raw_items = plan.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise SystemExit("Plan must contain a non-empty items list.")

    seen_ids: set[str] = set()
    seen_files: set[str] = set()
    items: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            raise SystemExit(f"Item {index} is not an object.")
        base = raw.get("id") or raw.get("filename") or raw.get("visual_brief") or f"item-{index}"
        item_id = slugify(str(base), f"item-{index}")[:80]
        if item_id in seen_ids:
            item_id = f"{index:03d}-{item_id}"
        seen_ids.add(item_id)

        filename = raw.get("filename")
        if filename:
            filename = slugify(str(Path(filename).stem), item_id) + ".png"
        else:
            filename = f"{index:03d}-{item_id}.png"
        if filename in seen_files:
            filename = f"{index:03d}-{filename}"
        seen_files.add(filename)

        contains_character = as_bool(raw.get("contains_character", False))
        category = str(raw.get("category") or "unspecified").strip().lower()
        if category in CHARACTER_CATEGORIES and not contains_character:
            raise SystemExit(
                f"Item {item_id} uses character-bearing category '{category}' but contains_character is false."
            )
        visual_brief = str(raw.get("visual_brief") or raw.get("brief") or "").strip()
        prompt = str(raw.get("prompt") or visual_brief).strip()
        if not visual_brief and not prompt:
            raise SystemExit(f"Item {item_id} needs visual_brief or prompt.")

        items.append(
            {
                "id": item_id,
                "filename": filename,
                "scene_refs": as_list(raw.get("scene_refs") or raw.get("scenes")),
                "category": category,
                "contains_character": contains_character,
                "purpose": str(raw.get("purpose") or ""),
                "visual_brief": visual_brief,
                "spatial_group": str(raw.get("spatial_group") or ""),
                "continuity_anchor": str(raw.get("continuity_anchor") or ""),
                "fixed_layout_notes": str(raw.get("fixed_layout_notes") or ""),
                "camera_view": str(raw.get("camera_view") or ""),
                "must_match": as_list(raw.get("must_match")),
                "web_references": normalize_web_references(raw.get("web_references"), run_dir, item_id),
                "web_reference_search_note": str(raw.get("web_reference_search_note") or ""),
                "prompt": prompt,
                "negative_prompt": str(raw.get("negative_prompt") or ""),
                "dependencies": as_list(raw.get("dependencies")),
                "notes": str(raw.get("notes") or ""),
                "status": "pending",
                "attempts": 0,
                "order": index,
                "rerun_pending": False,
                "rerun_history": [],
                "rerun_prompt_hints": [],
                "prompt_file": "",
                "batch_id": "",
                "worker_status": "",
                "worker_note": "",
                "worker_result": {},
                "parent_note": "",
                "parent_inspection": {},
                "artifact_paths": {},
            }
        )

    valid_ids = {item["id"] for item in items}
    filename_aliases = {slugify(Path(item["filename"]).stem): item["id"] for item in items}
    for item in items:
        normalized_deps = []
        raw_deps = list(item.get("dependencies", []))
        if item.get("continuity_anchor"):
            raw_deps.append(item["continuity_anchor"])
        for dep in raw_deps:
            dep_key = slugify(str(Path(dep).stem), str(dep))
            dep_id = dep if dep in valid_ids else filename_aliases.get(dep_key, dep_key)
            if dep_id != item["id"] and dep_id not in normalized_deps:
                normalized_deps.append(dep_id)
        if item.get("continuity_anchor"):
            anchor_key = slugify(str(Path(item["continuity_anchor"]).stem), item["continuity_anchor"])
            item["continuity_anchor"] = (
                item["continuity_anchor"]
                if item["continuity_anchor"] in valid_ids
                else filename_aliases.get(anchor_key, anchor_key)
            )
        item["dependencies"] = normalized_deps
    return items


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

    items = normalize_plan(plan, run_dir)
    valid_ids = {item["id"] for item in items}
    for item in items:
        missing = [dep for dep in item.get("dependencies", []) if dep not in valid_ids]
        if missing:
            raise SystemExit(f"Item {item['id']} has unknown dependencies: {', '.join(missing)}")

    state["title"] = plan.get("scenario_title") or state.get("title")
    state["plan_approved"] = True
    state["approved_at"] = now_iso()
    state["items"] = items
    state["batches"] = []
    state["anchor_facts"] = {}
    state.setdefault("notes", []).append(f"Approved {len(items)} image sources at {state['approved_at']}.")
    write_json_atomic(run_dir / "approved_image_plan.json", {"scenario_title": state["title"], "items": items})
    write_web_reference_manifest(run_dir, state)
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"APPROVED_ITEMS: {len(items)}")
    print(f"PLAN: {run_dir / 'approved_image_plan.json'}")
    print("NEXT: [스킬 경로]/scripts/video_scenario_image_pack_runner.py next-batch --run-dir <run-dir> --limit 4")


def dependency_passed(state: dict[str, Any], dep_id: str) -> bool:
    return any(item.get("id") == dep_id and item.get("status") in PASS_STATUSES for item in state.get("items", []))


def current_blockers(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in state.get("items", []) if item.get("status") in CURRENT_STATUSES]


def eligible_items(state: dict[str, Any]) -> list[dict[str, Any]]:
    pending = [
        item
        for item in state.get("items", [])
        if item.get("status") == "pending"
        and all(dependency_passed(state, dep) for dep in item.get("dependencies", []))
    ]
    reruns = [item for item in pending if item.get("rerun_pending")]
    if reruns:
        return sorted(reruns, key=lambda item: item.get("order", 9999))
    return sorted(pending, key=lambda item: item.get("order", 9999))


def command_next_batch(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    if not state.get("plan_approved"):
        raise SystemExit("Plan is not approved. Ask the user to approve the list, then run approve-plan.")
    blockers = current_blockers(state)
    if blockers:
        names = ", ".join(f"{item['filename']}({item['status']})" for item in blockers)
        raise SystemExit(f"Resolve current batch before reserving another: {names}")

    pending = eligible_items(state)
    if not pending:
        print("NO_ELIGIBLE_ITEMS")
        command_status(args)
        return
    limit = min(max(args.limit, 1), 4)
    selected = pending[:limit]
    batch_id = f"batch-{len(state.get('batches', [])) + 1:03d}"
    requested_at = now_iso()
    for item in selected:
        item["status"] = "generation_requested"
        item["batch_id"] = batch_id
        item["attempts"] = int(item.get("attempts", 0)) + 1
        item["requested_at"] = requested_at
        item["rerun_pending"] = False
        item["worker_status"] = ""
        item["worker_note"] = ""
        item["worker_result"] = {}
        item["parent_note"] = ""
        item["parent_inspection"] = {}
        write_item_artifacts(run_dir, item, state)
    state.setdefault("batches", []).append(
        {"id": batch_id, "created_at": requested_at, "items": [item["id"] for item in selected], "limit": limit}
    )
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)

    print(f"BATCH_ID: {batch_id}")
    print(f"RUN_DIR: {run_dir}")
    for item in selected:
        print(f"ITEM: {item['filename']}")
        print(f"ITEM_ID: {item['id']}")
        print(f"PROMPT_FILE: {item['prompt_file']}")
        print(f"SUBAGENT_PROMPT: {item['artifact_paths']['subagent_prompt']}")


def import_one(run_dir: Path, item_ref: str, generated_ref: str, worker_status: str, worker_note: str) -> None:
    state = load_state(run_dir)
    item = resolve_item(state, item_ref)
    generated = Path(generated_ref)
    if not generated.exists():
        raise SystemExit(f"Generated file not found: {generated}")
    if item.get("status") not in {"generation_requested", "imported"}:
        raise SystemExit(f"Item is not waiting for import: {item['filename']} ({item.get('status')})")
    destination = run_dir / item["filename"]
    if generated.resolve() != destination.resolve():
        shutil.copy2(generated, destination)
    imported_at = now_iso()
    worker_note_file = worker_note_path(run_dir, item)
    worker_note_file.parent.mkdir(parents=True, exist_ok=True)
    worker_note_file.write_text(worker_note, encoding="utf-8")
    item["status"] = "imported"
    item["generated_source"] = str(generated)
    item["output_path"] = str(destination)
    item["worker_status"] = worker_status
    item["worker_note"] = worker_note
    item["worker_result"] = {
        "status": worker_status,
        "note": worker_note,
        "imported_at": imported_at,
        "generated_source": str(generated),
    }
    item.setdefault("artifact_paths", {})["output"] = str(destination)
    item["artifact_paths"]["worker_note"] = str(worker_note_file)
    item["imported_at"] = imported_at
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)


def command_import(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    import_one(run_dir, args.item, args.generated, args.worker_status, args.worker_note)
    print(f"IMPORTED: {run_dir / resolve_item(load_state(run_dir), args.item)['filename']}")
    print("NEXT: Parent must inspect, then run inspect-pass or rerun.")


def command_import_batch(args: argparse.Namespace) -> None:
    manifest = load_json(Path(args.manifest))
    run_dir = Path(manifest.get("run_dir") or args.run_dir)
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        raise SystemExit("Manifest must contain a non-empty items list.")
    for entry in items:
        import_one(
            run_dir,
            str(entry["item"]),
            str(entry["generated"]),
            str(entry["worker_status"]),
            str(entry["worker_note"]),
        )
    print(f"IMPORTED: {len(items)}")


def inspect_one(run_dir: Path, item_ref: str, note: str) -> None:
    state = load_state(run_dir)
    item = resolve_item(state, item_ref)
    if item.get("status") not in {"imported", "inspected_pass", "complete"}:
        raise SystemExit(f"Item is not imported for inspection: {item['filename']} ({item.get('status')})")
    inspected_at = now_iso()
    parent_file = parent_note_path(run_dir, item)
    parent_file.parent.mkdir(parents=True, exist_ok=True)
    parent_file.write_text(note, encoding="utf-8")
    item["status"] = "inspected_pass"
    item["parent_note"] = note
    item["parent_inspection"] = {"result": "pass", "note": note, "inspected_at": inspected_at}
    item.setdefault("artifact_paths", {})["parent_note"] = str(parent_file)
    item["inspected_at"] = inspected_at
    if item.get("category") in {"location_master", "spatial_layout"}:
        state.setdefault("anchor_facts", {})[item["id"]] = note or item.get("fixed_layout_notes", "")
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)


def command_inspect_pass(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    inspect_one(run_dir, args.item, args.note)
    item = resolve_item(load_state(run_dir), args.item)
    print(f"INSPECTED_PASS: {item['filename']}")


def command_inspect_batch_pass(args: argparse.Namespace) -> None:
    manifest = load_json(Path(args.manifest))
    run_dir = Path(manifest.get("run_dir") or args.run_dir)
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        raise SystemExit("Manifest must contain a non-empty items list.")
    for entry in items:
        inspect_one(run_dir, str(entry["item"]), str(entry["note"]))
    print(f"INSPECTED_PASS: {len(items)}")


def command_rerun(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    item = resolve_item(state, args.item)
    if item.get("status") not in {"generation_requested", "imported", "inspected_pass", "pending"}:
        raise SystemExit(f"Cannot rerun item in status {item.get('status')}: {item['filename']}")
    history = item.setdefault("rerun_history", [])
    history.append(
        {
            "at": now_iso(),
            "from_status": item.get("status"),
            "note": args.note,
            "output_path": item.get("output_path", ""),
            "worker_result": item.get("worker_result", {}),
            "parent_inspection": item.get("parent_inspection", {}),
        }
    )
    hints = item.setdefault("rerun_prompt_hints", [])
    if args.note and args.note not in hints:
        hints.append(args.note)
    item["status"] = "pending"
    item["rerun_pending"] = True
    item["parent_note"] = args.note
    item["parent_inspection"] = {"result": "needs_rerun", "note": args.note, "inspected_at": now_iso()}
    item["batch_id"] = ""
    item["worker_status"] = ""
    item["worker_note"] = ""
    item["worker_result"] = {}
    write_batch_plan(run_dir, state)
    save_state(run_dir, state)
    print(f"RERUN_PENDING: {item['filename']}")
    print("NEXT: Resolve any other imported/current items, then run next-batch.")


def command_batch_status(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    batch = next((batch for batch in state.get("batches", []) if batch.get("id") == args.batch_id), None)
    if not batch:
        raise SystemExit(f"Unknown batch: {args.batch_id}")
    print(f"BATCH_ID: {args.batch_id}")
    print(f"ITEMS: {len(batch.get('items', []))}")
    for item_id in batch.get("items", []):
        item = resolve_item(state, item_id)
        worker = item.get("worker_result", {}).get("status") or item.get("worker_status", "")
        print(f"- {item['filename']}: {item.get('status')} worker={worker}")


def command_batch_prompts(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    batch = next((batch for batch in state.get("batches", []) if batch.get("id") == args.batch_id), None)
    if not batch:
        raise SystemExit(f"Unknown batch: {args.batch_id}")
    print(f"BATCH_ID: {args.batch_id}")
    for item_id in batch.get("items", []):
        item = resolve_item(state, item_id)
        if not item.get("artifact_paths", {}).get("subagent_prompt"):
            write_item_artifacts(run_dir, item, state)
        print(f"ITEM: {item['filename']}")
        print(f"PROMPT_FILE: {item['prompt_file']}")
        print(f"SUBAGENT_PROMPT: {item['artifact_paths']['subagent_prompt']}")
    save_state(run_dir, state)


def command_status(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    counts: dict[str, int] = {}
    for item in state.get("items", []):
        counts[item.get("status", "unknown")] = counts.get(item.get("status", "unknown"), 0) + 1
    print(f"RUN_DIR: {run_dir}")
    print(f"PLAN_APPROVED: {state.get('plan_approved')}")
    print(f"ITEMS: {len(state.get('items', []))}")
    for status in sorted(counts):
        print(f"{status}: {counts[status]}")
    blockers = current_blockers(state)
    if blockers:
        print("CURRENT_BLOCKERS:")
        for item in blockers:
            print(f"- {item['filename']}: {item.get('status')}")
    print(f"COMPLETE: {str(bool(state.get('complete'))).lower()}")


def command_report(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    total = len(state.get("items", []))
    inspected = sum(1 for item in state.get("items", []) if item.get("status") in PASS_STATUSES)
    rerun_count = sum(1 for item in state.get("items", []) if item.get("rerun_pending") or item.get("rerun_history"))
    blockers = current_blockers(state)
    spatial_groups = sorted({item.get("spatial_group") for item in state.get("items", []) if item.get("spatial_group")})
    web_reference_count = sum(len(item.get("web_references", [])) for item in state.get("items", []))
    zero_web_reference_items = [
        f"{item.get('filename', '')} - {item.get('web_reference_search_note') or '사유 미기록'}"
        for item in state.get("items", [])
        if len(item.get("web_references", [])) == 0
    ]
    below_recommended_web_reference_items = [
        f"{item.get('filename', '')} ({len(item.get('web_references', []))}개)"
        for item in state.get("items", [])
        if len(item.get("web_references", [])) < WEB_REFERENCE_RECOMMENDED_MIN
    ]
    missing_web_references = [
        ref.get("local_path", "")
        for item in state.get("items", [])
        for ref in item.get("web_references", [])
        if ref.get("local_path") and not Path(ref.get("local_path")).exists()
    ]
    batches = state.get("batches", [])
    current_batch = batches[-1]["id"] if batches else "없음"
    print("[영상 시나리오 이미지 팩 진행 결과]")
    print(f"- 시나리오: {state.get('title', '')}")
    print(f"- 저장 폴더: {run_dir}")
    print(f"- 상태 파일: {run_dir / 'state.json'}")
    print(f"- 승인된 이미지 수: {total}")
    print("- 캐릭터 포함 정책: 기본값 캐릭터/인물 미포함")
    print(f"- 공간 일관성 기준: {', '.join(spatial_groups) if spatial_groups else '없음'}")
    print(f"- 웹 참고 자료: {web_reference_count}개")
    print(f"- 웹 참고 자료 0개 항목: {', '.join(zero_web_reference_items) if zero_web_reference_items else '없음'}")
    print(
        f"- 웹 참고 자료 권장 미만(3개 미만): "
        f"{', '.join(below_recommended_web_reference_items) if below_recommended_web_reference_items else '없음'}"
    )
    print(f"- 웹 참고 자료 누락: {', '.join(missing_web_references) if missing_web_references else '없음'}")
    print(f"- 이번 병렬 그룹: {current_batch}")
    print(f"- worker 검수 결과: 상태 파일의 worker_result 참조")
    print(f"- 부모 검수 결과: {inspected}/{total} inspected_pass")
    print(f"- rerun 필요/진행 항목: {rerun_count}")
    print(f"- 현재 차단 항목: {', '.join(item['filename'] for item in blockers) if blockers else '없음'}")
    print(f"- 다음 결정: {'완료' if state.get('complete') else '남은 항목 진행 또는 rerun 처리'}")


def command_write_plan_template(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state = load_state(run_dir)
    template = {
        "scenario_title": state.get("title", "video-scenario"),
        "items": [
            {
                "id": "001-location-master",
                "filename": "001-location-master.png",
                "scene_refs": ["S01"],
                "category": "location_master",
                "contains_character": False,
                "purpose": "Reusable establishing source.",
                "visual_brief": "Empty location master with fixed landmarks.",
                "spatial_group": "main-location",
                "continuity_anchor": "",
                "fixed_layout_notes": "Record stable landmark positions here.",
                "camera_view": "wide establishing view",
                "must_match": ["no people, cars, silhouettes, or readable text"],
                "web_reference_search_note": "Search every source item before approval. Target at least 1 web reference; prefer 3-5. If 0 or fewer than 3 are usable, record search terms and exclusion/failure reasons here.",
                "web_references": [
                    {
                        "id": "location-layout-reference",
                        "local_path": "web_references/001-location-master/location-layout-reference.jpg",
                        "source_url": "https://example.com/location-layout-reference.jpg",
                        "page_url": "https://example.com/location-layout-reference",
                        "source_title": "Location layout reference page",
                        "reference_purpose": "Factual reference for material, spatial layout, landmarks, mood, or prop state.",
                        "observed_facts": ["wide empty layout", "stable landmark relationship"],
                        "usage_note": "Use only factual cues; do not copy composition, watermark, logo, people, brand styling, or artist-specific style.",
                    },
                    {
                        "id": "location-material-reference",
                        "local_path": "web_references/001-location-master/location-material-reference.jpg",
                        "source_url": "https://example.com/location-material-reference.jpg",
                        "page_url": "https://example.com/location-material-reference",
                        "source_title": "Location material reference page",
                        "reference_purpose": "Factual reference for surface and wall material.",
                        "observed_facts": ["weathered wall material", "empty pavement texture"],
                        "usage_note": "Use only factual cues; do not copy composition, watermark, logo, people, brand styling, or artist-specific style.",
                    },
                    {
                        "id": "location-mood-reference",
                        "local_path": "web_references/001-location-master/location-mood-reference.jpg",
                        "source_url": "https://example.com/location-mood-reference.jpg",
                        "page_url": "https://example.com/location-mood-reference",
                        "source_title": "Location mood reference page",
                        "reference_purpose": "Factual reference for time of day, weather, and mood.",
                        "observed_facts": ["late afternoon light", "dry clear weather"],
                        "usage_note": "Use only factual cues; do not copy composition, watermark, logo, people, brand styling, or artist-specific style.",
                    },
                ],
                "prompt": "Photoreal cinematic production reference of an empty location...",
                "negative_prompt": "",
                "dependencies": [],
                "notes": "",
            }
        ],
    }
    path = run_dir / "approved_image_plan.template.json"
    write_json_atomic(path, template)
    print(f"PLAN_TEMPLATE: {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage create-video-scenario-image-pack state.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--title", default="")
    init.add_argument("--scenario", default="")
    init.add_argument("--scenario-summary", default="")
    init.add_argument("--output-root", default="")
    init.add_argument("--run-dir", default="")
    init.set_defaults(func=command_init)

    approve = subparsers.add_parser("approve-plan")
    approve.add_argument("--run-dir", required=True)
    approve.add_argument("--plan-file", default="")
    approve.add_argument("--plan-json", default="")
    approve.set_defaults(func=command_approve_plan)

    write_template = subparsers.add_parser("write-plan-template")
    write_template.add_argument("--run-dir", required=True)
    write_template.set_defaults(func=command_write_plan_template)

    next_batch = subparsers.add_parser("next-batch")
    next_batch.add_argument("--run-dir", required=True)
    next_batch.add_argument("--limit", type=int, default=4)
    next_batch.set_defaults(func=command_next_batch)

    batch_prompts = subparsers.add_parser("batch-prompts")
    batch_prompts.add_argument("--run-dir", required=True)
    batch_prompts.add_argument("--batch-id", required=True)
    batch_prompts.set_defaults(func=command_batch_prompts)

    import_cmd = subparsers.add_parser("import")
    import_cmd.add_argument("--run-dir", required=True)
    import_cmd.add_argument("--item", required=True)
    import_cmd.add_argument("--generated", required=True)
    import_cmd.add_argument("--worker-status", choices=["pass", "needs_rerun"], required=True)
    import_cmd.add_argument("--worker-note", required=True)
    import_cmd.set_defaults(func=command_import)

    import_batch = subparsers.add_parser("import-batch")
    import_batch.add_argument("--manifest", required=True)
    import_batch.add_argument("--run-dir", default="")
    import_batch.set_defaults(func=command_import_batch)

    inspect_pass = subparsers.add_parser("inspect-pass")
    inspect_pass.add_argument("--run-dir", required=True)
    inspect_pass.add_argument("--item", required=True)
    inspect_pass.add_argument("--note", required=True)
    inspect_pass.set_defaults(func=command_inspect_pass)

    inspect_batch = subparsers.add_parser("inspect-batch-pass")
    inspect_batch.add_argument("--manifest", required=True)
    inspect_batch.add_argument("--run-dir", default="")
    inspect_batch.set_defaults(func=command_inspect_batch_pass)

    rerun = subparsers.add_parser("rerun")
    rerun.add_argument("--run-dir", required=True)
    rerun.add_argument("--item", required=True)
    rerun.add_argument("--note", required=True)
    rerun.set_defaults(func=command_rerun)

    batch_status = subparsers.add_parser("batch-status")
    batch_status.add_argument("--run-dir", required=True)
    batch_status.add_argument("--batch-id", required=True)
    batch_status.set_defaults(func=command_batch_status)

    status = subparsers.add_parser("status")
    status.add_argument("--run-dir", required=True)
    status.set_defaults(func=command_status)

    report = subparsers.add_parser("report")
    report.add_argument("--run-dir", required=True)
    report.set_defaults(func=command_report)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
