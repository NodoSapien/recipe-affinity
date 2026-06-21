"""Entidad de dominio `Recipe` (y su `Ingredient`).

Núcleo estable de Clean Architecture: no importa adaptadores, Astro ni librerías de scraping.
La (de)serialización es 1:1 con el esquema documentado en `CLAUDE.md` §3, para que el JSON en
`recipes/<slug>.json` sea predecible y reproducible entre ejecuciones.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

# Vocabularios cerrados del esquema (ver CLAUDE.md §3).
Difficulty = Literal["baja", "media", "alta"]
MealType = Literal["desayuno", "almuerzo", "cena", "snack", "postre"]


def _now_iso() -> str:
    """Marca de tiempo ISO-8601 en UTC (con sufijo 'Z')."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class Ingredient:
    """Un ingrediente con cantidad opcional (algunas recetas no la especifican)."""

    name: str
    amount: float | None = None
    unit: str | None = None

    @classmethod
    def from_dict(cls, d: dict) -> Ingredient:
        return cls(
            name=d["name"],
            amount=d.get("amount"),
            unit=d.get("unit"),
        )

    def to_dict(self) -> dict:
        return {"name": self.name, "amount": self.amount, "unit": self.unit}


@dataclass
class Recipe:
    """Una receta. La clave natural es `slug` (= nombre de archivo en `recipes/`)."""

    id: str
    slug: str
    title: str
    source_url: str | None = None
    language: str = "es"
    servings: int = 1

    ingredients: list[Ingredient] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)

    # --- Parámetros (clasifican y filtran) ---
    time_total_min: int | None = None
    time_active_min: int | None = None
    difficulty: Difficulty | None = None
    cuisine: str | None = None
    meal_type: MealType | None = None
    diet_tags: list[str] = field(default_factory=list)
    main_ingredients: list[str] = field(default_factory=list)
    techniques: list[str] = field(default_factory=list)
    season: list[str] = field(default_factory=list)

    # --- Gustos ---
    affinity_score: float = 0.0  # lo calcula el clasificador (Fase 2)
    my_rating: int | None = None  # feedback manual del autor (1–5 o None)
    notes: str = ""

    # --- Sistema ---
    created_at: str = ""  # ISO-8601; se rellena en new()/from_dict si falta
    classified_at: str | None = None
    tags: list[str] = field(default_factory=list)

    @classmethod
    def new(cls, title: str, **kw) -> Recipe:
        """Crea una receta nueva: genera `id` (uuid4), `slug` desde el título y `created_at`=ahora.

        Cualquier campo del esquema puede pasarse como keyword (p. ej. `cuisine="italiana"`).
        """
        kw.setdefault("id", str(uuid.uuid4()))
        kw.setdefault("slug", cls.make_slug(title))
        kw.setdefault("created_at", _now_iso())
        return cls(title=title, **kw)

    @classmethod
    def from_dict(cls, data: dict) -> Recipe:
        """Construye una `Recipe` tolerando campos faltantes (aplica los defaults del esquema)."""
        return cls(
            id=data["id"],
            slug=data["slug"],
            title=data["title"],
            source_url=data.get("source_url"),
            language=data.get("language", "es"),
            servings=data.get("servings", 1),
            ingredients=[Ingredient.from_dict(i) for i in data.get("ingredients", [])],
            steps=list(data.get("steps", [])),
            time_total_min=data.get("time_total_min"),
            time_active_min=data.get("time_active_min"),
            difficulty=data.get("difficulty"),
            cuisine=data.get("cuisine"),
            meal_type=data.get("meal_type"),
            diet_tags=list(data.get("diet_tags", [])),
            main_ingredients=list(data.get("main_ingredients", [])),
            techniques=list(data.get("techniques", [])),
            season=list(data.get("season", [])),
            affinity_score=data.get("affinity_score", 0.0),
            my_rating=data.get("my_rating"),
            notes=data.get("notes", ""),
            created_at=data.get("created_at") or _now_iso(),
            classified_at=data.get("classified_at"),
            tags=list(data.get("tags", [])),
        )

    def to_dict(self) -> dict:
        """Serializa con el mismo orden de claves del esquema (CLAUDE.md §3)."""
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "source_url": self.source_url,
            "language": self.language,
            "servings": self.servings,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "steps": list(self.steps),
            "time_total_min": self.time_total_min,
            "time_active_min": self.time_active_min,
            "difficulty": self.difficulty,
            "cuisine": self.cuisine,
            "meal_type": self.meal_type,
            "diet_tags": list(self.diet_tags),
            "main_ingredients": list(self.main_ingredients),
            "techniques": list(self.techniques),
            "season": list(self.season),
            "affinity_score": self.affinity_score,
            "my_rating": self.my_rating,
            "notes": self.notes,
            "created_at": self.created_at,
            "classified_at": self.classified_at,
            "tags": list(self.tags),
        }

    @staticmethod
    def make_slug(title: str) -> str:
        """'Pasta al Pesto' -> 'pasta-al-pesto' (minúsculas, sin acentos, guiones)."""
        # Descompone acentos y descarta los diacríticos (á -> a, ñ -> n).
        normalized = unicodedata.normalize("NFKD", title)
        ascii_str = normalized.encode("ascii", "ignore").decode("ascii").lower()
        # Todo lo que no sea [a-z0-9] se vuelve separador; colapsa y recorta guiones.
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_str).strip("-")
        return slug
