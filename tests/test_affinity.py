"""Tests de `core.domain.affinity` con casos fijos y reproducibles.

Los valores esperados se calculan manualmente contra la rúbrica documentada en SKILL.md
del clasificador. Si los weights o la rúbrica cambian, estos tests fallan explícitamente.
"""

from core.domain.affinity import score
from core.domain.recipe import Recipe
from core.domain.taste_profile import TasteProfile

# Perfil de referencia idéntico al preferences.json semilla.
PROFILE = TasteProfile(
    loved_cuisines=["italiana", "japonesa"],
    avoided_ingredients=["cilantro"],
    diet_constraints=[],
    weights={"cuisine": 0.3, "main_ingredients": 0.3, "diet_tags": 0.2, "difficulty": 0.1, "time": 0.1},
)


def _recipe(**kw) -> Recipe:
    return Recipe.new("Test", **kw)


# --- cuisine ---

def test_cuisine_amada_suma_maximo():
    r = _recipe(cuisine="italiana", main_ingredients=["pasta"], difficulty="media", time_total_min=30)
    # cuisine=1.0, main_ing=1.0(no avoided), diet=1.0(sin constraints), diff=0.8, time=1.0
    # = (0.3*1 + 0.3*1 + 0.2*1 + 0.1*0.8 + 0.1*1) / 1.0 = 0.98
    assert score(r, PROFILE) == 0.98


def test_cuisine_no_amada_penaliza():
    r = _recipe(cuisine="mexicana", main_ingredients=["pollo"], difficulty="baja", time_total_min=30)
    # cuisine=0.0, main_ing=1.0, diet=1.0, diff=1.0, time=1.0
    # = (0 + 0.3 + 0.2 + 0.1 + 0.1) / 1.0 = 0.7
    assert score(r, PROFILE) == 0.7


def test_cuisine_desconocida_neutral():
    r = _recipe(cuisine=None, main_ingredients=["pollo"], difficulty="baja", time_total_min=30)
    # cuisine=0.5, main_ing=1.0, diet=1.0, diff=1.0, time=1.0
    # = (0.15 + 0.3 + 0.2 + 0.1 + 0.1) = 0.85
    assert score(r, PROFILE) == 0.85


# --- main_ingredients (avoided) ---

def test_ingrediente_avoided_baja_score():
    r = _recipe(cuisine="italiana", main_ingredients=["cilantro", "pasta"], difficulty="baja", time_total_min=30)
    # main_ing: 1/2 ok = 0.5
    # = (0.3*1 + 0.3*0.5 + 0.2*1 + 0.1*1 + 0.1*1) = 0.3+0.15+0.2+0.1+0.1 = 0.85
    assert score(r, PROFILE) == 0.85


def test_todos_avoided_ingredientes():
    r = _recipe(cuisine="italiana", main_ingredients=["cilantro"], difficulty="baja", time_total_min=30)
    # main_ing=0.0
    # = (0.3 + 0 + 0.2 + 0.1 + 0.1) = 0.7
    assert score(r, PROFILE) == 0.7


# --- difficulty ---

def test_difficulty_alta_penaliza():
    r = _recipe(cuisine="italiana", main_ingredients=["pasta"], difficulty="alta", time_total_min=30)
    # diff=0.5
    # = (0.3 + 0.3 + 0.2 + 0.05 + 0.1) = 0.95
    assert score(r, PROFILE) == 0.95


# --- time ---

def test_tiempo_largo_penaliza():
    r = _recipe(cuisine="italiana", main_ingredients=["pasta"], difficulty="baja", time_total_min=120)
    # time=0.2
    # = (0.3 + 0.3 + 0.2 + 0.1 + 0.02) = 0.92
    assert score(r, PROFILE) == 0.92


def test_tiempo_intermedio_interpolado():
    r = _recipe(cuisine="italiana", main_ingredients=["pasta"], difficulty="baja", time_total_min=75)
    # time: 1 - (75-30)/(90)*0.8 = 1 - 45/90*0.8 = 1 - 0.4 = 0.6
    # = (0.3 + 0.3 + 0.2 + 0.1 + 0.06) = 0.96
    assert score(r, PROFILE) == 0.96


def test_sin_datos_usa_neutrales():
    """Sin ningún parámetro: todos los scorers devuelven su valor neutral."""
    r = _recipe()
    # cuisine=0.5, main_ing=0.5(vacío), diet=1.0, diff=0.7(None), time=0.6(None)
    # = (0.15 + 0.15 + 0.2 + 0.07 + 0.06) = 0.63
    assert score(r, PROFILE) == 0.63


def test_sin_pesos_devuelve_cero():
    perfil_vacio = TasteProfile(
        loved_cuisines=[], avoided_ingredients=[], diet_constraints=[],
        weights={},
    )
    assert score(_recipe(cuisine="italiana"), perfil_vacio) == 0.0


def test_score_dentro_de_rango():
    """El score siempre cae en [0.0, 1.0]."""
    casos = [
        _recipe(cuisine="italiana", main_ingredients=["pasta", "cilantro"], difficulty="alta", time_total_min=150),
        _recipe(cuisine="japonesa", difficulty="baja", time_total_min=10),
        _recipe(),
    ]
    for r in casos:
        s = score(r, PROFILE)
        assert 0.0 <= s <= 1.0
