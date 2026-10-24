
"""
rag_pipeline.py
---------------
Hotfix Fase 7.9.1

Asegura que RAGResponse incluya:
- response_mode
- structured_rows

y que la ruta estructurada propague structured_rows correctamente.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .multisource_retrieval import MultiSourceRetriever
from .ollama_llm import OllamaChatClient
from .prompt_builder import SYSTEM_PROMPT, build_user_prompt
from .structured_query import StructuredInventoryEngine


ABSTENTION_MESSAGE = (
    "No se encontró evidencia suficiente "
    "en las fuentes disponibles para "
    "responder esta consulta."
)


@dataclass
class RAGResponse:
    question: str
    answer: str
    abstained: bool
    sources: list
    retrieval_count: int
    abstention_stage: str | None = None
    response_mode: str = "rag"
    structured_rows: list[dict] = field(default_factory=list)


class RAGPipeline:
    def __init__(
        self,
        embedding_model: str = "qwen3-embedding:0.6b",
        llm_model: str = "qwen3.5:9b",
        dense_min_score: float = 0.45,
        bm25_min_score: float = 0.01,
        top_k: int = 5,
        temperature: float = 0.2,
    ):
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.dense_min_score = dense_min_score
        self.bm25_min_score = bm25_min_score
        self.top_k = top_k

        self.retriever = MultiSourceRetriever(
            dense_model=embedding_model,
            exact_match_boost=1.0,
            partial_identifier_boost=0.35,
        )

        self.llm = OllamaChatClient(
            model=llm_model,
            temperature=temperature,
        )

        self.structured_engine = None
        self._fitted = False

    def fit(self, records) -> "RAGPipeline":
        records = list(records)

        self.retriever.fit(records)
        self.structured_engine = StructuredInventoryEngine(records)

        self._fitted = True
        return self

    @staticmethod
    def _is_generation_abstention(answer: str) -> bool:
        normalized = (
            answer
            .strip()
            .lower()
            .replace("\n", " ")
        )

        patterns = [
            "no se encontró evidencia suficiente",
            "no hay evidencia suficiente",
            "la evidencia disponible no es suficiente",
            "no existe evidencia suficiente",
        ]

        return any(
            pattern in normalized
            for pattern in patterns
        )

    def ask(self, question: str) -> RAGResponse:
        if not self._fitted:
            raise RuntimeError(
                "Debe ejecutar fit() antes de ask()."
            )

        question = question.strip()

        if not question:
            raise ValueError(
                "La pregunta no puede estar vacía."
            )

        # ----------------------------------------------------------
        # Ruta estructurada
        # ----------------------------------------------------------
        structured = (
            self.structured_engine.execute(question)
            if self.structured_engine
            else None
        )

        if structured is not None:
            sources = (
                self.structured_engine
                .to_retrieval_results(
                    structured["records"]
                )
            )

            return RAGResponse(
                question=question,
                answer=structured["answer"],
                abstained=bool(
                    structured["abstained"]
                ),
                sources=sources,
                retrieval_count=len(sources),
                abstention_stage=(
                    "structured"
                    if structured["abstained"]
                    else None
                ),
                response_mode="structured",
                structured_rows=structured.get(
                    "structured_rows",
                    [],
                ),
            )

        # ----------------------------------------------------------
        # Ruta RAG
        # ----------------------------------------------------------
        results = self.retriever.search(
            query=question,
            top_k=self.top_k,
            dense_min_score=self.dense_min_score,
            bm25_min_score=self.bm25_min_score,
        )

        if not results:
            return RAGResponse(
                question=question,
                answer=ABSTENTION_MESSAGE,
                abstained=True,
                sources=[],
                retrieval_count=0,
                abstention_stage="retrieval",
                response_mode="rag",
                structured_rows=[],
            )

        prompt = build_user_prompt(
            question,
            results,
        )

        answer = self.llm.chat(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        generation_abstained = (
            self._is_generation_abstention(answer)
        )

        return RAGResponse(
            question=question,
            answer=answer,
            abstained=generation_abstained,
            sources=results,
            retrieval_count=len(results),
            abstention_stage=(
                "generation"
                if generation_abstained
                else None
            ),
            response_mode="rag",
            structured_rows=[],
        )
