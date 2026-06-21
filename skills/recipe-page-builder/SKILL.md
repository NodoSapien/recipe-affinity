# Skill: `recipe-page-builder`

> **Las skills orquestan; el dominio calcula.** Este archivo describe el *qué* y el *cómo* de la
> orquestación. El renderizado HTML real lo hace Astro; Python solo sincroniza los datos.

## Propósito

Publicar una receta en la app web:

1. Copia el JSON de la receta a `app/src/content/recipes/<slug>.json` (content collection de Astro).
2. (Opcional) Ejecuta `astro build` para exportar el HTML estático a `app/dist/`.

## Arquitectura del renderizado

```
recipes/<slug>.json          (fuente de verdad, escrita por FileRepository)
       |
       v  AstroRenderer.render()
app/src/content/recipes/<slug>.json   (copia en content collection)
       |
       v  astro build
app/dist/recipes/<slug>/index.html    (página estática final)
```

La separación es intencional: `AstroRenderer` es un adaptador del puerto `PageRenderer` del
dominio. Al migrar a Supabase (Fase 4), el loader de Astro cambia; el adaptador también cambia,
pero las páginas `.astro` permanecen intactas.

## Páginas generadas

### Catálogo (`/`)

- Lista todas las recetas ordenadas por `affinity_score` descendente.
- Filtros client-side (vanilla JS, sin framework): búsqueda de texto, cocina, tipo de comida, orden.
- Badges de afinidad por color (verde ≥ 75%, naranja ≥ 45%, rojo < 45%).

### Detalle (`/recipes/<slug>/`)

- **Escalador de porciones**: botones ± ajustan las cantidades de ingredientes en tiempo real.
- **Checklist de ingredientes**: tachado al marcar como añadido.
- **Timers por paso**: detecta "X min" en el texto del paso; un botón lo cuenta regresivamente.

## Uso

```bash
# Publicar una receta y reflejarla en la content collection:
python skills/recipe-page-builder/build_page.py pasta-al-pesto

# Publicar todas y exportar HTML estático:
python skills/recipe-page-builder/build_page.py --all --build

# Ver la app en desarrollo:
cd app && npm run dev
```

## Flujo completo (las tres skills encadenadas)

```bash
python skills/recipe-fetcher/fetch_recipe.py "https://ejemplo.com/receta"
# -> descarga, clasifica y guarda en recipes/

python skills/recipe-page-builder/build_page.py <slug> --build
# -> publica en app/dist/
```

## Archivos del dominio involucrados

| Archivo | Rol |
|---|---|
| `adapters/astro_renderer.py` | Implementa `PageRenderer`; escribe el JSON en content collection |
| `adapters/file_repository.py` | Lee la receta desde `recipes/` |
| `app/src/content.config.ts` | Schema Zod + glob loader (Astro v6) |
| `app/src/pages/index.astro` | Catálogo con filtros |
| `app/src/pages/recipes/[slug].astro` | Detalle con escalador, timers y checklist |
