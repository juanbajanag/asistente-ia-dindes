from __future__ import annotations

from typing import Any

from src.query_normalizer import (
    is_synthesis_query,
    rewrite_for_retrieval,
)
from src.rag_pipeline import RAGPipeline as BaseRAGPipeline


class RAGPipeline(BaseRAGPipeline):
    """
    Hotfix Fase 11.5.1

    Usa la reformulación validada experimentalmente en Fase 11.4
    para consultas de síntesis.

    Motivo del cambio:
    la versión 11.5 intentó interceptar métodos internos de recuperación,
    pero el pipeline base no expone de forma fiable una API pública separada
    retrieve()/generate(). La prueba funcional mostró que el interceptor
    estaba capturando métodos del propio adaptador y no alteraba la
    recuperación real.

    Esta versión adopta el comportamiento que ya fue validado:
    - consulta de síntesis -> super().ask(consulta reformulada)
    - consulta normal -> super().ask(consulta original)

    Se preserva trazabilidad mediante:
    - last_original_question
    - last_effective_question
    - last_synthesis_rewrite_applied

    No cambia:
    - Top-K
    - umbral
    - temperatura
    - política de abstención
    - modelos
    """

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.last_original_question: str | None = None
        self.last_effective_question: str | None = None
        self.last_retrieval_question: str | None = None
        self.last_synthesis_rewrite_applied: bool = False

    def ask(self, question: str):
        original_question = str(
            question or ""
        ).strip()

        self.last_original_question = original_question
        self.last_effective_question = original_question
        self.last_retrieval_question = original_question
        self.last_synthesis_rewrite_applied = False

        if not is_synthesis_query(
            original_question
        ):
            return super().ask(
                original_question
            )

        rewritten_question = rewrite_for_retrieval(
            original_question
        )

        if (
            not rewritten_question
            or rewritten_question
            == original_question
        ):
            return super().ask(
                original_question
            )

        self.last_synthesis_rewrite_applied = True
        self.last_effective_question = rewritten_question
        self.last_retrieval_question = rewritten_question

        return super().ask(
            rewritten_question
        )
