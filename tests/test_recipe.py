"""Tests de la entidad `Recipe` (y `Ingredient`)."""

import uuid

from core.domain.recipe import Ingredient, Recipe


def test_round_trip_to_dict_from_dict(recipe_ejemplo: Recipe):
    """to_dict -> from_dict reconstruye una receta idéntica."""
    reconstruida = Recipe.from_dict(recipe_ejemplo.to_dict())
    assert reconstruida == recipe_ejemplo


def test_from_dict_con_minimo_aplica_defaults():
    """from_dict tolera el dict mínimo (id/slug/title) y rellena todo lo demás."""
    minimo = {"id": "abc", "slug": "tortilla", "title": "Tortilla"}
    r = Recipe.from_dict(minimo)
    assert r.language == "es"
    assert r.servings == 1
    assert r.ingredients == []
    assert r.steps == []
    assert r.affinity_score == 0.0
    assert r.my_rating is None
    assert r.classified_at is None
    assert r.tags == []
    # created_at se rellena aunque falte en el dict.
    assert r.created_at


def test_make_slug_quita_acentos_y_espacios():
    assert Recipe.make_slug("Pasta al Pesto") == "pasta-al-pesto"
    assert Recipe.make_slug("Ñoquis con Jamón") == "noquis-con-jamon"
    assert Recipe.make_slug("  Arroz   a la cubana!  ") == "arroz-a-la-cubana"


def test_new_genera_id_uuid_slug_y_created_at():
    r = Recipe.new("Pan de plátano")
    # id es un uuid4 válido.
    uuid.UUID(r.id)
    assert r.slug == "pan-de-platano"
    assert r.created_at
    assert r.title == "Pan de plátano"


def test_ingredient_round_trip():
    ing = Ingredient(name="sal", amount=None, unit=None)
    assert Ingredient.from_dict(ing.to_dict()) == ing
