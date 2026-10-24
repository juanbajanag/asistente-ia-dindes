from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re

from .structured_query import StructuredInventoryEngine


TOKEN_RE = re.compile(
    r"\b[\wÁÉÍÓÚÜÑáéíóúüñ-]+\b",
    re.UNICODE,
)

STOPWORDS = {
    "de", "del", "la", "las", "el", "los", "un", "una", "unos", "unas",
    "y", "o", "en", "a", "al", "por", "para", "con", "sin", "sobre",
    "que", "qué", "cual", "cuál", "cuales", "cuáles", "como", "cómo",
    "es", "son", "se", "su", "sus", "este", "esta", "estos", "estas",
    "principal", "principales", "disponible", "disponibles", "informacion",
    "información", "evidencia", "numero", "número"
}

GENERIC_TOKENS = {
    "bien", "bienes", "serie", "sistema", "equipo", "equipos",
    "documento", "documentos", "registro", "registros",
    "fuente", "fuentes", "datos", "dato",
}


@dataclass
class CloudSource:
    source_type: str
    record_id: str
    title: str = ""
    score: float = 0.0
    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CloudResponse:
    answer: str
    question: str
    sources: list[CloudSource]
    abstained: bool
    abstention_stage: str | None
    retrieval_count: int
    response_mode: str = "rag"
    structured_rows: list[dict[str, Any]] = field(default_factory=list)

    @property
    def mode(self) -> str:
        return self.response_mode


def normalize_text(value: Any) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(value or "").strip().lower(),
    )


def tokenize(value: Any) -> set[str]:
    tokens = set()

    for raw in TOKEN_RE.findall(normalize_text(value)):
        if raw in STOPWORDS:
            continue

        # Conservar códigos cortos con dígitos: K1, 3D, etc.
        if len(raw) < 3 and not any(ch.isdigit() for ch in raw):
            continue

        token = raw

        # Normalización plural mínima.
        if len(token) > 4 and token.endswith("s"):
            token = token[:-1]

        tokens.add(token)

    return tokens


def informative_tokens(value: Any) -> set[str]:
    return {
        token
        for token in tokenize(value)
        if token not in GENERIC_TOKENS
    }


def get_record_text(record: Any) -> str:
    if isinstance(record, dict):
        for key in (
            "text",
            "content",
            "description",
            "descripcion",
            "chunk_text",
        ):
            value = record.get(key)
            if value:
                return str(value)

        return " ".join(
            str(v)
            for v in record.values()
            if isinstance(v, (str, int, float))
        )

    for attr in (
        "text",
        "content",
        "description",
        "descripcion",
        "chunk_text",
    ):
        value = getattr(record, attr, None)
        if value:
            return str(value)

    return str(record)


def get_record_id(record: Any, index: int) -> str:
    keys = (
        "record_id",
        "document_id",
        "id",
        "item",
        "item_id",
        "chunk_id",
    )

    if isinstance(record, dict):
        for key in keys:
            value = record.get(key)
            if value not in (None, ""):
                return str(value)
    else:
        for attr in keys:
            value = getattr(record, attr, None)
            if value not in (None, ""):
                return str(value)

    return f"CLOUD-{index:04d}"


def get_record_title(record: Any) -> str:
    keys = (
        "title",
        "titulo",
        "document_title",
        "description",
        "descripcion",
    )

    if isinstance(record, dict):
        for key in keys:
            value = record.get(key)
            if value:
                return str(value)
    else:
        for attr in keys:
            value = getattr(record, attr, None)
            if value:
                return str(value)

    return ""


def get_record_metadata(record: Any) -> dict[str, Any]:
    if isinstance(record, dict):
        metadata = record.get("metadata")

        if isinstance(metadata, dict):
            return dict(metadata)

        return {
            str(k): v
            for k, v in record.items()
            if k not in {"text", "content"}
        }

    metadata = getattr(record, "metadata", None)

    return (
        dict(metadata)
        if isinstance(metadata, dict)
        else {}
    )


