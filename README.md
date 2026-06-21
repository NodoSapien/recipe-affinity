# recipe-affinity

Recetario personal **AI-first** de [@Jrgil20](https://github.com/Jrgil20). No es solo un repositorio
de recetas: el sistema se alinea a los gustos del autor (un perfil de preferencias puntúa cada receta)
y expone tres capacidades operadas por Claude Skills:

1. **Descargar** una receta desde internet (URL → receta estructurada).
2. **Clasificar** una receta (parámetros + afinidad contra tus gustos).
3. **Generar** una página interactiva por receta (escalador de porciones, timers, checklist).

> Principio rector: **las skills orquestan; el dominio calcula.** La lógica determinista vive en
> código (Clean Architecture); las skills solo pegan piezas. Ver [`CLAUDE.md`](CLAUDE.md) y
> [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Estado

- **Fase 0 — completada**: núcleo de dominio (`Recipe`, `TasteProfile`), puertos
  (`RecipeRepository`, `RecipeSource`, `PageRenderer`) y el adaptador `FileRepository`
  (persistencia en `recipes/*.json`).
- **Fase 1 — completada**: skill [`recipe-fetcher`](skills/recipe-fetcher/SKILL.md) + adaptador
  `JsonLdSource` (URL → receta vía schema.org/Recipe con `recipe-scrapers`).

Roadmap completo en [`CLAUDE.md`](CLAUDE.md) §8.

## Descargar una receta

```bash
python skills/recipe-fetcher/fetch_recipe.py "https://www.bbcgoodfood.com/recipes/easy-chocolate-cake"
# -> recipes/easy-chocolate-cake.json
```

## Stack

- **Dominio + adaptadores + skills:** Python (≥ 3.11).
- **App web (Fase 3):** Astro.
- **Persistencia:** archivos hoy (`FileRepository`) → Supabase mañana (Fase 4), cambiando solo el adaptador.

## Desarrollo

```bash
python -m pip install -e ".[dev]"   # o: pip install pytest ruff
python -m pytest                     # tests verdes
python -m ruff check .               # lint
```

## Estructura

```
core/        # dominio (entidades) + puertos (interfaces) — estable, no conoce adaptadores
adapters/    # implementaciones intercambiables de los puertos
skills/      # Claude Skills (SKILL.md) — Fases 1–3
app/         # app Astro — Fase 3
recipes/     # fuente de verdad: una receta por archivo .json
```
