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


WORKFLOW = "create-character-sheet-closeup-reference-pack"
ANCHOR_POLICY = "auto_if_pass"
SOURCE_NAME = "source_character_sheet.png"
GENERATED_ROOT = Path("/Users/chasoik/.codex/generated_images")
STYLE_MODES = {"preserve_source_style", "photoreal_conversion", "custom_style_override"}
PRESETS = {"core", "full"}
DONE_STATUSES = {"inspected_pass", "complete"}
STATUS_VALUES = {
    "pending",
    "generation_requested",
    "imported",
    "inspected_pass",
    "needs_rerun",
    "complete",
}


CORE_ITEMS = [
    {
        "output": "01_face_front.png",
        "purpose": "Primary front-facing face identity closeup.",
        "request_group": "identity_anchor",
        "prompt_template": "01 Face Front",
        "dependencies": [SOURCE_NAME],
        "notes": "Master identity anchor. Front-facing head-and-shoulders closeup.",
        "prompt": (
            "Create a front-facing face identity closeup derived from the approved character sheet. "
            "Show the face, hairline, eyes, expression baseline, head shape, and upper shoulders clearly. "
            "Use a neutral or soft default expression and a simple clean background."
        ),
    },
    {
        "output": "02_03_face_3q_pair.png",
        "purpose": "Paired left/right three-quarter face views.",
        "request_group": "face_direction_pairs",
        "prompt_template": "02 03 Face Three-Quarter Pair",
        "dependencies": ["01_face_front.png"],
        "notes": "One two-panel image. Left panel points image-left; right panel points image-right.",
        "prompt": (
            "Create one image with two equal side-by-side three-quarter face closeup panels. "
            "Left panel: the character's nose and face direction point toward image-left. "
            "Right panel: the character's nose and face direction point toward image-right. "
            "Use the same crop, same source style, same lighting, same clothing, and same facial identity."
        ),
    },
    {
        "output": "04_05_face_side_pair.png",
        "purpose": "Paired left/right side profile face views.",
        "request_group": "face_direction_pairs",
        "prompt_template": "04 05 Face Side Pair",
        "dependencies": ["01_face_front.png"],
        "notes": "One two-panel image. Left panel points image-left; right panel points image-right.",
        "prompt": (
            "Create one image with two equal side-by-side clean side-profile face panels. "
            "Left panel: the character's nose and face direction point toward image-left. "
            "Right panel: the character's nose and face direction point toward image-right. "
            "Match hair silhouette, ears, accessories, neckline, and expression baseline."
        ),
    },
    {
        "output": "06_eye_detail.png",
        "purpose": "Eye shape, iris motif, lashes, makeup, highlights, or special eye effects.",
        "request_group": "parallel_details",
        "prompt_template": "Detail Outputs",
        "dependencies": ["01_face_front.png"],
        "notes": "Closeup focused on eye construction and approved eye styling.",
        "prompt": (
            "Create a closeup reference image focused on the character's eye design. "
            "Make eye shape, iris motif, eyelashes, makeup or markings, highlight style, and surrounding facial style clear."
        ),
    },
    {
        "output": "07_expression_sheet.png",
        "purpose": "Four to six expression closeups using the approved personality.",
        "request_group": "parallel_details",
        "prompt_template": "Expression Sheet",
        "dependencies": ["01_face_front.png"],
        "notes": "No-label expression sheet with consistent identity and source style.",
        "prompt": (
            "Create a four-to-six panel expression closeup sheet. Include neutral, smile, surprised, thinking, "
            "playful or embarrassed, and determined or confident expressions when appropriate. "
            "Keep the same face identity, hair, outfit neckline, lighting, and source style in every panel."
        ),
    },
    {
        "output": "08_hair_detail.png",
        "purpose": "Front hair silhouette, bangs, hair accessory, texture, color gradients, or tie shapes.",
        "request_group": "parallel_details",
        "prompt_template": "Detail Outputs",
        "dependencies": ["01_face_front.png"],
        "notes": "Closeup centered on approved hair silhouette and detail.",
        "prompt": (
            "Create a closeup reference image focused on the character's hair. "
            "Clarify front silhouette, bangs, hair accessory placement, texture, color gradients, tie shapes, and strand language."
        ),
    },
    {
        "output": "09_upper_outfit_detail.png",
        "purpose": "Collar, neck accessory, jacket, shirt, sleeve, chest emblem, fabric, and top construction.",
        "request_group": "parallel_details",
        "prompt_template": "Detail Outputs",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Closeup centered on upper outfit construction and motif details.",
        "prompt": (
            "Create a closeup reference image focused on upper outfit construction. "
            "Clarify collar, neck accessory, jacket or shirt structure, sleeves, chest emblem, fabric, trim, fasteners, and approved motifs."
        ),
    },
    {
        "output": "10_lower_outfit_shoes.png",
        "purpose": "Lower outfit, socks, shoes, soles, straps, boots, or non-human lower-body detail.",
        "request_group": "parallel_details",
        "prompt_template": "Detail Outputs",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Reference-oriented lower outfit and shoes closeup.",
        "prompt": (
            "Create a closeup reference image focused on lower outfit and shoes. "
            "Clarify garment hem, socks or stockings, shoe silhouette, soles, straps, laces, buckles, boots, or non-human lower-body details."
        ),
    },
    {
        "output": "11_hand_gesture_sheet.png",
        "purpose": "Hand shape, gloves, sleeve interaction, signature gestures, or tool-holding poses.",
        "request_group": "parallel_details",
        "prompt_template": "Hand Gesture Sheet",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Compact no-label hand and sleeve gesture reference sheet.",
        "prompt": (
            "Create a compact hand and sleeve gesture reference sheet. Include a relaxed open hand, "
            "a pointing or presenting gesture, a prop-holding gesture if a signature prop exists, "
            "and one character-specific gesture from the approved concept."
        ),
    },
    {
        "output": "12_signature_props.png",
        "purpose": "Props, weapons, mascot items, bag, belt items, charms, or other signature accessories.",
        "request_group": "parallel_details",
        "prompt_template": "Detail Outputs",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Closeup centered on signature props and accessory construction.",
        "prompt": (
            "Create a closeup reference image focused on the character's signature props and accessories. "
            "Clarify shape, material, color, attachment, motif details, scale, and how each prop belongs to the approved design."
        ),
    },
]


