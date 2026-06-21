---
name: recipe-fetcher
description: Descarga una receta desde una URL de internet y la guarda como recipes/<slug>.json normalizado al esquema del proyecto. Úsala cuando el usuario pegue un enlace a una receta o pida "descargar/importar esta receta".
---

# recipe-fetcher

Convierte una **URL de receta** en un archivo `recipes/<slug>.json` válido. La skill solo
**orquesta**: toda la extracción y normalización (schema.org/Recipe → esquema `Recipe`) es código
determinista en el adaptador `adapters/jsonld_source.py`.

## Cuándo usarla
- El usuario pega un enlace a una receta y quiere guardarla en el recetario.
- Se pide "importar", "descargar" o "añadir" una receta desde la web.

## Cómo ejecutarla

Desde la raíz del repo, ejecuta el entrypoint con la URL:

```bash
python skills/recipe-fetcher/fetch_recipe.py "<URL>"
```

Imprime una línea JSON con el resultado, por ejemplo:

```json
{"ok": true, "slug": "pasta-al-pesto", "title": "Pasta al Pesto", "path": "recipes/pasta-al-pesto.json"}
```

Si falla la extracción (sitio sin JSON-LD, red caída, etc.), imprime `{"ok": false, "error": "..."}`
y termina con código de salida 1. En ese caso, informa al usuario del error; no inventes datos.

## Qué hace por dentro
1. Descarga el HTML de la URL (User-Agent de navegador).
2. `JsonLdSource.from_html` extrae el bloque `schema.org/Recipe` (JSON-LD) con `recipe-scrapers`
   (`supported_only=False` → fallback genérico para sitios no soportados).
3. Normaliza al esquema `Recipe`: título, slug, `source_url`, porciones, tiempo total, cocina,
   ingredientes (con cantidad/unidad parseadas) y pasos.
4. Guarda con `FileRepository` en `recipes/<slug>.json` (UTF-8, escritura atómica).

## Límites (por diseño)
- Solo rellena lo que provee la fuente. Los parámetros derivados (dificultad, tipo de comida,
  `diet_tags`, `main_ingredients`, técnicas, temporada y `affinity_score`) los completa la skill
  **`recipe-classifier`** (Fase 2). En cuanto exista, encadénala tras un fetch exitoso.
- No hace scraping evasivo: si un sitio bloquea la descarga, reporta el error tal cual.
