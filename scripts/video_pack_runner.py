#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


WORKFLOW = "create-video-closeup-reference-pack"
ANCHOR_POLICY = "auto_if_pass"
SOURCE_NAME = "source_character_sheet.png"
GENERATED_ROOT = Path("/Users/chasoik/.codex/generated_images")
DONE_STATUSES = {"inspected_pass", "complete"}
GENERATED_STATUSES = {"imported", "inspected_pass", "complete"}
WORKER_STATUS_VALUES = {None, "pass", "needs_rerun"}
STATUS_VALUES = {
    "pending",
    "generation_requested",
    "imported",
    "inspected_pass",
    "needs_rerun",
    "complete",
}


ITEMS = [
    {
        "output": "01_face_front.png",
        "skill": "create-face-front-closeup",
        "dependencies": [SOURCE_NAME],
        "notes": "Master front-facing face identity anchor. Neutral head-and-shoulders studio portrait.",
        "prompt": "Generate a front-facing head-and-shoulders face closeup of the same person. Keep the face centered, neutral, photorealistic, and suitable as the master identity anchor.",
    },
    {
        "output": "02_03_face_3q_pair.png",
        "skill": "create-face-3q-left-closeup + create-face-3q-right-closeup",
        "dependencies": ["01_face_front.png"],
        "notes": "Paired 3/4 face views in one image. Left panel points image-left; right panel points image-right.",
        "prompt": "Create one image with two equal side-by-side 3/4 face closeup panels. Left panel: the subject's nose and face direction point toward image-left. Right panel: the subject's nose and face direction point toward image-right. Same person, same lighting, same crop, no text labels.",
    },
    {
        "output": "04_05_face_side_pair.png",
        "skill": "create-face-side-left-profile + create-face-side-right-profile",
        "dependencies": ["01_face_front.png"],
        "notes": "Paired full side profiles in one image. Left panel points image-left; right panel points image-right.",
        "prompt": "Create one image with two equal side-by-side full side-profile face panels. Left panel: the subject's nose and face direction point toward image-left. Right panel: the subject's nose and face direction point toward image-right. Same person, same lighting, same crop, no text labels.",
    },
    {
        "output": "06_eye_macro.png",
        "skill": "create-eye-brow-macro-closeup",
        "dependencies": ["01_face_front.png"],
        "notes": "Macro eyes and brows with natural skin and lash detail.",
        "prompt": "Generate a photoreal macro closeup of the same character's eyes, brows, lashes, eyelids, iris color, and surrounding natural skin texture.",
    },
    {
        "output": "07_expression_sheet.png",
        "skill": "create-expression-six-sheet",
        "dependencies": ["01_face_front.png"],
        "notes": "Six no-label expression panels.",
        "prompt": "Generate a six-panel no-label photoreal expression sheet of the same person: neutral, subtle smile, surprised, thinking, slightly embarrassed, and confident or determined. Keep camera, lighting, hair, and upper outfit consistent.",
    },
    {
        "output": "08_mouth_speech_sheet.png",
        "skill": "create-mouth-speech-sheet",
        "dependencies": ["01_face_front.png"],
        "notes": "Six no-label lip-sync mouth shape panels.",
        "prompt": "Generate a six-panel no-label photoreal dialogue mouth-shape sheet of the same person: closed neutral, small open mouth, wide vowel mouth, soft speaking smile, surprised open mouth, and thoughtful half-open mouth.",
    },
    {
        "output": "09_hair_front_detail.png",
        "skill": "create-hair-front-detail-closeup",
        "dependencies": ["01_face_front.png"],
        "notes": "Front hair, bangs, hairline, and front accessory placement.",
        "prompt": "Generate a photoreal front hair detail closeup preserving the same bangs, hairline, hair color, hair volume, side strands, flyaways, and front accessory placement.",
    },
    {
        "output": "10_hair_accessory_macro.png",
        "skill": "create-hair-accessory-macro",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Hair ornament material and attachment macro.",
        "prompt": "Generate a photoreal macro closeup of the character's hair accessory from the source sheet, showing material, shape, attachment to hair, ribbon or metal details, and realistic hair strands around it.",
    },
    {
        "output": "11_upper_costume_closeup.png",
        "skill": "create-upper-costume-closeup",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Upper outfit details, collar, bow or neck detail, trims, badges, cuffs, and fabric.",
        "prompt": "Generate a neutral photoreal upper-costume closeup focused on collar, neck accessory, top, jacket or vest, seams, buttons, trim, badges, cuffs, and fabric texture. Keep it reference-oriented and non-glamour.",
    },
    {
        "output": "12_hand_sleeve_closeup.png",
        "skill": "create-hand-sleeve-gesture-closeup",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Natural hand anatomy with sleeve or wrist details.",
        "prompt": "Generate a photoreal closeup of one natural hand gesture with accurate fingers, nails, wrist, sleeve cuff, and any small prop or accessory shown in the source sheet.",
    },
    {
        "output": "13_belt_props_closeup.png",
        "skill": "create-belt-props-closeup",
        "dependencies": [SOURCE_NAME],
        "notes": "Waist, belt, pouch, notebook, pen, emblem, chain, or other signature prop details.",
        "prompt": "Generate a photoreal closeup of the character's belt, waist details, small props, notebook, pen, emblem, pouch, chain, buckles, or signature hardware from the source sheet.",
    },
    {
        "output": "14_shoes_closeup.png",
        "skill": "create-shoes-lower-outfit-closeup",
        "dependencies": [SOURCE_NAME],
        "notes": "Shoes, lower outfit, stockings or socks, soles, buckles, laces, and hem.",
        "prompt": "Generate a photoreal lower-outfit and shoes closeup preserving shoe shape, material, heel or sole, laces or buckles, socks or tights, lower garment hem, and realistic scale.",
    },
    {
        "output": "15_full_body_front.png",
        "skill": "create-full-body-front-reference",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Neutral head-to-toe front reference.",
        "prompt": "Generate a neutral full-body front reference of the same character, head to toe, preserving face, hair, outfit, accessories, body proportions, and shoes. Use straight-on studio framing.",
    },
    {
        "output": "16_full_body_back.png",
        "skill": "create-full-body-back-reference",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Neutral full-body back reference.",
        "prompt": "Generate a neutral full-body back reference of the same character, preserving back hair silhouette, rear outfit details, accessories, lower outfit, and shoes. Use straight-on studio framing.",
    },
    {
        "output": "17_full_body_side.png",
        "skill": "create-full-body-side-reference",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Neutral full-body side reference.",
        "prompt": "Generate a neutral full-body side reference of the same character, preserving side face profile, hair volume, outfit thickness, accessories, proportions, and shoes. Use studio framing.",
    },
    {
        "output": "18_character_pose_idle.png",
        "skill": "create-character-idle-pose",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Relaxed neutral idle pose for video reference.",
        "prompt": "Generate a relaxed neutral idle standing pose of the same character for video reference. Preserve identity, outfit, accessories, and shoes. Keep the pose age-appropriate, non-glamour, and studio-reference oriented.",
    },
    {
        "output": "face_turnaround_sheet.png",
        "skill": "create-face-turnaround-sheet",
        "dependencies": ["01_face_front.png"],
        "notes": "Five-angle face sheet with no labels.",
        "prompt": "Generate a no-label five-angle photoreal face turnaround sheet of the same person: front, left 3/4, right 3/4, left side profile, and right side profile. Keep lighting, crop, hairstyle, and upper outfit consistent.",
    },
    {
        "output": "hand_gesture_four_sheet.png",
        "skill": "create-hand-gesture-four-sheet",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Four no-label hand gesture panels.",
        "prompt": "Generate a no-label four-panel photoreal hand gesture sheet preserving the character's sleeve and hand details: relaxed hand, pointing or explaining gesture, holding a small prop from the source sheet, and touching collar or accessory.",
    },
]