FULL_EXTENSION_ITEMS = [
    {
        "output": "13_face_turnaround_sheet.png",
        "purpose": "Front, three-quarter, side, and back-of-head face/hair reference in one sheet.",
        "request_group": "full_pack_extensions",
        "prompt_template": "Face Turnaround Sheet",
        "dependencies": ["01_face_front.png"],
        "notes": "No-label face and hair turnaround sheet.",
        "prompt": (
            "Create a no-label face turnaround sheet showing front, left three-quarter, right three-quarter, "
            "left side profile, right side profile, and back-of-head or rear hair reference as appropriate. "
            "Keep lighting, crop, hairstyle, and upper outfit consistent."
        ),
    },
    {
        "output": "14_mouth_speech_sheet.png",
        "purpose": "Speaking mouth shapes or emotion mouth variants while keeping face identity stable.",
        "request_group": "full_pack_extensions",
        "prompt_template": "Mouth Speech Sheet",
        "dependencies": ["01_face_front.png"],
        "notes": "No-label mouth and speech shape sheet.",
        "prompt": (
            "Create a no-label speaking mouth reference sheet for the same character. "
            "Show closed neutral, small open mouth, wide vowel mouth, speaking smile, surprised open mouth, "
            "and thoughtful half-open mouth while preserving face identity and source style."
        ),
    },
    {
        "output": "15_back_hair_or_back_detail.png",
        "purpose": "Back hair silhouette, back outfit closure, hood, wings, tail, or rear accessory.",
        "request_group": "full_pack_extensions",
        "prompt_template": "Detail Outputs",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Closeup centered on rear hair, rear outfit, or rear accessory detail.",
        "prompt": (
            "Create a closeup reference image focused on rear design details. "
            "Clarify back hair silhouette, back outfit closure, hood, wings, tail, or rear accessory details from the approved sheet."
        ),
    },
    {
        "output": "16_material_texture_details.png",
        "purpose": "Fabric, metal, leather, plastic, holographic, fur, scales, or special surface details.",
        "request_group": "full_pack_extensions",
        "prompt_template": "Detail Outputs",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Material and surface texture reference.",
        "prompt": (
            "Create a clean material and texture detail reference image. "
            "Isolate the approved fabrics, trims, metals, plastics, fur, scales, holographic materials, or special surfaces without inventing new materials."
        ),
    },
    {
        "output": "17_full_body_front.png",
        "purpose": "Full-body front pose for identity and proportion confirmation.",
        "request_group": "full_pack_extensions",
        "prompt_template": "Full Body And Pose Outputs",
        "dependencies": [SOURCE_NAME, "01_face_front.png"],
        "notes": "Neutral head-to-toe front reference.",
        "prompt": (
            "Create a full-body front reference derived from the approved character sheet. "
            "Use a neutral clean reference pose with the full body visible from head to toe."
        ),
    },
    {
        "output": "18_full_body_side_back_pair.png",
        "purpose": "Side/back or side-plus-back full-body views in one paired sheet.",
        "request_group": "full_pack_extensions",
        "prompt_template": "Full Body And Pose Outputs",
        "dependencies": ["17_full_body_front.png"],
        "notes": "One paired full-body sheet with matched outfit, proportions, and accessories.",
        "prompt": (
            "Create one image with equal side-by-side panels for full-body side and back reference views. "
            "Preserve the exact same outfit, body proportions, hairstyle, accessories, palette, and source style across views."
        ),
    },
    {
        "output": "19_idle_pose.png",
        "purpose": "Neutral standing pose for downstream animation or video use.",
        "request_group": "full_pack_extensions",
        "prompt_template": "Full Body And Pose Outputs",
        "dependencies": ["17_full_body_front.png"],
        "notes": "Neutral idle pose reference.",
        "prompt": (
            "Create a neutral idle standing pose reference derived from the approved character sheet. "
            "Preserve full-body proportions, silhouette, outfit, accessories, and source style."
        ),
    },
    {
        "output": "20_palette_motif_reference.png",
        "purpose": "Color swatches, motif icons, symbols, pattern fragments, or visual brand tokens.",
        "request_group": "full_pack_extensions",
        "prompt_template": "Palette Motif Reference",
        "dependencies": [SOURCE_NAME],
        "notes": "Clean palette and motif reference with no invented marks.",
        "prompt": (
            "Create a clean reference image for the approved color palette, motif icons, symbols, and pattern fragments. "
            "Use clean swatches and motif samples without inventing new brand marks or symbols."
        ),
    },
]


