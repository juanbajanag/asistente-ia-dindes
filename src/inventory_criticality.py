"""
inventory_criticality.py
------------------------
Fase 9.4 — Priorización por criticidad operativa.

Principios:
- No infiere criticidad con IA.
- No asigna automáticamente criticidad a partir de la descripción.
- La criticidad debe ser definida por un usuario autorizado.
- Si un artículo no ha sido clasificado, se mantiene como "No definida".
- La prioridad de stock de la Fase 9.3 se conserva por separado.

El catálogo se almacena localmente en CSV para el MVP.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path


VALID_CRITICALITIES = (
    "No definida",
    "Baja",
    "Media",
    "Alta",
)


@dataclass(frozen=True)
class CriticalitySummary:
    high: int
    medium: int
    low: int
    undefined: int


def _clean(value) -> str:
    return " ".join(str(value or "").split()).strip()


def make_record_key(row: dict) -> str:
    """
    Genera una clave estable a partir de los valores normalizados del registro.
    El ítem se conserva, pero no se usa solo porque algunos registros carecen
    de número de ítem.
    """
    raw = "|".join(
        [
            _clean(row.get("Ítem")),
            _clean(row.get("Descripción")).upper(),
            _clean(row.get("Marca")).upper(),
            _clean(row.get("Modelo")).upper(),
        ]
    )
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    item = _clean(row.get("Ítem")) or "SINITEM"
    return f"{item}-{digest}"


def operational_priority(
    stock_priority: str,
    criticality: str,
) -> str:
    """
    Combina la prioridad cuantitativa de stock con la criticidad autorizada.

    Si la criticidad no está definida, NO se fabrica una prioridad ajustada.
    """
    stock_priority = _clean(stock_priority)
    criticality = _clean(criticality)

    if criticality not in {"Alta", "Media", "Baja"}:
        return "Pendiente de criticidad"

    matrix = {
        "Alta": {
            "Urgente": "Crítica",
            "Alta": "Muy alta",
            "Media": "Alta",
            "Normal": "Normal",
            "Revisar": "Revisar",
        },
        "Media": {
            "Urgente": "Muy alta",
            "Alta": "Alta",
            "Media": "Media",
            "Normal": "Normal",
            "Revisar": "Revisar",
        },
        "Baja": {
            "Urgente": "Alta",
            "Alta": "Media",
            "Media": "Baja",
            "Normal": "Normal",
            "Revisar": "Revisar",
        },
    }
    return matrix[criticality].get(
        stock_priority,
        "Revisar",
    )


class InventoryCriticality:
    FIELDNAMES = [
        "record_key",
        "Ítem",
        "Descripción",
        "Marca",
        "Modelo",
        "Criticidad",
        "Impacto operativo",
        "Justificación",
    ]

    def __init__(
        self,
        rows: list[dict],
        catalog_path: str | Path,
    ):
        self.rows = list(rows)
        self.catalog_path = Path(catalog_path)
        self.catalog_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._catalog = self._load_catalog()
        self._sync_catalog()

    def _load_catalog(self) -> dict[str, dict]:
        if not self.catalog_path.exists():
            return {}

        result = {}
        with self.catalog_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                key = _clean(row.get("record_key"))
                if not key:
                    continue

                criticality = _clean(
                    row.get("Criticidad")
                )
                if criticality not in VALID_CRITICALITIES:
                    criticality = "No definida"

                result[key] = {
                    "record_key": key,
                    "Ítem": _clean(row.get("Ítem")),
                    "Descripción": _clean(
                        row.get("Descripción")
                    ),
                    "Marca": _clean(row.get("Marca")),
                    "Modelo": _clean(row.get("Modelo")),
                    "Criticidad": criticality,
                    "Impacto operativo": _clean(
                        row.get("Impacto operativo")
                    ),
                    "Justificación": _clean(
                        row.get("Justificación")
                    ),
                }
        return result

    def _sync_catalog(self) -> None:
        changed = False

        for source_row in self.rows:
            key = make_record_key(source_row)

            if key in self._catalog:
                # Refrescar datos descriptivos sin alterar clasificación.
                entry = self._catalog[key]
                for field in [
                    "Ítem",
                    "Descripción",
                    "Marca",
                    "Modelo",
                ]:
                    value = _clean(source_row.get(field))
                    if entry.get(field) != value:
                        entry[field] = value
                        changed = True
                continue

            self._catalog[key] = {
                "record_key": key,
                "Ítem": _clean(source_row.get("Ítem")),
                "Descripción": _clean(
                    source_row.get("Descripción")
                ),
                "Marca": _clean(source_row.get("Marca")),
                "Modelo": _clean(source_row.get("Modelo")),
                "Criticidad": "No definida",
                "Impacto operativo": "",
                "Justificación": "",
            }
            changed = True

        if changed or not self.catalog_path.exists():
            self.save_catalog(
                list(self._catalog.values())
            )

    def catalog_rows(self) -> list[dict]:
        order = {
            "Alta": 0,
            "Media": 1,
            "Baja": 2,
            "No definida": 3,
        }
        return sorted(
            [dict(row) for row in self._catalog.values()],
            key=lambda row: (
                order.get(row.get("Criticidad"), 9),
                str(row.get("Marca", "")),
                str(row.get("Descripción", "")),
            ),
        )

    def save_catalog(
        self,
        rows: list[dict],
    ) -> None:
        normalized = []

        for row in rows:
            key = _clean(row.get("record_key"))
            if not key:
                continue

            criticality = _clean(
                row.get("Criticidad")
            )
            if criticality not in VALID_CRITICALITIES:
                criticality = "No definida"

            normalized.append(
                {
                    "record_key": key,
                    "Ítem": _clean(row.get("Ítem")),
                    "Descripción": _clean(
                        row.get("Descripción")
                    ),
                    "Marca": _clean(row.get("Marca")),
                    "Modelo": _clean(row.get("Modelo")),
                    "Criticidad": criticality,
                    "Impacto operativo": _clean(
                        row.get("Impacto operativo")
                    ),
                    "Justificación": _clean(
                        row.get("Justificación")
                    ),
                }
            )

        with self.catalog_path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=self.FIELDNAMES,
            )
            writer.writeheader()
            writer.writerows(normalized)

        self._catalog = {
            row["record_key"]: row
            for row in normalized
        }

    def enrich_row(
        self,
        row: dict,
        stock_priority: str | None = None,
    ) -> dict:
        out = dict(row)
        key = make_record_key(row)
        entry = self._catalog.get(
            key,
            {},
        )

        criticality = entry.get(
            "Criticidad",
            "No definida",
        )

        out["record_key"] = key
        out["Criticidad"] = criticality
        out["Impacto operativo"] = entry.get(
            "Impacto operativo",
            "",
        )
        out["Justificación criticidad"] = entry.get(
            "Justificación",
            "",
        )

        if stock_priority is None:
            stock_priority = out.get(
                "Prioridad",
                "",
            )

        out["Prioridad stock"] = stock_priority
        out["Prioridad operativa"] = (
            operational_priority(
                stock_priority,
                criticality,
            )
        )
        return out

    def enrich_rows(
        self,
        rows: list[dict],
    ) -> list[dict]:
        return [
            self.enrich_row(
                row,
                stock_priority=row.get(
                    "Prioridad",
                    "",
                ),
            )
            for row in rows
        ]

    def summary(self) -> CriticalitySummary:
        counts = {
            "Alta": 0,
            "Media": 0,
            "Baja": 0,
            "No definida": 0,
        }

        for row in self.catalog_rows():
            value = row.get(
                "Criticidad",
                "No definida",
            )
            counts[value] = counts.get(
                value,
                0,
            ) + 1

        return CriticalitySummary(
            high=counts["Alta"],
            medium=counts["Media"],
            low=counts["Baja"],
            undefined=counts["No definida"],
        )

    def classified_count(self) -> int:
        summary = self.summary()
        return (
            summary.high
            + summary.medium
            + summary.low
        )
