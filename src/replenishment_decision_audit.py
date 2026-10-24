from __future__ import annotations

from datetime import datetime, date, time
from pathlib import Path
import csv
import uuid


AUDIT_FIELDS = [
    "event_id",
    "timestamp",
    "item",
    "description",
    "brand",
    "model",
    "operational_priority",
    "previous_status",
    "new_status",
    "responsible",
    "decision_notes",
]


def _clean(value) -> str:
    return " ".join(str(value or "").split()).strip()


def parse_timestamp(value):
    text = _clean(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None


def format_timestamp(value) -> str:
    dt = parse_timestamp(value)
    if dt is None:
        return _clean(value)
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def transition_label(row: dict) -> str:
    previous = _clean(row.get("previous_status"))
    new = _clean(row.get("new_status"))
    if previous or new:
        return f"{previous or 'Sin estado'} → {new or 'Sin estado'}"
    return ""


class ReplenishmentDecisionAuditStore:
    def __init__(self, path):
        self.path = Path(path)

    def append_event(
        self,
        *,
        item,
        description="",
        brand="",
        model="",
        operational_priority="",
        previous_status="",
        new_status="",
        responsible="",
        decision_notes="",
        timestamp=None,
    ):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        exists = self.path.exists()

        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": (
                timestamp
                or datetime.now().isoformat(
                    timespec="microseconds"
                )
            ),
            "item": _clean(item),
            "description": _clean(description),
            "brand": _clean(brand),
            "model": _clean(model),
            "operational_priority": _clean(
                operational_priority
            ),
            "previous_status": _clean(
                previous_status
            ),
            "new_status": _clean(
                new_status
            ),
            "responsible": _clean(
                responsible
            ),
            "decision_notes": _clean(
                decision_notes
            ),
        }

        with self.path.open(
            "a",
            encoding="utf-8-sig",
            newline="",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=AUDIT_FIELDS,
            )
            if not exists:
                writer.writeheader()
            writer.writerow(event)

        return event

    def load(self):
        if not self.path.exists():
            return []

        with self.path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as f:
            rows = list(csv.DictReader(f))

        rows.sort(
            key=lambda row: (
                row.get("timestamp", ""),
                row.get("event_id", ""),
            ),
            reverse=True,
        )

        return rows

    def count(self):
        return len(self.load())

    @staticmethod
    def filter_events(
        events,
        *,
        start_date=None,
        end_date=None,
        new_status=None,
        responsible=None,
        brand=None,
        item=None,
        transition=None,
        search=None,
    ):
        filtered = list(events)

        if start_date:
            start_dt = datetime.combine(
                start_date,
                time.min,
            )
            filtered = [
                row
                for row in filtered
                if (
                    parse_timestamp(
                        row.get("timestamp")
                    ) is not None
                    and parse_timestamp(
                        row.get("timestamp")
                    ) >= start_dt
                )
            ]

        if end_date:
            end_dt = datetime.combine(
                end_date,
                time.max,
            )
            filtered = [
                row
                for row in filtered
                if (
                    parse_timestamp(
                        row.get("timestamp")
                    ) is not None
                    and parse_timestamp(
                        row.get("timestamp")
                    ) <= end_dt
                )
            ]

        if new_status and new_status != "Todos":
            filtered = [
                row
                for row in filtered
                if _clean(
                    row.get("new_status")
                ) == _clean(new_status)
            ]

        if responsible and responsible != "Todos":
            filtered = [
                row
                for row in filtered
                if _clean(
                    row.get("responsible")
                ) == _clean(responsible)
            ]

        if brand and brand != "Todas":
            filtered = [
                row
                for row in filtered
                if _clean(
                    row.get("brand")
                ) == _clean(brand)
            ]

        if item:
            needle_item = _clean(item)
            filtered = [
                row
                for row in filtered
                if _clean(
                    row.get("item")
                ) == needle_item
            ]

        if transition and transition != "Todas":
            filtered = [
                row
                for row in filtered
                if transition_label(row)
                == transition
            ]

        if search:
            needle = _clean(search).lower()

            def haystack(row):
                fields = [
                    "description",
                    "brand",
                    "model",
                    "operational_priority",
                    "previous_status",
                    "new_status",
                    "responsible",
                    "decision_notes",
                ]
                return " ".join(
                    _clean(
                        row.get(field)
                    )
                    for field in fields
                ).lower()

            filtered = [
                row
                for row in filtered
                if needle in haystack(row)
            ]

        return filtered

    @staticmethod
    def summary(events):
        events = list(events)

        transitions = {}
        new_status = {}
        responsible = {}

        unique_items = set()

        for row in events:
            item = _clean(
                row.get("item")
            )
            if item:
                unique_items.add(item)

            transition = transition_label(row)
            if transition:
                transitions[transition] = (
                    transitions.get(
                        transition,
                        0,
                    )
                    + 1
                )

            status = _clean(
                row.get("new_status")
            )
            if status:
                new_status[status] = (
                    new_status.get(
                        status,
                        0,
                    )
                    + 1
                )

            owner = _clean(
                row.get("responsible")
            )
            if owner:
                responsible[owner] = (
                    responsible.get(
                        owner,
                        0,
                    )
                    + 1
                )

        return {
            "events": len(events),
            "unique_items": len(
                unique_items
            ),
            "approvals": new_status.get(
                "Aprobado",
                0,
            ),
            "managed": new_status.get(
                "Gestionado",
                0,
            ),
            "transitions": transitions,
            "new_status": new_status,
            "responsible": responsible,
        }
