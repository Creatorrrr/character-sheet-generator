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
    / "create-video-scenario-image-pack"
    / "scripts"
    / "video_scenario_image_pack_runner.py"
)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        text=True,
        capture_output=True,
        check=True,
    )


def run_cli_raw(*args):
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def run_dir_from(stdout):
    for line in stdout.splitlines():
        if line.startswith("RUN_DIR: "):
            return Path(line.split(": ", 1)[1])
    raise AssertionError(f"RUN_DIR missing from output:\n{stdout}")


def base_item(item_id, filename, *, anchor="", deps=None, category="set_detail"):
    return {
        "id": item_id,
        "filename": filename,
        "scene_refs": ["S01"],
        "category": category,
        "contains_character": False,
        "purpose": f"Purpose for {filename}",
        "visual_brief": f"Empty sunset court source for {filename}",
        "spatial_group": "basketball-court-sunset",
        "continuity_anchor": anchor,
        "fixed_layout_notes": "Hoop far/right, gate and bench left, blank masonry wall, no people or vehicles.",
        "camera_view": "wide reference",
        "must_match": ["no people", "no cars", "no silhouettes"],
        "prompt": f"Photoreal empty no-character source for {filename}.",
        "negative_prompt": "",
        "dependencies": deps or [],
        "notes": "",
    }


def sample_plan():
    return {
        "scenario_title": "Noeul Court",
        "items": [
            base_item(
                "001-court-master",
                "001-court-master.png",
                category="location_master",
            ),
            base_item(
                "002-hoop-detail",
                "002-hoop-detail.png",
                anchor="001-court-master",
            ),
            base_item(
                "003-ball-prop",
                "003-ball-prop.png",
                deps=["001-court-master"],
                category="prop",
            ),
        ],
    }


def web_reference(run_dir, item_id="001-court-master", ref_id="court-ref"):
    ref_dir = run_dir / "web_references" / item_id
    ref_dir.mkdir(parents=True, exist_ok=True)
    ref_path = ref_dir / f"{ref_id}.jpg"
    ref_path.write_bytes(b"web reference image")
    return {
        "id": ref_id,
        "local_path": str(ref_path),
        "source_url": f"https://example.com/images/{ref_id}.jpg",
        "page_url": "https://example.com/court-reference" if ref_id == "court-ref" else f"https://example.com/{ref_id}-reference",
        "source_title": f"Empty court reference {ref_id}",
        "reference_purpose": "Court surface, fence, and wall material reference",
        "observed_facts": [
            f"weathered asphalt texture {ref_id}",
            "chain-link fence behind the court",
            "blank masonry wall behind the hoop",
        ],
        "usage_note": "Use only factual material and layout cues; do not copy composition, watermark, logo, or style.",
    }


def web_references(run_dir, item_id="001-court-master", count=3):
    return [web_reference(run_dir, item_id=item_id, ref_id=f"{item_id}-ref-{index}") for index in range(1, count + 1)]


