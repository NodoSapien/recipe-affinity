"""Fixtures compartidas de la suite de Fase 0."""

from pathlib import Path

import pytest

from adapters.file_repository import FileRepository
from core.domain.recipe import Ingredient, Recipe


@pytest.fixture
def recipe_ejemplo() -> Recipe:
    """La pasta al pesto del esquema de CLAUDE.md §3, con campos representativos."""
    return Recipe.new(
        title="Pasta al pesto",
        source_url="https://example.com/pasta-al-pesto",
        servings=4,
        ingredients=[Ingredient(name="albahaca fresca", amount=60, unit="g")],
        steps=["Hervir la pasta...", "Triturar la albahaca..."],
        time_total_min=25,
        time_active_min=15,
        difficulty="media",
        cuisine="italiana",
        meal_type="almuerzo",
        diet_tags=["vegetariano"],
        main_ingredients=["albahaca", "pasta"],
        techniques=["hervido", "triturado"],
        season=["verano"],
    )


@pytest.fixture
def repo(tmp_path: Path) -> FileRepository:
    """Un FileRepository aislado en un directorio temporal."""
    return FileRepository(base_dir=tmp_path / "recipes")
