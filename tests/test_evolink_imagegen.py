import argparse
import importlib.util
import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "evolink-imagegen"
    / "scripts"
    / "evolink_imagegen.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("evolink_imagegen", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class EvolinkImageGenTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)

    def test_safe_label_blocks_path_traversal(self):
        self.assertEqual(self.module.safe_label("../../../escape", default="task"), "escape")

    def test_create_run_directory_is_unique(self):
        base_dir = Path(self.tempdir.name)
        with patch.object(self.module, "timestamp_slug", return_value="20260418_000000_000000"):
            first = self.module.create_run_directory(base_dir, "same-prompt")
            second = self.module.create_run_directory(base_dir, "same-prompt")

        self.assertNotEqual(first, second)
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())
        self.assertEqual(second.name, "20260418_000000_000000-same-prompt-2")

    def test_poll_command_returns_nonzero_for_failed_task(self):
        task = {
            "id": "task-1",
            "status": "failed",
            "progress": 100,
            "error": {"code": "content_policy_violation", "message": "blocked"},
            "results": [],
        }
        args = argparse.Namespace(
            base_url="https://api.evolink.ai",
            task_id="task-1",
            max_polls=1,
            poll_sleep=0,
            outdir=self.tempdir.name,
            no_download=True,
        )

        with patch.object(self.module, "require_token", return_value="token"), patch.object(
            self.module, "poll_until_complete", return_value=task
        ), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return_code = self.module.poll_command(args)

        self.assertEqual(return_code, 1)

    def test_poll_command_does_not_escape_output_directory(self):
        outside_path = Path(self.tempdir.name).parent / "escape"
        shutil.rmtree(outside_path, ignore_errors=True)
        self.addCleanup(lambda: shutil.rmtree(outside_path, ignore_errors=True))

        task = {
            "id": "task-1",
            "status": "failed",
            "progress": 100,
            "error": {"code": "content_policy_violation", "message": "blocked"},
            "results": [],
        }
        args = argparse.Namespace(
            base_url="https://api.evolink.ai",
            task_id="../../../escape",
            max_polls=1,
            poll_sleep=0,
            outdir=self.tempdir.name,
            no_download=True,
        )

        with patch.object(self.module, "require_token", return_value="token"), patch.object(
            self.module, "poll_until_complete", return_value=task
        ), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.module.poll_command(args)

        self.assertFalse(outside_path.exists())

    def test_generate_command_returns_nonzero_for_failed_task(self):
        task = {
            "id": "task-1",
            "status": "failed",
            "progress": 100,
            "error": {"code": "content_policy_violation", "message": "blocked"},
            "results": [],
        }
        args = argparse.Namespace(
            base_url="https://api.evolink.ai",
            model="z-image-turbo",
            prompt="soft watercolor spring garden illustration",
            size="1:1",
            seed=None,
            nsfw_check=False,
            callback_url=None,
            max_polls=1,
            poll_sleep=0,
            outdir=self.tempdir.name,
            dry_run=False,
        )

        with patch.object(self.module, "require_token", return_value="token"), patch.object(
            self.module, "request_json", return_value={"id": "task-1"}
        ), patch.object(self.module, "poll_until_complete", return_value=task), redirect_stdout(
            io.StringIO()
        ), redirect_stderr(io.StringIO()):
            return_code = self.module.generate_command(args)

        self.assertEqual(return_code, 1)


if __name__ == "__main__":
    unittest.main()