class VideoScenarioImagePackRunnerTest(unittest.TestCase):
    def init_run(self, root):
        scenario = root / "scenario.md"
        scenario.write_text("# Noeul Court\n\nEmpty sunset basketball court.", encoding="utf-8")
        result = run_cli(
            "init",
            "--title",
            "Noeul Court",
            "--scenario",
            str(scenario),
            "--output-root",
            str(root / "output"),
        )
        return run_dir_from(result.stdout)

    def approve_plan(self, run_dir):
        plan_file = run_dir / "plan.json"
        plan_file.write_text(json.dumps(sample_plan()), encoding="utf-8")
        run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))
        return plan_file

    def import_item(self, run_dir, filename, content=b"generated"):
        generated = run_dir / f"generated-{filename}"
        generated.write_bytes(content)
        run_cli(
            "import",
            "--run-dir",
            str(run_dir),
            "--item",
            filename,
            "--generated",
            str(generated),
            "--worker-status",
            "pass",
            "--worker-note",
            "worker pass",
        )

    def inspect_pass(self, run_dir, filename, note="parent pass"):
        run_cli(
            "inspect-pass",
            "--run-dir",
            str(run_dir),
            "--item",
            filename,
            "--note",
            note,
        )

    def test_next_batch_blocks_until_plan_is_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))

            result = run_cli_raw("next-batch", "--run-dir", str(run_dir), "--limit", "4")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Plan is not approved", result.stderr)

    def test_continuity_anchor_becomes_dependency_and_blocks_dependent_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            self.approve_plan(run_dir)

            state = json.loads((run_dir / "state.json").read_text())
            hoop = next(item for item in state["items"] if item["id"] == "002-hoop-detail")
            self.assertEqual(hoop["dependencies"], ["001-court-master"])

            batch = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            self.assertIn("BATCH_ID: batch-001", batch.stdout)
            self.assertIn("ITEM: 001-court-master.png", batch.stdout)
            self.assertNotIn("002-hoop-detail.png", batch.stdout)

    def test_rerun_reserves_item_before_other_pending_dependents_and_adds_prompt_hints(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            self.approve_plan(run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            self.import_item(run_dir, "001-court-master.png")
            self.inspect_pass(run_dir, "001-court-master.png", "anchor pass")

            first_dependent = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "1")
            self.assertIn("ITEM: 002-hoop-detail.png", first_dependent.stdout)
            self.import_item(run_dir, "002-hoop-detail.png")
            run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "002-hoop-detail.png",
                "--note",
                "background silhouette and car visible",
            )

            rerun_batch = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "2")

            self.assertIn("ITEM: 002-hoop-detail.png", rerun_batch.stdout)
            self.assertNotIn("003-ball-prop.png", rerun_batch.stdout.split("ITEM: 002-hoop-detail.png", 1)[0])
            state = json.loads((run_dir / "state.json").read_text())
            hoop = next(item for item in state["items"] if item["id"] == "002-hoop-detail")
            self.assertIn("background silhouette and car visible", hoop["rerun_prompt_hints"])
            prompt_text = Path(hoop["prompt_file"]).read_text()
            self.assertIn("Rerun prompt hints", prompt_text)
            self.assertIn("background silhouette and car visible", prompt_text)

    def test_import_batch_and_inspect_batch_pass_apply_sequentially(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            self.approve_plan(run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            self.import_item(run_dir, "001-court-master.png")
            self.inspect_pass(run_dir, "001-court-master.png", "anchor pass")

            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            generated_a = run_dir / "generated-hoop.png"
            generated_b = run_dir / "generated-ball.png"
            generated_a.write_bytes(b"hoop")
            generated_b.write_bytes(b"ball")
            import_manifest = run_dir / "import-manifest.json"
            import_manifest.write_text(
                json.dumps(
                    {
                        "run_dir": str(run_dir),
                        "items": [
                            {
                                "item": "002-hoop-detail.png",
                                "generated": str(generated_a),
                                "worker_status": "pass",
                                "worker_note": "worker hoop pass",
                            },
                            {
                                "item": "003-ball-prop.png",
                                "generated": str(generated_b),
                                "worker_status": "pass",
                                "worker_note": "worker ball pass",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            import_result = run_cli("import-batch", "--manifest", str(import_manifest))

            self.assertIn("IMPORTED: 2", import_result.stdout)
            self.assertEqual((run_dir / "002-hoop-detail.png").read_bytes(), b"hoop")
            self.assertEqual((run_dir / "003-ball-prop.png").read_bytes(), b"ball")

            inspect_manifest = run_dir / "inspect-manifest.json"
            inspect_manifest.write_text(
                json.dumps(
                    {
                        "run_dir": str(run_dir),
                        "items": [
                            {"item": "002-hoop-detail.png", "note": "parent hoop pass"},
                            {"item": "003-ball-prop.png", "note": "parent ball pass"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            inspect_result = run_cli("inspect-batch-pass", "--manifest", str(inspect_manifest))

            self.assertIn("INSPECTED_PASS: 2", inspect_result.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertTrue(all(item["status"] == "inspected_pass" for item in state["items"]))

    def test_batch_prompts_writes_ready_to_spawn_subagent_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            self.approve_plan(run_dir)
            batch = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            batch_id = next(line.split(": ", 1)[1] for line in batch.stdout.splitlines() if line.startswith("BATCH_ID: "))

            prompts = run_cli("batch-prompts", "--run-dir", str(run_dir), "--batch-id", batch_id)

            self.assertIn("SUBAGENT_PROMPT:", prompts.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            anchor = next(item for item in state["items"] if item["id"] == "001-court-master")
            self.assertTrue(Path(anchor["artifact_paths"]["subagent_prompt"]).exists())
            subagent_prompt = Path(anchor["artifact_paths"]["subagent_prompt"]).read_text()
            self.assertIn("You are generating exactly one image", subagent_prompt)
            self.assertIn("Do not edit state.json", subagent_prompt)

    def test_production_source_verification_lock_is_in_non_character_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            plan = sample_plan()
            plan["items"][0]["negative_prompt"] = "avoid muddy court texture"
            plan["items"][0]["must_match"] = [
                "사람처럼 읽히는 작은 세로 형상 금지",
                "고정 랜드마크 상대 위치 유지",
                "소품 형태/재질/손상 상태 유지",
            ]
            plan_file = run_dir / "plan.json"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            state = json.loads((run_dir / "state.json").read_text())
            anchor = next(item for item in state["items"] if item["id"] == "001-court-master")
            prompt = Path(anchor["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(anchor["artifact_paths"]["subagent_prompt"]).read_text(encoding="utf-8")

            for text in (prompt, subagent_prompt):
                self.assertIn("Production source verification lock:", text)
                self.assertIn("No-character artifact lock:", text)
                self.assertIn("tiny human-like marks", text)
                self.assertIn("human-like reflections", text)
                self.assertIn("poster/window figures", text)
                self.assertIn("vehicle silhouettes", text)
                self.assertIn("background street activity", text)
                self.assertIn("Spatial continuity lock:", text)
                self.assertIn("moved landmarks", text)
                self.assertIn("swapped building positions", text)
                self.assertIn("fixed landmark relative-position drift", text)
                self.assertIn("Prop/environment state lock:", text)
                self.assertIn("changed prop shape/material/scale", text)
                self.assertIn("wrong damage state", text)
                self.assertIn("wrong time of day/weather", text)
                self.assertIn("unapproved set dressing drift", text)

            self.assertIn("Hoop far/right, gate and bench left", prompt)
            self.assertIn("사람처럼 읽히는 작은 세로 형상 금지", prompt)
            self.assertIn("avoid muddy court texture", prompt)
            self.assertIn("people, person, pedestrian", prompt)
            self.assertIn("tiny human-like marks", prompt)

    def test_character_allowed_items_keep_spatial_and_prop_verification_without_no_character_ban(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            plan = {
                "scenario_title": "Character Allowed Insert",
                "items": [
                    {
                        **base_item("001-actor-mark", "001-actor-mark.png", category="character"),
                        "contains_character": True,
                        "purpose": "Approved character blocking reference.",
                        "prompt": "Approved performer standing on the marked court position.",
                    }
                ],
            }
            plan_file = run_dir / "plan.json"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            state = json.loads((run_dir / "state.json").read_text())
            item = state["items"][0]
            prompt = Path(item["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(item["artifact_paths"]["subagent_prompt"]).read_text(encoding="utf-8")

            for text in (prompt, subagent_prompt):
                self.assertIn("Character policy: explicit_character_allowed", text)
                self.assertIn("Production source verification lock:", text)
                self.assertIn("Spatial continuity lock:", text)
                self.assertIn("Prop/environment state lock:", text)
                self.assertIn("changed prop shape/material/scale", text)
                self.assertNotIn("Do not include people, pedestrians", text)
                self.assertNotIn("No-character artifact lock:", text)

    def test_web_references_are_preserved_and_included_in_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            plan = sample_plan()
            reference = web_reference(run_dir)
            plan["items"][0]["web_references"] = [reference]
            plan_file = run_dir / "plan.json"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))
            state = json.loads((run_dir / "state.json").read_text())
            anchor = next(item for item in state["items"] if item["id"] == "001-court-master")
            self.assertEqual(anchor["web_references"][0]["id"], "court-ref")
            self.assertEqual(anchor["web_references"][0]["source_url"], "https://example.com/images/court-ref.jpg")
            manifest = json.loads((run_dir / "web_reference_manifest.json").read_text())
            self.assertEqual(manifest["items"][0]["web_references"][0]["id"], "court-ref")

            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            state = json.loads((run_dir / "state.json").read_text())
            anchor = next(item for item in state["items"] if item["id"] == "001-court-master")
            prompt = Path(anchor["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(anchor["artifact_paths"]["subagent_prompt"]).read_text(encoding="utf-8")

            for text in (prompt, subagent_prompt):
                self.assertIn("Web reference policy:", text)
                self.assertIn("Web reference count: 1", text)
                self.assertIn(str(Path(reference["local_path"])), text)
                self.assertIn("https://example.com/images/court-ref.jpg", text)
                self.assertIn("https://example.com/court-reference", text)
                self.assertIn("weathered asphalt texture court-ref", text)
                self.assertIn("Use only factual material and layout cues", text)
                self.assertIn("do not copy composition, watermark, logo, or style", text)

    def test_web_reference_search_note_is_preserved_in_state_manifest_and_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            plan = sample_plan()
            plan["items"][0]["web_references"] = []
            plan["items"][0]["web_reference_search_note"] = "검색 실패: 적합한 빈 코트 참고 이미지를 찾지 못함"
            plan_file = run_dir / "plan.json"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))
            state = json.loads((run_dir / "state.json").read_text())
            anchor = next(item for item in state["items"] if item["id"] == "001-court-master")
            self.assertEqual(anchor["web_reference_search_note"], "검색 실패: 적합한 빈 코트 참고 이미지를 찾지 못함")
            manifest = json.loads((run_dir / "web_reference_manifest.json").read_text())
            manifest_item = next(item for item in manifest["items"] if item["id"] == "001-court-master")
            self.assertEqual(
                manifest_item["web_reference_search_note"],
                "검색 실패: 적합한 빈 코트 참고 이미지를 찾지 못함",
            )

            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            state = json.loads((run_dir / "state.json").read_text())
            anchor = next(item for item in state["items"] if item["id"] == "001-court-master")
            prompt = Path(anchor["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(anchor["artifact_paths"]["subagent_prompt"]).read_text(encoding="utf-8")

            for text in (prompt, subagent_prompt):
                self.assertIn("Web reference count: 0", text)
                self.assertIn("Web reference search note: 검색 실패: 적합한 빈 코트 참고 이미지를 찾지 못함", text)
                self.assertIn("- none registered", text)

    def test_three_registered_web_references_are_all_included_in_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            plan = sample_plan()
            references = web_references(run_dir, count=3)
            plan["items"][0]["web_references"] = references
            plan_file = run_dir / "plan.json"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            state = json.loads((run_dir / "state.json").read_text())
            anchor = next(item for item in state["items"] if item["id"] == "001-court-master")
            prompt = Path(anchor["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(anchor["artifact_paths"]["subagent_prompt"]).read_text(encoding="utf-8")

            for text in (prompt, subagent_prompt):
                self.assertIn("Web reference count: 3", text)
                for reference in references:
                    self.assertIn(str(Path(reference["local_path"])), text)
                    self.assertIn(reference["source_url"], text)
                    self.assertIn(reference["observed_facts"][0], text)

    def test_dependency_output_and_web_reference_are_both_reference_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            plan = sample_plan()
            reference = web_reference(run_dir, item_id="002-hoop-detail", ref_id="hoop-ref")
            plan["items"][1]["web_references"] = [reference]
            plan_file = run_dir / "plan.json"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            self.import_item(run_dir, "001-court-master.png")
            self.inspect_pass(run_dir, "001-court-master.png", "anchor pass")
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "1")
            state = json.loads((run_dir / "state.json").read_text())
            hoop = next(item for item in state["items"] if item["id"] == "002-hoop-detail")
            prompt = Path(hoop["prompt_file"]).read_text(encoding="utf-8")
            subagent_prompt = Path(hoop["artifact_paths"]["subagent_prompt"]).read_text(encoding="utf-8")

            self.assertIn(str(run_dir / "001-court-master.png"), prompt)
            self.assertIn(str(Path(reference["local_path"])), prompt)
            self.assertIn(str(run_dir / "001-court-master.png"), subagent_prompt)
            self.assertIn(str(Path(reference["local_path"])), subagent_prompt)

    def test_approve_plan_rejects_missing_or_out_of_run_web_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            plan = sample_plan()
            plan["items"][0]["web_references"] = [
                {
                    **web_reference(run_dir),
                    "id": "missing-ref",
                    "local_path": str(run_dir / "web_references" / "001-court-master" / "missing.jpg"),
                }
            ]
            plan_file = run_dir / "missing-reference-plan.json"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")

            missing = run_cli_raw("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))

            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("Web reference file not found", missing.stderr)

            outside = Path(tmp) / "outside-reference.jpg"
            outside.write_bytes(b"outside")
            plan["items"][0]["web_references"] = [{**web_reference(run_dir), "id": "outside-ref", "local_path": str(outside)}]
            plan_file.write_text(json.dumps(plan), encoding="utf-8")

            outside_result = run_cli_raw("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))

            self.assertNotEqual(outside_result.returncode, 0)
            self.assertIn("must be under the current run web_references folder", outside_result.stderr)

    def test_write_plan_template_includes_web_reference_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))

            run_cli("write-plan-template", "--run-dir", str(run_dir))
            template = json.loads((run_dir / "approved_image_plan.template.json").read_text())

            self.assertIn("web_reference_search_note", template["items"][0])
            self.assertIn("web_references", template["items"][0])
            self.assertEqual(len(template["items"][0]["web_references"]), 3)
            for reference in template["items"][0]["web_references"]:
                self.assertIn("local_path", reference)
                self.assertIn("source_url", reference)
                self.assertIn("observed_facts", reference)
                self.assertIn("usage_note", reference)

    def test_report_flags_zero_and_below_recommended_web_reference_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            plan = sample_plan()
            plan["items"][0]["web_references"] = []
            plan["items"][0]["web_reference_search_note"] = "검색 실패: 적합한 빈 코트 사진 없음"
            plan["items"][1]["web_references"] = web_references(run_dir, item_id="002-hoop-detail", count=1)
            plan["items"][1]["web_reference_search_note"] = "추가 후보는 사람이 포함되어 제외"
            plan["items"][2]["web_references"] = web_references(run_dir, item_id="003-ball-prop", count=3)
            plan_file = run_dir / "plan.json"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))

            report = run_cli("report", "--run-dir", str(run_dir))

            self.assertIn("웹 참고 자료: 4개", report.stdout)
            self.assertIn("웹 참고 자료 0개 항목: 001-court-master.png - 검색 실패: 적합한 빈 코트 사진 없음", report.stdout)
            self.assertIn(
                "웹 참고 자료 권장 미만(3개 미만): 001-court-master.png (0개), 002-hoop-detail.png (1개)",
                report.stdout,
            )

    def test_report_summarizes_completion_and_reruns_in_korean(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            self.approve_plan(run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            self.import_item(run_dir, "001-court-master.png")
            run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-court-master.png",
                "--note",
                "tiny background silhouette",
            )

            report = run_cli("report", "--run-dir", str(run_dir))

            self.assertIn("[영상 시나리오 이미지 팩 진행 결과]", report.stdout)
            self.assertIn("승인된 이미지 수: 3", report.stdout)
            self.assertIn("rerun 필요/진행 항목: 1", report.stdout)
            self.assertIn("현재 차단 항목: 없음", report.stdout)


if __name__ == "__main__":
    unittest.main()