COMMON_NEGATIVE = (
    "Avoid: manual crop-only output, pasted sheet fragments presented as final pack images, "
    "redesigned face, changed age, changed species or body type, changed hairstyle, changed outfit structure, "
    "changed palette, missing signature accessory, template mannequin lines, placeholder face circles, "
    "random labels, watermark, unreadable text, unrelated background scene, and over-stylization that differs from the approved sheet."
)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


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
    return slug or "character-closeup-pack"


def display_path(path):
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(resolved)


def items_for_preset(preset):
    if preset == "core":
        return CORE_ITEMS
    if preset == "full":
        return CORE_ITEMS + FULL_EXTENSION_ITEMS
    raise ValueError(f"invalid preset: {preset}")


def is_complete(state):
    return all(item["status"] in DONE_STATUSES for item in state["items"])


def output_root():
    return Path.cwd() / "output"


def generated_root():
    return Path(os.environ.get("CHARACTER_CLOSEUP_PACK_GENERATED_ROOT", str(GENERATED_ROOT)))


def read_state(run_dir):
    state_path = run_dir / "state.json"
    with state_path.open() as handle:
        state = json.load(handle)
    validate_state(state)
    return state


def write_state(run_dir, state):
    state["complete"] = is_complete(state)
    with (run_dir / "state.json").open("w") as handle:
        json.dump(state, handle, indent=2)
        handle.write("\n")


