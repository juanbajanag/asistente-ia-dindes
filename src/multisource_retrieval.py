"""
multisource_retrieval.py
------------------------
Fase 7.4 — Exact Match Global

Corrección del caso:
- La consulta contiene un identificador exacto (ej. 2341766).
- El chunk correcto existe en el corpus.
- Pero no entra en el candidate set semántico/BM25.
- Por tanto, el boost de Fase 7.3 nunca llega a aplicarse.

Solución:
1. Detectar identificadores en la consulta.
2. Buscar coincidencias exactas directamente en TODO el corpus.
3. Ejecutar retrieval semántico/BM25 normal.
4. Fusionar:
   - coincidencias exactas globales;
   - resultados semánticos/BM25;
5. Aplicar RRF + exact-match boost.
"""

from __future__ import annotations

import re
import unicodedata

from .hybrid_dense_retrieval import DenseBM25HybridRetriever
from .retrieval import QueryRouter, RetrievalResult


class MultiSourceRetriever:
    def __init__(
        self,
        dense_model: str = "qwen3-embedding:0.6b",
        rrf_k: int = 60,
        exact_match_boost: float = 1.0,
        partial_identifier_boost: float = 0.35,
    ):
        self.base = DenseBM25HybridRetriever(
            dense_model=dense_model
        )
        self.rrf_k = rrf_k
        self.exact_match_boost = exact_match_boost
        self.partial_identifier_boost = partial_identifier_boost
        self.records = []

    def fit(self, records):
        self.records = list(records)
        self.base.fit(self.records)
        return self

    # ============================================================
    # NORMALIZACIÓN
    # ============================================================
    @staticmethod
    def _normalize(text: str) -> str:
        text = unicodedata.normalize(
            "NFKD",
            str(text),
        )

        text = "".join(
            ch
            for ch in text
            if not unicodedata.combining(ch)
        )

        return text.lower()

    @staticmethod
    def _key(result: RetrievalResult) -> str:
        return str(result.record_id)

    # ============================================================
    # IDENTIFICADORES
    # ============================================================
    @classmethod
    def _extract_identifiers(
        cls,
        query: str,
    ) -> list[str]:

        query_norm = cls._normalize(
            query
        )

        candidates = []

        # Códigos con guiones.
        candidates.extend(
            re.findall(
                r"\b[a-z]{2,}(?:-[a-z0-9]+)+\b",
                query_norm,
                flags=re.IGNORECASE,
            )
        )

        # Números largos.
        candidates.extend(
            re.findall(
                r"\b\d{5,}\b",
                query_norm,
            )
        )

        # Tokens alfanuméricos mixtos.
        candidates.extend(
            re.findall(
                r"\b(?=[a-z0-9]*[a-z])(?=[a-z0-9]*\d)[a-z0-9]{4,}\b",
                query_norm,
                flags=re.IGNORECASE,
            )
        )

        # Modelos con espacio.
        candidates.extend(
            re.findall(
                r"\b[a-z]{2,}\s+\d{3,5}\b",
                query_norm,
                flags=re.IGNORECASE,
            )
        )

        seen = set()
        result = []

        for item in candidates:
            item = item.strip()

            if not item:
                continue

            if item in seen:
                continue

            seen.add(item)
            result.append(item)

        return result

    @classmethod
    def _record_searchable_text(
        cls,
        record,
    ) -> str:

        metadata = getattr(
            record,
            "metadata",
            {},
        ) or {}

        metadata_values = " ".join(
            str(value)
            for value in metadata.values()
            if value not in (None, "")
        )

        return cls._normalize(
            " ".join(
                [
                    str(
                        getattr(
                            record,
                            "record_id",
                            "",
                        )
                    ),
                    str(
                        getattr(
                            record,
                            "title",
                            "",
                        )
                    ),
                    str(
                        getattr(
                            record,
                            "text",
                            "",
                        )
                    ),
                    str(
                        getattr(
                            record,
                            "source_file",
                            "",
                        )
                    ),
                    metadata_values,
                ]
            )
        )

    @classmethod
    def _result_searchable_text(
        cls,
        result: RetrievalResult,
    ) -> str:

        metadata_values = " ".join(
            str(value)
            for value in result.metadata.values()
            if value not in (None, "")
        )

        return cls._normalize(
            " ".join(
                [
                    str(result.record_id),
                    str(result.title),
                    str(result.text),
                    str(result.source_file),
                    metadata_values,
                ]
            )
        )

    # ============================================================
    # COINCIDENCIA GLOBAL
    # ============================================================
    def _global_exact_matches(
        self,
        identifiers: list[str],
        *,
        source_type: str | None = None,
        access_level: str | None = "autorizado",
        source_status: str | None = None,
    ) -> list[RetrievalResult]:
        """
        Busca identificadores exactos directamente en TODOS los registros.

        Esto ocurre ANTES del retrieval semántico, por lo que una coincidencia
        literal no puede quedar excluida por el candidate_k.
        """

        if not identifiers:
            return []

        found = []

        for record in self.records:

            record_source_type = getattr(
                record,
                "source_type",
                None,
            )

            metadata = getattr(
                record,
                "metadata",
                {},
            ) or {}

            # Si hay filtro explícito de tipo, respetarlo.
            if (
                source_type is not None
                and record_source_type != source_type
            ):
                continue

            # Nivel de acceso.
            if access_level is not None:
                rec_access = str(
                    metadata.get(
                        "access_level",
                        "",
                    )
                ).lower()

                # Inventarios sample pueden no tener access_level.
                if (
                    rec_access
                    and rec_access != access_level.lower()
                ):
                    continue

            # Estado documental solo para documentos.
            if (
                source_status is not None
                and record_source_type == "document"
            ):
                rec_status = str(
                    metadata.get(
                        "source_status",
                        "",
                    )
                ).lower()

                if (
                    rec_status
                    and rec_status != source_status.lower()
                ):
                    continue

            searchable = self._record_searchable_text(
                record
            )

            matched = []

            for identifier in identifiers:
                ident = self._normalize(
                    identifier
                )

                if ident in searchable:
                    matched.append(identifier)

            if not matched:
                continue

            metadata_copy = dict(metadata)

            metadata_copy[
                "exact_match_identifiers"
            ] = matched

            metadata_copy[
                "exact_match_boost_applied"
            ] = True

            found.append(
                RetrievalResult(
                    rank=0,
                    score=0.0,
                    record_id=getattr(
                        record,
                        "record_id",
                        "",
                    ),
                    source_type=record_source_type,
                    title=getattr(
                        record,
                        "title",
                        "",
                    ),
                    text=getattr(
                        record,
                        "text",
                        "",
                    ),
                    source_file=getattr(
                        record,
                        "source_file",
                        "",
                    ),
                    metadata=metadata_copy,
                )
            )

        # Ranking interno estable: más identificadores exactos primero.
        found.sort(
            key=lambda r: len(
                r.metadata.get(
                    "exact_match_identifiers",
                    [],
                )
            ),
            reverse=True,
        )

        for rank, result in enumerate(
            found,
            start=1,
        ):
            result.rank = rank

        return found

    # ============================================================
    # BOOST
    # ============================================================
    @classmethod
    def _identifier_match_score(
        cls,
        result: RetrievalResult,
        identifiers: list[str],
        exact_match_boost: float,
        partial_identifier_boost: float,
    ) -> tuple[float, list[str]]:

        if not identifiers:
            return 0.0, []

        searchable = cls._result_searchable_text(
            result
        )

        boost = 0.0
        matches = []

        for identifier in identifiers:
            ident = cls._normalize(
                identifier
            )

            if ident in searchable:
                boost += exact_match_boost
                matches.append(identifier)
                continue

            compact_ident = re.sub(
                r"[\s\-_]+",
                "",
                ident,
            )

            compact_searchable = re.sub(
                r"[\s\-_]+",
                "",
                searchable,
            )

            if (
                len(compact_ident) >= 4
                and compact_ident in compact_searchable
            ):
                boost += partial_identifier_boost
                matches.append(identifier)

        return boost, matches

    # ============================================================
    # FUSIÓN
    # ============================================================
    def _merge_rankings(
        self,
        rankings: list[list[RetrievalResult]],
        top_k: int,
        query: str,
    ) -> list[RetrievalResult]:

        combined = {}

        for ranking in rankings:
            for result in ranking:

                key = self._key(
                    result
                )

                if key not in combined:
                    combined[key] = {
                        "result": result,
                        "rrf": 0.0,
                    }

                effective_rank = max(
                    int(result.rank),
                    1,
                )

                combined[key]["rrf"] += (
                    1.0
                    / (
                        self.rrf_k
                        + effective_rank
                    )
                )

        identifiers = (
            self._extract_identifiers(
                query
            )
        )

        rescored = []

        for item in combined.values():

            result = item["result"]

            boost, matches = (
                self._identifier_match_score(
                    result=result,
                    identifiers=identifiers,
                    exact_match_boost=(
                        self.exact_match_boost
                    ),
                    partial_identifier_boost=(
                        self.partial_identifier_boost
                    ),
                )
            )

            final_score = (
                float(item["rrf"])
                + boost
            )

            metadata = dict(
                result.metadata
            )

            metadata[
                "exact_match_identifiers"
            ] = matches

            metadata[
                "exact_match_boost_applied"
            ] = bool(matches)

            rescored.append(
                {
                    "result": result,
                    "metadata": metadata,
                    "score": final_score,
                }
            )

        ranked = sorted(
            rescored,
            key=lambda item: item[
                "score"
            ],
            reverse=True,
        )

        final = []

        for rank, item in enumerate(
            ranked[:top_k],
            start=1,
        ):

            base = item["result"]

            final.append(
                RetrievalResult(
                    rank=rank,
                    score=float(
                        item["score"]
                    ),
                    record_id=base.record_id,
                    source_type=base.source_type,
                    title=base.title,
                    text=base.text,
                    source_file=base.source_file,
                    metadata=item["metadata"],
                )
            )

        return final

    # ============================================================
    # SEARCH
    # ============================================================
    def search(
        self,
        query: str,
        top_k: int = 5,
        access_level: str | None = "autorizado",
        dense_min_score: float = 0.45,
        bm25_min_score: float = 0.01,
    ) -> list[RetrievalResult]:

        query = query.strip()

        if not query:
            raise ValueError(
                "La consulta no puede estar vacía."
            )

        route = QueryRouter.infer(
            query
        )

        source_type = route.get(
            "source_type"
        )

        source_status = route.get(
            "source_status"
        )

        inventory_status = route.get(
            "inventory_status"
        )

        category_contains = route.get(
            "category_contains"
        )

        identifiers = (
            self._extract_identifiers(
                query
            )
        )

        candidate_k = max(
            top_k * 5,
            25,
        )

        # --------------------------------------------------------
        # INVENTARIO: inventory + document + exact global
        # --------------------------------------------------------
        if source_type == "inventory":

            exact_global = (
                self._global_exact_matches(
                    identifiers,
                    source_type=None,
                    access_level=access_level,
                    source_status=source_status,
                )
            )

            inventory_results = (
                self.base.search(
                    query=query,
                    top_k=candidate_k,
                    source_type="inventory",
                    access_level=access_level,
                    source_status=None,
                    inventory_status=inventory_status,
                    category_contains=category_contains,
                    dense_min_score=dense_min_score,
                    bm25_min_score=bm25_min_score,
                    auto_route=False,
                )
            )

            document_results = (
                self.base.search(
                    query=query,
                    top_k=candidate_k,
                    source_type="document",
                    access_level=access_level,
                    source_status=source_status,
                    inventory_status=None,
                    category_contains=None,
                    dense_min_score=dense_min_score,
                    bm25_min_score=bm25_min_score,
                    auto_route=False,
                )
            )

            return self._merge_rankings(
                [
                    exact_global,
                    inventory_results,
                    document_results,
                ],
                top_k=top_k,
                query=query,
            )

        # --------------------------------------------------------
        # DOCUMENTO: documents + exact global documental
        # --------------------------------------------------------
        if source_type == "document":

            exact_global = (
                self._global_exact_matches(
                    identifiers,
                    source_type="document",
                    access_level=access_level,
                    source_status=source_status,
                )
            )

            document_results = (
                self.base.search(
                    query=query,
                    top_k=candidate_k,
                    source_type="document",
                    access_level=access_level,
                    source_status=source_status,
                    inventory_status=None,
                    category_contains=None,
                    dense_min_score=dense_min_score,
                    bm25_min_score=bm25_min_score,
                    auto_route=False,
                )
            )

            return self._merge_rankings(
                [
                    exact_global,
                    document_results,
                ],
                top_k=top_k,
                query=query,
            )

        # --------------------------------------------------------
        # ABIERTA: todo + exact global
        # --------------------------------------------------------
        exact_global = (
            self._global_exact_matches(
                identifiers,
                source_type=None,
                access_level=access_level,
                source_status=source_status,
            )
        )

        all_results = (
            self.base.search(
                query=query,
                top_k=candidate_k,
                source_type=None,
                access_level=access_level,
                source_status=source_status,
                inventory_status=inventory_status,
                category_contains=category_contains,
                dense_min_score=dense_min_score,
                bm25_min_score=bm25_min_score,
                auto_route=False,
            )
        )

        return self._merge_rankings(
            [
                exact_global,
                all_results,
            ],
            top_k=top_k,
            query=query,
        )

    def explain_route(
        self,
        query: str,
    ) -> dict:

        route = QueryRouter.infer(
            query
        )

        identifiers = (
            self._extract_identifiers(
                query
            )
        )

        route[
            "multisource_inventory"
        ] = (
            route.get("source_type")
            == "inventory"
        )

        route[
            "detected_identifiers"
        ] = identifiers

        route[
            "global_exact_match_count"
        ] = len(
            self._global_exact_matches(
                identifiers,
                source_type=(
                    "document"
                    if route.get(
                        "source_type"
                    ) == "document"
                    else None
                ),
                source_status=route.get(
                    "source_status"
                ),
            )
        )

        return route
