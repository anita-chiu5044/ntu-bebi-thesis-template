"""Regression checks for truthful progress data and its regeneration workflow.

Run from the repository root with:
    python -m unittest discover -s tests -p 'test_research_progress.py'
"""

import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_research_progress.py"
SPEC = importlib.util.spec_from_file_location("render_research_progress", SCRIPT)
progress = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = progress
SPEC.loader.exec_module(progress)


def source_data():
    return json.loads((ROOT / "research_progress.json").read_text(encoding="utf-8"))


class ProgressValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = source_data()

    def test_repository_source_is_valid(self):
        progress.validate_progress(self.data)

    def test_invalid_status_is_rejected_everywhere(self):
        for section in ("stages", "short_term_plan", "decision_points", "milestones", "timeline"):
            with self.subTest(section=section):
                data = copy.deepcopy(self.data)
                data[section][0]["status"] = "finished_without_review"
                with self.assertRaises(ValueError):
                    progress.validate_progress(data)

    def test_duplicate_identifiers_are_rejected(self):
        for section in ("stages", "evidence_sources", "short_term_plan", "decision_points", "milestones", "timeline"):
            with self.subTest(section=section):
                data = copy.deepcopy(self.data)
                data[section].append(copy.deepcopy(data[section][0]))
                with self.assertRaises(ValueError):
                    progress.validate_progress(data)

    def test_unknown_current_stage_is_rejected(self):
        self.data["current_stage"]["id"] = "missing_stage"
        with self.assertRaises(ValueError):
            progress.validate_progress(self.data)

    def test_unknown_dependency_is_rejected(self):
        self.data["stages"][0]["depends_on"] = ["missing_stage"]
        with self.assertRaises(ValueError):
            progress.validate_progress(self.data)

    def test_unknown_evidence_source_is_rejected(self):
        self.data["stages"][0]["evidence"] = ["missing_evidence"]
        with self.assertRaises(ValueError):
            progress.validate_progress(self.data)

    def test_unknown_planning_stage_reference_is_rejected(self):
        for section in ("short_term_plan", "decision_points", "milestones", "timeline"):
            with self.subTest(section=section):
                data = copy.deepcopy(self.data)
                data[section][0]["stage_ids"] = ["missing_stage"]
                with self.assertRaises(ValueError):
                    progress.validate_progress(data)

    def test_dependency_cycle_is_rejected(self):
        first, second = self.data["stages"][:2]
        first["depends_on"] = [second["id"]]
        second["depends_on"] = [first["id"]]
        with self.assertRaises(ValueError):
            progress.validate_progress(self.data)

    def test_invalid_calendar_dates_are_rejected(self):
        for path in (("updated_at",), ("deadline", "date"),
                     ("timeline", 0, "start"), ("milestones", 0, "date")):
            with self.subTest(path=path):
                data = copy.deepcopy(self.data)
                target = data
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = "2026-02-30"
                with self.assertRaises(ValueError):
                    progress.validate_progress(data)

    def test_reversed_planning_dates_are_rejected(self):
        for section in ("short_term_plan", "timeline"):
            with self.subTest(section=section):
                data = copy.deepcopy(self.data)
                data[section][0]["start"] = "2026-12-15"
                data[section][0]["end"] = "2026-09-28"
                with self.assertRaises(ValueError):
                    progress.validate_progress(data)

    def test_verified_completion_requires_artifact_evidence(self):
        stage = self.data["stages"][0]
        stage["status"] = "verified_complete"
        stage["artifacts"] = []
        # Even a cited verified source is not a stage-specific output record.
        stage["evidence"] = [source["id"] for source in self.data["evidence_sources"]
                             if source["type"] == "artifact_verified"]
        with self.assertRaises(ValueError):
            progress.validate_progress(self.data)

    def test_reported_completion_is_distinct_from_verified_completion(self):
        self.data["evidence_sources"].append({
            "id": "synthetic_report", "type": "user_confirmed", "label": "Test fixture",
            "reference": "Synthetic report, not actual research evidence", "note": "Test only",
        })
        stage = self.data["stages"][0]
        stage.update(status="reported_complete", evidence=["synthetic_report"], artifacts=[])
        progress.validate_progress(self.data)
        stage.update(status="verified_complete", artifacts=["synthetic/output.json (test only)"])
        with self.assertRaises(ValueError):
            progress.validate_progress(self.data)

    def test_verified_completion_accepts_registered_artifact_evidence(self):
        self.data["evidence_sources"].append({
            "id": "synthetic_artifact", "type": "artifact_verified", "label": "Test fixture",
            "reference": "Synthetic artifact, not actual research evidence", "note": "Test only",
        })
        self.data["stages"][0].update(
            status="verified_complete", evidence=["synthetic_artifact"],
            artifacts=["synthetic/output.json (test only)"],
        )
        progress.validate_progress(self.data)


