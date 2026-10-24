"""
inventory_analytics.py
----------------------
Fase 9.2 — Calidad y normalización del inventario.

Incluye:
- validación heredada de Fase 9.1;
- normalización conservadora de marca, modelo y descripción;
- puntuación de calidad por registro;
- detección de posibles duplicados;
- identificación de texto posiblemente contaminado por OCR;
- preservación del valor original para trazabilidad.

No utiliza el LLM.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import re
import unicodedata

from .structured_query import StructuredInventoryEngine, as_number


@dataclass
class InventoryKPIs:
    total_records: int
    total_quantity: int
    total_stock: int
    available_records: int
    zero_stock_records: int
    reorder_records: int
    total_brands: int
    excluded_records: int = 0
    high_quality_records: int = 0
    review_records: int = 0
    duplicate_groups: int = 0



KNOWN_BRANDS = (
    "STANLEY",
    "DEWALT",
    "TRUPER",
    "INGCO",
    "DORMER",
    "BELLOTA",
    "BEST VALUE",
)

MODEL_PATTERNS = (
    r"\b\d{2,3}-\d{2,4}(?:\s*/\s*\d{2,3}-\d{2,4})*\b",
    r"\bDWD[0-9A-Z-]+\b",
    r"\bHG[A-Z0-9-]{4,}\b",
    r"\bHHKT[0-9A-Z-]+\b",
)

def _clean_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()

def _recover_explicit_brand_model(
    description: str,
    brand: str,
    model: str,
) -> tuple[str, str, list[str]]:
    """
    Recupera marca/modelo únicamente si aparecen explícitamente
    en la descripción. No usa inferencia semántica.
    """
    desc = _clean_spaces(description)
    desc_u = desc.upper()
    notes = []

    recovered_brand = _clean_spaces(brand).upper()
    recovered_model = _clean_spaces(model).upper()

    if not recovered_brand:
        for known in KNOWN_BRANDS:
            if re.search(rf"(?<![A-Z0-9]){re.escape(known)}(?![A-Z0-9])", desc_u):
                recovered_brand = known
                notes.append("Marca recuperada explícitamente desde descripción")
                break

    if not recovered_model:
        matches = []
        for pattern in MODEL_PATTERNS:
            matches.extend(re.findall(pattern, desc_u))

        # Filtrar falsos positivos muy cortos o valores que parezcan medidas
        clean_matches = []
        for value in matches:
            value = _clean_spaces(value).upper()
            if len(value) < 4:
                continue
            if value not in clean_matches:
                clean_matches.append(value)

        # Si hay exactamente un candidato claro, lo usamos.
        if len(clean_matches) == 1:
            recovered_model = clean_matches[0]
            notes.append("Modelo recuperado explícitamente desde descripción")
        elif len(clean_matches) > 1:
            # Preferir coincidencia cercana a una marca conocida o a palabra MODELO.
            model_match = re.search(
                r"(?:MODELO\s*:?\s*|STANLEY\s+|DEWALT\s+|TRUPER\s+|INGCO\s+|DORMER\s+|BELLOTA\s+)"
                r"([A-Z0-9]+(?:-[A-Z0-9]+)+(?:\s*/\s*[A-Z0-9]+(?:-[A-Z0-9]+)+)*)",
                desc_u,
            )
            if model_match:
                recovered_model = _clean_spaces(model_match.group(1)).upper()
                notes.append("Modelo recuperado explícitamente desde descripción")

    return recovered_brand, recovered_model, notes


class InventoryAnalytics:
    def _normalize_quality_row(self, row: dict) -> dict:
        out = dict(row)

        description = _clean_spaces(out.get("Descripción", ""))
        brand = _clean_spaces(out.get("Marca", ""))
        model = _clean_spaces(out.get("Modelo", ""))

        recovered_brand, recovered_model, recovery_notes = _recover_explicit_brand_model(
            description,
            brand,
            model,
        )

        if recovered_brand:
            out["Marca"] = recovered_brand
        if recovered_model:
            out["Modelo"] = recovered_model

        existing_notes = _clean_spaces(
            out.get("Observaciones calidad", "")
        )

        notes = []
        if existing_notes and existing_notes.lower() != "sin observaciones":
            notes.extend(
                [part.strip() for part in existing_notes.split(";") if part.strip()]
            )

        # Quitar observaciones que ya fueron resueltas
        if out.get("Marca"):
            notes = [n for n in notes if n.lower() != "marca ausente"]
        if out.get("Modelo"):
            notes = [n for n in notes if n.lower() != "modelo ausente"]

        notes.extend(recovery_notes)

        # recalcular calidad conservando penalizaciones por OCR/duplicado
        score = 100

        if not out.get("Marca"):
            score -= 15
            if "Marca ausente" not in notes:
                notes.append("Marca ausente")

        if not out.get("Modelo"):
            score -= 15
            if "Modelo ausente" not in notes:
                notes.append("Modelo ausente")

        if "Posible ruido OCR en descripción" in notes:
            score -= 15

        score = max(0, min(100, score))

        if score >= 85:
            level = "Alta"
        elif score >= 60:
            level = "Media"
        else:
            level = "Revisar"

        out["Calidad"] = score
        out["Nivel calidad"] = level
        out["Observaciones calidad"] = (
            "; ".join(dict.fromkeys(notes))
            if notes
            else "Sin observaciones"
        )

        return out

    def __init__(self, records):
        self.engine = StructuredInventoryEngine(records)
        raw_records = list(self.engine.rows)
        raw_rows = [self.engine.record_to_row(record) for record in raw_records]

        self.records = []
        self.rows = []
        self.rejected_records = []
        self.rejected_rows = []

        for record, raw_row in zip(raw_records, raw_rows):
            if not self._is_valid_inventory_row(raw_row):
                self.rejected_records.append(record)
                self.rejected_rows.append(raw_row)
                continue

            normalized = self._normalize_row(raw_row)
            quality = self._quality_info(normalized, raw_row)
            normalized.update(quality)

            # Fase 9.2.1: recuperar únicamente datos explícitos presentes
            # en la descripción y recalcular la calidad después de esa
            # recuperación. Esto evita marcar como ausente una marca/modelo
            # que sí aparece literalmente en el registro fuente.
            normalized = self._normalize_quality_row(normalized)

            self.records.append(record)
            self.rows.append(normalized)

        self._duplicate_map = self._build_duplicate_map()
        for row in self.rows:
            key = self._duplicate_key(row)
            count = len(self._duplicate_map.get(key, [])) if key else 0
            row["Posible duplicado"] = "Sí" if count > 1 else "No"

    @staticmethod
    def _num_or_none(value):
        return as_number(value)

    @staticmethod
    def _num(value) -> float:
        number = as_number(value)
        return 0.0 if number is None else number

    @staticmethod
    def _normalized(value) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip().upper())

    @staticmethod
    def _fold(value) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", text).strip().upper()

    @classmethod
    def _looks_like_header(cls, row: dict) -> bool:
        item = cls._normalized(row.get("Ítem"))
        desc = cls._normalized(row.get("Descripción"))
        qty = cls._normalized(row.get("Cantidad"))
        stock = cls._normalized(row.get("Stock"))

        header_tokens = {
            "ITEM", "ÍTEM", "ITEN", "DESCRIPCION", "DESCRIPCIÓN",
            "CANT", "CANTIDAD", "STOCK",
        }

        if item in header_tokens or desc in header_tokens:
            return True
        if qty in header_tokens or stock in header_tokens:
            return True

        title_text = f"{item} {desc}".strip()
        return any(token in title_text for token in (
            "SUMINISTRO DE HERRAMIENTA",
            "LISTADO DE EQUIPOS",
            "INVENTARIO DE BODEGA",
        ))

    @classmethod
    def _is_valid_inventory_row(cls, row: dict) -> bool:
        if cls._looks_like_header(row):
            return False

        quantity = cls._num_or_none(row.get("Cantidad"))
        stock = cls._num_or_none(row.get("Stock"))
        if quantity is None and stock is None:
            return False

        description = str(row.get("Descripción", "")).strip()
        item = str(row.get("Ítem", "")).strip()
        return bool(description or item)

    @classmethod
    def _clean_brand(cls, value: str) -> str:
        text = cls._fold(value)
        text = re.sub(r"^MARCA\s*:\s*", "", text)
        text = re.split(r"\s*,?\s*MODELO\s*:", text, maxsplit=1)[0]
        text = re.split(r"\s+(?:CANTIDAD|STOCK)\s*:", text, maxsplit=1)[0]
        return text.strip(" ,;.-")

    @classmethod
    def _clean_model(cls, value: str) -> str:
        text = cls._fold(value)
        text = re.sub(r"^MODELO\s*:\s*", "", text)
        text = re.split(r"\s+(?:MARCA|CANTIDAD|STOCK)\s*:", text, maxsplit=1)[0]

        # Si el campo trae un modelo seguido de descripción contaminada,
        # conservar solo el prefijo de código plausible.
        if len(text) > 28 and " " in text:
            match = re.match(
                r"^([A-Z0-9]+(?:\s*[-/]\s*[A-Z0-9]+)*(?:\s*/\s*[A-Z0-9-]+)*)\b",
                text,
            )
            if match:
                candidate = match.group(1).strip()
                if any(ch.isdigit() for ch in candidate):
                    text = candidate

        text = re.sub(r"\s*/\s*", " / ", text)
        text = re.sub(r"\s*-\s*", "-", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip(" ,;.-")

    @classmethod
    def _clean_description(cls, value: str, model: str = "") -> str:
        text = cls._fold(value)
        text = re.sub(r"^DESCRIPCION\s*:\s*", "", text)

        # Caso típico: el parser puso "Modelo: XX" al inicio de descripción.
        if text.startswith("MODELO:"):
            text = re.sub(r"^MODELO\s*:\s*[^ ]+\s*", "", text, count=1)

        text = re.split(r"\s+MARCA\s*:", text, maxsplit=1)[0]
        text = re.split(r"\s+MODELO\s*:", text, maxsplit=1)[0]
        text = re.sub(r"\s+", " ", text).strip(" ,;.-")
        return text

    @classmethod
    def _normalize_row(cls, raw: dict) -> dict:
        model = cls._clean_model(raw.get("Modelo", ""))
        return {
            "Ítem": str(raw.get("Ítem", "")).strip(),
            "Descripción": cls._clean_description(raw.get("Descripción", ""), model),
            "Marca": cls._clean_brand(raw.get("Marca", "")),
            "Modelo": model,
            "Cantidad": cls._pretty_numeric(raw.get("Cantidad")),
            "Stock": cls._pretty_numeric(raw.get("Stock")),
        }

    @classmethod
    def _pretty_numeric(cls, value):
        number = cls._num_or_none(value)
        if number is None:
            return ""
        if float(number).is_integer():
            return str(int(number))
        return str(number)

    @classmethod
    def _ocr_suspicious(cls, text: str) -> bool:
        text = str(text or "")
        if not text:
            return False

        patterns = (
            r"[a-z][A-Z][a-z]",          # alternancia extraña de caja
            r"[:;]{2,}",                # puntuación repetida típica de OCR
            r"\b[Oo0]:[dD]\b",
            r"\b[eE][tT][lL][lL][oO][pP]\b",
            r"[A-Z]\d[A-Z]\d[A-Z]",   # mezcla improbable en descripción
        )
        return any(re.search(p, text) for p in patterns)

    @classmethod
    def _quality_info(cls, row: dict, raw: dict) -> dict:
        score = 0
        issues = []

        description = str(row.get("Descripción", "")).strip()
        brand = str(row.get("Marca", "")).strip()
        model = str(row.get("Modelo", "")).strip()
        quantity = cls._num_or_none(row.get("Cantidad"))
        stock = cls._num_or_none(row.get("Stock"))

        if len(description) >= 8:
            score += 30
        else:
            issues.append("Descripción incompleta")

        if brand:
            score += 15
        else:
            issues.append("Marca ausente")

        if model:
            score += 15
        else:
            issues.append("Modelo ausente")

        if quantity is not None:
            score += 20
        else:
            issues.append("Cantidad ausente")

        if stock is not None:
            score += 20
        else:
            issues.append("Stock ausente")

        if cls._ocr_suspicious(raw.get("Descripción", "")):
            score = max(0, score - 15)
            issues.append("Posible ruido OCR en descripción")

        if quantity is not None and stock is not None and stock > quantity:
            score = max(0, score - 10)
            issues.append("Stock mayor que cantidad")

        if score >= 85:
            level = "Alta"
        elif score >= 65:
            level = "Media"
        else:
            level = "Revisar"

        return {
            "Calidad": score,
            "Nivel calidad": level,
            "Observaciones calidad": "; ".join(issues) if issues else "Sin observaciones",
        }

    @classmethod
    def _duplicate_key(cls, row: dict):
        desc = cls._fold(row.get("Descripción"))
        brand = cls._fold(row.get("Marca"))
        model = cls._fold(row.get("Modelo"))
        if not desc:
            return None
        # Modelo + marca es la clave más fuerte; descripción se usa de respaldo.
        if model:
            return (brand, model)
        return (brand, desc)

    def _build_duplicate_map(self):
        groups = defaultdict(list)
        for row in self.rows:
            key = self._duplicate_key(row)
            if key:
                groups[key].append(row)
        return {key: values for key, values in groups.items() if len(values) > 1}

    def duplicate_groups(self) -> list[dict]:
        output = []
        group_id = 1
        for key, rows in sorted(self._duplicate_map.items(), key=lambda kv: (-len(kv[1]), str(kv[0]))):
            output.append({
                "Grupo": group_id,
                "Registros": len(rows),
                "Marca": rows[0].get("Marca", ""),
                "Modelo": rows[0].get("Modelo", ""),
                "Descripción ejemplo": rows[0].get("Descripción", ""),
                "Ítems": ", ".join(str(r.get("Ítem", "")) for r in rows),
            })
            group_id += 1
        return output

    def quality_review_rows(self) -> list[dict]:
        return sorted(
            [row for row in self.rows if row.get("Nivel calidad") != "Alta"],
            key=lambda row: (int(row.get("Calidad", 0)), str(row.get("Ítem", ""))),
        )

    def quality_distribution(self) -> list[dict]:
        counts = Counter(str(row.get("Nivel calidad", "")) for row in self.rows)
        order = ["Alta", "Media", "Revisar"]
        return [{"Nivel": level, "Registros": counts.get(level, 0)} for level in order]

    def kpis(self) -> InventoryKPIs:
        quantity_values = [self._num_or_none(row.get("Cantidad")) for row in self.rows]
        stock_values = [self._num_or_none(row.get("Stock")) for row in self.rows]

        total_quantity = sum(v for v in quantity_values if v is not None)
        total_stock = sum(v for v in stock_values if v is not None)
        available = sum(1 for v in stock_values if v is not None and v > 0)
        zero_stock = sum(1 for v in stock_values if v is not None and v == 0)
        reorder = sum(1 for v in stock_values if v is not None and v <= 1)
        brands = {str(row.get("Marca", "")).strip() for row in self.rows if str(row.get("Marca", "")).strip()}
        high_quality = sum(1 for row in self.rows if row.get("Nivel calidad") == "Alta")
        review = len(self.rows) - high_quality

        return InventoryKPIs(
            total_records=len(self.rows),
            total_quantity=int(total_quantity),
            total_stock=int(total_stock),
            available_records=available,
            zero_stock_records=zero_stock,
            reorder_records=reorder,
            total_brands=len(brands),
            excluded_records=len(self.rejected_rows),
            high_quality_records=high_quality,
            review_records=review,
            duplicate_groups=len(self._duplicate_map),
        )

    def brands(self) -> list[str]:
        return sorted({str(row.get("Marca", "")).strip() for row in self.rows if str(row.get("Marca", "")).strip()})

    def rows_filtered(self, *, brand: str | None = None, status: str = "Todos", search: str = "", quality: str = "Todos") -> list[dict]:
        search_n = self._fold(search)
        output = []

        for row in self.rows:
            if brand and brand != "Todas" and str(row.get("Marca", "")).strip() != brand:
                continue

            stock = self._num_or_none(row.get("Stock"))
            if status == "Disponible" and (stock is None or stock <= 0):
                continue
            if status == "Sin stock" and (stock is None or stock != 0):
                continue
            if status == "Reposición" and (stock is None or stock > 1):
                continue

            if quality != "Todos" and row.get("Nivel calidad") != quality:
                continue

            if search_n:
                haystack = self._fold(" ".join(str(row.get(k, "")) for k in ("Ítem", "Descripción", "Marca", "Modelo")))
                if search_n not in haystack:
                    continue

            output.append(row)
        return output

    def stock_by_brand(self) -> list[dict]:
        totals = defaultdict(float)
        for row in self.rows:
            brand = str(row.get("Marca", "")).strip()
            stock = self._num_or_none(row.get("Stock"))
            if not brand or stock is None:
                continue
            totals[brand] += stock
        return [{"Marca": b, "Stock total": int(v)} for b, v in sorted(totals.items(), key=lambda p: p[1], reverse=True)]

    def records_by_brand(self) -> list[dict]:
        counter = Counter(str(row.get("Marca", "")).strip() for row in self.rows if str(row.get("Marca", "")).strip())
        return [{"Marca": brand, "Registros": count} for brand, count in counter.most_common()]

    def reorder_rows(self) -> list[dict]:
        rows = []
        for row in self.rows:
            stock = self._num_or_none(row.get("Stock"))
            if stock is not None and stock <= 1:
                rows.append(row)
        return sorted(rows, key=lambda row: (self._num(row.get("Stock")), str(row.get("Marca", "")), str(row.get("Descripción", ""))))

    def top_low_stock(self, limit: int = 10) -> list[dict]:
        rows = [row for row in self.rows if self._num_or_none(row.get("Stock")) is not None]
        return sorted(rows, key=lambda row: self._num(row.get("Stock")))[:limit]

    def top_high_stock(self, limit: int = 10) -> list[dict]:
        rows = [row for row in self.rows if self._num_or_none(row.get("Stock")) is not None]
        return sorted(rows, key=lambda row: self._num(row.get("Stock")), reverse=True)[:limit]
