from __future__ import annotations

from dataclasses import is_dataclass, replace
import re
from typing import Any


ABSTENTION_MARKERS = (
    "no se encontró evidencia suficiente",
    "no se encontro evidencia suficiente",
    "no hay evidencia suficiente",
    "no dispongo de evidencia suficiente",
    "no puedo responder con la evidencia disponible",
    "no es posible responder con la evidencia disponible",
)

SOURCE_CITATION_RE = re.compile(r"\[F\d+\]", re.IGNORECASE)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def contains_abstention_marker(text: str) -> bool:
    lowered = normalize_space(text).lower()
    return any(marker in lowered for marker in ABSTENTION_MARKERS)


def remove_abstention_sentences(text: str) -> str:
    """
    Elimina únicamente oraciones que contienen un marcador de abstención.
    Conserva el contenido sustantivo y las citas.
    """
    raw = str(text or "").strip()

    if not raw:
        return ""

    # Trabajamos por líneas para conservar listas Markdown.
    kept = []

    for line in raw.splitlines():
        lowered = normalize_space(line).lower()

        if any(marker in lowered for marker in ABSTENTION_MARKERS):
            continue

        # "Fuentes utilizadas" aislado suele ser parte del cierre de abstención.
        if normalize_space(line).lower() in {
            "fuentes utilizadas",
            "fuentes utilizadas:",
        }:
            continue

        kept.append(line)

    cleaned = "\n".join(kept).strip()

    # Limpieza ligera de espacios verticales.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned


def substantive_score(text: str) -> dict[str, Any]:
    cleaned = remove_abstention_sentences(text)

    words = re.findall(
        r"\b[\wÁÉÍÓÚÜÑáéíóúüñ-]+\b",
        cleaned,
        flags=re.UNICODE,
    )

    citations = SOURCE_CITATION_RE.findall(cleaned)

    bullets = len(
        re.findall(
            r"(?m)^\s*(?:[-*•]|\d+[.)])\s+",
            cleaned,
        )
    )

    return {
        "cleaned_answer": cleaned,
        "word_count": len(words),
        "citation_count": len(citations),
        "bullet_count": bullets,
        "has_abstention_marker": contains_abstention_marker(text),
    }


def is_mixed_generation_abstention(response: Any) -> bool:
    """
    Criterio intencionalmente estricto.

    Solo considera "mixta" una respuesta cuando:
    - el pipeline la marcó como abstención;
    - la etapa fue generation;
    - el texto contiene marcador explícito de abstención;
    - al retirar ese marcador queda contenido sustantivo;
    - existe al menos una cita [F#] o una lista estructurada.
    """
    if response is None:
        return False

    if not bool(getattr(response, "abstained", False)):
        return False

    stage = str(
        getattr(response, "abstention_stage", "") or ""
    ).strip().lower()

    if stage != "generation":
        return False

    answer = str(
        getattr(response, "answer", "") or ""
    )

    info = substantive_score(answer)

    if not info["has_abstention_marker"]:
        return False

    enough_content = (
        info["word_count"] >= 18
        and len(info["cleaned_answer"]) >= 100
    )

    grounded_shape = (
        info["citation_count"] >= 1
        or info["bullet_count"] >= 2
    )

    return enough_content and grounded_shape


def normalize_mixed_abstention(response: Any) -> tuple[Any, dict[str, Any]]:
    """
    Si detecta abstención mixta, conserva la respuesta sustantiva y cambia
    únicamente el estado de abstención para la UI.

    No modifica retrieval, Top-K, threshold ni fuentes.
    """
    answer = str(
        getattr(response, "answer", "") or ""
    )

    info = substantive_score(answer)

    decision = {
        **info,
        "corrected": False,
        "reason": "sin cambios",
    }

    if not is_mixed_generation_abstention(response):
        return response, decision

    cleaned_answer = info["cleaned_answer"]

    if not cleaned_answer:
        decision["reason"] = (
            "el contenido restante quedó vacío; se conserva la abstención"
        )
        return response, decision

    # Dataclass: preferimos replace para no depender de mutabilidad.
    if is_dataclass(response):
        try:
            corrected = replace(
                response,
                answer=cleaned_answer,
                abstained=False,
                abstention_stage=None,
            )
            decision["corrected"] = True
            decision["reason"] = (
                "abstención mixta corregida mediante dataclasses.replace"
            )
            return corrected, decision
        except Exception:
            pass

    # Objeto mutable.
    try:
        setattr(
            response,
            "answer",
            cleaned_answer,
        )
        setattr(
            response,
            "abstained",
            False,
        )

        if hasattr(
            response,
            "abstention_stage",
        ):
            setattr(
                response,
                "abstention_stage",
                None,
            )

        decision["corrected"] = True
        decision["reason"] = (
            "abstención mixta corregida sobre objeto mutable"
        )
        return response, decision

    except Exception:
        decision["reason"] = (
            "respuesta inmutable/no compatible; no se aplicó corrección"
        )
        return response, decision
