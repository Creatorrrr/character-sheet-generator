import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = (
    REPO_ROOT
    / ".agents"
    / "skills"
    / "create-comic-storyboard-pack"
    / "scripts"
    / "comic_storyboard_runner.py"
)
BLOCKING_STAGE = "storyboard_blocking"
SKETCH_INK_STAGE = "storyboard_sketch_ink"
FIRST_STAGE = BLOCKING_STAGE
FINISH_STAGE = "finish"
STAGE_ORDER = [BLOCKING_STAGE, SKETCH_INK_STAGE, FINISH_STAGE]


def run_cli(*args, cwd):
    args = tuple(default_blocking_description_args(args, cwd))
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )


def run_cli_raw(*args, cwd):
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def default_blocking_description_args(args, cwd):
    args = list(args)
    if not args or args[0] != "import" or "--description" in args:
        return args
    try:
        stage = args[args.index("--stage") + 1]
    except (ValueError, IndexError):
        return args
    if stage != BLOCKING_STAGE:
        return args
    try:
        run_dir = Path(args[args.index("--run-dir") + 1])
        item = args[args.index("--item") + 1]
    except (ValueError, IndexError):
        return args
    description = make_blocking_description(Path(cwd), run_dir, item)
    return [*args, "--description", str(description)]


def make_blocking_description(root, run_dir, item):
    state_path = run_dir / "state.json"
    stem = Path(item).stem
    entity_ids = []
    constraint_ids = []
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        page = next(
            (
                page
                for page in state.get("pages", [])
                if item in {page.get("filename"), page.get("id"), Path(page.get("filename", "")).stem}
            ),
            None,
        )
        if page:
            stem = Path(page.get("filename") or item).stem
            contract = page.get("spatial_contract") or {}
            entity_ids = [entity.get("id") for entity in contract.get("entities", []) if entity.get("id")]
            constraint_ids = [
                constraint.get("id")
                for constraint in contract.get("constraints", [])
                if constraint.get("id")
            ]
    path = root / f"{stem}_desc.md"
    path.write_text(
        "\n".join(
            [
                f"# {stem}_desc",
                "",
                "## Symbol Legend",
                "- character circle: character marker",
                "- square: object or occlusion marker",
                "- arrow: facing, direction, or movement vector",
                "- silhouette/shadow: visibility and occlusion marker",
                "- entities: " + (", ".join(entity_ids) or "none"),
                "",
                "## Panel Spatial Map",
                "- simplified positions and vectors are mapped panel by panel.",
                "",
                "## Constraint Check",
                "- constraints: " + (", ".join(constraint_ids) or "none"),
                "",
                "## Temporal Continuity Check",
                "- pose, cover, visibility, occlusion, location_anchor, held_props, and state_tags are preserved unless an allowed transition is listed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def run_dir_from_init(result):
    for line in result.stdout.splitlines():
        if line.startswith("RUN_DIR: "):
            return Path(line.split(": ", 1)[1])
    raise AssertionError(f"RUN_DIR not found in output: {result.stdout}")


def sample_page(page_index, panel_count=3):
    panels = []
    for panel_index in range(1, panel_count + 1):
        panels.append(
            {
                "id": f"{page_index:03d}-panel-{panel_index}",
                "panel_no": panel_index,
                "scene_refs": [f"S{page_index:02d}"],
                "beat": f"Story beat {page_index}-{panel_index}",
                "visual_brief": f"Comic panel visual brief {page_index}-{panel_index}",
                "setting": "station corridor",
                "characters": ["main character"],
                "action": "guides a rolling suitcase toward the exit marker",
                "composition": "subject in foreground with exit marker in background",
                "source_dialogue": [f"raw line {page_index}-{panel_index}"],
                "adapted_dialogue": [f"각색 대사 {page_index}-{panel_index}"],
                "sfx": ["휙"],
                "caption": ["늦은 오후 복도"],
                "speech_balloon": "small balloon near the speaker",
                "sfx_placement": "near the moving suitcase",
                "detail_density_notes": "detail the hand, suitcase wheel, exit marker, and face; simplify the far wall",
                "visual_emphasis_notes": "use stronger line weight on the traveler and suitcase, lighter background lines",
                "comic_effects_notes": "motion lines follow the suitcase toward the marker and focus lines guide the eye to the destination",
                "spatial_logic_notes": "suitcase travels from hand toward exit marker",
                "motion_checks": ["rolling suitcase moves toward exit marker, not away from the path"],
                "must_match": ["exit marker stays on far wall"],
                "prompt": f"Generate comic panel {page_index}-{panel_index}",
            }
        )
    return {
        "id": f"{page_index:03d}-page-{page_index}",
        "filename": f"{page_index:03d}-page-{page_index}.png",
        "page_no": page_index,
        "scene_refs": [f"S{page_index:02d}"],
        "layout_brief": "Three-panel cinematic Korean comic page with one wide open top panel and two asymmetric lower panels.",
        "reading_order": "top-to-bottom, left-to-right within rows",
        "pacing_notes": "3-5 panels by default with measured cinematic pacing.",
        "panel_shape_notes": "Use experimental freeform panel design with diagonal, asymmetric, inset, or borderless panels.",
        "negative_space_notes": "Leave wide negative space around faces, object motion, balloons, and quiet reaction beats.",
        "detail_density_notes": "Keep the traveler, suitcase, exit marker, and hand details crisp; simplify distant walls.",
        "visual_emphasis_notes": "Strongest visual emphasis goes to the guided movement and final reaction closeup.",
        "comic_effects_notes": "Use motion lines on the suitcase, subtle focus lines toward the exit marker, and small contact lines near the wheels.",
        "page_dialogue_notes": "Adapt dialogue for comic timing; do not copy source lines verbatim.",
        "spatial_logic_notes": "Exit marker remains on far wall; suitcase moves toward exit marker after release.",
        "motion_checks": ["rolling suitcase path follows the hand release toward the exit marker"],
        "must_match": ["multi-panel comic page", "legible balloons and SFX"],
        "panels": panels,
        "references": [],
        "prompt": f"Generate complete comic page {page_index}",
    }


def sample_plan(page_count=5, panel_count=3):
    return {
        "scenario_title": "Corridor Story",
        "style_brief": "clean cinematic Korean comic style",
        "reading_order": "top-to-bottom, left-to-right within rows",
        "pages": [sample_page(index, panel_count=panel_count) for index in range(1, page_count + 1)],
    }


def plan_with_spatial_continuity(page_count=2):
    plan = sample_plan(page_count=page_count, panel_count=2)
    plan["spatial_continuity_plan"] = {
        "scope": "single recurring corridor set across all pages",
        "locations": [
            {
                "id": "station-corridor",
                "name": "Station corridor",
                "layout_summary": "Long corridor with entrance foreground, ticket window on right wall, exit marker on far wall.",
                "camera_axis": "depth runs from near-left foreground toward far-right background",
                "fixed_landmarks": [
                    {
                        "id": "entrance-door",
                        "description": "near foreground door frame",
                        "relative_position": "near-left foreground",
                    },
                    {
                        "id": "ticket-window",
                        "description": "right wall service window",
                        "relative_position": "mid-right wall",
                    },
                    {
                        "id": "exit-marker",
                        "description": "far wall destination marker",
                        "relative_position": "far-right background",
                    },
                ],
            }
        ],
        "continuity_rules": [
            "same location_id means the same physical corridor and landmark layout",
            "fixed landmarks may be cropped but must not move to a different wall",
        ],
        "allowed_changes": ["doors may open only after a panel action causes it"],
    }
    for page in plan["pages"]:
        page["location_id"] = "station-corridor"
        page["location_continuity"] = {
            "location_id": "station-corridor",
            "zone": "main corridor axis",
            "fixed_landmarks_visible": ["ticket-window", "exit-marker"],
            "offscreen_landmarks": ["entrance-door"],
            "must_preserve": ["ticket-window remains on right wall", "exit-marker remains on far wall"],
            "changes_from_previous_page": [],
        }
    return plan


def action_spatial_contract():
    return {
        "coordinate_space": {
            "type": "panel_screen_2d",
            "origin": "top_left",
            "x_axis": "right",
            "y_axis": "down",
        },
        "entities": [
            {"id": "guide", "type": "character", "role": "main subject"},
            {"id": "observer", "type": "character", "role": "attention target"},
            {"id": "pointer_object", "type": "object", "role": "held direction cue"},
            {"id": "observer_gaze", "type": "object", "role": "gaze direction cue"},
            {"id": "screen", "type": "object", "role": "occluding element"},
            {"id": "rolling_suitcase", "type": "object", "role": "moving object"},
            {"id": "exit_marker", "type": "landmark", "role": "destination landmark"},
            {"id": "window_light", "type": "landmark", "role": "visibility source"},
        ],
        "panel_snapshots": [
            {
                "panel": 1,
                "entities": [
                    {"id": "guide", "position": [0.2, 0.5], "facing_vector": [1, 0]},
                    {"id": "observer", "position": [0.8, 0.5], "facing_vector": [-1, 0]},
                    {"id": "pointer_object", "position": [0.28, 0.5], "aim_vector": [1, 0]},
                    {"id": "observer_gaze", "position": [0.72, 0.5], "aim_vector": [-1, 0]},
                    {"id": "screen", "position": [0.5, 0.5], "occlusion": "between guide and window_light"},
                    {"id": "rolling_suitcase", "position": [0.32, 0.82], "trajectory_vector": [1, -0.85]},
                    {"id": "exit_marker", "position": [0.82, 0.38]},
                    {"id": "window_light", "position": [0.85, 0.5]},
                ],
            }
        ],
        "constraints": [
            {"id": "pointer-directed-to-observer", "type": "aims_at", "panel": 1, "actor": "guide", "object": "pointer_object", "target": "observer"},
            {"id": "observer-gaze-to-guide", "type": "aims_at", "panel": 1, "actor": "observer", "object": "observer_gaze", "target": "guide"},
            {"id": "screen-between-guide-and-window", "type": "cover_between", "panel": 1, "actor": "guide", "cover": "screen", "source": "window_light"},
            {"id": "suitcase-to-exit-marker", "type": "trajectory_to", "panel": 1, "object": "rolling_suitcase", "target": "exit_marker"},
        ],
    }


def tactical_cover_contract(
    *,
    include_no_line=True,
    screen_box=None,
    grok_pose="distant behind APC, does not fire",
    grok_aim_vector=None,
):
    grok_state = {
        "id": "grok",
        "position": [0.2, 0.5],
        "pose": grok_pose,
        "cover": "apc",
        "visibility": "tiny side-edge peek",
        "occlusion": "APC hides body",
    }
    if grok_aim_vector is not None:
        grok_state["aim_vector"] = grok_aim_vector
    constraints = [
        {
            "id": "grok-behind-apc-from-gipi",
            "type": "behind_cover_from",
            "panel": 1,
            "actor": "grok",
            "threat": "gipi",
            "viewpoint_entity": "gipi",
            "cover": "apc",
            "allowed_exposure": ["side_edge_peek_only", "weapon_edge_only"],
            "forbidden_exposure": ["torso_visible", "above_roofline"],
        }
    ]
    if screen_box is not None:
        constraints[0]["screen_box"] = screen_box
    if include_no_line:
        constraints.append(
            {
                "id": "grok-no-fire-line",
                "type": "no_line_of_fire",
                "panel": 1,
                "source": "grok",
                "target": "gipi",
            }
        )
    return {
        "coordinate_space": {
            "type": "panel_screen_2d",
            "origin": "top_left",
            "x_axis": "right",
            "y_axis": "down",
        },
        "entities": [
            {"id": "grok", "type": "character", "role": "support pressure"},
            {"id": "gipi", "type": "character", "role": "viewpoint threat"},
            {"id": "apc", "type": "cover", "role": "grok_cover"},
        ],
        "panel_snapshots": [
            {
                "panel": 1,
                "entities": [
                    grok_state,
                    {"id": "gipi", "position": [0.8, 0.5], "pose": "behind rubble"},
                    {"id": "apc", "position": [0.5, 0.5]},
                ],
            }
        ],
        "constraints": constraints,
    }


def plan_with_spatial_contract(contract):
    plan = sample_plan(page_count=1, panel_count=1)
    plan["pages"][0]["spatial_contract"] = contract
    return plan


def scene_3d_plan():
    plan = sample_plan(page_count=1, panel_count=2)
    plan["spatial_continuity_plan"] = {
        "scope": "two-level lobby with a stairwell and balcony",
        "scene_3d_scenes": [
            {
                "id": "school-building-main",
                "status": "provisional",
                "usage": "validation_only",
                "units": "meters",
                "origin": "building_ground_floor_center",
                "axes": {"x": "east", "y": "north", "z": "up"},
                "levels": [
                    {"id": "floor_1", "label": "1층", "z_range": [0, 3]},
                    {"id": "floor_2", "label": "2층", "z_range": [3, 6]},
                ],
                "locations": [
                    {"id": "floor_1_lobby", "level_id": "floor_1"},
                    {"id": "floor_2_balcony", "level_id": "floor_2"},
                ],
                "fixed_entities": [
                    {
                        "id": "stairwell",
                        "type": "landmark",
                        "position": [0, 1.5, 0],
                        "preview_geometry": {
                            "shape": "box",
                            "size": [1.2, 2.6, 3.4],
                            "anchor": "base_center",
                            "style": "building",
                        },
                    },
                    {
                        "id": "balcony_railing",
                        "type": "landmark",
                        "position": [0, 0.5, 3.2],
                        "preview_geometry": {
                            "shape": "box",
                            "size": [3.2, 0.22, 0.9],
                            "anchor": "base_center",
                            "style": "cover",
                        },
                    },
                    {
                        "id": "lobby_door",
                        "type": "door",
                        "position": [-2, -2, 1],
                        "preview_geometry": {
                            "shape": "box",
                            "size": [1.1, 0.22, 2.1],
                            "anchor": "center",
                            "style": "door",
                        },
                    },
                ],
                "reconciliation_policy": {
                    "mode": "adjust_soft_geometry_preserve_hard_invariants",
                    "first_panel_calibration_weight": "high",
                },
            }
        ],
        "continuity_rules": [
            "scene_3d starts provisional and may reconcile soft/inferred geometry after approved storyboard inspection",
            "hard invariants from the page plan must not be reconciled away",
        ],
    }
    page = plan["pages"][0]
    page["location_id"] = "floor_1_lobby"
    page["location_continuity"] = {
        "location_id": "floor_1_lobby",
        "zone": "lobby looking toward second-floor balcony",
        "fixed_landmarks_visible": [],
        "offscreen_landmarks": [],
        "must_preserve": ["hero remains on floor_1", "villain remains above on floor_2 balcony"],
        "changes_from_previous_page": [],
    }
    page["spatial_contract"] = {
        "coordinate_space": {
            "type": "scene_3d",
            "usage": "validation_only",
            "scene_id": "school-building-main",
            "location_id": "floor_1_lobby",
        },
        "entities": [
            {"id": "hero", "type": "character", "role": "ground-floor protagonist"},
            {"id": "villain", "type": "character", "role": "second-floor observer"},
            {"id": "lobby_door", "type": "door", "role": "state-changing landmark"},
            {"id": "balcony_railing", "type": "landmark", "role": "second-floor level evidence"},
        ],
        "locks": [
            {
                "id": "hero-floor-hard-lock",
                "type": "hard",
                "source": "page_plan",
                "rule": "hero must remain on floor_1",
                "entities": ["hero"],
                "panels": [1, 2],
            },
            {
                "id": "camera-fov-soft-lock",
                "type": "soft",
                "source": "model_inferred",
                "rule": "camera fov may reconcile to match the approved comic panel",
                "panels": [1],
                "warning": "camera FOV is provisional and may adjust after storyboard inspection",
            },
            {
                "id": "first-panel-calibration",
                "type": "inferred",
                "source": "model_inferred",
                "rule": "first panel can calibrate soft scene geometry if page design remains intact",
                "panels": [1],
            },
        ],
        "panel_snapshots": [
            {
                "panel": 1,
                "location_id": "floor_1_lobby",
                "camera": {"position": [-3, -4, 1.6], "look_at": [0, 0.5, 2.2], "fov": 45},
                "entities": [
                    {"id": "hero", "position": [0, -1, 0], "level_id": "floor_1", "facing_vector": [0, 1, 0], "state_tags": ["looking_up"]},
                    {"id": "villain", "position": [0, 0.7, 3.4], "level_id": "floor_2", "visibility": "visible_above_railing"},
                    {"id": "lobby_door", "position": [-2, -2, 1], "state_tags": ["closed"]},
                    {"id": "balcony_railing", "position": [0, 0.5, 3.2], "level_id": "floor_2"},
                ],
            },
            {
                "panel": 2,
                "location_id": "floor_1_lobby",
                "camera": {"position": [-2, -3, 1.8], "look_at": [0, 0.5, 1.8], "fov": 50},
                "entities": [
                    {"id": "hero", "position": [0.5, 0.4, 0], "level_id": "floor_1", "trajectory_vector": [-0.5, 0.1, 3.2], "state_tags": ["moving_to_stairs"]},
                    {"id": "villain", "position": [0, 0.7, 3.4], "level_id": "floor_2", "visibility": "visible_above_railing"},
                    {"id": "lobby_door", "position": [-2, -2, 1], "state_tags": ["open"]},
                    {"id": "balcony_railing", "position": [0, 0.5, 3.2], "level_id": "floor_2"},
                ],
            },
        ],
        "transitions": [
            {
                "id": "door-opened-by-hero",
                "from_panel": 1,
                "to_panel": 2,
                "entity": "lobby_door",
                "type": "state_change",
                "from_state": "closed",
                "to_state": "open",
                "cause": "hero opens the lobby door before moving",
            }
        ],
        "constraints": [
            {"id": "hero-on-floor-1", "type": "on_level", "panel": 1, "entity": "hero", "level": "floor_1"},
            {"id": "villain-on-floor-2", "type": "on_level", "panel": 1, "entity": "villain", "level": "floor_2"},
            {"id": "villain-above-hero", "type": "above", "panel": 1, "subject": "villain", "anchor": "hero"},
            {"id": "hero-villain-separated", "type": "vertical_separation", "panel": 1, "subject": "villain", "anchor": "hero", "min_delta_z": 3.0},
            {"id": "hero-moves-toward-stairs", "type": "trajectory_to", "panel": 2, "object": "hero", "target": "balcony_railing"},
            {"id": "door-open-cause", "type": "requires_cause", "entity": "lobby_door", "state_change": "closed_to_open", "cause_panel": 2},
            {"id": "floor-readability", "type": "visual_evidence_required", "panel": 1, "evidence": ["villain is visibly above hero", "balcony railing separates floor_2 from floor_1"]},
        ],
    }
    return plan


def temporal_cover_plan(current_cover="tall_partition", include_allowed_transition=False, cause_panel=1):
    plan = sample_plan(page_count=2, panel_count=1)
    shared_entities = [
        {"id": "guide", "type": "character", "role": "partly occluded subject"},
        {"id": "floor_partition", "type": "object", "role": "waist-height occluding element"},
        {"id": "tall_partition", "type": "landmark", "role": "full-height occluding landmark"},
    ]
    plan["pages"][0]["spatial_contract"] = {
        "entities": shared_entities,
        "panel_snapshots": [
            {
                "panel": 1,
                "entities": [
                    {
                        "id": "guide",
                        "position": [0.3, 0.65],
                        "pose": "crouching",
                        "cover": "floor_partition",
                        "visibility": "partly_hidden_from_viewer",
                        "occlusion": "occluded_by_floor_partition",
                        "location_anchor": "behind_floor_partition",
                        "held_props": ["folder"],
                        "state_tags": ["partly_obscured"],
                    },
                    {"id": "floor_partition", "position": [0.42, 0.65]},
                    {"id": "tall_partition", "position": [0.9, 0.6]},
                ],
            }
        ],
    }
    constraints = [
        {
            "id": "guide-same-occluder",
            "type": "same_cover_as",
            "panel": 1,
            "entity": "guide",
            "reference_page": "001-page-1",
            "reference_panel": 1,
        },
        {
            "id": "guide-state-persists",
            "type": "state_persists_from",
            "panel": 1,
            "entity": "guide",
            "reference_page": "001-page-1",
            "reference_panel": 1,
            "state_fields": ["pose", "cover", "location_anchor", "held_props", "state_tags"],
        },
    ]
    if include_allowed_transition:
        constraints.append(
            {
                "id": "guide-occluder-change-cause",
                "type": "allowed_transition",
                "entity": "guide",
                "from_page": "001-page-1",
                "from_panel": 1,
                "to_page": "002-page-2",
                "to_panel": 1,
                "cause_page": "002-page-2",
                "cause_panel": cause_panel,
            }
        )
    plan["pages"][1]["spatial_contract"] = {
        "entities": shared_entities,
        "panel_snapshots": [
            {
                "panel": 1,
                "entities": [
                    {
                        "id": "guide",
                        "position": [0.84, 0.62],
                        "pose": "standing",
                        "cover": current_cover,
                        "visibility": "partly_hidden_from_viewer",
                        "occlusion": f"occluded_by_{current_cover}",
                        "location_anchor": f"behind_{current_cover}",
                        "held_props": ["folder"],
                        "state_tags": ["partly_obscured"],
                    },
                    {"id": "floor_partition", "position": [0.42, 0.65]},
                    {"id": "tall_partition", "position": [0.9, 0.6]},
                ],
            }
        ],
        "constraints": constraints,
    }
    return plan


def legacy_panel_plan(panel_count=2):
    panels = []
    for index in range(1, panel_count + 1):
        panels.append(
            {
                "id": f"{index:03d}-legacy-panel",
                "filename": f"{index:03d}-legacy-panel.png",
                "panel_no": index,
                "visual_brief": f"Legacy panel brief {index}",
                "prompt": f"Generate legacy panel {index}",
            }
        )
    return {"scenario_title": "Legacy Story", "panels": panels}


def init_run(root):
    result = run_cli(
        "init",
        "--title",
        "Corridor Story",
        "--scenario-summary",
        "A short corridor scene.",
        "--output-root",
        str(root / "output"),
        cwd=root,
    )
    return run_dir_from_init(result)


def approve_plan(root, run_dir, page_count=5, panel_count=3):
    plan_path = root / "plan.json"
    plan_path.write_text(json.dumps(sample_plan(page_count, panel_count), indent=2), encoding="utf-8")
    return run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)


def approve_plan_with_target(root, run_dir, target_stage, page_count=5, panel_count=3):
    plan_path = root / f"plan-{target_stage}.json"
    plan_path.write_text(json.dumps(sample_plan(page_count, panel_count), indent=2), encoding="utf-8")
    return run_cli(
        "approve-plan",
        "--run-dir",
        str(run_dir),
        "--plan-file",
        str(plan_path),
        "--target-stage",
        target_stage,
        cwd=root,
    )


def approve_finish_stage(root, run_dir, note="user approved finish"):
    ensure_stage_review_passed(root, run_dir, SKETCH_INK_STAGE, note="sketch/ink continuity pass")
    feedback_request = feedback_request_for(run_dir)
    return run_cli(
        "approve-next-stage",
        "--run-dir",
        str(run_dir),
        "--from-stage",
        SKETCH_INK_STAGE,
        "--to-stage",
        FINISH_STAGE,
        "--feedback-request",
        str(feedback_request),
        "--feedback-choice",
        "approve_finish",
        "--note",
        note,
        cwd=root,
    )


def approve_sketch_ink_stage(root, run_dir, note="user approved sketch/ink"):
    state = json.loads((run_dir / "state.json").read_text())
    gate = state["stage_gates"][f"{BLOCKING_STAGE}_to_{SKETCH_INK_STAGE}"]
    if gate.get("status") == "approved":
        return
    feedback_request = feedback_request_for(run_dir, BLOCKING_STAGE, SKETCH_INK_STAGE)
    return run_cli(
        "approve-next-stage",
        "--run-dir",
        str(run_dir),
        "--from-stage",
        BLOCKING_STAGE,
        "--to-stage",
        SKETCH_INK_STAGE,
        "--feedback-request",
        str(feedback_request),
        "--feedback-choice",
        "approve_sketch_ink",
        "--note",
        note,
        cwd=root,
    )


def feedback_request_for(run_dir, from_stage=SKETCH_INK_STAGE, to_stage=FINISH_STAGE):
    state = json.loads((run_dir / "state.json").read_text())
    gate = state["stage_gates"][f"{from_stage}_to_{to_stage}"]
    return Path(gate.get("feedback_request") or run_dir / "feedback_requests" / f"{from_stage}_to_{to_stage}.json")


def generate_file(root, name="generated.png", data=b"generated image"):
    path = root / name
    path.write_bytes(data)
    return path


def make_state_legacy_parallel(run_dir):
    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.pop("page_generation_mode", None)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def import_and_inspect(root, run_dir, item, stage_id, generated):
    run_cli(
        "import",
        "--run-dir",
        str(run_dir),
        "--item",
        item,
        "--stage",
        stage_id,
        "--generated",
        str(generated),
        "--worker-status",
        "pass",
        "--worker-note",
        "worker pass",
        cwd=root,
    )
    run_cli(
        "inspect-pass",
        "--run-dir",
        str(run_dir),
        "--item",
        item,
        "--stage",
        stage_id,
        "--note",
        "parent pass",
        cwd=root,
    )


def anchor_review_pass(root, run_dir, stage_id, item="001-page-1.png", note="stage level anchor pass"):
    return run_cli(
        "anchor-review",
        "--run-dir",
        str(run_dir),
        "--stage",
        stage_id,
        "--item",
        item,
        "--status",
        "pass",
        "--note",
        note,
        cwd=root,
    )


def maybe_anchor_review_first_page(root, run_dir, stage_id, page):
    state = json.loads((run_dir / "state.json").read_text())
    if state.get("page_generation_mode") != "sequential_prior_pages":
        return
    if not state.get("pages") or state["pages"][0]["id"] != page["id"]:
        return
    review = state.get("stage_anchor_reviews", {}).get(stage_id, {})
    if review.get("status") == "passed":
        return
    anchor_review_pass(root, run_dir, stage_id, item=page["filename"], note=f"{stage_id} anchor level pass")


def stage_is_complete(state, stage_id):
    pages = state.get("pages", [])
    return bool(pages) and all(
        page.get("stages", {}).get(stage_id, {}).get("status") in {"inspected_pass", "complete"}
        for page in pages
    ) and state.get("stage_reviews", {}).get(stage_id, {}).get("status") == "passed"


def ensure_stage_review_passed(root, run_dir, stage_id, note="stage review pass"):
    state = json.loads((run_dir / "state.json").read_text())
    if stage_is_complete(state, stage_id):
        return
    if stage_id == SKETCH_INK_STAGE:
        if BLOCKING_STAGE in state.get("target_stages", []):
            ensure_stage_review_passed(root, run_dir, BLOCKING_STAGE, note="blocking continuity pass")
            approve_sketch_ink_stage(root, run_dir)
    generated = generate_file(root, name=f"{stage_id}-generated.png", data=f"{stage_id} generated".encode())
    while True:
        state = json.loads((run_dir / "state.json").read_text())
        if all(
            page["stages"][stage_id]["status"] in {"inspected_pass", "complete"}
            for page in state.get("pages", [])
        ):
            break
        requested = [
            page
            for page in state.get("pages", [])
            if page["stages"][stage_id]["status"] == "generation_requested"
        ]
        if not requested:
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            requested = [
                page
                for page in state.get("pages", [])
                if page["stages"][stage_id]["status"] == "generation_requested"
            ]
        if not requested:
            break
        for page in requested:
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                page["filename"],
                "--stage",
                stage_id,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                page["filename"],
                "--stage",
                stage_id,
                "--note",
                "parent pass",
                cwd=root,
            )
            maybe_anchor_review_first_page(root, run_dir, stage_id, page)
    state = json.loads((run_dir / "state.json").read_text())
    if state["stage_reviews"][stage_id]["status"] != "passed":
        run_cli(
            "stage-review",
            "--run-dir",
            str(run_dir),
            "--stage",
            stage_id,
            "--status",
            "pass",
            "--note",
            note,
            cwd=root,
        )


def stage_record(status, output_path=""):
    return {
        "status": status,
        "attempts": 1 if status != "pending" else 0,
        "rerun_pending": False,
        "batch_id": "",
        "prompt_file": "",
        "output_path": output_path,
        "generated_source": "",
        "worker_status": "pass" if status != "pending" else "",
        "worker_note": "",
        "parent_note": "parent pass" if status != "pending" else "",
    }


class ComicStoryboardRunnerTest(unittest.TestCase):
    def test_init_creates_approval_gated_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            state = json.loads((run_dir / "state.json").read_text())

            self.assertEqual(state["workflow"], "create-comic-storyboard-pack")
            self.assertFalse(state["plan_approved"])
            self.assertEqual(state["stage_order"], STAGE_ORDER)
            self.assertEqual(state["pages"], [])
            self.assertTrue((run_dir / "scenario.md").exists())
            self.assertTrue((run_dir / "prompts" / FIRST_STAGE).exists())
            self.assertTrue((run_dir / "prompts" / SKETCH_INK_STAGE).exists())
            self.assertTrue((run_dir / "prompts" / FINISH_STAGE).exists())
            self.assertTrue((run_dir / "01_storyboard_blocking").exists())
            self.assertTrue((run_dir / "02_storyboard_sketch_ink").exists())
            self.assertTrue((run_dir / "03_finish").exists())
            self.assertEqual(state["stage_reviews"][FIRST_STAGE]["status"], "pending")
            self.assertEqual(state["stage_reviews"][SKETCH_INK_STAGE]["status"], "pending")
            self.assertEqual(state["stage_reviews"][FINISH_STAGE]["status"], "pending")
            self.assertEqual(state["stage_anchor_reviews"][FIRST_STAGE]["status"], "pending")
            self.assertEqual(state["stage_anchor_reviews"][SKETCH_INK_STAGE]["status"], "pending")
            self.assertEqual(state["stage_anchor_reviews"][FINISH_STAGE]["status"], "pending")
            self.assertEqual(state["stage_gates"][f"{BLOCKING_STAGE}_to_{SKETCH_INK_STAGE}"]["status"], "pending")
            self.assertEqual(state["stage_gates"][f"{SKETCH_INK_STAGE}_to_{FINISH_STAGE}"]["status"], "pending")
            self.assertEqual(state["page_generation_mode"], "sequential_prior_pages")

    def test_approve_plan_normalizes_pages_and_nested_panels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)

            result = approve_plan(root, run_dir, page_count=2, panel_count=3)
            self.assertIn("APPROVED_PAGES: 2", result.stdout)
            state = json.loads((run_dir / "state.json").read_text())

            self.assertTrue(state["plan_approved"])
            self.assertEqual(state["target_stages"], STAGE_ORDER)
            self.assertEqual(state["page_generation_mode"], "sequential_prior_pages")
            self.assertEqual(len(state["pages"]), 2)
            first = state["pages"][0]
            self.assertEqual(first["id"], "001-page-1")
            self.assertEqual(first["filename"], "001-page-1.png")
            self.assertEqual(len(first["panels"]), 3)
            self.assertEqual(first["panels"][0]["adapted_dialogue"], ["각색 대사 1-1"])
            self.assertEqual(first["pacing_notes"], "3-5 panels by default with measured cinematic pacing.")
            self.assertIn("experimental freeform panel design", first["panel_shape_notes"])
            self.assertIn("wide negative space", first["negative_space_notes"])
            self.assertIn("traveler, suitcase, exit marker", first["detail_density_notes"])
            self.assertIn("guided movement", first["visual_emphasis_notes"])
            self.assertIn("motion lines", first["comic_effects_notes"])
            self.assertIn("hand, suitcase wheel, exit marker", first["panels"][0]["detail_density_notes"])
            self.assertIn("stronger line weight", first["panels"][0]["visual_emphasis_notes"])
            self.assertIn("focus lines", first["panels"][0]["comic_effects_notes"])
            self.assertEqual(state["source_root"], "/Users/chasoik/Projects/character-sheet-generator/sources")
            self.assertEqual(state["excluded_source_roots"], ["/Users/chasoik/Projects/character-sheet-generator/output"])
            self.assertEqual(set(first["stages"].keys()), set(STAGE_ORDER))
            self.assertEqual(first["stages"][FIRST_STAGE]["status"], "pending")
            self.assertEqual(set(state["stage_reviews"].keys()), set(STAGE_ORDER))
            self.assertEqual(set(state["stage_anchor_reviews"].keys()), set(STAGE_ORDER))
            self.assertEqual(
                set(state["stage_gates"].keys()),
                {f"{BLOCKING_STAGE}_to_{SKETCH_INK_STAGE}", f"{SKETCH_INK_STAGE}_to_{FINISH_STAGE}"},
            )
            self.assertEqual(state["stage_reviews"][FIRST_STAGE]["status"], "pending")
            self.assertEqual(state["stage_anchor_reviews"][FIRST_STAGE]["status"], "pending")
            self.assertTrue((run_dir / "approved_storyboard_plan.json").exists())
            self.assertTrue((run_dir / "batch_plan.md").exists())

    def test_approve_plan_rejects_output_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = sample_plan(page_count=1)
            plan["pages"][0]["references"] = [
                "/Users/chasoik/Projects/character-sheet-generator/output/failed-page.png"
            ]
            plan_path = root / "plan-output-ref.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            result = run_cli_raw("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Reference path is under output/", result.stderr)
            self.assertIn("cannot be used as source data", result.stderr)

    def test_spatial_contract_check_accepts_aim_cover_and_trajectory_and_prompts_include_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = plan_with_spatial_contract(action_spatial_contract())
            plan_path = root / "spatial-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
            generated = generate_file(root)

            check = run_cli("spatial-check", "--plan-file", str(plan_path), cwd=root)
            self.assertIn("SPATIAL_CHECK: pass", check.stdout)
            self.assertIn("STRUCTURED_PAGES: 1", check.stdout)

            approve = run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            self.assertIn("SPATIAL_CHECK: pass (1 structured pages)", approve.stdout)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            prompt = Path(stage["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(stage["subagent_prompt_file"]).read_text(encoding="utf-8")
            batch_plan = (run_dir / "batch_plan.md").read_text(encoding="utf-8")

            for text in (prompt, subagent_prompt, batch_plan):
                self.assertIn("Structured spatial contract", text)
                self.assertIn("pointer-directed-to-observer", text)
                self.assertIn("screen-between-guide-and-window", text)
                self.assertIn("suitcase-to-exit-marker", text)
            self.assertIn("Rejects target-opposite direction vectors", prompt)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                "--spatial-verdict",
                "pass",
                "--spatial-note",
                "direction, occlusion, and movement-path pass",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(stage["status"], "inspected_pass")
            self.assertEqual(stage["spatial_verdict"], "pass")
            self.assertEqual(stage["spatial_note"], "direction, occlusion, and movement-path pass")

    def test_viewpoint_cover_and_no_fire_constraints_are_prompted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = plan_with_spatial_contract(
                tactical_cover_contract(screen_box=[0.44, 0.2, 0.12, 0.6])
            )
            plan_path = root / "viewpoint-cover-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            prompt = Path(stage["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(stage["subagent_prompt_file"]).read_text(encoding="utf-8")

            for text in (prompt, subagent_prompt):
                self.assertIn("reader POV is insufficient", text)
                self.assertIn("threat viewpoint", text)
                self.assertIn("from gipi's line of fire", text)
                self.assertIn("forbidden_exposure", text)
                self.assertIn("do not draw dashed/aim/pressure line", text)

    def test_cover_contract_prompts_visual_occlusion_translation_before_raw_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            contract = tactical_cover_contract(screen_box=[0.44, 0.2, 0.12, 0.6])
            contract["constraints"][0]["allowed_exposure"] = ["eyes_and_weapon_edge_only"]
            plan = plan_with_spatial_contract(contract)
            plan_path = root / "visual-occlusion-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            prompt = Path(stage["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(stage["subagent_prompt_file"]).read_text(encoding="utf-8")

            self.assertLess(prompt.index("Narrative-first page design:"), prompt.index("Visual occlusion rendering rules:"))
            self.assertLess(prompt.index("Panels on this page:"), prompt.index("Visual occlusion rendering rules:"))
            self.assertLess(prompt.index("Visual occlusion rendering rules:"), prompt.index("Structured spatial contract:"))

            for text in (prompt, subagent_prompt):
                self.assertIn("Visual occlusion rendering rules", text)
                self.assertIn("clean border", text)
                self.assertIn("shadow gap", text)
                self.assertIn("negative-space sliver", text)
                self.assertIn("no shared contour/hatching", text)
                self.assertIn("do not paste eye/weapon on cover edge", text)
                self.assertIn("full concealment is acceptable and preferred", text)
                self.assertIn("eyes_and_weapon_edge_only", text)
                self.assertIn("Structured spatial contract", text)
                self.assertIn("reader POV is insufficient", text)
                self.assertIn("forbidden_exposure", text)

    def test_spatial_contract_screen_box_must_intersect_cover_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid_path = root / "valid-screen-box-plan.json"
            valid_path.write_text(
                json.dumps(
                    plan_with_spatial_contract(
                        tactical_cover_contract(screen_box=[0.44, 0.2, 0.12, 0.6])
                    ),
                    indent=2,
                ),
                encoding="utf-8",
            )

            valid = run_cli("spatial-check", "--plan-file", str(valid_path), cwd=root)
            self.assertIn("SPATIAL_CHECK: pass", valid.stdout)

            invalid_path = root / "invalid-screen-box-plan.json"
            invalid_path.write_text(
                json.dumps(
                    plan_with_spatial_contract(
                        tactical_cover_contract(screen_box=[0.05, 0.8, 0.1, 0.1])
                    ),
                    indent=2,
                ),
                encoding="utf-8",
            )

            invalid = run_cli_raw("spatial-check", "--plan-file", str(invalid_path), cwd=root)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("screen_box does not intersect", invalid.stdout)

    def test_non_firing_spatial_contract_requires_no_line_of_fire(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            invalid_path = root / "missing-no-line-plan.json"
            invalid_path.write_text(
                json.dumps(
                    plan_with_spatial_contract(tactical_cover_contract(include_no_line=False)),
                    indent=2,
                ),
                encoding="utf-8",
            )

            invalid = run_cli_raw("spatial-check", "--plan-file", str(invalid_path), cwd=root)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("non-firing spatial cue requires a no_line_of_fire constraint", invalid.stdout)

            valid_path = root / "with-no-line-plan.json"
            valid_path.write_text(
                json.dumps(
                    plan_with_spatial_contract(tactical_cover_contract(include_no_line=True)),
                    indent=2,
                ),
                encoding="utf-8",
            )
            valid = run_cli("spatial-check", "--plan-file", str(valid_path), cwd=root)
            self.assertIn("SPATIAL_CHECK: pass", valid.stdout)

    def test_no_line_of_fire_and_not_aims_at_reject_target_vectors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = plan_with_spatial_contract(
                tactical_cover_contract(include_no_line=True, grok_aim_vector=[1, 0])
            )
            plan["pages"][0]["spatial_contract"]["constraints"].append(
                {
                    "id": "grok-not-aiming-at-gipi",
                    "type": "not_aims_at",
                    "panel": 1,
                    "actor": "grok",
                    "target": "gipi",
                    "max_dot": 0.2,
                }
            )
            plan_path = root / "negative-aim-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            result = run_cli_raw("spatial-check", "--plan-file", str(plan_path), cwd=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("forbidden vector points toward the target", result.stdout)

    def test_narrative_first_spatial_contract_metadata_is_preserved_and_prompted_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = plan_with_spatial_contract(action_spatial_contract())
            page = plan["pages"][0]
            page["narrative_plan"] = {
                "story_function": "The page sells the reversal beat before explaining spatial relation logic.",
                "reader_experience": "Reader should feel the interruption first, then understand occlusion logic.",
                "pacing_intent": "One held reaction beat before the action resumes.",
                "composition_intent": "Cinematic comic composition, not a spatial diagram.",
            }
            page["spatial_contract_extraction"] = {
                "derived_from": "narrative_plan_and_panels",
                "verification_purpose": "Check direction, occlusion, and movement path after the page design is chosen.",
                "must_not_override_page_design": True,
                "focus": ["direction alignment", "occluding element placement", "moving object path"],
            }
            plan_path = root / "narrative-first-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            approved = json.loads((run_dir / "approved_storyboard_plan.json").read_text(encoding="utf-8"))
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))

            self.assertEqual(approved["pages"][0]["narrative_plan"], page["narrative_plan"])
            self.assertEqual(
                approved["pages"][0]["spatial_contract_extraction"],
                page["spatial_contract_extraction"],
            )
            self.assertEqual(state["pages"][0]["narrative_plan"], page["narrative_plan"])
            self.assertEqual(
                state["pages"][0]["spatial_contract_extraction"],
                page["spatial_contract_extraction"],
            )

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            prompt = Path(stage["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(stage["subagent_prompt_file"]).read_text(encoding="utf-8")
            batch_plan = (run_dir / "batch_plan.md").read_text(encoding="utf-8")

            self.assertLess(prompt.index("Narrative-first page design:"), prompt.index("Structured spatial contract:"))
            self.assertLess(prompt.index("Panels on this page:"), prompt.index("Structured spatial contract:"))
            self.assertIn(
                "spatial_contract is a validation overlay, not a page or composition driver",
                prompt,
            )
            self.assertIn(
                "spatially important panels default to scene_3d unless an exception is explicitly justified",
                prompt,
            )
            self.assertIn("Narrative-first page design", subagent_prompt)
            self.assertIn(
                "spatial_contract is a validation overlay, not a page or composition driver",
                subagent_prompt,
            )
            self.assertIn(
                "spatially important panels default to scene_3d unless an exception is explicitly justified",
                subagent_prompt,
            )
            self.assertIn(
                "spatial_contract is a validation overlay, not a page or composition driver",
                batch_plan,
            )
            self.assertIn(
                "spatially important panels default to scene_3d unless an exception is explicitly justified",
                batch_plan,
            )

    def test_spatial_continuity_plan_is_preserved_validated_and_prompted_before_page_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = plan_with_spatial_continuity(page_count=2)
            plan_path = root / "spatial-continuity-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            check = run_cli("spatial-check", "--plan-file", str(plan_path), cwd=root)
            self.assertIn("SPATIAL_CHECK: pass", check.stdout)

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            approved = json.loads((run_dir / "approved_storyboard_plan.json").read_text(encoding="utf-8"))
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))

            self.assertEqual(approved["spatial_continuity_plan"]["locations"][0]["id"], "station-corridor")
            self.assertEqual(state["spatial_continuity_plan"]["locations"][0]["id"], "station-corridor")
            self.assertEqual(state["pages"][0]["location_id"], "station-corridor")
            self.assertEqual(
                state["pages"][0]["location_continuity"]["fixed_landmarks_visible"],
                ["ticket-window", "exit-marker"],
            )

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            prompt = Path(stage["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(stage["subagent_prompt_file"]).read_text(encoding="utf-8")
            batch_plan = (run_dir / "batch_plan.md").read_text(encoding="utf-8")

            self.assertLess(
                prompt.index("Pre-page spatial continuity plan:"),
                prompt.index("Narrative-first page design:"),
            )
            self.assertIn("same location_id means the same physical set", prompt)
            self.assertIn("station-corridor", prompt)
            self.assertIn("ticket-window", prompt)
            self.assertIn("Pre-page spatial continuity plan", subagent_prompt)
            self.assertIn("spatial_continuity_plan is the pre-page location bible", batch_plan)

    def test_scene_3d_contract_is_preserved_validated_prompted_and_previewed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = scene_3d_plan()
            plan_path = root / "scene-3d-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            check = run_cli("spatial-check", "--plan-file", str(plan_path), cwd=root)
            self.assertIn("SPATIAL_CHECK: pass", check.stdout)

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            approved = json.loads((run_dir / "approved_storyboard_plan.json").read_text(encoding="utf-8"))
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            approved_contract = approved["pages"][0]["spatial_contract"]
            state_contract = state["pages"][0]["spatial_contract"]

            self.assertEqual(approved["spatial_continuity_plan"]["scene_3d_scenes"][0]["id"], "school-building-main")
            self.assertEqual(approved_contract["coordinate_space"]["type"], "scene_3d")
            self.assertEqual(state_contract["transitions"][0]["id"], "door-opened-by-hero")
            self.assertEqual(state_contract["locks"][0]["type"], "hard")

            preview = run_cli("spatial-preview", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("SPATIAL_CHECK: pass", preview.stdout)
            html = (run_dir / "spatial_contract_preview.html").read_text(encoding="utf-8")
            self.assertIn("Scene 3D Preview", html)
            self.assertIn("school-building-main", html)
            self.assertIn("floor_2", html)
            self.assertIn("door-opened-by-hero", html)
            self.assertIn("hero-floor-hard-lock", html)
            self.assertIn("camera FOV is provisional", html)
            self.assertIn("first panel can calibrate soft scene geometry", html)
            self.assertIn("floor-readability", html)
            self.assertIn('data-scene-id="school-building-main"', html)
            self.assertIn("data-scene3d-control", html)
            self.assertIn("pointerdown", html)
            self.assertIn("wheel", html)
            self.assertIn("Sync scene view", html)
            self.assertIn("Camera", html)
            self.assertIn("Iso", html)
            self.assertIn('data-scene3d-control="iso"', html)
            self.assertIn("ISOMETRIC_YAW", html)
            self.assertIn("DEFAULT_YAW = ISOMETRIC_YAW", html)
            self.assertIn('data-scene3d-label-mode="key"', html)
            self.assertIn('data-scene3d-label-mode="all"', html)
            self.assertIn('data-scene3d-label-mode="off"', html)
            self.assertIn('data-scene3d-layer="actors"', html)
            self.assertIn('data-scene3d-layer="obstacles"', html)
            self.assertIn('data-scene3d-layer="relations"', html)
            self.assertIn('data-scene3d-layer="vectors"', html)
            self.assertIn('data-scene3d-layer="ghosts"', html)
            self.assertIn('data-scene3d-status-strip', html)
            self.assertIn('data-scene3d-level-rail', html)
            self.assertNotIn('class="raw-2d-projection"', html)
            self.assertNotIn("Raw 2D Projection", html)
            self.assertIn("preview_geometry", html)
            self.assertIn("visibleLayers", html)
            self.assertIn("levelPlaneBounds", html)
            self.assertIn("levelColors", html)
            self.assertIn("drawWireBox", html)
            self.assertIn("drawOrientedEntity", html)
            self.assertIn("drawRelationOverlay", html)
            self.assertIn("placeSceneLabel", html)
            self.assertIn("labelBoxes", html)
            self.assertIn("compactEntityLabel", html)
            self.assertIn("data-preview-targets", html)
            self.assertIn("HERO floor_1", html)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            prompt = Path(stage["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(stage["subagent_prompt_file"]).read_text(encoding="utf-8")

            for text in (prompt, subagent_prompt):
                self.assertIn("scene_3d validation-only", text)
                self.assertIn("hard locks are rerun criteria", text)
                self.assertIn("soft/inferred geometry may reconcile", text)
                self.assertIn("first panel is a calibration anchor", text)
                self.assertIn("visual_evidence_required", text)

    def test_scene_3d_check_rejects_hard_spatial_contradictions_but_not_soft_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            soft_warning = scene_3d_plan()
            soft_warning_path = root / "scene-3d-soft-warning.json"
            soft_warning_path.write_text(json.dumps(soft_warning, indent=2), encoding="utf-8")
            valid = run_cli("spatial-check", "--plan-file", str(soft_warning_path), cwd=root)
            self.assertIn("SPATIAL_CHECK: pass", valid.stdout)
            self.assertIn("SPATIAL_WARNINGS: 2", valid.stdout)

            cases = []
            wrong_level = scene_3d_plan()
            wrong_level["pages"][0]["spatial_contract"]["panel_snapshots"][0]["entities"][0]["level_id"] = "floor_2"
            cases.append((wrong_level, "level_id floor_2 does not match z_range for z=0.0"))

            wrong_above = scene_3d_plan()
            wrong_above["pages"][0]["spatial_contract"]["panel_snapshots"][0]["entities"][1]["position"] = [0, 0.7, -0.5]
            cases.append((wrong_above, "is not above"))

            wrong_trajectory = scene_3d_plan()
            wrong_trajectory["pages"][0]["spatial_contract"]["panel_snapshots"][1]["entities"][0]["trajectory_vector"] = [-1, -1, 0]
            cases.append((wrong_trajectory, "vector points away"))

            unknown_scene = scene_3d_plan()
            unknown_scene["pages"][0]["spatial_contract"]["coordinate_space"]["scene_id"] = "missing-scene"
            cases.append((unknown_scene, "unknown scene_3d scene_id missing-scene"))

            missing_cause = scene_3d_plan()
            missing_cause["pages"][0]["spatial_contract"]["transitions"] = []
            cases.append((missing_cause, "requires_cause has no matching transition cause"))

            for index, (plan, expected) in enumerate(cases, start=1):
                with self.subTest(case=index):
                    plan_path = root / f"bad-scene-3d-{index}.json"
                    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
                    result = run_cli_raw("spatial-check", "--plan-file", str(plan_path), cwd=root)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("SPATIAL_CHECK: fail", result.stdout)
                    self.assertIn(expected, result.stdout)

    def test_spatial_check_rejects_incomplete_spatial_continuity_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_location = plan_with_spatial_continuity(page_count=1)
            missing_location["pages"][0].pop("location_id")
            missing_location["pages"][0].pop("location_continuity")
            missing_path = root / "missing-location-plan.json"
            missing_path.write_text(json.dumps(missing_location, indent=2), encoding="utf-8")

            missing_result = run_cli_raw("spatial-check", "--plan-file", str(missing_path), cwd=root)
            self.assertNotEqual(missing_result.returncode, 0)
            self.assertIn("requires location_id", missing_result.stdout)

            unknown_landmark = plan_with_spatial_continuity(page_count=1)
            unknown_landmark["pages"][0]["location_continuity"]["fixed_landmarks_visible"] = ["wrong-window"]
            unknown_path = root / "unknown-landmark-plan.json"
            unknown_path.write_text(json.dumps(unknown_landmark, indent=2), encoding="utf-8")

            unknown_result = run_cli_raw("spatial-check", "--plan-file", str(unknown_path), cwd=root)
            self.assertNotEqual(unknown_result.returncode, 0)
            self.assertIn("unknown fixed landmark ids", unknown_result.stdout)

    def test_spatial_check_rejects_action_and_landmark_contradictions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = []

            bad_aim = action_spatial_contract()
            bad_aim["panel_snapshots"][0]["entities"][2]["aim_vector"] = [-1, 0]
            cases.append((plan_with_spatial_contract(bad_aim), "vector points away"))

            bad_cover = action_spatial_contract()
            bad_cover["panel_snapshots"][0]["entities"][4]["position"] = [0.2, 0.9]
            cases.append((plan_with_spatial_contract(bad_cover), "occluding element is not between"))

            bad_trajectory = action_spatial_contract()
            bad_trajectory["panel_snapshots"][0]["entities"][5]["trajectory_vector"] = [-1, 0.85]
            cases.append((plan_with_spatial_contract(bad_trajectory), "vector points away"))

            landmark_plan = sample_plan(page_count=2, panel_count=1)
            landmark_plan["pages"][0]["spatial_contract"] = {
                "entities": [
                    {"id": "exit_marker", "type": "landmark"},
                    {"id": "gate", "type": "landmark"},
                ],
                "panel_snapshots": [
                    {
                        "panel": 1,
                        "entities": [
                            {"id": "exit_marker", "position": [0.8, 0.4]},
                            {"id": "gate", "position": [0.2, 0.4]},
                        ],
                    }
                ],
            }
            landmark_plan["pages"][1]["spatial_contract"] = {
                "entities": [
                    {"id": "exit_marker", "type": "landmark"},
                    {"id": "gate", "type": "landmark"},
                ],
                "panel_snapshots": [
                    {
                        "panel": 1,
                        "entities": [
                            {"id": "exit_marker", "position": [0.1, 0.4]},
                            {"id": "gate", "position": [0.9, 0.4]},
                        ],
                    }
                ],
                "constraints": [
                    {
                        "id": "keep-exit-marker-gate-relation",
                        "type": "same_landmark_relation_as",
                        "panel": 1,
                        "reference_page": "001-page-1",
                        "reference_panel": 1,
                        "subject": "exit_marker",
                        "anchor": "gate",
                    }
                ],
            }
            cases.append((landmark_plan, "landmark relation drift"))

            for index, (plan, expected) in enumerate(cases, start=1):
                with self.subTest(case=index):
                    plan_path = root / f"bad-spatial-{index}.json"
                    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
                    result = run_cli_raw("spatial-check", "--plan-file", str(plan_path), cwd=root)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("SPATIAL_CHECK: fail", result.stdout)
                    self.assertIn(expected, result.stdout)

    def test_approve_plan_blocks_failed_spatial_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            bad_contract = action_spatial_contract()
            bad_contract["panel_snapshots"][0]["entities"][2]["aim_vector"] = [-1, 0]
            plan = plan_with_spatial_contract(bad_contract)
            plan_path = root / "bad-aim-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            result = run_cli_raw("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Spatial contract check failed", result.stderr)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertFalse(state["plan_approved"])

    def test_spatial_preview_generates_html_for_plan_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = plan_with_spatial_contract(action_spatial_contract())
            plan_path = root / "spatial-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            result = run_cli("spatial-preview", "--plan-file", str(plan_path), cwd=root)

            preview_path = root / "spatial-plan_spatial_preview.html"
            self.assertTrue(preview_path.exists())
            self.assertIn(f"SPATIAL_PREVIEW: {preview_path}", result.stdout)
            self.assertIn("SPATIAL_CHECK: pass", result.stdout)
            html = preview_path.read_text(encoding="utf-8")
            self.assertIn("001-page-1.png", html)
            self.assertIn("pointer-directed-to-observer", html)
            self.assertIn("screen-between-guide-and-window", html)
            self.assertIn("suitcase-to-exit-marker", html)
            self.assertIn("spatial-check: pass", html)

    def test_spatial_preview_generates_html_when_spatial_check_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_contract = action_spatial_contract()
            bad_contract["panel_snapshots"][0]["entities"][2]["aim_vector"] = [-1, 0]
            plan = plan_with_spatial_contract(bad_contract)
            plan_path = root / "bad-spatial-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            result = run_cli("spatial-preview", "--plan-file", str(plan_path), cwd=root)

            preview_path = root / "bad-spatial-plan_spatial_preview.html"
            self.assertTrue(preview_path.exists())
            self.assertIn("SPATIAL_CHECK: fail", result.stdout)
            html = preview_path.read_text(encoding="utf-8")
            self.assertIn("spatial-check: fail", html)
            self.assertIn("vector points away", html)

    def test_spatial_preview_run_dir_default_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = plan_with_spatial_contract(action_spatial_contract())
            plan_path = root / "spatial-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)

            result = run_cli("spatial-preview", "--run-dir", str(run_dir), cwd=root)

            preview_path = run_dir / "spatial_contract_preview.html"
            self.assertTrue(preview_path.exists())
            self.assertIn(f"SPATIAL_PREVIEW: {preview_path}", result.stdout)
            html = preview_path.read_text(encoding="utf-8")
            self.assertIn("Corridor Story", html)
            self.assertIn("pointer-directed-to-observer", html)

    def test_spatial_preview_plan_json_requires_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_json = json.dumps(plan_with_spatial_contract(action_spatial_contract()))

            result = run_cli_raw("spatial-preview", "--plan-json", plan_json, cwd=root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires --output", result.stderr)

    def test_temporal_constraints_reject_cover_and_state_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "bad-temporal-plan.json"
            plan_path.write_text(json.dumps(temporal_cover_plan(), indent=2), encoding="utf-8")

            result = run_cli_raw("spatial-check", "--plan-file", str(plan_path), cwd=root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SPATIAL_CHECK: fail", result.stdout)
            self.assertIn("cover drift", result.stdout)
            self.assertIn("location_anchor drift", result.stdout)

    def test_allowed_transition_requires_existing_cause_and_can_permit_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            invalid_path = root / "invalid-transition-plan.json"
            invalid_path.write_text(
                json.dumps(temporal_cover_plan(include_allowed_transition=True, cause_panel=99), indent=2),
                encoding="utf-8",
            )

            invalid = run_cli_raw("spatial-check", "--plan-file", str(invalid_path), cwd=root)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("allowed_transition requires an existing cause reference", invalid.stdout)

            valid_path = root / "valid-transition-plan.json"
            valid_path.write_text(
                json.dumps(temporal_cover_plan(include_allowed_transition=True, cause_panel=1), indent=2),
                encoding="utf-8",
            )
            valid = run_cli("spatial-check", "--plan-file", str(valid_path), cwd=root)
            self.assertIn("SPATIAL_CHECK: pass", valid.stdout)

    def test_spatial_verdict_needs_rerun_blocks_inspect_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = plan_with_spatial_contract(action_spatial_contract())
            plan_path = root / "spatial-rerun-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
            generated = generate_file(root)

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            result = run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent finds spatial contradiction",
                "--spatial-verdict",
                "needs_rerun",
                "--spatial-note",
                "subject is exposed instead of behind screen",
                cwd=root,
            )

            self.assertIn("SPATIAL_RERUN_REQUIRED", result.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(stage["status"], "pending")
            self.assertTrue(stage["rerun_pending"])
            self.assertIn("Spatial inspection needs rerun", stage["parent_note"])
            self.assertEqual(stage["rerun_history"][-1]["spatial_verdict"], "needs_rerun")

    def test_spatial_verdict_reconciled_records_reconciliation_without_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = scene_3d_plan()
            plan_path = root / "scene-3d-reconcile-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
            generated = generate_file(root)

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )

            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent accepts storyboard and reconciles soft geometry",
                "--spatial-verdict",
                "reconciled",
                "--spatial-note",
                "hard invariants pass; camera fov is reconciled",
                "--reconciliation-note",
                "soft camera and desk offsets calibrated from first panel",
                cwd=root,
            )

            state = json.loads((run_dir / "state.json").read_text())
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(stage["status"], "inspected_pass")
            self.assertEqual(stage["spatial_verdict"], "reconciled")
            self.assertEqual(stage["reconciliation_note"], "soft camera and desk offsets calibrated from first panel")
            self.assertEqual(state["spatial_reconciliations"][0]["stage"], FIRST_STAGE)

    def test_legacy_flat_panels_are_converted_to_single_panel_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan_path = root / "legacy-plan.json"
            plan_path.write_text(json.dumps(legacy_panel_plan(), indent=2), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())

            self.assertEqual(len(state["pages"]), 2)
            self.assertEqual(len(state["pages"][0]["panels"]), 1)
            self.assertNotIn("panels", state)

    def test_next_batch_requires_approved_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)

            result = run_cli_raw("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Plan is not approved", result.stderr)

    def test_next_batch_reserves_one_page_by_default_in_sequential_prior_pages_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=5)

            result = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "10", cwd=root)
            self.assertIn(f"STAGE: {FIRST_STAGE}", result.stdout)
            self.assertEqual(result.stdout.count("ITEM: "), 1)
            self.assertIn("ITEM: 001-page-1.png", result.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["page_generation_mode"], "sequential_prior_pages")
            reserved = [
                page
                for page in state["pages"]
                if page["stages"][FIRST_STAGE]["status"] == "generation_requested"
            ]
            self.assertEqual(len(reserved), 1)
            self.assertEqual({page["stages"][FIRST_STAGE]["batch_id"] for page in reserved}, {"batch-001"})
            self.assertEqual(state["pages"][1]["stages"][FIRST_STAGE]["status"], "pending")

    def test_stage_anchor_review_blocks_second_page_until_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=2)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            import_and_inspect(root, run_dir, "001-page-1.png", FIRST_STAGE, generated)

            blocked = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn(f"STAGE_ANCHOR_REVIEW_REQUIRED: {FIRST_STAGE}", blocked.stdout)
            self.assertIn("ANCHOR_REVIEW_COMMAND:", blocked.stdout)
            self.assertNotIn("BATCH_ID:", blocked.stdout)

            anchor_review_pass(root, run_dir, FIRST_STAGE, note="blocking anchor level is correct")
            second = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn("ITEM: 002-page-2.png", second.stdout)

            state = json.loads((run_dir / "state.json").read_text())
            review = state["stage_anchor_reviews"][FIRST_STAGE]
            self.assertEqual(review["status"], "passed")
            self.assertEqual(review["anchor_item"], "001-page-1.png")
            self.assertEqual(review["anchor_level_note"], "blocking anchor level is correct")
            second_stage = state["pages"][1]["stages"][FIRST_STAGE]
            second_prompt = Path(second_stage["prompt_file"]).read_text(encoding="utf-8")
            second_subagent = Path(second_stage["subagent_prompt_file"]).read_text(encoding="utf-8")
            self.assertIn("Stage level anchor reference:", second_prompt)
            self.assertIn("blocking anchor level is correct", second_prompt)
            self.assertIn("Stage level anchor reference:", second_subagent)

    def test_stage_anchor_review_needs_rerun_resets_anchor_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=2)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            import_and_inspect(root, run_dir, "001-page-1.png", FIRST_STAGE, generated)

            result = run_cli(
                "anchor-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--item",
                "001-page-1.png",
                "--status",
                "needs_rerun",
                "--note",
                "blocking is too polished for the rough anchor",
                "--issue",
                "too polished",
                cwd=root,
            )
            self.assertIn(f"STAGE_ANCHOR_REVIEW: {FIRST_STAGE}", result.stdout)
            self.assertIn("STATUS: needs_rerun", result.stdout)

            state = json.loads((run_dir / "state.json").read_text())
            first_stage = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(first_stage["status"], "pending")
            self.assertTrue(first_stage["rerun_pending"])
            self.assertIn("blocking is too polished", first_stage["parent_note"])
            review = state["stage_anchor_reviews"][FIRST_STAGE]
            self.assertEqual(review["status"], "needs_rerun")
            self.assertEqual(review["issues"], ["too polished"])
            self.assertEqual(state["stage_reviews"][FIRST_STAGE]["status"], "pending")

    def test_legacy_parallel_batch_reserves_at_most_four_current_stage_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=5)
            make_state_legacy_parallel(run_dir)

            result = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "10", cwd=root)
            self.assertIn(f"STAGE: {FIRST_STAGE}", result.stdout)
            self.assertEqual(result.stdout.count("ITEM: "), 4)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["page_generation_mode"], "parallel_batch")
            reserved = [
                page
                for page in state["pages"]
                if page["stages"][FIRST_STAGE]["status"] == "generation_requested"
            ]
            self.assertEqual(len(reserved), 4)
            self.assertEqual({page["stages"][FIRST_STAGE]["batch_id"] for page in reserved}, {"batch-001"})
            self.assertEqual(state["pages"][4]["stages"][FIRST_STAGE]["status"], "pending")

    def test_sequential_prior_pages_records_required_image_attachments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=3)
            generated = generate_file(root)

            first = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertEqual(first.stdout.count("ITEM: "), 1)
            self.assertIn("ITEM: 001-page-1.png", first.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            first_stage = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(first_stage["visual_reference_paths"], [])
            first_prompt = Path(first_stage["prompt_file"]).read_text(encoding="utf-8")
            first_subagent = Path(first_stage["subagent_prompt_file"]).read_text(encoding="utf-8")
            self.assertIn("Required image attachments:\n- none", first_prompt)
            self.assertIn("Prior page continuity references:\n- none", first_subagent)

            import_and_inspect(root, run_dir, "001-page-1.png", FIRST_STAGE, generated)
            anchor_review_pass(root, run_dir, FIRST_STAGE, note="blocking anchor level pass")
            second = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            page1_blocking = str(run_dir / "01_storyboard_blocking" / "001-page-1.png")
            self.assertEqual(second.stdout.count("ITEM: "), 1)
            self.assertIn("ITEM: 002-page-2.png", second.stdout)
            self.assertIn(f"VISUAL_REFERENCE_IMAGE: {page1_blocking}", second.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            second_stage = state["pages"][1]["stages"][FIRST_STAGE]
            self.assertEqual(second_stage["visual_reference_paths"], [page1_blocking])
            second_prompt = Path(second_stage["prompt_file"]).read_text(encoding="utf-8")
            second_subagent = Path(second_stage["subagent_prompt_file"]).read_text(encoding="utf-8")
            self.assertIn("Required image attachments:", second_prompt)
            self.assertIn(page1_blocking, second_prompt)
            self.assertIn("priority 1: 001-page-1.png", second_subagent)

            import_and_inspect(root, run_dir, "002-page-2.png", FIRST_STAGE, generated)
            third = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            page2_blocking = str(run_dir / "01_storyboard_blocking" / "002-page-2.png")
            self.assertEqual(third.stdout.count("ITEM: "), 1)
            self.assertIn("ITEM: 003-page-3.png", third.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            third_stage = state["pages"][2]["stages"][FIRST_STAGE]
            self.assertEqual(third_stage["visual_reference_paths"], [page2_blocking, page1_blocking])
            third_subagent = Path(third_stage["subagent_prompt_file"]).read_text(encoding="utf-8")
            self.assertIn("priority 1: 002-page-2.png", third_subagent)
            self.assertIn("priority 2: 001-page-1.png", third_subagent)

    def test_later_stages_include_current_prior_stage_and_prior_page_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=2)
            generated = generate_file(root)

            ensure_stage_review_passed(root, run_dir, BLOCKING_STAGE, note="blocking pass")
            approve_sketch_ink_stage(root, run_dir)

            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            page1_sketch = state["pages"][0]["stages"][SKETCH_INK_STAGE]
            page1_blocking_path = str(run_dir / "01_storyboard_blocking" / "001-page-1.png")
            self.assertEqual(page1_sketch["visual_reference_paths"], [page1_blocking_path])
            self.assertIn("Prior-stage reference:", Path(page1_sketch["subagent_prompt_file"]).read_text(encoding="utf-8"))

            import_and_inspect(root, run_dir, "001-page-1.png", SKETCH_INK_STAGE, generated)
            anchor_review_pass(root, run_dir, SKETCH_INK_STAGE, note="sketch/ink anchor level pass")
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            page2_sketch = state["pages"][1]["stages"][SKETCH_INK_STAGE]
            page2_blocking_path = str(run_dir / "01_storyboard_blocking" / "002-page-2.png")
            page1_sketch_path = str(run_dir / "02_storyboard_sketch_ink" / "001-page-1.png")
            self.assertEqual(page2_sketch["visual_reference_paths"], [page2_blocking_path, page1_sketch_path])

            import_and_inspect(root, run_dir, "002-page-2.png", SKETCH_INK_STAGE, generated)
            approve_finish_stage(root, run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            page1_finish = state["pages"][0]["stages"][FINISH_STAGE]
            page1_sketch_path = str(run_dir / "02_storyboard_sketch_ink" / "001-page-1.png")
            self.assertEqual(page1_finish["visual_reference_paths"], [page1_sketch_path])

            import_and_inspect(root, run_dir, "001-page-1.png", FINISH_STAGE, generated)
            anchor_review_pass(root, run_dir, FINISH_STAGE, note="finish anchor level pass")
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            page2_finish = state["pages"][1]["stages"][FINISH_STAGE]
            page2_sketch_path = str(run_dir / "02_storyboard_sketch_ink" / "002-page-2.png")
            page1_finish_path = str(run_dir / "03_finish" / "001-page-1.png")
            self.assertEqual(page2_finish["visual_reference_paths"], [page2_sketch_path, page1_finish_path])

    def test_prior_page_rerun_marks_later_same_stage_pages_for_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=3)
            ensure_stage_review_passed(root, run_dir, FIRST_STAGE, note="blocking pass")

            result = run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "page 1 continuity defect",
                cwd=root,
            )
            self.assertIn("DOWNSTREAM_RERUN_ITEM: 002-page-2.png", result.stdout)
            self.assertIn("DOWNSTREAM_RERUN_ITEM: 003-page-3.png", result.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            for page in state["pages"]:
                stage = page["stages"][FIRST_STAGE]
                self.assertEqual(stage["status"], "pending")
                self.assertTrue(stage["rerun_pending"])
                self.assertEqual(stage["visual_reference_paths"], [])
            self.assertEqual(state["stage_reviews"][FIRST_STAGE]["status"], "pending")

    def test_legacy_stage_names_are_not_cli_choices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)

            result = run_cli_raw(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                "storyboard",
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid choice", result.stderr)
            self.assertIn(FIRST_STAGE, result.stderr)

    def test_blocking_import_requires_description_and_stores_description_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)

            missing = run_cli_raw(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                BLOCKING_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("requires --description", missing.stderr)

            desc = make_blocking_description(root, run_dir, "001-page-1.png")
            imported = run_cli_raw(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                BLOCKING_STAGE,
                "--generated",
                str(generated),
                "--description",
                str(desc),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            self.assertEqual(imported.returncode, 0, imported.stderr)
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            stage = state["pages"][0]["stages"][BLOCKING_STAGE]
            self.assertEqual(stage["status"], "imported")
            self.assertTrue(Path(stage["description_path"]).exists())
            self.assertEqual(stage["description_source"], str(desc))

    def test_prompt_contains_page_text_and_spatial_motion_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1, panel_count=3)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"][FIRST_STAGE]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")

            self.assertIn("one complete rough comic-page blocking image", prompt)
            self.assertIn("Assigned blocking description:", prompt)
            self.assertIn("write the description body text in Korean", prompt)
            self.assertIn("3 seconds of effort per entity", prompt)
            self.assertIn("recognizable enough to identify the entity and action", prompt)
            self.assertIn("Simplify or omit unimportant props/background elements", prompt)
            self.assertIn("sight/direction lines, movement-path arrows, visibility/occlusion", prompt)
            self.assertIn("meaningless pure-symbol blocking", prompt)
            self.assertIn("Semantic labels belong only in the *_desc.md", prompt)
            self.assertIn("measured cinematic pacing", prompt)
            self.assertIn("No prior-stage image is used for storyboard_blocking", prompt)
            self.assertIn("Requires explicit story justification for six or more panels", prompt)
            self.assertIn("experimental freeform panel design", prompt)
            self.assertIn("approved panel count and reading order", prompt)
            self.assertIn("unintentional uniform rectangular grids", prompt)
            self.assertIn("dialogue/SFX without breathing room", prompt)
            self.assertIn("Comic visual direction:", prompt)
            self.assertIn("detail density", prompt)
            self.assertIn("visual emphasis", prompt)
            self.assertIn("speed lines", prompt)
            self.assertIn("focus lines", prompt)
            self.assertIn("impact bursts", prompt)
            self.assertIn("emotion lines", prompt)
            self.assertIn("effect-line direction must match action direction", prompt)
            self.assertIn("same flat visual intensity", prompt)
            self.assertIn("Approved final-page text_policy is dialogue_sfx_captions", prompt)
            self.assertIn("storyboard_blocking must render no text", prompt)
            self.assertIn("각색 대사 1-1", prompt)
            self.assertIn("휙", prompt)
            self.assertIn("suitcase moves toward exit marker after release", prompt)
            self.assertIn("rolling suitcase moves toward exit marker, not away from the path", prompt)
            self.assertIn("No impossible staging", prompt)
            self.assertIn("Source consistency checklist:", prompt)
            self.assertIn("Panel and page continuity checklist:", prompt)

    def test_sfx_only_text_policy_prompt_rejects_dialogue_captions_signage_and_panel_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = sample_plan(page_count=1, panel_count=2)
            plan["text_policy"] = "sfx_only"
            plan_path = root / "sfx-only-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"][FIRST_STAGE]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")

            self.assertEqual(state["text_policy"], "sfx_only")
            self.assertIn("Text policy: storyboard_blocking_text_free", prompt)
            self.assertIn("Approved final-page text_policy is sfx_only", prompt)
            self.assertIn("storyboard_blocking must render no text", prompt)
            self.assertIn("Do not render dialogue, SFX", prompt)
            self.assertIn("speech balloons", prompt)
            self.assertIn("captions", prompt)
            self.assertIn("signage", prompt)
            self.assertIn("page or panel numbers", prompt)
            self.assertIn("Rejects all rendered text/glyphs", prompt)
            self.assertNotIn("Use adapted_dialogue, approved SFX, and approved captions", prompt)

    def test_text_free_policy_prompt_rejects_all_text_including_sfx(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = sample_plan(page_count=1, panel_count=2)
            plan["text_policy"] = "text_free"
            plan_path = root / "text-free-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"][FIRST_STAGE]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")

            self.assertEqual(state["text_policy"], "text_free")
            self.assertIn("Text policy: storyboard_blocking_text_free", prompt)
            self.assertIn("Approved final-page text_policy is text_free", prompt)
            self.assertIn("Do not render dialogue, SFX", prompt)
            self.assertIn("no text", prompt.lower())
            self.assertIn("Rejects all rendered text/glyphs, including SFX, dialogue, captions, signage, labels, panel/page numbers", prompt)
            self.assertNotIn("Only approved SFX may appear", prompt)

    def test_character_locks_and_visual_text_guard_are_in_storyboard_and_finish_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = sample_plan(page_count=1, panel_count=2)
            plan["character_locks"] = ["그림자마왕: 검은 물방울형 몸 표식 유지, 해골 장식 금지"]
            plan["visual_text_guard"] = ["건물/깃발/책/장식/컷 모서리에 임의 문자 금지"]
            plan_path = root / "locks-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
            generated = generate_file(root)

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            storyboard_prompt_path = Path(state["pages"][0]["stages"][FIRST_STAGE]["prompt_file"])
            storyboard_prompt = storyboard_prompt_path.read_text(encoding="utf-8")

            self.assertIn("Character locks:", storyboard_prompt)
            self.assertIn("그림자마왕: 검은 물방울형 몸 표식 유지, 해골 장식 금지", storyboard_prompt)
            self.assertIn("Visual text guard:", storyboard_prompt)
            self.assertIn("건물/깃발/책/장식/컷 모서리에 임의 문자 금지", storyboard_prompt)
            self.assertIn("Preserves every Character locks item listed above", storyboard_prompt)
            self.assertIn("Enforces every Visual text guard item listed above", storyboard_prompt)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage source and continuity pass",
                cwd=root,
            )
            approve_finish_stage(root, run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            finish_prompt_path = Path(state["pages"][0]["stages"][FINISH_STAGE]["prompt_file"])
            finish_prompt = finish_prompt_path.read_text(encoding="utf-8")

            self.assertIn("Character locks:", finish_prompt)
            self.assertIn("그림자마왕: 검은 물방울형 몸 표식 유지, 해골 장식 금지", finish_prompt)
            self.assertIn("Visual text guard:", finish_prompt)
            self.assertIn("건물/깃발/책/장식/컷 모서리에 임의 문자 금지", finish_prompt)
            self.assertIn("Preserves every Character locks item listed above", finish_prompt)
            self.assertIn("Enforces every Visual text guard item listed above", finish_prompt)

    def test_character_appearance_anatomy_lock_is_in_stage_and_subagent_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = sample_plan(page_count=1, panel_count=2)
            plan["character_locks"] = [
                "주인공: 두 눈 구조 유지, 양쪽 눈 위치와 얼굴형 유지, 팔/다리/손가락 개수 정상 유지"
            ]
            plan["pages"][0]["must_match"] = [
                "두 눈 캐릭터는 두 눈이 보이거나 각도상 자연스럽게 가려져야 함"
            ]
            plan_path = root / "appearance-anatomy-lock-plan.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
            generated = generate_file(root)

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            storyboard_stage = state["pages"][0]["stages"][FIRST_STAGE]
            storyboard_prompt = Path(storyboard_stage["prompt_file"]).read_text(encoding="utf-8")
            storyboard_subagent = Path(storyboard_stage["subagent_prompt_file"]).read_text(encoding="utf-8")

            for prompt in (storyboard_prompt, storyboard_subagent):
                self.assertIn("Character appearance/anatomy lock:", prompt)
                self.assertIn("one-eyed appearance for a two-eyed character", prompt)
                self.assertIn("missing/extra/merged eyes", prompt)
                self.assertIn("one-eyed face unless explicitly approved", prompt)
                self.assertIn("주인공: 두 눈 구조 유지", prompt)
            self.assertIn("두 눈 캐릭터는 두 눈이 보이거나 각도상 자연스럽게 가려져야 함", storyboard_prompt)
            self.assertIn("missing eyes", storyboard_prompt)
            self.assertIn("extra fingers", storyboard_prompt)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage appearance/anatomy pass",
                cwd=root,
            )
            approve_finish_stage(root, run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            finish_stage = state["pages"][0]["stages"][FINISH_STAGE]
            finish_prompt = Path(finish_stage["prompt_file"]).read_text(encoding="utf-8")
            finish_subagent = Path(finish_stage["subagent_prompt_file"]).read_text(encoding="utf-8")

            for prompt in (finish_prompt, finish_subagent):
                self.assertIn("Character appearance/anatomy lock:", prompt)
                self.assertIn("one-eyed appearance for a two-eyed character", prompt)
                self.assertIn("missing/extra/merged eyes", prompt)
                self.assertIn("one-eyed face unless explicitly approved", prompt)
                self.assertIn("주인공: 두 눈 구조 유지", prompt)
            self.assertIn("preserve the inspected storyboard_sketch_ink eye, face, hand, limb, silhouette, body proportion, and posture structure", finish_prompt)

    def test_prompt_uses_sources_by_default_and_excludes_output_source_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1, panel_count=2)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"][FIRST_STAGE]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")
            batch_plan = (run_dir / "batch_plan.md").read_text(encoding="utf-8")

            self.assertIn("Default source data folder:", prompt)
            self.assertIn("/Users/chasoik/Projects/character-sheet-generator/sources", prompt)
            self.assertIn("Output source exclusion:", prompt)
            self.assertIn("Do not use /Users/chasoik/Projects/character-sheet-generator/output", prompt)
            self.assertIn("Only the current run's parent-inspected prior-stage reference", prompt)
            self.assertIn("default source data folder", batch_plan)
            self.assertIn("Do not use /Users/chasoik/Projects/character-sheet-generator/output", batch_plan)
            self.assertIn("Stage reviews:", batch_plan)
            self.assertIn("Stage finish review checks source consistency", batch_plan)
            self.assertIn("3-5 panels by default", batch_plan)
            self.assertIn("1-2 panels for special staging", batch_plan)
            self.assertIn("six or more panels", batch_plan)
            self.assertIn("experimental freeform panel design", batch_plan)
            self.assertIn("negative_space:", batch_plan)
            self.assertIn("comic visual direction", batch_plan)
            self.assertIn("detail_density:", batch_plan)
            self.assertIn("visual_emphasis:", batch_plan)
            self.assertIn("comic_effects:", batch_plan)

    def test_subagent_prompt_uses_stage_specific_skill_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1, panel_count=2)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            storyboard_stage = state["pages"][0]["stages"][FIRST_STAGE]
            storyboard_subagent = Path(storyboard_stage["subagent_prompt_file"]).read_text(encoding="utf-8")

            self.assertIn("$create-comic-storyboard-blocking", storyboard_subagent)
            self.assertIn("Stage: storyboard_blocking", storyboard_subagent)
            self.assertIn("Assigned description path:", storyboard_subagent)
            self.assertIn("image_gen exactly once", storyboard_subagent)
            self.assertIn("quick recognizable 3-second rough forms", storyboard_subagent)
            self.assertIn("simplify or omit unimportant props/background elements", storyboard_subagent)
            self.assertIn("write the description body text in Korean", storyboard_subagent)
            self.assertIn("description path when stage is storyboard_blocking", storyboard_subagent)

            ensure_stage_review_passed(root, run_dir, BLOCKING_STAGE, note="blocking pass")
            approve_sketch_ink_stage(root, run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            sketch_stage = state["pages"][0]["stages"][SKETCH_INK_STAGE]
            storyboard_subagent = Path(sketch_stage["subagent_prompt_file"]).read_text(encoding="utf-8")

            self.assertIn("$create-comic-storyboard-sketch-ink", storyboard_subagent)
            self.assertIn("Stage: storyboard_sketch_ink", storyboard_subagent)
            self.assertIn("Do not edit state.json", storyboard_subagent)
            self.assertIn("Return only:", storyboard_subagent)
            self.assertIn("worker_status: pass or needs_rerun", storyboard_subagent)
            self.assertIn("Prior-stage reference:", storyboard_subagent)
            self.assertIn("Blocking description reference:", storyboard_subagent)
            self.assertIn("Agent-driven overlay option:", storyboard_subagent)
            self.assertIn("review_overlay_server.py", storyboard_subagent)
            self.assertIn("create-markup", storyboard_subagent)
            self.assertIn("include the manifest path in `worker_note`", storyboard_subagent)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                SKETCH_INK_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                SKETCH_INK_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                SKETCH_INK_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage continuity pass",
                cwd=root,
            )
            approve_finish_stage(root, run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            finish_stage = state["pages"][0]["stages"][FINISH_STAGE]
            finish_subagent = Path(finish_stage["subagent_prompt_file"]).read_text(encoding="utf-8")

            self.assertIn("$create-comic-storyboard-finish", finish_subagent)
            self.assertIn("Stage: finish", finish_subagent)
            self.assertIn("Prior-stage reference:", finish_subagent)
            self.assertIn(str(run_dir / "02_storyboard_sketch_ink" / "001-page-1.png"), finish_subagent)
            self.assertIn("Agent-driven overlay option:", finish_subagent)

    def test_imported_or_requested_pages_block_next_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=4)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            generated = generate_file(root)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )

            result = run_cli_raw("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Resolve current batch before reserving another", result.stderr)

    def test_next_stage_waits_until_all_pages_pass_parent_inspection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=5)
            make_state_legacy_parallel(run_dir)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            for index in range(1, 5):
                item = f"{index:03d}-page-{index}.png"
                run_cli(
                    "import",
                    "--run-dir",
                    str(run_dir),
                    "--item",
                    item,
                    "--stage",
                    FIRST_STAGE,
                    "--generated",
                    str(generated),
                    "--worker-status",
                    "pass",
                    "--worker-note",
                    "worker pass",
                    cwd=root,
                )
                run_cli(
                    "inspect-pass",
                    "--run-dir",
                    str(run_dir),
                    "--item",
                    item,
                    "--stage",
                    FIRST_STAGE,
                    "--note",
                    "parent pass",
                    cwd=root,
                )

            remaining = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn(f"STAGE: {FIRST_STAGE}", remaining.stdout)
            self.assertIn("005-page-5.png", remaining.stdout)
            self.assertNotIn(f"STAGE: {FINISH_STAGE}", remaining.stdout)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "005-page-5.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "005-page-5.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )

            blocked = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn(f"STAGE_REVIEW_REQUIRED: {FIRST_STAGE}", blocked.stdout)
            self.assertNotIn(f"STAGE: {FINISH_STAGE}", blocked.stdout)

            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "source consistency and panel continuity pass",
                cwd=root,
            )
            gate_blocked = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn("USER_FEEDBACK_REQUIRED: storyboard_blocking -> storyboard_sketch_ink", gate_blocked.stdout)
            self.assertIn("FEEDBACK_CHOICES: approve_sketch_ink | open_overlay_ui | stop_after_stage", gate_blocked.stdout)
            self.assertNotIn("BATCH_ID:", gate_blocked.stdout)

            approve_sketch_ink_stage(root, run_dir)
            sketch = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn(f"STAGE: {SKETCH_INK_STAGE}", sketch.stdout)
            self.assertIn("ITEM: 001-page-1.png", sketch.stdout)

            ensure_stage_review_passed(root, run_dir, SKETCH_INK_STAGE, note="sketch/ink continuity pass")
            feedback_blocked = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn("USER_FEEDBACK_REQUIRED: storyboard_sketch_ink -> finish", feedback_blocked.stdout)
            self.assertNotIn("BATCH_ID:", feedback_blocked.stdout)

            approve_finish_stage(root, run_dir)
            finish = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn(f"STAGE: {FINISH_STAGE}", finish.stdout)
            self.assertEqual(finish.stdout.count("ITEM: "), 4)

    def test_blocking_stage_review_creates_feedback_request_and_blocks_sketch_until_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                BLOCKING_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                BLOCKING_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            review = run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                BLOCKING_STAGE,
                "--status",
                "pass",
                "--note",
                "blocking spatial and temporal continuity pass",
                cwd=root,
            )

            self.assertIn("USER_FEEDBACK_REQUIRED: storyboard_blocking -> storyboard_sketch_ink", review.stdout)
            feedback_request = feedback_request_for(run_dir, BLOCKING_STAGE, SKETCH_INK_STAGE)
            self.assertTrue(feedback_request.exists())
            request = json.loads(feedback_request.read_text(encoding="utf-8"))
            self.assertEqual(request["from_stage"], BLOCKING_STAGE)
            self.assertEqual(request["to_stage"], SKETCH_INK_STAGE)
            self.assertEqual(request["choices"][0]["id"], "approve_sketch_ink")

            blocked = run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("USER_FEEDBACK_REQUIRED: storyboard_blocking -> storyboard_sketch_ink", blocked.stdout)
            self.assertIn("FEEDBACK_CHOICES: approve_sketch_ink | open_overlay_ui | stop_after_stage", blocked.stdout)
            self.assertNotIn("BATCH_ID:", blocked.stdout)

            approve_sketch_ink_stage(root, run_dir)
            sketch = run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertIn(f"STAGE: {SKETCH_INK_STAGE}", sketch.stdout)
            self.assertIn("001-page-1.png", sketch.stdout)

    def test_stage_review_pass_creates_feedback_request_and_note_only_approval_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage continuity pass",
                cwd=root,
            )
            approve_sketch_ink_stage(root, run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                SKETCH_INK_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                SKETCH_INK_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            review = run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                SKETCH_INK_STAGE,
                "--status",
                "pass",
                "--note",
                "sketch/ink continuity pass",
                cwd=root,
            )

            self.assertIn("USER_FEEDBACK_REQUIRED", review.stdout)
            feedback_request = feedback_request_for(run_dir)
            feedback_markdown = feedback_request.with_suffix(".md")
            self.assertTrue(feedback_request.exists())
            self.assertTrue(feedback_markdown.exists())
            self.assertIn(str(feedback_request), review.stdout)

            request = json.loads(feedback_request.read_text(encoding="utf-8"))
            self.assertEqual(request["from_stage"], SKETCH_INK_STAGE)
            self.assertEqual(request["to_stage"], FINISH_STAGE)
            self.assertEqual(request["gate_key"], f"{SKETCH_INK_STAGE}_to_{FINISH_STAGE}")
            self.assertEqual(request["stage_review"]["status"], "passed")
            self.assertEqual(request["choices"][0]["id"], "approve_finish")
            self.assertEqual(request["outputs"][0]["filename"], "001-page-1.png")

            state = json.loads((run_dir / "state.json").read_text())
            gate = state["stage_gates"][f"{SKETCH_INK_STAGE}_to_{FINISH_STAGE}"]
            self.assertEqual(gate["status"], "pending_user_feedback")
            self.assertEqual(gate["feedback_request"], str(feedback_request.resolve(strict=False)))
            self.assertEqual(gate["feedback_choice"], "")

            note_only = run_cli_raw(
                "approve-next-stage",
                "--run-dir",
                str(run_dir),
                "--from-stage",
                SKETCH_INK_STAGE,
                "--to-stage",
                FINISH_STAGE,
                "--note",
                "parent-only approval should fail",
                cwd=root,
            )
            self.assertNotEqual(note_only.returncode, 0)
            self.assertIn("--feedback-request", note_only.stderr)

            blocked = run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("USER_FEEDBACK_REQUIRED", blocked.stdout)
            self.assertIn(f"FEEDBACK_REQUEST: {feedback_request}", blocked.stdout)
            self.assertIn("FEEDBACK_CHOICES: approve_finish | open_overlay_ui | stop_after_stage", blocked.stdout)

            approve_finish_stage(root, run_dir)
            approved_state = json.loads((run_dir / "state.json").read_text())
            approved_gate = approved_state["stage_gates"][f"{SKETCH_INK_STAGE}_to_{FINISH_STAGE}"]
            self.assertEqual(approved_gate["status"], "approved")
            self.assertEqual(approved_gate["feedback_choice"], "approve_finish")

    def test_approve_next_stage_rejects_mismatched_feedback_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage continuity pass",
                cwd=root,
            )
            ensure_stage_review_passed(root, run_dir, SKETCH_INK_STAGE, note="sketch/ink continuity pass")

            active_request = feedback_request_for(run_dir)
            request = json.loads(active_request.read_text(encoding="utf-8"))
            stale_request = dict(request)
            stale_request["created_at"] = "2000-01-01T00:00:00"
            active_request.write_text(json.dumps(stale_request), encoding="utf-8")

            stale_result = run_cli_raw(
                "approve-next-stage",
                "--run-dir",
                str(run_dir),
                "--from-stage",
                SKETCH_INK_STAGE,
                "--to-stage",
                FINISH_STAGE,
                "--feedback-request",
                str(active_request),
                "--feedback-choice",
                "approve_finish",
                "--note",
                "user approved finish",
                cwd=root,
            )

            self.assertNotEqual(stale_result.returncode, 0)
            self.assertIn("created_at does not match", stale_result.stderr)

            request["to_stage"] = FIRST_STAGE
            mismatched_request = run_dir / "feedback_requests" / "mismatched.json"
            mismatched_request.write_text(json.dumps(request), encoding="utf-8")

            result = run_cli_raw(
                "approve-next-stage",
                "--run-dir",
                str(run_dir),
                "--from-stage",
                SKETCH_INK_STAGE,
                "--to-stage",
                FINISH_STAGE,
                "--feedback-request",
                str(mismatched_request),
                "--feedback-choice",
                "approve_finish",
                "--note",
                "user approved finish",
                cwd=root,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("stage transition does not match", result.stderr)

    def test_storyboard_only_target_completes_after_first_stage_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan_with_target(root, run_dir, FIRST_STAGE, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "storyboard only complete",
                cwd=root,
            )

            status = run_cli("status", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("TARGET_STAGES: storyboard_blocking", status.stdout)
            self.assertIn("CURRENT_STAGE: complete", status.stdout)
            self.assertIn("COMPLETE: true", status.stdout)

    def test_stop_after_stage_marks_full_workflow_complete_at_first_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage complete",
                cwd=root,
            )
            run_cli(
                "stop-after-stage",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--note",
                "user stops before finish",
                cwd=root,
            )

            status = run_cli("status", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("TARGET_STAGES: storyboard_blocking", status.stdout)
            self.assertIn("COMPLETE: true", status.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            gate = state["stage_gates"][f"{BLOCKING_STAGE}_to_{SKETCH_INK_STAGE}"]
            self.assertEqual(gate["status"], "stopped")
            self.assertEqual(gate["feedback_choice"], "stop_after_stage")

    def test_finish_prompt_uses_first_stage_image_as_required_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage final review pass",
                cwd=root,
            )

            approve_finish_stage(root, run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"][FINISH_STAGE]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")
            first_stage_output = run_dir / "02_storyboard_sketch_ink" / "001-page-1.png"

            self.assertTrue(first_stage_output.exists())
            self.assertIn(str(first_stage_output), prompt)
            self.assertIn("required visual input / structure reference", prompt)
            self.assertIn("Do not redraw the page from scratch", prompt)
            self.assertIn("preserve the inspected storyboard_sketch_ink visual emphasis", prompt)
            self.assertIn("effect-line direction", prompt)
            self.assertIn("ink rhythm", prompt)

    def test_stage_review_pass_requires_all_pages_parent_inspected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=2)
            make_state_legacy_parallel(run_dir)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )

            result = run_cli_raw(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "not ready",
                cwd=root,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Stage review requires every page", result.stderr)

    def test_stage_review_needs_rerun_marks_items_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=2)
            make_state_legacy_parallel(run_dir)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            for index in range(1, 3):
                item = f"{index:03d}-page-{index}.png"
                run_cli(
                    "import",
                    "--run-dir",
                    str(run_dir),
                    "--item",
                    item,
                    "--stage",
                    FIRST_STAGE,
                    "--generated",
                    str(generated),
                    "--worker-status",
                    "pass",
                    "--worker-note",
                    "worker pass",
                    cwd=root,
                )
                run_cli(
                    "inspect-pass",
                    "--run-dir",
                    str(run_dir),
                    "--item",
                    item,
                    "--stage",
                    FIRST_STAGE,
                    "--note",
                    "parent pass",
                    cwd=root,
                )

            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "needs_rerun",
                "--note",
                "character source consistency drift on page 2",
                "--issue",
                "page 2 character hair and prop shape drift from sources",
                "--rerun-item",
                "002-page-2.png",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            second = state["pages"][1]["stages"][FIRST_STAGE]

            self.assertEqual(state["stage_reviews"][FIRST_STAGE]["status"], "needs_rerun")
            self.assertEqual(second["status"], "pending")
            self.assertTrue(second["rerun_pending"])
            self.assertIn("page 2 character hair", state["stage_reviews"][FIRST_STAGE]["issues"][0])

            next_batch = run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("002-page-2.png", next_batch.stdout)
            self.assertNotIn(f"STAGE: {FINISH_STAGE}", next_batch.stdout)

    def test_request_revisions_marks_overlay_items_for_rerun_and_prompts_include_overlays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage continuity pass",
                cwd=root,
            )
            review_dir = run_dir / "review_overlays" / FIRST_STAGE / "manual-review"
            review_dir.mkdir(parents=True)
            overlay = review_dir / "001-page-1_overlay_red.png"
            request = review_dir / "001-page-1_overlay_red.txt"
            overlay.write_bytes(b"overlay")
            request.write_text("Make the hand smaller but keep the panel layout.", encoding="utf-8")
            manifest = {
                "workflow": "review-image-overlays",
                "run_dir": str(run_dir),
                "stage": FIRST_STAGE,
                "items": [
                    {
                        "filename": "001-page-1.png",
                        "overlays": [
                            {
                                "color_id": "red",
                                "color": "#ff3b30",
                                "overlay_path": str(overlay),
                                "request_path": str(request),
                                "request": "Make the hand smaller but keep the panel layout.",
                            }
                        ],
                    }
                ],
            }
            manifest_path = review_dir / "revision_requests.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = run_cli(
                "request-revisions",
                "--run-dir",
                str(run_dir),
                "--review-manifest",
                str(manifest_path),
                cwd=root,
            )

            self.assertIn("REVISION_REQUESTED", result.stdout)
            self.assertIn("001-page-1.png", result.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(stage["status"], "pending")
            self.assertTrue(stage["rerun_pending"])
            self.assertEqual(state["stage_reviews"][FIRST_STAGE]["status"], "pending")
            self.assertEqual(state["stage_gates"][f"{BLOCKING_STAGE}_to_{SKETCH_INK_STAGE}"]["status"], "pending")
            self.assertEqual(state["stage_gates"][f"{BLOCKING_STAGE}_to_{SKETCH_INK_STAGE}"]["feedback_request"], "")
            self.assertEqual(state["stage_gates"][f"{BLOCKING_STAGE}_to_{SKETCH_INK_STAGE}"]["feedback_choice"], "")
            self.assertEqual(state["stage_gates"][f"{SKETCH_INK_STAGE}_to_{FINISH_STAGE}"]["status"], "pending")
            self.assertEqual(state["stage_gates"][f"{SKETCH_INK_STAGE}_to_{FINISH_STAGE}"]["feedback_request"], "")
            self.assertEqual(state["stage_gates"][f"{SKETCH_INK_STAGE}_to_{FINISH_STAGE}"]["feedback_choice"], "")
            self.assertIn("user_revision_overlays", stage)
            self.assertEqual(stage["user_revision_overlays"][0]["overlay_path"], str(overlay.resolve(strict=False)))

            next_batch = run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("001-page-1.png", next_batch.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            prompt = Path(state["pages"][0]["stages"][FIRST_STAGE]["prompt_file"]).read_text(encoding="utf-8")
            subagent = Path(state["pages"][0]["stages"][FIRST_STAGE]["subagent_prompt_file"]).read_text(encoding="utf-8")
            for text in (prompt, subagent):
                self.assertIn("User revision overlays", text)
                self.assertIn(str(overlay.resolve(strict=False)), text)
                self.assertIn("Make the hand smaller", text)

    def test_finish_stage_review_required_before_workflow_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage continuity pass",
                cwd=root,
            )
            approve_finish_stage(root, run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FINISH_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FINISH_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )

            status_before = run_cli("status", "--run-dir", str(run_dir), cwd=root)
            self.assertIn(f"CURRENT_STAGE: {FINISH_STAGE}", status_before.stdout)
            self.assertIn("finish_review: pending", status_before.stdout)
            self.assertIn("COMPLETE: false", status_before.stdout)

            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FINISH_STAGE,
                "--status",
                "pass",
                "--note",
                "final source consistency and continuity pass",
                cwd=root,
            )
            status_after = run_cli("status", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("CURRENT_STAGE: complete", status_after.stdout)
            self.assertIn("finish_review: passed", status_after.stdout)
            self.assertIn("COMPLETE: true", status_after.stdout)

    def test_finish_only_target_requires_imported_prior_stage_before_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan_with_target(root, run_dir, FINISH_STAGE, page_count=1)

            missing_prior = run_cli_raw("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertNotEqual(missing_prior.returncode, 0)
            self.assertIn("Finish stage requires the parent-inspected storyboard_sketch_ink image", missing_prior.stderr)

            generated = generate_file(root, name="external-sketch.png")
            run_cli(
                "import-prior-stage",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                SKETCH_INK_STAGE,
                "--generated",
                str(generated),
                "--note",
                "external sketch/ink reference approved by user",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                SKETCH_INK_STAGE,
                "--status",
                "pass",
                "--note",
                "external prior stage accepted",
                cwd=root,
            )
            approve_finish_stage(root, run_dir, note="user approves finishing external prior")
            finish = run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertIn(f"STAGE: {FINISH_STAGE}", finish.stdout)
            self.assertIn("001-page-1.png", finish.stdout)

    def test_finish_batch_fails_when_first_stage_output_file_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage final review pass",
                cwd=root,
            )
            approve_finish_stage(root, run_dir)
            first_stage_output = run_dir / "02_storyboard_sketch_ink" / "001-page-1.png"
            first_stage_output.unlink()

            result = run_cli_raw("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Finish stage requires the parent-inspected storyboard_sketch_ink image", result.stderr)
            self.assertIn(str(first_stage_output), result.stderr)

            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["pages"][0]["stages"][FINISH_STAGE]["status"], "pending")

    def test_old_three_stage_state_is_migrated_conservatively(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            state = json.loads((run_dir / "state.json").read_text())
            page_one = sample_page(1)
            page_two = sample_page(2)
            page_one["stages"] = {
                "storyboard": stage_record("inspected_pass"),
                "sketch_ink": stage_record("inspected_pass"),
                "finish": stage_record("pending"),
            }
            page_two["stages"] = {
                "storyboard": stage_record("inspected_pass"),
                "sketch_ink": stage_record("pending"),
                "finish": stage_record("pending"),
            }
            state["plan_approved"] = True
            state["stage_order"] = ["storyboard", "sketch_ink", "finish"]
            state["pages"] = [page_one, page_two]
            (run_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

            result = run_cli("status", "--run-dir", str(run_dir), cwd=root)

            self.assertIn(f"CURRENT_STAGE: {FIRST_STAGE}", result.stdout)
            self.assertIn(f"{FIRST_STAGE}: inspected_pass=2", result.stdout)
            self.assertIn(f"{SKETCH_INK_STAGE}: inspected_pass=1, pending=1", result.stdout)
            self.assertIn(f"{FINISH_STAGE}: pending=2", result.stdout)

    def test_rerun_note_is_included_in_next_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "LIBRARY 표기 금지",
                cwd=root,
            )
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"][FIRST_STAGE]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")

            self.assertIn("Current rerun correction:", prompt)
            self.assertIn("LIBRARY 표기 금지", prompt)

    def test_import_accepts_generated_path_that_is_already_stage_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            stage = state["pages"][0]["stages"][FIRST_STAGE]
            generated = Path(stage["output_path"])
            generated.parent.mkdir(parents=True, exist_ok=True)
            generated.write_bytes(b"already generated in place")

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            stage = state["pages"][0]["stages"][FIRST_STAGE]

            self.assertEqual(stage["status"], "imported")
            self.assertEqual(stage["generated_source"], str(generated))
            self.assertEqual(Path(stage["output_path"]), generated)
            self.assertEqual(generated.read_bytes(), b"already generated in place")

    def test_worker_needs_rerun_is_advisory_until_parent_decides(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "needs_rerun",
                "--worker-note",
                "worker sees impossible moving-object path",
                cwd=root,
            )

            state = json.loads((run_dir / "state.json").read_text())
            first = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(first["status"], "imported")
            self.assertEqual(first["worker_status"], "needs_rerun")

            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent accepts after inspection",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            first = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(first["status"], "inspected_pass")
            self.assertEqual(first["worker_status"], "needs_rerun")

            run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent changed decision",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            first = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(first["status"], "pending")
            self.assertTrue(first["rerun_pending"])


if __name__ == "__main__":
    unittest.main()
