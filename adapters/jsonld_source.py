"""Adaptador `JsonLdSource`: obtiene una receta desde una URL (schema.org/Recipe → JSON-LD).

Cumple el puerto `core.ports.recipe_source.RecipeSource` por tipado estructural. Usa la librería
`recipe-scrapers` (cientos de sitios soportados + fallback genérico a JSON-LD vía `wild_mode`).

La descarga HTTP y el parseo están separados: `fetch(url)` baja el HTML y delega en `from_html`,
que es **determinista** y se puede testear offline con un HTML de muestra. Toda la normalización al
esquema `Recipe` es código (la skill solo orquesta).

Lo que este adaptador rellena es lo que provee la fuente (título, ingredientes, pasos, porciones,
tiempo total, cocina). Los parámetros derivados que faltan (difficulty, meal_type, diet_tags,
main_ingredients, techniques, season, affinity_score) los completa el clasificador en la Fase 2.
"""

from __future__ import annotations

import re
import urllib.request
from collections.abc import Callable

from recipe_scrapers import scrape_html

from core.domain.recipe import Ingredient, Recipe

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 recipe-affinity/0.1"
)

# Unidades reconocidas para el parseo ligero de ingredientes (es + métricas comunes).
_KNOWN_UNITS = {
    "g", "gr", "kg", "mg", "ml", "l", "cl", "dl", "oz", "lb",
    "cda", "cdas", "cucharada", "cucharadas", "cdta", "cdita",
    "cucharadita", "cucharaditas", "taza", "tazas", "vaso", "vasos",
    "diente", "dientes", "unidad", "unidades", "ud", "uds",
    "pizca", "pizcas", "hoja", "hojas", "rama", "ramas",
    "lata", "latas", "sobre", "sobres", "puñado", "puñados",
    "cup", "cups", "tbsp", "tsp",
}

# Fracciones unicode comunes en recetas.
_UNICODE_FRACTIONS = {
    "½": 0.5, "⅓": 1 / 3, "⅔": 2 / 3, "¼": 0.25, "¾": 0.75,
    "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875,
    "⅕": 0.2, "⅖": 0.4, "⅗": 0.6, "⅘": 0.8, "⅙": 1 / 6, "⅚": 5 / 6,
}
_UNI_CHARS = "".join(_UNICODE_FRACTIONS)


def _parse_quantity(text: str) -> tuple[float | None, str]:
    """Extrae una cantidad inicial (entero, decimal, fracción a/b, mixta o unicode).

    Devuelve `(amount, resto)`; si no hay cantidad al inicio, `(None, texto)`.
    """
    s = text.strip()
    # Fracción mixta "1 1/2".
    m = re.match(r"^(\d+)\s+(\d+)\s*/\s*(\d+)\b", s)
    if m:
        amt = int(m.group(1)) + int(m.group(2)) / int(m.group(3))
        return amt, s[m.end():].strip()
    # Fracción simple "1/2".
    m = re.match(r"^(\d+)\s*/\s*(\d+)\b", s)
    if m:
        return int(m.group(1)) / int(m.group(2)), s[m.end():].strip()
    # Entero/decimal con posible fracción unicode pegada ("1½").
    m = re.match(rf"^(\d+(?:[.,]\d+)?)\s*([{_UNI_CHARS}])?", s)
    if m and m.group(1):
        amt = float(m.group(1).replace(",", "."))
        if m.group(2):
            amt += _UNICODE_FRACTIONS[m.group(2)]
        return amt, s[m.end():].strip()
    # Fracción unicode sola al inicio ("½ taza").
    if s and s[0] in _UNICODE_FRACTIONS:
        return _UNICODE_FRACTIONS[s[0]], s[1:].strip()
    return None, s


def _http_get(url: str, *, timeout: float = 20.0) -> str:
    """Descarga el HTML de `url` con un User-Agent de navegador."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (URL del usuario)
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def parse_ingredient(text: str) -> Ingredient:
    """Parseo ligero y determinista de un ingrediente en texto a `Ingredient`.

    Extrae una cantidad numérica inicial y, si el token siguiente es una unidad conocida, la separa.
    Si no hay número al inicio, deja `amount`/`unit` en None y todo el texto como `name`.
    """
    text = text.strip()
    amount, rest = _parse_quantity(text)
    if amount is None:
        return Ingredient(name=text)
    if isinstance(amount, float) and amount.is_integer():
        amount = int(amount)

    # ¿El primer token del resto es una unidad conocida?
    tokens = rest.split(None, 1)
    if tokens and tokens[0].lower().strip(".") in _KNOWN_UNITS:
        unit: str | None = tokens[0].lower().strip(".")
        name = tokens[1].strip() if len(tokens) > 1 else ""
    else:
        unit = None
        name = rest.strip()

    # Limpia un "de"/"of" colgante tras separar cantidad/unidad ("2 dientes de ajo" -> "ajo").
    name = re.sub(r"^(de|of)\s+", "", name, flags=re.IGNORECASE)

    return Ingredient(name=name or text, amount=amount, unit=unit)


def _first_int(value: str | None) -> int | None:
    """Primer entero que aparezca en un texto (p. ej. '4 servings' -> 4)."""
    if not value:
        return None
    m = re.search(r"\d+", value)
    return int(m.group()) if m else None


def _safe(getter: Callable[[], object]) -> object | None:
    """Llama a un getter de recipe-scrapers devolviendo None si el campo no está disponible."""
    try:
        return getter()
    except Exception:
        return None


class JsonLdSource:
    """Fuente de recetas que extrae schema.org/Recipe de una página web."""

    def __init__(self, *, html_fetcher: Callable[[str], str] | None = None) -> None:
        # Inyectable para tests offline; por defecto descarga por HTTP.
        self._fetch_html = html_fetcher or _http_get

    def fetch(self, url: str) -> Recipe:
        html = self._fetch_html(url)
        return self.from_html(html, url)

    def from_html(self, html: str, url: str) -> Recipe:
        """Normaliza el HTML (con su JSON-LD) al esquema `Recipe`. Determinista, sin red."""
        # supported_only=False habilita el fallback genérico a JSON-LD para sitios no soportados.
        scraper = scrape_html(html, org_url=url, supported_only=False)

        title = scraper.title()
        if not title:
            raise ValueError(f"No se encontró título de receta en {url}")

        raw_ingredients = _safe(scraper.ingredients) or []
        ingredients = [parse_ingredient(t) for t in raw_ingredients]
        steps = list(_safe(scraper.instructions_list) or [])

        servings = _first_int(_safe(scraper.yields)) or 1  # type: ignore[arg-type]
        time_total = _safe(scraper.total_time)
        time_total_min = int(time_total) if isinstance(time_total, int | float) and time_total else None

        cuisine_raw = _safe(scraper.cuisine)
        cuisine = None
        if isinstance(cuisine_raw, str) and cuisine_raw.strip():
            # schema.org puede traer varias separadas por coma; tomamos la primera, en minúsculas.
            cuisine = cuisine_raw.split(",")[0].strip().lower()

        return Recipe.new(
            title=title,
            source_url=url,
            servings=servings,
            ingredients=ingredients,
            steps=steps,
            time_total_min=time_total_min,
            cuisine=cuisine,
        )