COMMON_NEGATIVE = (
    "Negative prompt:\n"
    "anime, manga, cartoon, illustration, digital painting, semi-realistic art, "
    "3D render, CGI, game asset, doll-like face, wax figure, plastic skin, glossy AI smoothness, "
    "overly perfect beauty retouching, over-sharpening, unreal symmetry, mannequin body, "
    "artificial lighting, random outfit changes, redesigned face, different age, inconsistent hairstyle, "
    "extra fingers, distorted hands, unreadable text, watermark, logo text, low resolution, "
    "low-angle body framing, suggestive pose."
)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_batch_id():
    return "batch-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or "video-closeup-pack"


def display_path(path):
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(resolved)


def is_complete(state):
    return all(item["status"] in DONE_STATUSES for item in state["items"])


def output_root():
    return Path.cwd() / "output"


def generated_root():
    return Path(os.environ.get("VIDEO_PACK_GENERATED_ROOT", str(GENERATED_ROOT)))


def read_state(run_dir):
    state_path = run_dir / "state.json"
    with state_path.open() as handle:
        state = json.load(handle)
    normalize_state(state)
    validate_state(state)
    return state


def write_state(run_dir, state):
    state["complete"] = is_complete(state)
    with (run_dir / "state.json").open("w") as handle:
        json.dump(state, handle, indent=2)
        handle.write("\n")