class ProgressWorkflowTests(unittest.TestCase):
    def invoke(self, source, output, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--source", str(source),
             "--output-dir", str(output), *extra],
            cwd=ROOT, text=True, capture_output=True, timeout=120,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_source_changes_stay_stale_until_regenerated(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / "progress.json"
            output = directory / "generated"
            original = source_data()

            def write(data):
                source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            write(original)
            self.assert_success(self.invoke(source, output))
            self.assert_success(self.invoke(source, output, "--check"))
            png = output / "research_progress.png"
            with Image.open(png) as rendered:
                self.assertEqual(rendered.format, "PNG")
                rendered.verify()
            original_files = {path.relative_to(output): path.read_bytes()
                              for path in output.rglob("*") if path.is_file()}

            mutations = (
                ("focus", lambda data: data["current_stage"].update(focus="Regression test focus")),
                ("status", lambda data: data["stages"][0].update(
                    status="blocked" if data["stages"][0]["status"] != "blocked" else "planned")),
                ("plan", lambda data: data["short_term_plan"][0].update(deliverable="Regression test deliverable")),
            )
            for label, mutate in mutations:
                with self.subTest(change=label):
                    changed = copy.deepcopy(original)
                    mutate(changed)
                    write(changed)
                    result = self.invoke(source, output, "--check")
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    current_files = {path.relative_to(output): path.read_bytes()
                                     for path in output.rglob("*") if path.is_file()}
                    self.assertEqual(original_files, current_files, "--check must not rewrite outputs")

            self.assert_success(self.invoke(source, output))
            self.assert_success(self.invoke(source, output, "--check"))
            self.assertNotEqual(png.read_bytes(), original_files[Path("research_progress.png")])
            png.unlink()
            self.assertNotEqual(self.invoke(source, output, "--check").returncode, 0)

    def test_invalid_source_fails_without_creating_a_figure(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / "invalid.json"
            output = directory / "generated"
            data = source_data()
            data["current_stage"]["id"] = "unknown"
            source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = self.invoke(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((output / "research_progress.png").exists())

    def test_primary_documents_embed_the_same_canonical_image(self):
        canonical = ROOT / "docs" / "research_progress.png"
        for relative in ("README.md", "docs/RESEARCH_ARCHITECTURE.md", "docs/THESIS_STRUCTURE.md"):
            with self.subTest(document=relative):
                document = ROOT / relative
                text = document.read_text(encoding="utf-8")
                matches = list(re.finditer(r"!\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", text))
                canonical_matches = [match for match in matches
                                     if (document.parent / match.group(1)).resolve() == canonical]
                self.assertTrue(canonical_matches, "Document must embed docs/research_progress.png")
                if relative == "README.md":
                    self.assertLessEqual(text[:canonical_matches[0].start()].count("\n"), 35,
                                         "Progress should be visible near the top of README")


if __name__ == "__main__":
    unittest.main()
