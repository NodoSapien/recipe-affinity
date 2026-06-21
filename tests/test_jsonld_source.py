"""Tests del adaptador `JsonLdSource` — todos offline (sin red), con HTML de muestra."""

from pathlib import Path

import pytest

from adapters.file_repository import FileRepository
from adapters.jsonld_source import JsonLdSource, parse_ingredient
from core.domain.recipe import Recipe

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pasta.html"
URL = "https://example.com/pasta-al-pesto"


@pytest.fixture
def html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_from_html_normaliza_campos_basicos(html: str):
    r = JsonLdSource().from_html(html, URL)
    assert isinstance(r, Recipe)
    assert r.title == "Pasta al Pesto"
    assert r.slug == "pasta-al-pesto"
    assert r.source_url == URL
    assert r.servings == 4
    assert r.time_total_min == 25
    assert r.cuisine == "italiana"
    assert r.steps[0].startswith("Hervir la pasta")
    assert len(r.steps) == 3


def test_from_html_parsea_ingredientes(html: str):
    r = JsonLdSource().from_html(html, URL)
    porprimero = r.ingredients[0]
    assert porprimero.name == "albahaca fresca"
    assert porprimero.amount == 60
    assert porprimero.unit == "g"
    # La fracción "1/2 taza" se normaliza a 0.5.
    aceite = next(i for i in r.ingredients if "aceite" in i.name)
    assert aceite.amount == 0.5
    assert aceite.unit == "taza"


def test_fetch_usa_el_html_fetcher_inyectado_sin_red(html: str):
    """fetch() no toca la red si se inyecta un html_fetcher (determinismo en CI)."""
    llamado = {}

    def fake_fetcher(url: str) -> str:
        llamado["url"] = url
        return html

    source = JsonLdSource(html_fetcher=fake_fetcher)
    r = source.fetch(URL)
    assert llamado["url"] == URL
    assert r.title == "Pasta al Pesto"


def test_fetch_integra_con_file_repository(html: str, tmp_path: Path):
    """End-to-end de la skill: URL (mockeada) -> Recipe -> recipes/<slug>.json válido."""
    repo = FileRepository(base_dir=tmp_path / "recipes")
    source = JsonLdSource(html_fetcher=lambda _u: html)

    receta = source.fetch(URL)
    repo.save(receta)

    assert repo.exists("pasta-al-pesto")
    leida = repo.get("pasta-al-pesto")
    assert leida == receta


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("60 g albahaca fresca", {"name": "albahaca fresca", "amount": 60, "unit": "g"}),
        ("2 dientes de ajo", {"name": "ajo", "amount": 2, "unit": "dientes"}),
        ("1 1/2 taza harina", {"name": "harina", "amount": 1.5, "unit": "taza"}),
        ("2,5 kg harina", {"name": "harina", "amount": 2.5, "unit": "kg"}),
        ("Sal al gusto", {"name": "Sal al gusto", "amount": None, "unit": None}),
        ("3 huevos", {"name": "huevos", "amount": 3, "unit": None}),
    ],
)
def test_parse_ingredient(texto: str, esperado: dict):
    assert parse_ingredient(texto).to_dict() == esperado
