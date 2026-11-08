"""Language detection, heading normalization and family discovery."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from docconcord.i18n import (  # noqa: E402
    canonical_language, choose_base, detect_language,
    discover_documents, normalize_heading, slugify,
)


class I18nTest(unittest.TestCase):
    def test_canonical_language(self):
        self.assertEqual(canonical_language("zh_hans"), "zh-CN")
        self.assertEqual(canonical_language("ZH-TW"), "zh-TW")
        self.assertEqual(canonical_language("en-US"), "en")
        self.assertEqual(canonical_language("ja-JP"), "ja")

    def test_detect_language(self):
        cases = {
            "README.md": ("und", "README"),
            "README.en.md": ("en", "README"),
            "README.zh-CN.md": ("zh-CN", "README"),
            "README.zh-TW.md": ("zh-TW", "README"),
            "guide_en_US.markdown": ("en", "guide"),
            "getting-started.md": ("und", "getting-started"),
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(detect_language(name), expected)

    def test_normalize_heading_strips_noise(self):
        self.assertEqual(normalize_heading("1. 🎉 项目介绍：核心"), "项目介绍 核心")
        self.assertEqual(normalize_heading("**Quick Start** 🚀"), "quick start")
        self.assertEqual(
            normalize_heading("🎉 快速开始", {"快速开始": "quick-start"}),
            "quick-start",
        )

    def test_slugify_duplicate_suffix(self):
        seen = {}
        self.assertEqual(slugify("Install Guide", seen), "install-guide")
        self.assertEqual(slugify("Install Guide", seen), "install-guide-1")
        self.assertEqual(slugify("### 打包与部署", seen), "打包与部署")

    def test_discover_documents_groups_only_multilingual_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.mkdir(os.path.join(tmp, "docs"))
            for name in ("README.md", "README.en.md", "README.zh-TW.md",
                         "docs/GUIDE.md", "CHANGELOG.md"):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    fh.write("# " + name + "\n")
            items = discover_documents(tmp)
            self.assertEqual(len(items), 3)
            self.assertEqual({i[3] for i in items}, {"README"})

    def test_choose_base_prefers_untagged_then_hint(self):
        items = [
            ("/r/README.en.md", "README.en.md", "en", "README"),
            ("/r/README.md", "README.md", "und", "README"),
            ("/r/README.zh-TW.md", "README.zh-TW.md", "zh-TW", "README"),
        ]
        self.assertEqual(choose_base(items, ""), 1)
        self.assertEqual(choose_base(items, "README.en.md"), 0)
        self.assertEqual(choose_base(items, "README.zh-TW.md"), 2)


if __name__ == "__main__":
    unittest.main()
