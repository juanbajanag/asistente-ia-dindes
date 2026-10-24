"""
audit.py
--------
Logging estructurado local para el MVP.

Registra:
- usuario;
- rol;
- pregunta;
- abstención;
- fuentes;
- timestamp;
- duración;
- evento.

No registra contraseñas ni credenciales.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from time import perf_counter


AUDIT_FIELDS = [
    "timestamp",
    "event",
    "username",
    "role",
    "question",
    "abstained",
    "retrieval_count",
    "source_ids",
    "duration_seconds",
    "detail",
]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


def write_audit_event(
    path: Path,
    *,
    event: str,
    username: str,
    role: str,
    question: str = "",
    abstained: bool | str = "",
    retrieval_count: int | str = "",
    source_ids: list[str] | None = None,
    duration_seconds: float | str = "",
    detail: str = "",
) -> None:
    ensure_parent(path)

    exists = path.exists()

    with path.open(
        "a",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=AUDIT_FIELDS,
        )

        if not exists:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(
                    timespec="seconds"
                ),
                "event": event,
                "username": username,
                "role": role,
                "question": question,
                "abstained": abstained,
                "retrieval_count": retrieval_count,
                "source_ids": ";".join(
                    source_ids or []
                ),
                "duration_seconds": (
                    f"{duration_seconds:.4f}"
                    if isinstance(
                        duration_seconds,
                        float,
                    )
                    else duration_seconds
                ),
                "detail": detail,
            }
        )


class AuditTimer:
    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        self.elapsed = (
            perf_counter()
            - self.start
        )
