from __future__ import annotations

from typing import Any
from src.runtime_config import is_cloud_runtime


def build_runtime_pipeline(
    *,
    embedding_model: str,
    llm_model: str,
    dense_min_score: float,
    top_k: int,
    temperature: float,
) -> Any:
    if is_cloud_runtime():
        from src.cloud_backend import CloudRAGPipeline

        return CloudRAGPipeline(
            dense_min_score=dense_min_score,
            top_k=top_k,
            temperature=temperature,
        )

    from src.rag_pipeline import RAGPipeline

    return RAGPipeline(
        embedding_model=embedding_model,
        llm_model=llm_model,
        dense_min_score=dense_min_score,
        top_k=top_k,
        temperature=temperature,
    )
