from __future__ import annotations

import re
import unicodedata


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _strip_terminal_punctuation(text: str) -> str:
    return text.rstrip(" ?!.,;:")


def _strip_leading_article(text: str) -> str:
    """
    Elimina artículos/determinantes iniciales frecuentes del tema recuperado.
    Ejemplos:
    - "el inventario de bodega" -> "inventario de bodega"
    - "la documentación técnica" -> "documentación técnica"
    - "los procedimientos de mantenimiento" -> "procedimientos de mantenimiento"
    """
    text = _normalize_spaces(text)

    return re.sub(
        r"^(?:el|la|los|las|un|una|unos|unas)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()


def normalize_for_detection(text: str) -> str:
    text = _normalize_spaces(str(text or ""))
    text = text.lower()

    text = "".join(
        ch
        for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )

    return text


def is_synthesis_query(question: str) -> bool:
    normalized = normalize_for_detection(question)

    synthesis_markers = (
        "resume ",
        "resuma ",
        "resumir ",
        "sintetiza ",
        "sintetice ",
        "sintetizar ",
        "haz un resumen",
        "haga un resumen",
        "evidencia disponible sobre",
        "sintesis de",
        "sintesis sobre",
    )

    return any(
        marker in normalized
        for marker in synthesis_markers
    )


def extract_subject(question: str) -> str:
    """
    Extrae el tema principal de una consulta de síntesis sin codificar
    dominios concretos.

    Ejemplo:
    "Resume la evidencia disponible sobre el inventario de bodega."
    -> "inventario de bodega"
    """
    original = _normalize_spaces(
        str(question or "")
    )

    normalized = normalize_for_detection(
        original
    )

    candidates = [
        r"evidencia disponible sobre\s+(.+)$",
        r"resumen (?:de|sobre)\s+(.+)$",
        r"sintesis (?:de|sobre)\s+(.+)$",
        r"sintetiza\s+(.+)$",
        r"sintetice\s+(.+)$",
        r"resume\s+(.+)$",
        r"resuma\s+(.+)$",
    ]

    for pattern in candidates:
        match = re.search(
            pattern,
            normalized,
        )

        if match:
            subject = match.group(1)
            subject = _strip_terminal_punctuation(
                subject
            )
            subject = _strip_leading_article(
                subject
            )
            return _normalize_spaces(
                subject
            )

    fallback = _strip_terminal_punctuation(
        normalized
    )

    fallback = _strip_leading_article(
        fallback
    )

    return _normalize_spaces(
        fallback
    )


def rewrite_for_retrieval(question: str) -> str:
    """
    Reformulación genérica para recuperación.

    No cambia la intención final del usuario. Solo genera una consulta
    auxiliar orientada a localizar evidencia/documentos sobre el tema.

    Si no es una consulta de síntesis, devuelve la pregunta original.
    """
    question = _normalize_spaces(
        str(question or "")
    )

    if not is_synthesis_query(
        question
    ):
        return question

    subject = extract_subject(
        question
    )

    if not subject:
        return question

    return (
        f"información, documentos y evidencia "
        f"sobre {subject}"
    )
