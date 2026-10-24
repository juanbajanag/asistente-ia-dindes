
"""
tabular_ingestion.py
--------------------
Fase 7.8 — Ingestión estructurada de tablas.

Objetivo:
Convertir tablas extraídas de PDF/CSV/XLS/XLSX en registros semánticos
independientes, evitando que el LLM tenga que reconstruir columnas desde
texto desalineado.

Diseñado para tablas con encabezados como:
ITEM | DESCRIPCION | CANT | STOCK

y extensible a otras tablas institucionales.
"""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def normalize_text(value) -> str:
    if value is None:
        return ""

    text = str(value).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_header(value) -> str:
    text = normalize_text(value)

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        ch for ch in text
        if not unicodedata.combining(ch)
    )

    text = text.upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


HEADER_ALIASES = {
    "ITEM": {
        "ITEM", "ITEN", "N", "NRO", "NO", "NUMERO", "NUM",
    },
    "DESCRIPCION": {
        "DESCRIPCION", "DESCRIPCIÓN", "DETALLE",
        "NOMBRE", "NOMBRE BIEN", "BIEN",
    },
    "CANTIDAD": {
        "CANT", "CANTIDAD", "CANT.", "CANTIDAD TOTAL",
    },
    "STOCK": {
        "STOCK", "DISPONIBLE", "EXISTENCIA",
        "SALDO", "STOCK ACTUAL",
    },
    "MARCA": {
        "MARCA", "FABRICANTE",
    },
    "MODELO": {
        "MODELO", "MODEL",
    },
    "CODIGO": {
        "CODIGO", "CODIGO BIEN", "CÓDIGO BIEN",
        "CODIGO DEL BIEN", "ID",
    },
}


def canonical_header(value) -> str:
    norm = normalize_header(value)

    for canonical, aliases in HEADER_ALIASES.items():
        alias_norms = {
            normalize_header(a)
            for a in aliases
        }
        if norm in alias_norms:
            return canonical

    return norm or "CAMPO"


def _to_int_if_possible(value):
    text = normalize_text(value)

    if not text:
        return ""

    # Evitar convertir modelos o códigos con letras.
    if re.fullmatch(r"-?\d+(?:\.0+)?", text):
        try:
            return int(float(text))
        except Exception:
            return text

    return text


def parse_brand_model(description: str) -> tuple[str, str]:
    """
    Extrae marca/modelo cuando vienen embebidos en DESCRIPCION.

    Ejemplo:
    'ALICATE ... Marca: STANLEY, Modelo: 84-023'
    """
    text = normalize_text(description)

    brand = ""
    model = ""

    brand_match = re.search(
        r"\bMarca\s*:\s*([^,;\n]+)",
        text,
        flags=re.IGNORECASE,
    )

    if brand_match:
        brand = normalize_text(
            brand_match.group(1)
        )

    model_match = re.search(
        r"\bModelo\s*:\s*([^,;\n]+)",
        text,
        flags=re.IGNORECASE,
    )

    if model_match:
        model = normalize_text(
            model_match.group(1)
        )

    return brand, model


# ----------------------------------------------------------------------
# Registros tabulares
# ----------------------------------------------------------------------
@dataclass
class StructuredRow:
    sheet_or_page: str
    row_index: int
    values: dict

    def to_semantic_text(self) -> str:
        """
        Genera texto explícito para RAG.

        Se priorizan nombres claros de campos para evitar ambigüedad
        entre CANTIDAD y STOCK.
        """
        preferred_order = [
            "ITEM",
            "CODIGO",
            "DESCRIPCION",
            "MARCA",
            "MODELO",
            "CANTIDAD",
            "STOCK",
        ]

        pieces = []

        for key in preferred_order:
            value = self.values.get(key)

            if value not in ("", None):
                pieces.append(
                    f"{key}: {value}"
                )

        for key, value in self.values.items():
            if (
                key not in preferred_order
                and value not in ("", None)
            ):
                pieces.append(
                    f"{key}: {value}"
                )

        return ". ".join(pieces) + "."


def dataframe_to_structured_rows(
    df: pd.DataFrame,
    source_label: str,
) -> list[StructuredRow]:

    if df is None or df.empty:
        return []

    work = df.copy()

    # Normalizar nombres de columnas.
    work.columns = [
        canonical_header(col)
        for col in work.columns
    ]

    # Resolver nombres duplicados.
    seen = {}
    cols = []

    for col in work.columns:
        if col not in seen:
            seen[col] = 1
            cols.append(col)
        else:
            seen[col] += 1
            cols.append(
                f"{col}_{seen[col]}"
            )

    work.columns = cols

    rows = []

    for index, row in work.iterrows():
        values = {}

        for col, raw_value in row.items():
            value = normalize_text(
                raw_value
            )

            if (
                not value
                or value.lower() == "nan"
            ):
                continue

            if col in {
                "CANTIDAD",
                "STOCK",
                "ITEM",
            }:
                value = _to_int_if_possible(
                    value
                )

            values[col] = value

        if not values:
            continue

        # Si marca/modelo no son columnas propias, intentar extraerlas
        # desde la descripción.
        description = str(
            values.get(
                "DESCRIPCION",
                "",
            )
        )

        if description:
            brand, model = (
                parse_brand_model(
                    description
                )
            )

            if (
                brand
                and "MARCA" not in values
            ):
                values[
                    "MARCA"
                ] = brand

            if (
                model
                and "MODELO" not in values
            ):
                values[
                    "MODELO"
                ] = model

        rows.append(
            StructuredRow(
                sheet_or_page=source_label,
                row_index=int(index) + 1,
                values=values,
            )
        )

    return rows


