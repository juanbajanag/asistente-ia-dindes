from __future__ import annotations

from datetime import datetime
from pathlib import Path
import csv

VALID_MANAGEMENT_STATUS = [
    "Pendiente",
    "En revisión",
    "Aprobado",
    "No aprobado",
    "Gestionado",
]

FIELDNAMES = [
    "item",
    "description",
    "brand",
    "model",
    "operational_priority",
    "management_status",
    "responsible",
    "decision_notes",
    "updated_at",
]


def _clean(value) -> str:
    return " ".join(str(value or "").split()).strip()


class ReplenishmentDecisionStore:
    def __init__(self, path, audit_store=None):
        self.path = Path(path)
        self.audit_store = audit_store

    def load(self):
        if not self.path.exists():
            return {}

        out = {}
        with self.path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = _clean(row.get("item"))
                if item:
                    out[item] = {
                        key: _clean(row.get(key))
                        for key in FIELDNAMES
                    }
        return out

    def upsert_many(self, rows):
        current = self.load()
        changed = 0

        for row in rows:
            item = _clean(
                row.get("item")
                or row.get("Ítem")
            )
            if not item:
                continue

            status = _clean(
                row.get("management_status")
                or row.get("Estado gestión")
                or "Pendiente"
            )
            if status not in VALID_MANAGEMENT_STATUS:
                status = "Pendiente"

            payload = {
                "item": item,
                "description": _clean(
                    row.get("description")
                    or row.get("Descripción")
                ),
                "brand": _clean(
                    row.get("brand")
                    or row.get("Marca")
                ),
                "model": _clean(
                    row.get("model")
                    or row.get("Modelo")
                ),
                "operational_priority": _clean(
                    row.get("operational_priority")
                    or row.get("Prioridad operativa")
                ),
                "management_status": status,
                "responsible": _clean(
                    row.get("responsible")
                    or row.get("Responsable")
                ),
                "decision_notes": _clean(
                    row.get("decision_notes")
                    or row.get("Observación decisión")
                ),
                "updated_at": datetime.now().isoformat(
                    timespec="microseconds"
                ),
            }

            previous = current.get(item)
            comparable_previous = None
            if previous:
                comparable_previous = dict(previous)
                comparable_previous["updated_at"] = payload["updated_at"]

            if comparable_previous != payload:
                previous_status = (
                    previous.get("management_status")
                    if previous
                    else "Pendiente"
                )

                if self.audit_store is not None:
                    self.audit_store.append_event(
                        item=item,
                        description=payload["description"],
                        brand=payload["brand"],
                        model=payload["model"],
                        operational_priority=payload[
                            "operational_priority"
                        ],
                        previous_status=previous_status,
                        new_status=payload[
                            "management_status"
                        ],
                        responsible=payload[
                            "responsible"
                        ],
                        decision_notes=payload[
                            "decision_notes"
                        ],
                        timestamp=payload[
                            "updated_at"
                        ],
                    )

                current[item] = payload
                changed += 1

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=FIELDNAMES,
            )
            writer.writeheader()
            for item in sorted(
                current,
                key=lambda x: (
                    len(str(x)),
                    str(x),
                ),
            ):
                writer.writerow(
                    current[item]
                )

        return changed

    def enrich_rows(self, rows):
        saved = self.load()
        out = []

        for row in rows:
            item = _clean(
                row.get("Ítem")
            )
            saved_row = saved.get(
                item,
                {},
            )

            enriched = dict(row)
            enriched["Estado gestión"] = (
                saved_row.get(
                    "management_status"
                )
                or "Pendiente"
            )
            enriched["Responsable"] = (
                saved_row.get(
                    "responsible"
                )
                or ""
            )
            enriched["Observación decisión"] = (
                saved_row.get(
                    "decision_notes"
                )
                or ""
            )
            enriched["Última actualización"] = (
                saved_row.get(
                    "updated_at"
                )
                or ""
            )
            out.append(enriched)

        return out

    def summary(self, rows):
        counts = {
            status: 0
            for status in VALID_MANAGEMENT_STATUS
        }

        for row in self.enrich_rows(rows):
            status = row.get(
                "Estado gestión",
                "Pendiente",
            )
            counts[status] = (
                counts.get(status, 0)
                + 1
            )

        return counts
