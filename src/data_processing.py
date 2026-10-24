"""
Carga y normalización de los datasets sample del Asistente IA DINDES.
Fase 1.1: incorpora metadatos útiles para filtros explícitos.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
import pandas as pd

@dataclass
class KnowledgeRecord:
    record_id: str
    source_type: str
    title: str
    text: str
    source_file: str
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)

def _safe_str(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()

def load_document_dataset(csv_path: str | Path) -> list[KnowledgeRecord]:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {csv_path}")
    df = pd.read_csv(csv_path)

    required = {
        "document_id","project_id","document_type","title","responsible_unit",
        "document_date","version","section","chunk_id","text","source_status","access_level"
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {sorted(missing)}")

    records = []
    for _, row in df.iterrows():
        title = _safe_str(row["title"])
        searchable_text = (
            f"Título: {title}. "
            f"Proyecto: {_safe_str(row['project_id'])}. "
            f"Tipo de documento: {_safe_str(row['document_type'])}. "
            f"Sección: {_safe_str(row['section'])}. "
            f"Estado de la fuente: {_safe_str(row['source_status'])}. "
            f"Nivel de acceso: {_safe_str(row['access_level'])}. "
            f"Versión: {_safe_str(row['version'])}. "
            f"Fecha: {_safe_str(row['document_date'])}. "
            f"Contenido: {_safe_str(row['text'])}"
        )

        metadata = {
            "document_id": _safe_str(row["document_id"]),
            "project_id": _safe_str(row["project_id"]),
            "document_type": _safe_str(row["document_type"]),
            "responsible_unit": _safe_str(row["responsible_unit"]),
            "document_date": _safe_str(row["document_date"]),
            "version": _safe_str(row["version"]),
            "section": _safe_str(row["section"]),
            "chunk_id": _safe_str(row["chunk_id"]),
            "source_status": _safe_str(row["source_status"]).lower(),
            "access_level": _safe_str(row["access_level"]).lower(),
        }

        records.append(KnowledgeRecord(
            record_id=metadata["chunk_id"] or metadata["document_id"],
            source_type="document",
            title=title,
            text=searchable_text,
            source_file=csv_path.name,
            metadata=metadata
        ))
    return records

def load_inventory_dataset(csv_path: str | Path) -> list[KnowledgeRecord]:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {csv_path}")
    df = pd.read_csv(csv_path)

    required = {
        "codigo","descripcion","categoria","marca","modelo","cantidad","unidad",
        "estado","ubicacion","responsable","fecha_actualizacion"
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {sorted(missing)}")

    records = []
    for _, row in df.iterrows():
        code = _safe_str(row["codigo"])
        description = _safe_str(row["descripcion"])
        searchable_text = (
            f"Código: {code}. "
            f"Descripción: {description}. "
            f"Categoría: {_safe_str(row['categoria'])}. "
            f"Marca: {_safe_str(row['marca'])}. "
            f"Modelo: {_safe_str(row['modelo'])}. "
            f"Cantidad: {_safe_str(row['cantidad'])} {_safe_str(row['unidad'])}. "
            f"Estado: {_safe_str(row['estado'])}. "
            f"Ubicación: {_safe_str(row['ubicacion'])}. "
            f"Responsable: {_safe_str(row['responsable'])}. "
            f"Fecha de actualización: {_safe_str(row['fecha_actualizacion'])}."
        )

        metadata = {
            "codigo": code,
            "descripcion": description,
            "categoria": _safe_str(row["categoria"]),
            "marca": _safe_str(row["marca"]),
            "modelo": _safe_str(row["modelo"]),
            "cantidad": _safe_str(row["cantidad"]),
            "unidad": _safe_str(row["unidad"]),
            "estado": _safe_str(row["estado"]).lower(),
            "ubicacion": _safe_str(row["ubicacion"]),
            "responsable": _safe_str(row["responsable"]),
            "fecha_actualizacion": _safe_str(row["fecha_actualizacion"]),
        }

        records.append(KnowledgeRecord(
            record_id=code,
            source_type="inventory",
            title=description or code,
            text=searchable_text,
            source_file=csv_path.name,
            metadata=metadata
        ))
    return records

def build_sample_corpus(data_dir: str | Path) -> list[KnowledgeRecord]:
    data_dir = Path(data_dir)
    records = []
    records.extend(load_document_dataset(
        data_dir / "Dataset_1_Documentacion_Tecnica_DINDES_Sample.csv"
    ))
    records.extend(load_inventory_dataset(
        data_dir / "Dataset_2_Inventario_Institucional_DINDES_Sample.csv"
    ))
    return records

def records_to_dataframe(records: Iterable[KnowledgeRecord]) -> pd.DataFrame:
    return pd.DataFrame([r.to_dict() for r in records])