def evidence_metrics(
    question: str,
    title: str,
    text: str,
) -> dict[str, float | int]:
    q_tokens = informative_tokens(question)
    title_tokens = informative_tokens(title)
    text_tokens = informative_tokens(text)
    combined_tokens = title_tokens | text_tokens

    title_overlap = q_tokens & title_tokens
    text_overlap = q_tokens & text_tokens
    combined_overlap = q_tokens & combined_tokens

    coverage = (
        len(combined_overlap) / len(q_tokens)
        if q_tokens
        else 0.0
    )

    title_coverage = (
        len(title_overlap) / len(q_tokens)
        if q_tokens
        else 0.0
    )

    score = (
        (0.55 * coverage)
        + (0.35 * title_coverage)
        + (0.10 * min(len(combined_overlap), 4) / 4.0)
    )

    return {
        "score": float(score),
        "coverage": float(coverage),
        "title_coverage": float(title_coverage),
        "overlap_count": int(len(combined_overlap)),
        "title_overlap_count": int(len(title_overlap)),
        "text_overlap_count": int(len(text_overlap)),
        "query_token_count": int(len(q_tokens)),
    }


def sentence_split(text: str) -> list[str]:
    parts = re.split(
        r"(?<=[.!?])\s+|\n+",
        str(text or "").strip(),
    )

    return [
        part.strip(" \t-*•")
        for part in parts
        if part.strip(" \t-*•")
    ]