def validate_state(state):
    if state.get("workflow") != WORKFLOW:
        raise ValueError("state.json is not a character sheet closeup reference pack run")
    if state.get("pack_preset") not in PRESETS:
        raise ValueError(f"invalid pack_preset: {state.get('pack_preset')}")
    if state.get("style_mode") not in STYLE_MODES:
        raise ValueError(f"invalid style_mode: {state.get('style_mode')}")
    for item in state.get("items", []):
        if item.get("status") not in STATUS_VALUES:
            raise ValueError(f"invalid item status: {item.get('status')}")


def find_incomplete_run(source_hash, preset, style_mode):
    root = output_root()
    if not root.exists():
        return None
    matches = []
    for state_path in root.glob("*/state.json"):
        try:
            state = read_state(state_path.parent)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if (
            state.get("source_sha256") == source_hash
            and state.get("pack_preset") == preset
            and state.get("style_mode") == style_mode
            and not is_complete(state)
        ):
            matches.append(state_path.parent)
    if not matches:
        return None
    matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0]


def prompt_file_for(output):
    stem = Path(output).stem
    return f"prompts/{stem}.prompt.txt"


def style_instruction(style_mode):
    if style_mode == "photoreal_conversion":
        return (
            "Convert to photoreal only because the run style_mode explicitly requests photoreal_conversion. "
            "Preserve identity, proportions, outfit logic, palette, motifs, and accessories from the approved source sheet."
        )
    if style_mode == "custom_style_override":
        return (
            "Use the explicit custom style override supplied by the user while preserving identity, outfit logic, palette, motifs, and accessories. "
            "If the custom style is not available in the conversation, stop and ask before generating."
        )
    return (
        "Preserve the exact approved source style. Do not convert anime, mascot, semi-real, stylized, or custom sheets into photoreal output unless explicitly requested."
    )


def build_prompt(item, state):
    return (
        "Use Codex built-in image_gen for this request. Do not call an external image API.\n"
        "Use the approved character sheet and any inspected_pass anchor images in this run folder as the only visual authority.\n"
        "Generate a new closeup reference pack image; do not finish by manually cropping or extracting a region from the source sheet.\n\n"
        f"Intended output filename: {item['output']}\n"
        f"Prompt template: {item['prompt_template']}\n"
        f"Reference purpose: {item['purpose']}\n\n"
        "Request:\n"
        f"{item['prompt']}\n\n"
        "Source of truth:\n"
        f"- Approved character sheet: {state['source_image']}\n"
        "- Approved identity anchor, if available: 01_face_front.png after inspected_pass\n\n"
        "Style requirement:\n"
        f"- style_mode: {state['style_mode']}\n"
        f"- {style_instruction(state['style_mode'])}\n"
        "- Keep the same rendering language, proportions, line quality, surface treatment, lighting logic, and color design as the approved sheet.\n\n"
        "Identity lock:\n"
        "- Preserve face shape, hair silhouette, eye design, outfit structure, palette, motifs, accessories, age appearance, and species or body type.\n\n"
        "Output rules:\n"
        "- Make the image useful as production reference, not a beauty image.\n"
        "- Use a simple clean background unless the item specifically needs isolated swatches or material samples.\n"
        "- No text labels unless the user explicitly requested labels.\n"
        "- Do not copy template placeholders, mannequin construction lines, plus icons, blank wireframe boxes, UI guide lines, random logo text, or watermarks.\n\n"
        f"{COMMON_NEGATIVE}\n"
    )