def validate_state(state):
    if state.get("workflow") != WORKFLOW:
        raise ValueError("state.json is not a video closeup reference pack run")
    for item in state.get("items", []):
        if item.get("status") not in STATUS_VALUES:
            raise ValueError(f"invalid item status: {item.get('status')}")
        if item.get("worker_status") not in WORKER_STATUS_VALUES:
            raise ValueError(f"invalid worker_status: {item.get('worker_status')}")


def normalize_state(state):
    for item in state.get("items", []):
        item.setdefault("batch_id", None)
        item.setdefault("worker_status", None)
        item.setdefault("worker_note", "")
        item.setdefault("parent_inspected_at", None)


def find_incomplete_run(source_hash):
    root = output_root()
    if not root.exists():
        return None
    matches = []
    for state_path in root.glob("*/state.json"):
        try:
            state = read_state(state_path.parent)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if state.get("source_sha256") == source_hash and not is_complete(state):
            matches.append(state_path.parent)
    if not matches:
        return None
    matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0]


def prompt_file_for(output):
    stem = Path(output).stem
    return f"prompts/{stem}.prompt.txt"


def build_prompt(item):
    return (
        "Use the provided source character sheet and any approved master face anchor in this run folder "
        "as the only visual authority. Generate the requested video-production photoreal reference image.\n\n"
        f"Intended output filename: {item['output']}\n"
        f"Skill: {item['skill']}\n\n"
        "Request:\n"
        f"{item['prompt']}\n\n"
        "Global preservation rules:\n"
        "- Preserve the same person, age impression, face shape, eye shape, skin tone, hair color, hairstyle, outfit logic, accessories, and material palette from the source sheet.\n"
        "- Use true photorealistic live-action studio reference photography with natural skin texture, realistic hair strands, slight asymmetry, and restrained retouching.\n"
        "- Use a simple white, light gray, or neutral studio background unless the item specifically requires a prop closeup.\n"
        "- Do not add text labels, watermarks, logos, or redesigned costume details.\n"
        "- Keep every output age-appropriate, neutral, non-glamour, and non-sensual.\n\n"
        f"{COMMON_NEGATIVE}\n"
    )


def write_prompt_files(run_dir):
    prompts_dir = run_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for item in ITEMS:
        prompt_path = run_dir / prompt_file_for(item["output"])
        prompt_path.write_text(build_prompt(item))


def write_batch_plan(run_dir):
    lines = [
        "# Video Closeup Reference Pack Batch Plan",
        "",
        f"Run folder: {display_path(run_dir)}",
        "",
        "Generation policy:",
        "- Use state.json as the source of truth.",
        "- For serial generation, call `next` before each image generation so the item is marked generation_requested.",
        "- For parallel generation, call `next-batch --limit 4` and assign one reserved item to each subagent.",
        "- In parallel mode, import each generated file with explicit `import --item <filename> --generated <path>` mapping.",
        "- After import, the parent session must inspect the image, then run `inspect-pass` or `rerun`.",
        "- Do not create a new run when an incomplete run with the same source hash exists.",
        "",
        "Batch items:",
        "",
    ]
    for item in ITEMS:
        lines.extend(
            [
                f"- output: {item['output']}",
                f"  skill: {item['skill']}",
                f"  request_group: {request_group(item['output'])}",
                f"  dependencies: {', '.join(item['dependencies'])}",
                f"  notes: {item['notes']}",
                "",
            ]
        )
    (run_dir / "batch_plan.md").write_text("\n".join(lines).rstrip() + "\n")


def request_group(output):
    if output == "01_face_front.png":
        return "anchor"
    if output in {"02_03_face_3q_pair.png", "04_05_face_side_pair.png"}:
        return "paired-face-views"
    if output.startswith(("06_", "07_", "08_", "09_", "10_")) or output == "face_turnaround_sheet.png":
        return "parallel-face-detail"
    if output.startswith(("11_", "13_", "14_")):
        return "parallel-costume-props"
    if output.startswith("12_") or output == "hand_gesture_four_sheet.png":
        return "parallel-hands"
    return "parallel-full-body"


