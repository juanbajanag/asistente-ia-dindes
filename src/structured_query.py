
"""
structured_query.py
-------------------
Fase 8 — Analítica de inventario y consultas avanzadas.

Amplía la ruta estructurada con:
- conteos con filtros
- stock total y cantidad total
- comparación cantidad vs stock
- herramientas que requieren reposición
- rankings por menor/mayor stock
- filtros por marca
- lookup puntual por modelo

La ruta documental RAG permanece separada.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass

from .retrieval import RetrievalResult


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def as_number(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    text = text.replace(",", "")

    try:
        return float(text)
    except Exception:
        return None


def pretty_number(value) -> str:
    number = as_number(value)

    if number is None:
        return str(value or "")

    if number.is_integer():
        return str(int(number))

    return f"{number:.2f}".rstrip("0").rstrip(".")


def _canonical_from_text(text: str, field: str) -> str:
    text = str(text or "")

    patterns = {
        "item": (
            r"(?:^|\.\s+)ITEM:\s*(.*?)"
            r"(?=\.\s+DESCRIPCION:|$)"
        ),
        "description": (
            r"(?:^|\.\s+)DESCRIPCION:\s*(.*?)"
            r"(?=\.\s+MARCA:|\.\s+MODELO:|\.\s+CANTIDAD:|\.\s+STOCK:|$)"
        ),
        "brand": (
            r"(?:^|\.\s+)MARCA:\s*(.*?)"
            r"(?=\.\s+MODELO:|\.\s+CANTIDAD:|\.\s+STOCK:|$)"
        ),
        "model": (
            r"(?:^|\.\s+)MODELO:\s*(.*?)"
            r"(?=\.\s+CANTIDAD:|\.\s+STOCK:|$)"
        ),
        "quantity": (
            r"(?:^|\.\s+)CANTIDAD:\s*(.*?)"
            r"(?=\.\s+STOCK:|$)"
        ),
        "stock": (
            r"(?:^|\.\s+)STOCK:\s*(.*?)"
            r"(?=\.|$)"
        ),
    }

    pattern = patterns.get(field)

    if not pattern:
        return ""

    matches = re.findall(pattern, text, flags=re.DOTALL)

    if not matches:
        return ""

    return str(matches[-1]).strip().rstrip(".")


def _clean_brand(value: str) -> str:
    value = str(value or "").strip()
    value = re.split(
        r",?\s*Modelo\s*:",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return value.strip(" ,;.-")


def _clean_model(value: str) -> str:
    value = str(value or "").strip()
    value = re.sub(
        r"^\s*Modelo\s*:\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.split(
        r"\s+(?:Marca|Cantidad|Stock)\s*:",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return value.strip(" ,;.-")


def _clean_description(value: str) -> str:
    value = str(value or "").strip()
    value = re.split(
        r"\s+Marca\s*:",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return value.strip(" ,;.-")


@dataclass
class StructuredQuery:
    matched: bool
    field: str | None = None
    operator: str | None = None
    value: float | None = None
    aggregate: str | None = None
    brand: str | None = None
    model: str | None = None
    description_contains: str | None = None
    reason: str = ""
    comparison: str | None = None
    ranking: str | None = None
    limit: int | None = None


class StructuredQueryRouter:
    KNOWN_BRANDS = [
        "stanley",
        "dewalt",
        "bosch",
        "makita",
        "milwaukee",
        "truper",
        "ingco",
        "bellota",
        "dormer",
        "best value",
        "creality",
    ]

    @classmethod
    def _extract_brand(cls, q: str) -> str | None:
        match = re.search(
            r"\bmarca\s+([a-z0-9&._ -]+?)(?=\s+(?:tienen|con|dispon|stock|cantidad|$))",
            q,
        )

        if match:
            return match.group(1).strip().upper()

        for token in cls.KNOWN_BRANDS:
            if re.search(rf"\b{re.escape(token)}\b", q):
                return token.upper()

        return None

    @classmethod
    def _extract_model(cls, q: str) -> str | None:
        # Forma explícita: modelo DWD024-B3
        match = re.search(
            r"\bmodelo\s+([a-z0-9./_-]+)",
            q,
        )

        if match:
            return match.group(1).upper()

        # Forma natural: Creality K1, DEWALT DWD024-B3, etc.
        # Solo se usa después de una marca conocida.
        for brand in cls.KNOWN_BRANDS:
            brand_pattern = re.escape(brand)

            match = re.search(
                rf"\b{brand_pattern}\b\s+([a-z0-9./_-]+)",
                q,
            )

            if not match:
                continue

            candidate = match.group(1).strip()
            blocked = {
                "con", "sin", "stock", "cantidad",
                "disponible", "disponibles",
                "operativo", "operativos", "modelo",
            }

            if candidate and candidate not in blocked:
                return candidate.upper()

        return None

    @classmethod
    def infer(cls, question: str) -> StructuredQuery:
        q = normalize(question)

        inventory_terms = (
            "stock",
            "cantidad",
            "disponib",
            "existencia",
            "reposicion",
            "reponer",
            "inventario",
            "herramienta",
            "articulo",
            "item",
        )

        if not any(term in q for term in inventory_terms):
            return StructuredQuery(
                matched=False,
                reason="No contiene una intención estructurada de inventario.",
            )

        brand = cls._extract_brand(q)
        model = cls._extract_model(q)

        # -------------------------------------------------------------
        # Lookup puntual prioritario
        # -------------------------------------------------------------
        if model is not None and any(
            phrase in q
            for phrase in (
                "cual es",
                "cuanto",
                "cuanta",
                "cuantos",
                "cuantas",
            )
        ):
            requested_field = (
                "quantity"
                if "cantidad" in q and "stock" not in q
                else "stock"
            )

            return StructuredQuery(
                matched=True,
                field=requested_field,
                operator="lookup",
                brand=brand,
                model=model,
                reason="Lookup puntual prioritario por modelo.",
            )

        # -------------------------------------------------------------
        # Comparaciones entre cantidad y stock
        # -------------------------------------------------------------
        if any(
            phrase in q
            for phrase in (
                "cantidad mayor que stock",
                "cantidad mayor al stock",
                "cantidad es mayor que el stock",
                "cantidad superior al stock",
            )
        ):
            return StructuredQuery(
                matched=True,
                comparison="quantity_gt_stock",
                brand=brand,
                reason="Comparación estructurada cantidad > stock.",
            )

        if any(
            phrase in q
            for phrase in (
                "stock igual a cantidad",
                "stock igual que cantidad",
                "stock coincide con cantidad",
            )
        ):
            return StructuredQuery(
                matched=True,
                comparison="stock_eq_quantity",
                brand=brand,
                reason="Comparación estructurada stock == cantidad.",
            )

        # -------------------------------------------------------------
        # Reposición
        # Regla MVP: stock <= 1
        # -------------------------------------------------------------
        if any(
            term in q
            for term in (
                "requieren reposicion",
                "requiere reposicion",
                "para reposicion",
                "deben reponerse",
                "deben reponer",
                "reponer",
            )
        ):
            return StructuredQuery(
                matched=True,
                field="stock",
                operator="<=",
                value=1.0,
                brand=brand,
                reason="Regla de reposición MVP: stock <= 1.",
            )

        # -------------------------------------------------------------
        # Rankings
        # -------------------------------------------------------------
        ranking_match = re.search(
            r"\b(?:las|los)?\s*(\d+)\s+"
            r"(?:herramientas|articulos|items|productos)?\s*"
            r"(?:con\s+)?"
            r"(menor|mayor)\s+stock",
            q,
        )

        if ranking_match:
            limit = int(ranking_match.group(1))
            direction = ranking_match.group(2)

            return StructuredQuery(
                matched=True,
                field="stock",
                ranking=(
                    "asc"
                    if direction == "menor"
                    else "desc"
                ),
                limit=max(1, min(limit, 100)),
                brand=brand,
                reason="Ranking estructurado por stock.",
            )

        if "menor stock" in q:
            return StructuredQuery(
                matched=True,
                field="stock",
                ranking="asc",
                limit=10,
                brand=brand,
                reason="Ranking estructurado por menor stock.",
            )

        if "mayor stock" in q:
            return StructuredQuery(
                matched=True,
                field="stock",
                ranking="desc",
                limit=10,
                brand=brand,
                reason="Ranking estructurado por mayor stock.",
            )

        # -------------------------------------------------------------
        # Agregaciones
        # -------------------------------------------------------------
        if any(
            phrase in q
            for phrase in (
                "stock total por marca",
                "stock por marca",
                "total de stock por marca",
            )
        ):
            return StructuredQuery(
                matched=True,
                field="stock",
                aggregate="group_sum_brand",
                reason="Agregación de stock por marca.",
            )

        if any(
            phrase in q
            for phrase in (
                "cantidad total por marca",
                "cantidad por marca",
                "total de cantidad por marca",
            )
        ):
            return StructuredQuery(
                matched=True,
                field="quantity",
                aggregate="group_sum_brand",
                reason="Agregación de cantidad por marca.",
            )

        if any(
            phrase in q
            for phrase in (
                "stock total",
                "total de stock",
                "suma del stock",
                "sumatoria de stock",
            )
        ):
            return StructuredQuery(
                matched=True,
                field="stock",
                aggregate="sum",
                brand=brand,
                reason="Suma estructurada de stock.",
            )

        if any(
            phrase in q
            for phrase in (
                "cantidad total",
                "total de cantidad",
                "suma de cantidad",
            )
        ):
            return StructuredQuery(
                matched=True,
                field="quantity",
                aggregate="sum",
                brand=brand,
                reason="Suma estructurada de cantidad.",
            )

        # -------------------------------------------------------------
        # Campo principal
        # -------------------------------------------------------------
        if (
            "stock" in q
            or "disponib" in q
            or "existencia" in q
        ):
            field = "stock"
        elif "cantidad" in q:
            field = "quantity"
        else:
            field = "stock"

        aggregate = None

        if re.search(r"\bcuantas?\b|\bcuantos?\b", q):
            if any(
                marker in q
                for marker in (
                    "tienen stock",
                    "con stock",
                    "herramientas",
                    "articulos",
                    "items",
                    "disponibles",
                    "disponibilidad",
                )
            ):
                aggregate = "count"

        operator = None
        value = None

        if any(
            phrase in q
            for phrase in (
                "stock cero",
                "stock 0",
                "sin stock",
                "agotad",
                "no tienen disponibilidad",
                "sin disponibilidad",
            )
        ):
            operator = "=="
            value = 0.0

        elif any(
            phrase in q
            for phrase in (
                "disponibles",
                "disponibilidad",
                "con stock",
                "stock disponible",
                "stock mayor a cero",
                "stock mayor que cero",
            )
        ):
            operator = ">"
            value = 0.0

        else:
            patterns = [
                (
                    r"(?:stock|cantidad)\s+"
                    r"(?:menor(?:\s+o\s+igual)?\s+(?:a|que)|<=?)\s*"
                    r"(\d+(?:[.,]\d+)?)",
                    "<",
                ),
                (
                    r"(?:stock|cantidad)\s+"
                    r"(?:mayor(?:\s+o\s+igual)?\s+(?:a|que)|>=?)\s*"
                    r"(\d+(?:[.,]\d+)?)",
                    ">",
                ),
                (
                    r"(?:stock|cantidad)\s+"
                    r"(?:igual\s+(?:a|que)|=)\s*"
                    r"(\d+(?:[.,]\d+)?)",
                    "==",
                ),
            ]

            for pattern, op in patterns:
                match = re.search(pattern, q)
                if match:
                    operator = op
                    value = float(match.group(1).replace(",", "."))
                    break

        if operator is None and (brand is not None or model is not None):
            operator = "lookup"

        if (
            operator is None
            and any(
                phrase in q
                for phrase in (
                    "cual es el stock",
                    "cuanto stock",
                    "cuantas unidades",
                    "cuantos hay en stock",
                    "cuantas hay en stock",
                )
            )
        ):
            operator = "lookup"

        if operator is None and aggregate is None:
            return StructuredQuery(
                matched=False,
                reason=(
                    "La pregunta menciona inventario, "
                    "pero no se pudo determinar una operación segura."
                ),
            )

        return StructuredQuery(
            matched=True,
            field=field,
            operator=operator,
            value=value,
            aggregate=aggregate,
            brand=brand,
            model=model,
            reason="Consulta estructurada detectada.",
        )


class StructuredInventoryEngine:
    def __init__(self, records):
        self.records = list(records)

        self.rows = [
            record
            for record in self.records
            if self._is_structured_row(record)
        ]

    @staticmethod
    def _metadata(record) -> dict:
        return getattr(record, "metadata", {}) or {}

    @classmethod
    def _is_structured_row(cls, record) -> bool:
        metadata = cls._metadata(record)
        return (
            str(metadata.get("content_mode", ""))
            == "structured_table_row"
        )

    @classmethod
    def _get(cls, record, key: str, default=""):
        text = str(getattr(record, "text", ""))

        canonical = _canonical_from_text(text, key)

        if canonical not in (None, ""):
            if key == "brand":
                return _clean_brand(canonical)
            if key == "model":
                return _clean_model(canonical)
            if key == "description":
                return _clean_description(canonical)
            return canonical

        metadata = cls._metadata(record)

        aliases = {
            "stock": ["stock", "STOCK"],
            "quantity": ["quantity", "cantidad", "CANTIDAD"],
            "brand": ["brand", "marca", "MARCA"],
            "model": ["model", "modelo", "MODELO"],
            "description": ["description", "descripcion", "DESCRIPCION"],
            "item": ["item", "ITEM"],
        }

        for alias in aliases.get(key, [key]):
            value = metadata.get(alias)

            if value not in (None, ""):
                if key == "brand":
                    return _clean_brand(value)
                if key == "model":
                    return _clean_model(value)
                if key == "description":
                    return _clean_description(value)
                return value

        return default

    @classmethod
    def _matches_brand(cls, record, brand: str | None) -> bool:
        if not brand:
            return True

        target = normalize(brand)
        return target in normalize(cls._get(record, "brand", ""))

    @classmethod
    def _matches_model(cls, record, model: str | None) -> bool:
        if not model:
            return True

        target = normalize(model)

        return (
            target in normalize(cls._get(record, "model", ""))
            or target in normalize(getattr(record, "text", ""))
        )

    @staticmethod
    def _compare(actual, operator: str, expected) -> bool:
        actual_n = as_number(actual)

        if actual_n is None:
            return False

        if operator == "==":
            return actual_n == expected
        if operator == ">":
            return actual_n > expected
        if operator == "<":
            return actual_n < expected
        if operator == ">=":
            return actual_n >= expected
        if operator == "<=":
            return actual_n <= expected

        return False

    def record_to_row(self, record) -> dict:
        return {
            "Ítem": self._get(record, "item", ""),
            "Descripción": self._get(record, "description", ""),
            "Marca": self._get(record, "brand", ""),
            "Modelo": self._get(record, "model", ""),
            "Cantidad": pretty_number(self._get(record, "quantity", "")),
            "Stock": pretty_number(self._get(record, "stock", "")),
        }

    def _filter_brand_model(self, query: StructuredQuery):
        return [
            record
            for record in self.rows
            if self._matches_brand(record, query.brand)
            and self._matches_model(record, query.model)
        ]

    def _response(self, answer, records, query, abstained=False):
        return {
            "answer": answer,
            "records": records,
            "structured_rows": [
                self.record_to_row(record)
                for record in records
            ],
            "query": query,
            "abstained": abstained,
        }

    def execute(self, question: str):
        query = StructuredQueryRouter.infer(question)

        if not query.matched:
            return None

        candidates = self._filter_brand_model(query)

        # -------------------------------------------------------------
        # Group by brand
        # -------------------------------------------------------------
        if query.aggregate == "group_sum_brand":
            totals = {}

            for record in candidates:
                brand = self._get(record, "brand", "")
                value = as_number(self._get(record, query.field, None))

                if not brand or value is None:
                    continue

                totals[brand] = totals.get(brand, 0.0) + value

            ordered = sorted(
                totals.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            rows = [
                {
                    "Marca": brand,
                    (
                        "Stock total"
                        if query.field == "stock"
                        else "Cantidad total"
                    ): pretty_number(total),
                }
                for brand, total in ordered
            ]

            label = "stock" if query.field == "stock" else "cantidad"

            return {
                "answer": (
                    f"Se calculó el {label} total por marca "
                    f"para {len(rows)} marca(s)."
                ),
                "records": candidates,
                "structured_rows": rows,
                "query": query,
                "abstained": False,
            }

        # -------------------------------------------------------------
        # Quantity vs Stock
        # -------------------------------------------------------------
        if query.comparison == "quantity_gt_stock":
            filtered = []

            for record in candidates:
                quantity = as_number(self._get(record, "quantity", None))
                stock = as_number(self._get(record, "stock", None))

                if (
                    quantity is not None
                    and stock is not None
                    and quantity > stock
                ):
                    filtered.append(record)

            return self._response(
                (
                    f"Se encontraron {len(filtered)} registro(s) "
                    "donde la cantidad total es mayor que el stock."
                ),
                filtered,
                query,
            )

        if query.comparison == "stock_eq_quantity":
            filtered = []

            for record in candidates:
                quantity = as_number(self._get(record, "quantity", None))
                stock = as_number(self._get(record, "stock", None))

                if (
                    quantity is not None
                    and stock is not None
                    and quantity == stock
                ):
                    filtered.append(record)

            return self._response(
                (
                    f"Se encontraron {len(filtered)} registro(s) "
                    "donde stock y cantidad son iguales."
                ),
                filtered,
                query,
            )

        # -------------------------------------------------------------
        # Ranking
        # -------------------------------------------------------------
        if query.ranking:
            scored = []

            for record in candidates:
                value = as_number(self._get(record, "stock", None))

                if value is not None:
                    scored.append((value, record))

            scored.sort(
                key=lambda pair: pair[0],
                reverse=(query.ranking == "desc"),
            )

            selected = [
                record
                for _, record
                in scored[: query.limit or 10]
            ]

            direction = (
                "menor"
                if query.ranking == "asc"
                else "mayor"
            )

            return self._response(
                (
                    f"Se muestran {len(selected)} registro(s) "
                    f"con {direction} stock."
                ),
                selected,
                query,
            )

        # -------------------------------------------------------------
        # Lookup
        # -------------------------------------------------------------
        if query.operator == "lookup":
            # Si el router ya obtuvo marca/modelo y el filtro produjo
            # candidatos, esa coincidencia estructurada es suficiente.
            exact_entity_match = bool(
                (query.brand or query.model)
                and candidates
            )

            if not exact_entity_match:
                q_tokens = set(
                    re.findall(
                        r"[a-z0-9._/-]{2,}",
                        normalize(question),
                    )
                )

                stop = {
                    "cual", "stock", "cantidad", "total", "del",
                    "las", "los", "una", "uno", "hay", "modelo",
                    "marca", "herramienta", "herramientas", "unidades",
                    "cuanto", "cuanta", "cuantos", "cuantas",
                    "estan", "disponible", "disponibles",
                }

                q_tokens -= stop
                scored = []

                for record in candidates:
                    record_text = " ".join(
                        str(value)
                        for value in (
                            getattr(record, "title", ""),
                            getattr(record, "text", ""),
                            self._get(record, "description", ""),
                            self._get(record, "brand", ""),
                            self._get(record, "model", ""),
                        )
                        if value not in (None, "")
                    )

                    text_tokens = set(
                        re.findall(
                            r"[a-z0-9._/-]{2,}",
                            normalize(record_text),
                        )
                    )

                    score = len(
                        q_tokens.intersection(text_tokens)
                    )
                    scored.append(
                        (score, record)
                    )

                scored.sort(
                    key=lambda pair: pair[0],
                    reverse=True,
                )

                candidates = [
                    record
                    for score, record in scored
                    if score > 0
                ]

            if not candidates:
                return {
                    "answer": (
                        "No se encontró un registro estructurado "
                        "que coincida con la consulta."
                    ),
                    "records": [],
                    "structured_rows": [],
                    "query": query,
                    "abstained": True,
                }

            top = candidates[0]
            row = self.record_to_row(top)

            if (
                "cantidad" in normalize(question)
                and "stock" in normalize(question)
            ):
                answer = (
                    f"{row['Descripción']} "
                    f"tiene una cantidad total de {row['Cantidad']} "
                    f"unidad(es) y un stock de {row['Stock']} "
                    "unidad(es) [F1]."
                )
            else:
                field_label = (
                    "stock"
                    if query.field == "stock"
                    else "cantidad"
                )

                value = (
                    row["Stock"]
                    if query.field == "stock"
                    else row["Cantidad"]
                )

                identity = row["Descripción"] or "el registro"

                if row["Marca"]:
                    identity += f" {row['Marca']}"

                if row["Modelo"]:
                    identity += f" {row['Modelo']}"

                answer = (
                    f"El {field_label} de {identity} "
                    f"es de {value} unidad(es) [F1]."
                )

            return {
                "answer": answer,
                "records": [top],
                "structured_rows": [row],
                "query": query,
                "abstained": False,
            }

        # -------------------------------------------------------------
        # Sum
        # -------------------------------------------------------------
        if query.aggregate == "sum":
            valid_records = []
            values = []

            for record in candidates:
                value = as_number(self._get(record, query.field, None))

                if value is not None:
                    values.append(value)
                    valid_records.append(record)

            if not values:
                return {
                    "answer": (
                        "No se encontraron valores estructurados "
                        "suficientes para calcular el total."
                    ),
                    "records": [],
                    "structured_rows": [],
                    "query": query,
                    "abstained": True,
                }

            total = sum(values)
            label = "stock" if query.field == "stock" else "cantidad"

            return {
                "answer": (
                    f"El {label} total de los registros consultados "
                    f"es {pretty_number(total)} unidad(es)."
                ),
                "records": valid_records,
                "structured_rows": [
                    self.record_to_row(record)
                    for record in valid_records
                ],
                "query": query,
                "abstained": False,
            }

        # -------------------------------------------------------------
        # Filter
        # -------------------------------------------------------------
        filtered = [
            record
            for record in candidates
            if self._compare(
                self._get(record, query.field, None),
                query.operator,
                query.value,
            )
        ]

        if query.aggregate == "count":
            return self._response(
                (
                    f"Se encontraron {len(filtered)} registro(s) "
                    "que cumplen el criterio."
                ),
                filtered,
                query,
            )

        if not filtered:
            return {
                "answer": (
                    "No se encontraron registros estructurados "
                    "que cumplan el criterio solicitado."
                ),
                "records": [],
                "structured_rows": [],
                "query": query,
                "abstained": False,
            }

        criterion = (
            f"{query.field} {query.operator} "
            f"{pretty_number(query.value)}"
        )

        if query.brand:
            criterion += f", marca {query.brand}"

        return self._response(
            (
                f"Se encontraron {len(filtered)} registro(s) "
                f"que cumplen el criterio ({criterion})."
            ),
            filtered,
            query,
        )

    def to_retrieval_results(self, records) -> list[RetrievalResult]:
        results = []

        for rank, record in enumerate(records, start=1):
            metadata = dict(getattr(record, "metadata", {}) or {})
            metadata["structured_query_match"] = True

            results.append(
                RetrievalResult(
                    rank=rank,
                    score=1.0,
                    record_id=str(
                        getattr(record, "record_id", f"STRUCT-{rank}")
                    ),
                    source_type=str(
                        getattr(record, "source_type", "document")
                    ),
                    title=str(
                        getattr(record, "title", "Registro estructurado")
                    ),
                    text=str(getattr(record, "text", "")),
                    source_file=str(
                        getattr(record, "source_file", "")
                    ),
                    metadata=metadata,
                )
            )

        return results