def write_prompt_files(run_dir, state, items):
    prompts_dir = run_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for item in items:
        prompt_path = run_dir / prompt_file_for(item["output"])
        prompt_path.write_text(build_prompt(item, state))


def write_batch_plan(run_dir, state, items):
    lines = [
        "# Character Sheet Closeup Reference Pack Batch Plan",
        "",
        f"Run folder: {display_path(run_dir)}",
        f"Preset: {state['pack_preset']}",
        f"Style mode: {state['style_mode']}",
        "",
        "Generation policy:",
        "- Use state.json as the source of truth.",
        "- Use Codex built-in image_gen for every pack output.",
        "- Crop-only or manually extracted sheet regions do not count as completed pack outputs.",
        "- Call `next` before each image generation so the item is marked generation_requested.",
        "- After image_gen returns in a later turn, run `import-latest`, inspect the image, then run `inspect-pass` or `rerun`.",
        "- Do not create a new run when an incomplete run with the same source hash, preset, and style mode exists.",
        "",
        "Batch items:",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"- output: {item['output']}",
                f"  purpose: {item['purpose']}",
                f"  request_group: {item['request_group']}",
                f"  dependencies: {', '.join(item['dependencies'])}",
                f"  prompt_template: {item['prompt_template']}",
                f"  notes: {item['notes']}",
                "",
            ]
        )
    (run_dir / "batch_plan.md").write_text("\n".join(lines).rstrip() + "\n")


