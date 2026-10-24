from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import re
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "cloud_config.json"


def is_cloud_runtime() -> bool:
    return (
        os.getenv("DINDES_RUNTIME", "").strip().lower() == "cloud"
        or os.getenv("DINDES_CLOUD_MODE", "").strip() == "1"
    )


def load_cloud_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return re.sub(r"\s+", " ", str(value)).strip()


def object_to_text(obj: Any) -> str:
    """
    Convierte objetos de recuperación heterogéneos a texto sin exigir
    que sean JSON serializables.
    """
    if obj is None:
        return ""

    if isinstance(obj, str):
        return normalize_text(obj)

    if isinstance(obj, dict):
        for key in ("text", "content", "chunk", "answer", "description", "title"):
            if key in obj and obj[key]:
                return normalize_text(obj[key])
        return normalize_text(obj)

    for attr in ("text", "content", "chunk", "answer", "description", "title"):
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            if value:
                return normalize_text(value)

    return normalize_text(obj)


@dataclass
class CloudGenerationResult:
    answer: str
    abstained: bool
    mode: str = "cloud-evidence"
    provider: str = "deterministic-fallback"


class EvidenceExtractGenerator:
    """
    Fallback ligero para la versión pública.

    No inventa contenido. Resume únicamente evidencia recuperada.
    Se usa cuando el LLM local está deshabilitado en cloud.
    """

    def __init__(self, max_sources: int = 3, max_chars_per_source: int = 650):
        self.max_sources = max_sources
        self.max_chars_per_source = max_chars_per_source

    def generate(
        self,
        question: str,
        sources: Iterable[Any] | None = None,
        **_: Any,
    ) -> CloudGenerationResult:
        sources = list(sources or [])
        evidence = []

        for source in sources[: self.max_sources]:
            text = object_to_text(source)
            if text:
                evidence.append(text[: self.max_chars_per_source].rstrip())

        if not evidence:
            return CloudGenerationResult(
                answer=(
                    "No se encontró evidencia suficiente en las fuentes "
                    "disponibles para responder esta consulta."
                ),
                abstained=True,
            )

        bullets = "\n".join(
            f"- {text}" for text in evidence
        )

        answer = (
            "Evidencia recuperada para la consulta:\n\n"
            f"{bullets}\n\n"
            "Esta versión pública utiliza una generación ligera y "
            "conservadora. Verifique las fuentes mostradas por la aplicación."
        )

        return CloudGenerationResult(
            answer=answer,
            abstained=False,
        )


def get_cloud_generator() -> EvidenceExtractGenerator:
    return EvidenceExtractGenerator()
