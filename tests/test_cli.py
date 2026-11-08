"""End-to-end CLI smoke tests through main(), with captured stdout."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from docconcord.cli import main  # noqa: E402

NAV = "> 🌐 [English](README.en.md) · [简体中文](README.zh-CN.md)"
BASE = ("# T\n\n" + NAV + "\n\n## 🎉 Intro\n\nText.\n\n"
        "```bash\npip install docconcord\n```\n")
OK = ("# T\n\n" + NAV + "\n\n## 🎉 介绍\n\n文字。\n\n"
      "```bash\npip install docconcord\n```\n")
BROKEN = ("# T\n\n" + NAV + "\n\n## 🎉 介绍\n\n文字。\n\n"
          "```bash\npip install docconcord\n```\n\n[坏锚点](#nope)\n")


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = main(argv)
    return code, buf.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.write("README.en.md", BASE)
        self.write("README.zh-CN.md", OK)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        with open(os.path.join(self.tmp.name, name), "w", encoding="utf-8") as fh:
            fh.write(text)

    def test_version_and_rules(self):
        code, out = run(["version"])
        self.assertEqual(code, 0)
        self.assertIn("1.0.0", out)
        code, out = run(["rules"])
        self.assertIn("S001", out)
        self.assertIn("X002", out)

    def test_scan_lists_families(self):
        code, out = run(["scan", self.tmp.name])
        self.assertEqual(code, 0)
        self.assertIn("README", out)
        self.assertIn("基准", out)

    def test_check_json_output(self):
        code, out = run(["check", self.tmp.name, "--format", "json", "--fail-on", "never"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["summary"]["documents"], 2)

    def test_check_gate_fails_on_error(self):
        self.write("README.zh-CN.md", BROKEN)
        code, out = run(["check", self.tmp.name, "--fail-on", "error"])
        self.assertEqual(code, 1)
        self.assertIn("L002", out)

    def test_check_output_file(self):
        target = os.path.join(self.tmp.name, "report.json")
        code, _ = run(["check", self.tmp.name, "--format", "json", "-o", target])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(target))
        with open(target, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["tool"], "DocConcord")

    def test_fix_dry_run_and_apply(self):
        self.write("README.en.md", "# T\n\nNo nav.\n\n```\necho hello\n```\n")
        self.write("README.zh-CN.md", "# T\n\n无导航。\n\n```\necho hello\n```\n")
        code, out = run(["fix", self.tmp.name])
        self.assertEqual(code, 0)
        self.assertIn("补充语言切换导航", out)
        self.assertIn("dry-run", out)
        code, out = run(["fix", self.tmp.name, "--apply"])
        self.assertIn("已写回", out)
        with open(os.path.join(self.tmp.name, "README.en.md"), encoding="utf-8") as fh:
            self.assertIn("```text", fh.read())

    def test_bad_path_returns_runtime_error(self):
        code, _ = run(["check", "/definitely/not/a/real/path"])
        self.assertEqual(code, 2)

    def test_no_args_prints_help(self):
        code, out = run([])
        self.assertEqual(code, 0)
        self.assertIn("usage", out.lower())


if __name__ == "__main__":
    unittest.main()