def create_state(run_dir, source, source_hash):
    items = []
    for item in ITEMS:
        items.append(
            {
                "output": item["output"],
                "skill": item["skill"],
                "prompt_file": prompt_file_for(item["output"]),
                "dependencies": item["dependencies"],
                "status": "pending",
                "requested_at": None,
                "generated_source": None,
                "batch_id": None,
                "worker_status": None,
                "worker_note": "",
                "parent_inspected_at": None,
                "inspection": {},
            }
        )
    return {
        "source_image": SOURCE_NAME,
        "source_sha256": source_hash,
        "workflow": WORKFLOW,
        "run_dir": str(run_dir.resolve()),
        "anchor_policy": ANCHOR_POLICY,
        "source_original": str(source.resolve()),
        "complete": False,
        "items": items,
    }


def command_init(args):
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"source not found: {source}")
    source_hash = sha256_file(source)

    if args.run_dir:
        run_dir = Path(args.run_dir).expanduser().resolve()
    else:
        existing = find_incomplete_run(source_hash)
        if existing:
            print(display_path(existing))
            return 0
        folder_slug = slugify(source.stem)
        prefix = folder_slug if folder_slug == "video-closeup-pack" else f"{folder_slug}-video-closeup-pack"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = (output_root() / f"{prefix}-{timestamp}").resolve()

    run_dir.mkdir(parents=True, exist_ok=True)
    state_path = run_dir / "state.json"
    if state_path.exists():
        state = read_state(run_dir)
        if state.get("source_sha256") != source_hash:
            raise SystemExit("existing run-dir state.json has a different source_sha256")
        print(display_path(run_dir))
        return 0

    shutil.copy2(source, run_dir / SOURCE_NAME)
    write_prompt_files(run_dir)
    write_batch_plan(run_dir)
    write_state(run_dir, create_state(run_dir, source, source_hash))
    print(display_path(run_dir))
    return 0


def item_by_output(state, output):
    for item in state["items"]:
        if item["output"] == output:
            return item
    raise SystemExit(f"item not found: {output}")


def anchor_ready(state):
    try:
        anchor = item_by_output(state, "01_face_front.png")
    except SystemExit:
        return False
    return anchor["status"] in DONE_STATUSES


def dependency_ready(state, item):
    if item["output"] != "01_face_front.png" and not anchor_ready(state):
        return False
    by_output = {entry["output"]: entry for entry in state["items"]}
    for dependency in item["dependencies"]:
        if dependency in by_output and by_output[dependency]["status"] not in DONE_STATUSES:
            return False
    return True


def import_blocking_items(state):
    return [item for item in state["items"] if item["status"] == "imported"]


def requested_items(state):
    return [item for item in state["items"] if item["status"] == "generation_requested"]


def next_item(state):
    requested = requested_items(state)
    if requested:
        return requested[0], False
    if import_blocking_items(state):
        return None, False
    for item in state["items"]:
        if item["status"] in {"needs_rerun", "pending"} and dependency_ready(state, item):
            return item, True
    return None, False


def next_batch_candidates(state, limit):
    if limit < 1:
        raise SystemExit("--limit must be greater than 0")

    imported = import_blocking_items(state)
    if imported:
        return [], None, "imported_blocking"

    requested = requested_items(state)
    if requested:
        batch_id = requested[0].get("batch_id") or "single-item"
        return requested, batch_id, "existing"

    candidates = []
    for status in ("needs_rerun", "pending"):
        for item in state["items"]:
            if item["status"] == status and dependency_ready(state, item):
                candidates.append(item)
                if len(candidates) >= limit:
                    return candidates, None, "new"
    return candidates, None, "new"


def print_item_request(run_dir, item, include_prompt=True):
    prompt_path = run_dir / item["prompt_file"]
    print(f"output: {item['output']}")
    print(f"skill: {item['skill']}")
    print(f"prompt_file: {item['prompt_file']}")
    if item.get("batch_id"):
        print(f"batch_id: {item['batch_id']}")
    print("")
    if include_prompt:
        print(prompt_path.read_text())


