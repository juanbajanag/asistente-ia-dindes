
"""
inventory_replenishment.py
--------------------------
Fase 9.3 — Gestión de reposición y alertas operativas.

Política provisional del MVP:
- "Cantidad" se usa como nivel objetivo de referencia.
- "Stock" es la existencia actual.
- La reposición sugerida = max(Cantidad - Stock, 0).
- La prioridad se calcula con la relación Stock/Cantidad.

No modifica el inventario fuente y no usa LLM.
"""

from __future__ import annotations

from dataclasses import dataclass

from .structured_query import as_number


@dataclass(frozen=True)
class ReplenishmentPolicy:
    critical_ratio: float = 0.25
    low_ratio: float = 0.50


class InventoryReplenishment:
    def __init__(
        self,
        rows: list[dict],
        policy: ReplenishmentPolicy | None = None,
    ):
        self.rows = list(rows)
        self.policy = policy or ReplenishmentPolicy()

    @staticmethod
    def _num(value):
        return as_number(value)

    @staticmethod
    def _pretty(value):
        if value is None:
            return ""
        if float(value).is_integer():
            return int(value)
        return round(float(value), 2)

    def classify_row(self, row: dict) -> dict:
        quantity = self._num(row.get("Cantidad"))
        stock = self._num(row.get("Stock"))

        out = dict(row)

        # Si faltan datos cuantitativos, no se inventa una política.
        if quantity is None or stock is None or quantity <= 0:
            out.update(
                {
                    "Estado reposición": "Sin datos",
                    "Prioridad": "Revisar",
                    "Cobertura stock %": "",
                    "Reposición sugerida": "",
                    "Motivo reposición": (
                        "Cantidad o stock insuficiente para calcular la política."
                    ),
                }
            )
            return out

        ratio = stock / quantity
        suggested = max(quantity - stock, 0)

        if stock <= 0:
            status = "Sin stock"
            priority = "Urgente"
            reason = "Stock igual a cero."
        elif ratio <= self.policy.critical_ratio:
            status = "Crítico"
            priority = "Alta"
            reason = (
                f"Cobertura ≤ {int(self.policy.critical_ratio * 100)}% "
                "de la cantidad objetivo."
            )
        elif ratio <= self.policy.low_ratio:
            status = "Bajo"
            priority = "Media"
            reason = (
                f"Cobertura ≤ {int(self.policy.low_ratio * 100)}% "
                "de la cantidad objetivo."
            )
        else:
            status = "Adecuado"
            priority = "Normal"
            reason = "Cobertura superior al umbral provisional de reposición."

        if stock >= quantity:
            suggested = 0

        out.update(
            {
                "Estado reposición": status,
                "Prioridad": priority,
                "Cobertura stock %": round(ratio * 100, 1),
                "Reposición sugerida": self._pretty(suggested),
                "Motivo reposición": reason,
            }
        )

        return out

    def evaluated_rows(self) -> list[dict]:
        return [
            self.classify_row(row)
            for row in self.rows
        ]

    def proposal_rows(
        self,
        include_medium: bool = True,
    ) -> list[dict]:
        allowed = {"Urgente", "Alta"}
        if include_medium:
            allowed.add("Media")

        rows = [
            row
            for row in self.evaluated_rows()
            if row.get("Prioridad") in allowed
            and self._num(row.get("Reposición sugerida")) not in (None, 0)
        ]

        order = {
            "Urgente": 0,
            "Alta": 1,
            "Media": 2,
            "Normal": 3,
            "Revisar": 4,
        }

        return sorted(
            rows,
            key=lambda row: (
                order.get(row.get("Prioridad"), 9),
                self._num(row.get("Stock")) or 0,
                str(row.get("Marca", "")),
                str(row.get("Descripción", "")),
            ),
        )

    def summary(self) -> dict:
        rows = self.evaluated_rows()

        def count_status(name):
            return sum(
                1
                for row in rows
                if row.get("Estado reposición") == name
            )

        proposal = self.proposal_rows(
            include_medium=True
        )

        units = sum(
            self._num(row.get("Reposición sugerida")) or 0
            for row in proposal
        )

        return {
            "Sin stock": count_status("Sin stock"),
            "Crítico": count_status("Crítico"),
            "Bajo": count_status("Bajo"),
            "Adecuado": count_status("Adecuado"),
            "Sin datos": count_status("Sin datos"),
            "Artículos a reponer": len(proposal),
            "Unidades sugeridas": int(units),
        }

    def priority_distribution(self) -> list[dict]:
        order = ["Urgente", "Alta", "Media", "Normal", "Revisar"]
        rows = self.evaluated_rows()

        return [
            {
                "Prioridad": priority,
                "Registros": sum(
                    1
                    for row in rows
                    if row.get("Prioridad") == priority
                ),
            }
            for priority in order
        ]

    def status_distribution(self) -> list[dict]:
        order = ["Sin stock", "Crítico", "Bajo", "Adecuado", "Sin datos"]
        rows = self.evaluated_rows()

        return [
            {
                "Estado": status,
                "Registros": sum(
                    1
                    for row in rows
                    if row.get("Estado reposición") == status
                ),
            }
            for status in order
        ]
