"""Entidad de dominio `TasteProfile`: el perfil de gustos del autor.

Espeja `preferences.json` (CLAUDE.md §4). En la Fase 0 es solo una estructura de datos con
(de)serialización; el cálculo de `affinity_score` contra este perfil llega en la Fase 2
(`core/domain/affinity.py`). No implementar scoring aquí todavía.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TasteProfile:
    loved_cuisines: list[str] = field(default_factory=list)
    avoided_ingredients: list[str] = field(default_factory=list)
    diet_constraints: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> TasteProfile:
        return cls(
            loved_cuisines=list(d.get("loved_cuisines", [])),
            avoided_ingredients=list(d.get("avoided_ingredients", [])),
            diet_constraints=list(d.get("diet_constraints", [])),
            weights=dict(d.get("weights", {})),
        )

    def to_dict(self) -> dict:
        return {
            "loved_cuisines": list(self.loved_cuisines),
            "avoided_ingredients": list(self.avoided_ingredients),
            "diet_constraints": list(self.diet_constraints),
            "weights": dict(self.weights),
        }
