
"""
corpus_builder.py
-----------------
Fase 7.9.2 — Normalización del corpus.

Objetivos:
1. Preservar TODO el metadata de knowledge_chunks.jsonl.
2. Mantener content_mode="structured_table_row".
3. Conservar item, description, brand, model, quantity y stock.
4. Evitar que los registros estructurados dependan del fallback textual.
5. Mantener compatibilidad con los datasets sample existentes.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CorpusRecord:
    record_id: str
    source_type: str
    title: str
    text: str
    source_file: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []

    if not path.exists():
        return rows

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return rows


def _load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def _clean(value) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _metadata_from_raw_chunk(row: dict) -> dict:
    """
    Conserva todos los campos del JSONL.

    Esto es deliberado: los motores posteriores necesitan metadata como
    content_mode, stock, quantity, brand, model, item, etc.
    """
    metadata = dict(row)

    # Alias normalizados para compatibilidad entre versiones.
    alias_pairs = {
        "item": ("item", "ITEM"),
        "description": (
            "description",
            "descripcion",
            "DESCRIPCION",
        ),
        "brand": (
            "brand",
            "marca",
            "MARCA",
        ),
        "model": (
            "model",
            "modelo",
            "MODELO",
        ),
        "quantity": (
            "quantity",
            "cantidad",
            "CANTIDAD",
        ),
        "stock": (
            "stock",
            "STOCK",
        ),
    }

    for canonical, aliases in alias_pairs.items():
        if metadata.get(canonical) not in (None, ""):
            continue

        for alias in aliases:
            if row.get(alias) not in (None, ""):
                metadata[canonical] = row.get(alias)
                break

    metadata.setdefault(
        "document_id",
        row.get("document_id", ""),
    )

    metadata.setdefault(
        "chunk_id",
        row.get(
            "chunk_id",
            row.get("record_id", ""),
        ),
    )

    metadata.setdefault(
        "content_mode",
        row.get("content_mode", ""),
    )

    return metadata


def _private_chunk_to_record(row: dict) -> CorpusRecord:
    record_id = _clean(
        row.get("chunk_id")
        or row.get("record_id")
        or row.get("document_id")
    )

    source_type = _clean(
        row.get("source_type")
        or "document"
    )

    title = _clean(
        row.get("title")
        or row.get("document_id")
        or record_id
    )

    text = _clean(
        row.get("text")
    )

    source_file = _clean(
        row.get("source_file")
    )

    return CorpusRecord(
        record_id=record_id,
        source_type=source_type,
        title=title,
        text=text,
        source_file=source_file,
        metadata=_metadata_from_raw_chunk(row),
    )


def _sample_document_to_record(row: dict) -> CorpusRecord:
    record_id = _clean(
        row.get("chunk_id")
        or row.get("document_id")
    )

    document_id = _clean(
        row.get("document_id")
    )

    title = _clean(
        row.get("title")
    )

    text = _clean(
        row.get("text")
    )

    metadata = dict(row)
    metadata["document_id"] = document_id
    metadata.setdefault("chunk_id", record_id)
    metadata.setdefault("content_mode", "sample_document")

    return CorpusRecord(
        record_id=record_id,
        source_type="document",
        title=title,
        text=text,
        source_file=_clean(
            row.get("source_file")
        ),
        metadata=metadata,
    )


def _inventory_text(row: dict) -> str:
    fields = [
        ("Código", row.get("item_id") or row.get("inventory_id") or row.get("codigo")),
        ("Descripción", row.get("description") or row.get("descripcion")),
        ("Categoría", row.get("category") or row.get("categoria")),
        ("Marca", row.get("brand") or row.get("marca")),
        ("Modelo", row.get("model") or row.get("modelo")),
        ("Cantidad", row.get("quantity") or row.get("cantidad")),
        ("Estado", row.get("status") or row.get("estado")),
        ("Ubicación", row.get("location") or row.get("ubicacion")),
        ("Responsable", row.get("responsible") or row.get("responsable")),
        (
            "Fecha de actualización",
            row.get("updated_at")
            or row.get("update_date")
            or row.get("fecha_actualizacion"),
        ),
    ]

    parts = []

    for label, value in fields:
        value = _clean(value)

        if value:
            parts.append(
                f"{label}: {value}"
            )

    return ". ".join(parts) + ("." if parts else "")


def _sample_inventory_to_record(row: dict) -> CorpusRecord:
    record_id = _clean(
        row.get("item_id")
        or row.get("inventory_id")
        or row.get("codigo")
        or row.get("code")
    )

    title = _clean(
        row.get("description")
        or row.get("descripcion")
        or record_id
    )

    metadata = dict(row)
    metadata.setdefault("content_mode", "sample_inventory")

    return CorpusRecord(
        record_id=record_id,
        source_type="inventory",
        title=title,
        text=_inventory_text(row),
        source_file="",
        metadata=metadata,
    )


def _find_first_existing(
    data_dir: Path,
    names: list[str],
) -> Path | None:
    for name in names:
        path = data_dir / name

        if path.exists():
            return path

    return None


def build_complete_corpus(
    data_dir,
    include_sample: bool = True,
) -> list[CorpusRecord]:
    """
    Construye un único corpus.

    Orden:
      1) datasets sample, si include_sample=True
      2) knowledge_chunks.jsonl privado

    La deduplicación se realiza únicamente por record_id.
    """
    data_dir = Path(data_dir)

    records: list[CorpusRecord] = []

    if include_sample:
        doc_path = _find_first_existing(
            data_dir,
            [
                "Dataset_1_Documentacion_Tecnica_DINDES_Sample.csv",
                "dataset_1_documentacion_tecnica_dindes_sample.csv",
            ],
        )

        inventory_path = _find_first_existing(
            data_dir,
            [
                "Dataset_2_Inventario_Institucional_DINDES_Sample.csv",
                "dataset_2_inventario_institucional_dindes_sample.csv",
            ],
        )

        if doc_path:
            for row in _load_csv(doc_path):
                record = _sample_document_to_record(row)

                if record.record_id and record.text:
                    records.append(record)

        if inventory_path:
            for row in _load_csv(inventory_path):
                record = _sample_inventory_to_record(row)

                if record.record_id and record.text:
                    records.append(record)

    private_chunks_path = (
        data_dir
        / "private_ingested"
        / "knowledge_chunks.jsonl"
    )

    for row in _load_jsonl(private_chunks_path):
        record = _private_chunk_to_record(row)

        if record.record_id and record.text:
            records.append(record)

    # Deduplicación estable.
    deduped: dict[str, CorpusRecord] = {}

    for record in records:
        deduped[record.record_id] = record

    return list(deduped.values())
