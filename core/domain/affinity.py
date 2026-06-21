"""Cálculo determinista de `affinity_score` entre una `Recipe` y un `TasteProfile`.

Rúbrica documentada (reproduce el mismo número entre ejecuciones y modelos):

  score = sum(weight[dim] * match[dim]) / sum(weight[dim])      [0.0 – 1.0]

Dimensiones (CLAUDE.md §4 / preferences.json):

  cuisine          → 1.0 si recipe.cuisine ∈ loved_cuisines; 0.0 si no
  main_ingredients → fracción de main_ingredients que NO son avoided_ingredients
  diet_tags        → 1.0 si recipe.diet_tags no viola diet_constraints (o no hay constraints)
  difficulty       → penalización: "baja"→1.0, "media"→0.8, "alta"→0.5, None→0.7
  time             → escala lineal inversa: ≤30 min→1.0, ≥120 min→0.2, None→0.6

Todos los matches caen entre 0.0 y 1.0.  El score final se redondea a 4 decimales.
"""

from __future__ import annotations

from core.domain.recipe import Recipe
from core.domain.taste_profile import TasteProfile

_DIFFICULTY_SCORE: dict[str | None, float] = {
    "baja": 1.0,
    "media": 0.8,
    "alta": 0.5,
    None: 0.7,
}


def _score_cuisine(recipe: Recipe, profile: TasteProfile) -> float:
    if not recipe.cuisine:
        return 0.5  # desconocida: neutral
    return 1.0 if recipe.cuisine.lower() in [c.lower() for c in profile.loved_cuisines] else 0.0


def _score_main_ingredients(recipe: Recipe, profile: TasteProfile) -> float:
    if not recipe.main_ingredients:
        return 0.5  # sin datos: neutral
    avoided = {a.lower() for a in profile.avoided_ingredients}
    ok = sum(1 for i in recipe.main_ingredients if i.lower() not in avoided)
    return ok / len(recipe.main_ingredients)


def _score_diet_tags(recipe: Recipe, profile: TasteProfile) -> float:
    if not profile.diet_constraints:
        return 1.0  # sin restricciones: siempre ok
    constraints = {c.lower() for c in profile.diet_constraints}
    # La receta satisface una restricción si ese tag aparece en sus diet_tags.
    tags = {t.lower() for t in recipe.diet_tags}
    satisfied = constraints & tags
    return len(satisfied) / len(constraints)


def _score_difficulty(recipe: Recipe, _profile: TasteProfile) -> float:
    return _DIFFICULTY_SCORE.get(recipe.difficulty, 0.7)


def _score_time(recipe: Recipe, _profile: TasteProfile) -> float:
    t = recipe.time_total_min
    if t is None:
        return 0.6
    if t <= 30:
        return 1.0
    if t >= 120:
        return 0.2
    # Interpolación lineal inversa entre 30 y 120 min.
    return 1.0 - (t - 30) / (120 - 30) * 0.8


_SCORERS = {
    "cuisine": _score_cuisine,
    "main_ingredients": _score_main_ingredients,
    "diet_tags": _score_diet_tags,
    "difficulty": _score_difficulty,
    "time": _score_time,
}


def score(recipe: Recipe, profile: TasteProfile) -> float:
    """Devuelve el affinity_score (0.0–1.0) entre la receta y el perfil.

    Usa los pesos de `profile.weights`; ignora dimensiones sin peso o con peso 0.
    El resultado se redondea a 4 decimales para diffs estables en JSON.
    """
    total_weight = 0.0
    weighted_sum = 0.0
    for dim, fn in _SCORERS.items():
        w = profile.weights.get(dim, 0.0)
        if w <= 0:
            continue
        weighted_sum += w * fn(recipe, profile)
        total_weight += w
    if total_weight == 0:
        return 0.0
    return round(weighted_sum / total_weight, 4)
