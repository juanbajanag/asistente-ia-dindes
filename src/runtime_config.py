from __future__ import annotations

from pathlib import Path
import json
import os
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "runtime_config.json"

def is_cloud_runtime() -> bool:
    return (
        os.getenv("DINDES_RUNTIME", "").strip().lower() == "cloud"
        or os.getenv("DINDES_CLOUD_MODE", "").strip() == "1"
    )

def load_runtime_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

def get_runtime_profile() -> str:
    return "cloud" if is_cloud_runtime() else "local"

def get_rag_runtime_settings() -> dict[str, Any]:
    cfg = load_runtime_config()
    if cfg["local"]["top_k"] != cfg["cloud"]["top_k"]:
        raise RuntimeError("Top-K difiere entre perfiles.")
    if cfg["local"]["dense_min_score"] != cfg["cloud"]["dense_min_score"]:
        raise RuntimeError("Threshold difiere entre perfiles.")
    profile = get_runtime_profile()
    settings = dict(cfg[profile])
    settings["profile"] = profile
    return settings