def create_state(run_dir, source, source_hash, preset, style_mode):
    items = []
    for item in items_for_preset(preset):
        items.append(
            {
                "output": item["output"],
                "purpose": item["purpose"],
                "request_group": item["request_group"],
                "prompt_template": item["prompt_template"],
                "prompt_file": prompt_file_for(item["output"]),
                "dependencies": item["dependencies"],
                "status": "pending",
                "requested_at": None,
                "generated_source": None,
                "inspection": {},
            }
        )
    return {
        "source_image": SOURCE_NAME,
        "source_sha256": source_hash,
        "workflow": WORKFLOW,
        "run_dir": str(run_dir.resolve()),
        "anchor_policy": ANCHOR_POLICY,
        "pack_preset": preset,
        "style_mode": style_mode,
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
        existing = find_incomplete_run(source_hash, args.preset, args.style_mode)
        if existing:
            print(display_path(existing))
            return 0
        folder_slug = slugify(source.stem)
        prefix = folder_slug if folder_slug == "character-closeup-pack" else f"{folder_slug}-character-closeup-pack"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = (output_root() / f"{prefix}-{timestamp}").resolve()

    run_dir.mkdir(parents=True, exist_ok=True)
    state_path = run_dir / "state.json"
    if state_path.exists():
        state = read_state(run_dir)
        if state.get("source_sha256") != source_hash:
            raise SystemExit("existing run-dir state.json has a different source_sha256")
        if state.get("pack_preset") != args.preset or state.get("style_mode") != args.style_mode:
            raise SystemExit("existing run-dir state.json has a different preset or style_mode")
        print(display_path(run_dir))
        return 0

    shutil.copy2(source, run_dir / SOURCE_NAME)
    state = create_state(run_dir, source, source_hash, args.preset, args.style_mode)
    items = items_for_preset(args.preset)
    write_prompt_files(run_dir, state, items)
    write_batch_plan(run_dir, state, items)
    write_state(run_dir, state)
    print(display_path(run_dir))
    return 0


def item_by_output(state, output):
    for item in state["items"]:
        if item["output"] == output:
            return item
    raise SystemExit(f"item not found: {output}")


def dependency_ready(state, item):
    by_output = {entry["output"]: entry for entry in state["items"]}
    for dependency in item["dependencies"]:
        if dependency in by_output and by_output[dependency]["status"] not in DONE_STATUSES:
            return False
    return True


def next_item(state):
    for item in state["items"]:
        if item["status"] == "generation_requested":
            return item, False
    for item in state["items"]:
        if item["status"] in {"needs_rerun", "pending"} and dependency_ready(state, item):
            return item, True
    return None, False


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
        item["inspection"] = {}
        write_state(run_dir, state)

    prompt_path = run_dir / item["prompt_file"]
    print(f"output: {item['output']}")
    print(f"prompt_template: {item['prompt_template']}")
    print(f"prompt_file: {item['prompt_file']}")
    print("")
    print(prompt_path.read_text())
    return 0


def requested_item(state):
    for item in state["items"]:
        if item["status"] == "generation_requested":
            return item
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
    item["inspection"] = {}
    write_state(run_dir, state)
    print(f"imported: {item['output']}")
    print(f"generated_source: {generated}")
    return 0


def command_inspect_pass(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    item = item_by_output(state, args.item)
    if not (run_dir / item["output"]).exists():
        raise SystemExit(f"output file does not exist: {item['output']}")
    item["status"] = "inspected_pass"
    item["inspection"] = {
        "result": "pass",
        "note": args.note or "",
        "inspected_at": now_iso(),
    }
    write_state(run_dir, state)
    print(f"inspected_pass: {item['output']}")
    return 0


def command_status(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    generated = sum(1 for item in state["items"] if item["status"] in DONE_STATUSES)
    pending = sum(1 for item in state["items"] if item["status"] == "pending")
    needs_rerun = sum(1 for item in state["items"] if item["status"] == "needs_rerun")
    generation_requested = sum(1 for item in state["items"] if item["status"] == "generation_requested")
    imported = sum(1 for item in state["items"] if item["status"] == "imported")
    complete = is_complete(state)

    print(f"run_dir: {display_path(run_dir)}")
    print(f"complete: {str(complete).lower()}")
    print(f"generated: {generated}")
    print(f"imported_uninspected: {imported}")
    print(f"pending: {pending}")
    print(f"needs_rerun: {needs_rerun}")
    print(f"generation_requested: {generation_requested}")
    return 0


def command_rerun(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    state = read_state(run_dir)
    item = item_by_output(state, args.item)
    item["status"] = "needs_rerun"
    item["requested_at"] = None
    item["inspection"] = {
        "result": "needs_rerun",
        "note": args.note or "",
        "inspected_at": now_iso(),
    }
    write_state(run_dir, state)
    print(f"needs_rerun: {item['output']}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Manage resumable character sheet closeup reference pack runs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--source", required=True)
    init.add_argument("--run-dir")
    init.add_argument("--preset", choices=sorted(PRESETS), default="core")
    init.add_argument("--style-mode", choices=sorted(STYLE_MODES), default="preserve_source_style")
    init.set_defaults(func=command_init)

    next_parser = subparsers.add_parser("next")
    next_parser.add_argument("--run-dir", required=True)
    next_parser.set_defaults(func=command_next)

    import_latest = subparsers.add_parser("import-latest")
    import_latest.add_argument("--run-dir", required=True)
    import_latest.add_argument("--generated")
    import_latest.set_defaults(func=command_import_latest)

    inspect_pass = subparsers.add_parser("inspect-pass")
    inspect_pass.add_argument("--run-dir", required=True)
    inspect_pass.add_argument("--item", required=True)
    inspect_pass.add_argument("--note")
    inspect_pass.set_defaults(func=command_inspect_pass)

    status = subparsers.add_parser("status")
    status.add_argument("--run-dir", required=True)
    status.set_defaults(func=command_status)

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
