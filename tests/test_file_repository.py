"""Tests del adaptador `FileRepository` (persistencia en archivos)."""

import json

from adapters.file_repository import FileRepository
from core.domain.recipe import Recipe


def test_ciclo_completo(repo: FileRepository, recipe_ejemplo: Recipe):
    """save -> get -> list -> exists -> delete."""
    assert repo.exists(recipe_ejemplo.slug) is False
    assert repo.get(recipe_ejemplo.slug) is None

    repo.save(recipe_ejemplo)

    assert repo.exists(recipe_ejemplo.slug) is True
    recuperada = repo.get(recipe_ejemplo.slug)
    assert recuperada == recipe_ejemplo

    todas = repo.list()
    assert len(todas) == 1
    assert todas[0] == recipe_ejemplo

    repo.delete(recipe_ejemplo.slug)
    assert repo.exists(recipe_ejemplo.slug) is False
    assert repo.get(recipe_ejemplo.slug) is None


def test_get_inexistente_devuelve_none(repo: FileRepository):
    assert repo.get("no-existe") is None


def test_delete_es_idempotente(repo: FileRepository):
    # No debe lanzar aunque el slug no exista.
    repo.delete("no-existe")


def test_list_ordenado_por_slug(repo: FileRepository):
    repo.save(Recipe.new("Zanahoria asada"))
    repo.save(Recipe.new("Arroz blanco"))
    repo.save(Recipe.new("Manzana al horno"))
    slugs = [r.slug for r in repo.list()]
    assert slugs == sorted(slugs)


def test_acentos_se_preservan_en_disco(repo: FileRepository, recipe_ejemplo: Recipe):
    """El JSON en disco es UTF-8 legible (ensure_ascii=False), no escapes \\uXXXX."""
    recipe_ejemplo.notes = "Añadir piñones y jamón"
    repo.save(recipe_ejemplo)

    path = repo._path(recipe_ejemplo.slug)
    crudo = path.read_text(encoding="utf-8")
    assert "Añadir piñones y jamón" in crudo
    assert "\\u" not in crudo

    # Y round-trip­ea sin pérdida.
    data = json.loads(crudo)
    assert data["notes"] == "Añadir piñones y jamón"


def test_save_es_atomico_sin_dejar_temporales(repo: FileRepository, recipe_ejemplo: Recipe):
    repo.save(recipe_ejemplo)
    # No deben quedar archivos .tmp tras un guardado exitoso.
    assert list(repo._base_dir.glob("*.tmp")) == []
