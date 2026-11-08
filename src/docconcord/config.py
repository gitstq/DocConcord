"""Configuration loading and validation.

Priority (low -> high): built-in defaults, ``.docconcord.json`` in the audited
root, explicit CLI flags. No environment variables are required to run the
tool; the ones documented in docs/ENVIRONMENT.md are purely optional overrides.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Optional

DEFAULTS: Dict[str, object] = {
    "base": "",
    "format": "text",
    "fail_on": "error",
    "online": False,
    "aliases": {},
    "disabled_rules": [],
    "max_file_bytes": 2_000_000,
}

FORMATS = ("text", "json", "markdown", "junit")
FAIL_ON = ("error", "warning", "info", "never")
CONFIG_FILE = ".docconcord.json"

_ENV_MAP = {
    "DOCCONCORD_BASE": "base",
    "DOCCONCORD_FORMAT": "format",
    "DOCCONCORD_FAIL_ON": "fail_on",
}


def load_config(root: str, overrides: Optional[dict] = None) -> dict:
    cfg: Dict[str, object] = dict(DEFAULTS)
    cfg["aliases"] = {}
    cfg["disabled_rules"] = []

    path = os.path.join(root, CONFIG_FILE)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            if isinstance(raw, dict):
                for key, value in raw.items():
                    if key == "aliases" and isinstance(value, dict):
                        cfg["aliases"] = {str(k).lower(): str(v) for k, v in value.items()}
                    elif key in DEFAULTS:
                        cfg[key] = value
        except (OSError, ValueError) as exc:
            raise ValueError(f"无法解析 {CONFIG_FILE}: {exc}") from exc

    for key, value in _ENV_MAP.items():
        if os.environ.get(key):
            cfg[value] = os.environ[key]

    if overrides:
        for key, value in overrides.items():
            if value is not None and key in DEFAULTS:
                cfg[key] = value

    fmt = str(cfg.get("format", "text")).lower()
    fail = str(cfg.get("fail_on", "error")).lower()
    if fmt not in FORMATS:
        raise ValueError(f"未知输出格式: {fmt}（可选 {', '.join(FORMATS)}）")
    if fail not in FAIL_ON:
        raise ValueError(f"未知 --fail-on: {fail}（可选 {', '.join(FAIL_ON)}）")
    cfg["format"], cfg["fail_on"] = fmt, fail
    cfg["online"] = bool(cfg.get("online"))
    cfg["aliases"] = cfg.get("aliases") or {}
    cfg["disabled_rules"] = list(cfg.get("disabled_rules") or [])
    return cfg