def print_batch_request(run_dir, batch_id, items):
    print(f"batch_id: {batch_id}")
    print(f"items: {len(items)}")
    print("")
    for index, item in enumerate(items, start=1):
        print(f"--- item {index} ---")
        print_item_request(run_dir, item, include_prompt=True)


def command_next_batch(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    if is_complete(state):
        print("No pending items. Pack is complete.")
        return 0

    items, batch_id, mode = next_batch_candidates(state, args.limit)
    if mode == "imported_blocking":
        print("A batch has imported items awaiting parent inspection. Inspect or rerun them before reserving another batch.")
        return 0
    if not items:
        print("No pending items are dependency-ready. Inspect or rerun the blocking item first.")
        return 0

    if mode == "new":
        batch_id = new_batch_id()
        requested_at = now_iso()
        for item in items:
            item["status"] = "generation_requested"
            item["requested_at"] = requested_at
            item["batch_id"] = batch_id
            item["worker_status"] = None
            item["worker_note"] = ""
            item["parent_inspected_at"] = None
            item["inspection"] = {}
        write_state(run_dir, state)

    print_batch_request(run_dir, batch_id, items)
    return 0


def command_next(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    if is_complete(state):
        print("No pending items. Pack is complete.")
        return 0

    item, should_mark = next_item(state)
    if item is None:
        print("No pending items are dependency-ready. Inspect or rerun the blocking item first.")
        return 0
    if should_mark:
        item["status"] = "generation_requested"
        item["requested_at"] = now_iso()
        item["batch_id"] = None
        item["worker_status"] = None
        item["worker_note"] = ""
        item["parent_inspected_at"] = None
        item["inspection"] = {}
        write_state(run_dir, state)

    print_item_request(run_dir, item, include_prompt=True)
    return 0


def requested_item(state):
    requested = requested_items(state)
    if len(requested) == 1:
        return requested[0]
    if len(requested) > 1:
        raise SystemExit("multiple items are marked generation_requested; use `import --item <filename> --generated <path>`")
    raise SystemExit("no item is marked generation_requested")


def latest_generated_after(requested_at):
    threshold = datetime.fromisoformat(requested_at).timestamp()
    candidates = []
    root = generated_root()
    if not root.exists():
        raise SystemExit(f"generated image root not found: {root}")
    for path in root.glob("**/*.png"):
        if path.stat().st_mtime >= threshold:
            candidates.append(path)
    if not candidates:
        raise SystemExit("no generated PNG found after requested_at")
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0]


def command_import_latest(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    item = requested_item(state)
    if args.generated:
        generated = Path(args.generated).expanduser().resolve()
    else:
        generated = latest_generated_after(item["requested_at"])
    if not generated.exists():
        raise SystemExit(f"generated image not found: {generated}")

    shutil.copy2(generated, run_dir / item["output"])
    item["status"] = "imported"
    item["generated_source"] = str(generated)
    item["worker_status"] = None
    item["worker_note"] = ""
    item["parent_inspected_at"] = None
    item["inspection"] = {}
    write_state(run_dir, state)
    print(f"imported: {item['output']}")
    print(f"generated_source: {generated}")
    return 0


def command_import(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    item = item_by_output(state, args.item)
    if item["status"] != "generation_requested":
        raise SystemExit(f"item is not marked generation_requested: {item['output']}")

    generated = Path(args.generated).expanduser().resolve()
    if not generated.exists():
        raise SystemExit(f"generated image not found: {generated}")

    shutil.copy2(generated, run_dir / item["output"])
    item["status"] = "imported"
    item["generated_source"] = str(generated)
    item["worker_status"] = args.worker_status
    item["worker_note"] = args.worker_note or ""
    item["parent_inspected_at"] = None
    item["inspection"] = {}
    write_state(run_dir, state)
    print(f"imported: {item['output']}")
    print(f"generated_source: {generated}")
    if args.worker_status:
        print(f"worker_status: {args.worker_status}")
    return 0


def command_inspect_pass(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    item = item_by_output(state, args.item)
    if not (run_dir / item["output"]).exists():
        raise SystemExit(f"output file does not exist: {item['output']}")
    inspected_at = now_iso()
    item["status"] = "inspected_pass"
    item["parent_inspected_at"] = inspected_at
    item["inspection"] = {
        "result": "pass",
        "note": args.note or "",
        "inspected_at": inspected_at,
    }
    write_state(run_dir, state)
    print(f"inspected_pass: {item['output']}")
    return 0


def command_status(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    generated = sum(1 for item in state["items"] if item["status"] in GENERATED_STATUSES)
    pending = sum(1 for item in state["items"] if item["status"] == "pending")
    needs_rerun = sum(1 for item in state["items"] if item["status"] == "needs_rerun")
    generation_requested = sum(1 for item in state["items"] if item["status"] == "generation_requested")
    imported = sum(1 for item in state["items"] if item["status"] == "imported")
    active_batches = sorted(
        {
            item["batch_id"]
            for item in state["items"]
            if item.get("batch_id") and item["status"] in {"generation_requested", "imported"}
        }
    )
    complete = is_complete(state)

    print(f"run_dir: {display_path(run_dir)}")
    print(f"complete: {str(complete).lower()}")
    print(f"generated: {generated}")
    print(f"imported_uninspected: {imported}")
    print(f"pending: {pending}")
    print(f"needs_rerun: {needs_rerun}")
    print(f"generation_requested: {generation_requested}")
    print(f"active_batches: {len(active_batches)}")
    for batch_id in active_batches:
        print(f"- {batch_id}")
    return 0


def command_batch_status(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    items = [item for item in state["items"] if item.get("batch_id") == args.batch_id]
    if not items:
        raise SystemExit(f"batch not found: {args.batch_id}")

    print(f"batch_id: {args.batch_id}")
    print(f"items: {len(items)}")
    for status in ("generation_requested", "imported", "inspected_pass", "needs_rerun", "pending", "complete"):
        count = sum(1 for item in items if item["status"] == status)
        print(f"{status}: {count}")
    worker_pass = sum(1 for item in items if item.get("worker_status") == "pass")
    worker_needs_rerun = sum(1 for item in items if item.get("worker_status") == "needs_rerun")
    print(f"worker_pass: {worker_pass}")
    print(f"worker_needs_rerun: {worker_needs_rerun}")
    print("items_detail:")
    for item in items:
        worker_status = item.get("worker_status") or "none"
        print(f"- {item['output']}: status={item['status']} worker_status={worker_status}")
    return 0


def command_rerun(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    item = item_by_output(state, args.item)
    item["status"] = "needs_rerun"
    item["requested_at"] = None
    item["worker_status"] = None
    item["worker_note"] = ""
    item["parent_inspected_at"] = None
    item["inspection"] = {
        "result": "needs_rerun",
        "note": args.note or "",
        "inspected_at": now_iso(),
    }
    write_state(run_dir, state)
    print(f"needs_rerun: {item['output']}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Manage resumable video closeup reference pack runs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--source", required=True)
    init.add_argument("--run-dir")
    init.set_defaults(func=command_init)

    next_parser = subparsers.add_parser("next")
    next_parser.add_argument("--run-dir", required=True)
    next_parser.set_defaults(func=command_next)

    next_batch = subparsers.add_parser("next-batch")
    next_batch.add_argument("--run-dir", required=True)
    next_batch.add_argument("--limit", type=int, default=4)
    next_batch.set_defaults(func=command_next_batch)

    import_latest = subparsers.add_parser("import-latest")
    import_latest.add_argument("--run-dir", required=True)
    import_latest.add_argument("--generated")
    import_latest.set_defaults(func=command_import_latest)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--run-dir", required=True)
    import_parser.add_argument("--item", required=True)
    import_parser.add_argument("--generated", required=True)
    import_parser.add_argument("--worker-status", choices=["pass", "needs_rerun"])
    import_parser.add_argument("--worker-note")
    import_parser.set_defaults(func=command_import)

    inspect_pass = subparsers.add_parser("inspect-pass")
    inspect_pass.add_argument("--run-dir", required=True)
    inspect_pass.add_argument("--item", required=True)
    inspect_pass.add_argument("--note")
    inspect_pass.set_defaults(func=command_inspect_pass)

    status = subparsers.add_parser("status")
    status.add_argument("--run-dir", required=True)
    status.set_defaults(func=command_status)

    batch_status = subparsers.add_parser("batch-status")
    batch_status.add_argument("--run-dir", required=True)
    batch_status.add_argument("--batch-id", required=True)
    batch_status.set_defaults(func=command_batch_status)

    rerun = subparsers.add_parser("rerun")
    rerun.add_argument("--run-dir", required=True)
    rerun.add_argument("--item", required=True)
    rerun.add_argument("--note")
    rerun.set_defaults(func=command_rerun)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    sys.exit(main())