# ----------------------------------------------------------------------
# PDF
# ----------------------------------------------------------------------
def extract_pdf_tables(
    file_bytes: bytes,
) -> list[StructuredRow]:
    """
    Extrae tablas usando pdfplumber.

    Estrategia:
    - Detecta tablas por página.
    - Usa la primera fila como encabezado cuando contiene vocabulario
      típico (ITEM/DESCRIPCION/CANT/STOCK/CODIGO/etc.).
    - Si no hay encabezado confiable, intenta inferir una tabla de
      cuatro columnas para inventarios de herramientas.
    """
    import pdfplumber

    structured_rows = []

    with pdfplumber.open(
        io.BytesIO(file_bytes)
    ) as pdf:

        for page_no, page in enumerate(
            pdf.pages,
            start=1,
        ):
            tables = page.extract_tables() or []

            for table_no, table in enumerate(
                tables,
                start=1,
            ):
                if not table:
                    continue

                cleaned = [
                    [
                        normalize_text(cell)
                        for cell in row
                    ]
                    for row in table
                    if row
                ]

                cleaned = [
                    row
                    for row in cleaned
                    if any(row)
                ]

                if not cleaned:
                    continue

                first = cleaned[0]
                first_norm = {
                    canonical_header(x)
                    for x in first
                    if x
                }

                known = {
                    "ITEM",
                    "DESCRIPCION",
                    "CANTIDAD",
                    "STOCK",
                    "CODIGO",
                }

                has_header = (
                    len(
                        first_norm.intersection(
                            known
                        )
                    )
                    >= 2
                )

                if has_header:
                    headers = [
                        canonical_header(x)
                        for x in first
                    ]
                    data_rows = cleaned[1:]
                else:
                    # Caso típico del inventario de herramientas:
                    # ITEM | DESCRIPCION | CANT | STOCK
                    width = max(
                        len(row)
                        for row in cleaned
                    )

                    if width >= 4:
                        headers = [
                            "ITEM",
                            "DESCRIPCION",
                            "CANTIDAD",
                            "STOCK",
                        ] + [
                            f"CAMPO_{i}"
                            for i in range(
                                5,
                                width + 1,
                            )
                        ]
                    else:
                        headers = [
                            f"CAMPO_{i}"
                            for i in range(
                                1,
                                width + 1,
                            )
                        ]

                    data_rows = cleaned

                width = len(headers)
                normalized_rows = []

                for row in data_rows:
                    row = (
                        row
                        + [""] * width
                    )[:width]
                    normalized_rows.append(
                        row
                    )

                df = pd.DataFrame(
                    normalized_rows,
                    columns=headers,
                )

                label = (
                    f"Página {page_no} "
                    f"- Tabla {table_no}"
                )

                structured_rows.extend(
                    dataframe_to_structured_rows(
                        df,
                        label,
                    )
                )

    return structured_rows


# ----------------------------------------------------------------------
# CSV / Excel
# ----------------------------------------------------------------------
def extract_csv_rows(
    file_bytes: bytes,
    filename: str,
) -> list[StructuredRow]:

    last_error = None

    for encoding in (
        "utf-8-sig",
        "utf-8",
        "latin-1",
    ):
        try:
            df = pd.read_csv(
                io.BytesIO(
                    file_bytes
                ),
                encoding=encoding,
            )

            return dataframe_to_structured_rows(
                df,
                source_label=filename,
            )

        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        f"No fue posible leer CSV: {last_error}"
    )


def extract_excel_rows(
    file_bytes: bytes,
    filename: str,
) -> list[StructuredRow]:

    sheets = pd.read_excel(
        io.BytesIO(
            file_bytes
        ),
        sheet_name=None,
    )

    rows = []

    for sheet_name, df in sheets.items():
        rows.extend(
            dataframe_to_structured_rows(
                df,
                source_label=(
                    f"{filename} / "
                    f"Hoja {sheet_name}"
                ),
            )
        )

    return rows


# ----------------------------------------------------------------------
# Conversión a chunks RAG
# ----------------------------------------------------------------------
def rows_to_chunks(
    rows: Iterable[StructuredRow],
    *,
    document_id: str,
    title: str,
    source_file: str,
    document_type: str,
    source_status: str,
    access_level: str,
    document_date: str,
    version: str,
    file_hash: str,
    ingested_at: str,
) -> list[dict]:

    chunks = []

    for idx, row in enumerate(
        rows,
        start=1,
    ):
        values = row.values

        item_value = str(
            values.get(
                "ITEM",
                "",
            )
        ).strip()

        code_value = str(
            values.get(
                "CODIGO",
                "",
            )
        ).strip()

        description = str(
            values.get(
                "DESCRIPCION",
                "",
            )
        ).strip()

        brand = str(
            values.get(
                "MARCA",
                "",
            )
        ).strip()

        model = str(
            values.get(
                "MODELO",
                "",
            )
        ).strip()

        quantity = values.get(
            "CANTIDAD",
            "",
        )

        stock = values.get(
            "STOCK",
            "",
        )

        chunk = {
            "chunk_id": (
                f"{document_id}-T{idx:04d}"
            ),
            "document_id": document_id,
            "title": title,
            "source_file": source_file,
            "document_type": document_type,
            "section": row.sheet_or_page,
            "chunk_index": idx,
            "text": row.to_semantic_text(),
            "source_status": source_status,
            "access_level": access_level,
            "document_date": document_date,
            "version": version,
            "file_hash": file_hash,
            "ingested_at": ingested_at,
            "content_mode": "structured_table_row",
            "table_row_index": row.row_index,
            "item": item_value,
            "code": code_value,
            "description": description,
            "brand": brand,
            "model": model,
            "quantity": quantity,
            "stock": stock,
        }

        chunks.append(
            chunk
        )

    return chunks