class CloudRAGPipeline:
    """
    Backend cloud ligero con política de evidencia balanceada.

    - título del documento actúa como ancla temática;
    - el contenido aporta evidencia específica;
    - coincidencias genéricas aisladas no bastan;
    - ante duda, se abstiene.
    """

    MIN_COMBINED_OVERLAP = 2
    MIN_COMBINED_COVERAGE = 0.30
    MIN_TITLE_ANCHOR_OVERLAP = 2
    MIN_SENTENCE_OVERLAP = 1

    def __init__(
        self,
        *,
        dense_min_score: float = 0.45,
        top_k: int = 5,
        temperature: float = 0.0,
        **_: Any,
    ):
        self.dense_min_score = float(dense_min_score)
        self.top_k = int(top_k)
        self.temperature = float(temperature)
        self.records: list[Any] = []
        self.structured_engine: StructuredInventoryEngine | None = None

    def fit(
        self,
        records: list[Any],
    ) -> "CloudRAGPipeline":
        self.records = list(records or [])
        self.structured_engine = StructuredInventoryEngine(self.records)
        return self

    def _record_is_supported(
        self,
        metrics: dict[str, float | int],
    ) -> bool:
        general_support = (
            metrics["overlap_count"] >= self.MIN_COMBINED_OVERLAP
            and metrics["coverage"] >= self.MIN_COMBINED_COVERAGE
        )

        title_anchor = (
            metrics["title_overlap_count"] >= self.MIN_TITLE_ANCHOR_OVERLAP
        )

        return bool(general_support or title_anchor)

    def _retrieve(
        self,
        question: str,
    ) -> list[CloudSource]:
        scored = []

        for idx, record in enumerate(
            self.records,
            start=1,
        ):
            text = get_record_text(record)
            title = get_record_title(record)

            metrics = evidence_metrics(
                question,
                title,
                text,
            )

            if not self._record_is_supported(metrics):
                continue

            source_type = (
                record.get(
                    "source_type",
                    "document",
                )
                if isinstance(record, dict)
                else getattr(
                    record,
                    "source_type",
                    "document",
                )
            )

            metadata = get_record_metadata(record)
            metadata = dict(metadata)
            metadata["_cloud_metrics"] = metrics

            scored.append(
                CloudSource(
                    source_type=str(source_type),
                    record_id=get_record_id(record, idx),
                    title=title,
                    score=float(metrics["score"]),
                    text=text,
                    metadata=metadata,
                )
            )

        scored.sort(
            key=lambda x: x.score,
            reverse=True,
        )

        return scored[: self.top_k]

    def _select_evidence_sentences(
        self,
        question: str,
        sources: list[CloudSource],
        max_sentences: int = 4,
    ) -> list[tuple[int, str]]:
        q_tokens = informative_tokens(question)
        candidates = []

        for source_idx, source in enumerate(
            sources,
            start=1,
        ):
            title_tokens = informative_tokens(source.title)
            title_overlap = len(q_tokens & title_tokens)

            for sentence in sentence_split(source.text):
                s_tokens = informative_tokens(sentence)
                sentence_overlap = len(q_tokens & s_tokens)

                # Un documento con título fuertemente anclado puede aportar
                # una oración con una sola coincidencia informativa.
                min_required = (
                    1
                    if title_overlap >= self.MIN_TITLE_ANCHOR_OVERLAP
                    else self.MIN_SENTENCE_OVERLAP + 1
                )

                if sentence_overlap < min_required:
                    continue

                coverage = (
                    sentence_overlap / max(len(q_tokens), 1)
                )

                candidates.append(
                    (
                        title_overlap,
                        coverage,
                        sentence_overlap,
                        source_idx,
                        sentence,
                    )
                )

        candidates.sort(
            key=lambda x: (
                x[0],
                x[1],
                x[2],
            ),
            reverse=True,
        )

        selected = []
        seen = set()

        for (
            _,
            _,
            _,
            source_idx,
            sentence,
        ) in candidates:
            key = normalize_text(sentence)

            if key in seen:
                continue

            seen.add(key)
            selected.append(
                (source_idx, sentence)
            )

            if len(selected) >= max_sentences:
                break

        return selected

    def ask(
        self,
        question: str,
    ) -> CloudResponse:
        question = str(question or "").strip()

        if not question:
            raise ValueError("La pregunta no puede estar vacía.")

        # Ruta estructurada cloud
        structured = (
            self.structured_engine.execute(question)
            if self.structured_engine is not None
            else None
        )

        if structured is not None:
            query = structured.get("query")
            records = list(structured.get("records", []))

            has_entity_filter = bool(
                getattr(query, "brand", None)
                or getattr(query, "model", None)
                or getattr(query, "description_contains", None)
            )

            # Si se pidió una entidad concreta y no existe en las
            # filas estructuradas, permitir fallback a RAG.
            fallback_to_rag = has_entity_filter and not records

            if not fallback_to_rag:
                sources = self.structured_engine.to_retrieval_results(records)

                return CloudResponse(
                    question=question,
                    answer=str(structured.get("answer", "")),
                    sources=sources,
                    abstained=bool(structured.get("abstained", False)),
                    abstention_stage=(
                        "structured"
                        if structured.get("abstained", False)
                        else None
                    ),
                    retrieval_count=len(sources),
                    response_mode="structured",
                    structured_rows=list(
                        structured.get("structured_rows", [])
                    ),
                )

        # Ruta RAG cloud
        sources = self._retrieve(question)

        if not sources:
            return CloudResponse(
                                question=question,
answer=(
                    "No se encontró evidencia suficiente en las "
                    "fuentes disponibles para responder esta consulta."
                ),
                sources=[],
                abstained=True,
                abstention_stage="retrieval",
                retrieval_count=0,
            )

        selected = self._select_evidence_sentences(
            question,
            sources,
        )

        if not selected:
            return CloudResponse(
                                question=question,
answer=(
                    "No se encontró evidencia suficiente en las "
                    "fuentes disponibles para responder esta consulta."
                ),
                sources=sources,
                abstained=True,
                abstention_stage="retrieval",
                retrieval_count=len(sources),
            )

        lines = [
            (
                "Según la evidencia disponible, se encontraron "
                "los siguientes elementos relevantes:"
            ),
            "",
        ]

        for source_idx, sentence in selected:
            lines.append(
                f"- {sentence} [F{source_idx}]"
            )

        return CloudResponse(
                        question=question,
answer="\n".join(lines).strip(),
            sources=sources,
            abstained=False,
            abstention_stage=None,
            retrieval_count=len(sources),
        )
