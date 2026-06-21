"""Tests de la entidad `TasteProfile` y su carga desde `preferences.json`."""

import json
from pathlib import Path

from core.domain.taste_profile import TasteProfile

PREFERENCES_PATH = Path(__file__).resolve().parent.parent / "preferences.json"


def test_from_dict_carga_preferences_json():
    """El preferences.json semilla se carga con cuisines y weights correctos."""
    data = json.loads(PREFERENCES_PATH.read_text(encoding="utf-8"))
    profile = TasteProfile.from_dict(data)

    assert "italiana" in profile.loved_cuisines
    assert "japonesa" in profile.loved_cuisines
    assert profile.avoided_ingredients == ["cilantro"]
    assert profile.weights["cuisine"] == 0.3
    # Los pesos suman 1.0 (rúbrica del esquema).
    assert round(sum(profile.weights.values()), 6) == 1.0


def test_round_trip():
    profile = TasteProfile(
        loved_cuisines=["italiana"],
        avoided_ingredients=["cilantro"],
        diet_constraints=[],
        weights={"cuisine": 1.0},
    )
    assert TasteProfile.from_dict(profile.to_dict()) == profile
