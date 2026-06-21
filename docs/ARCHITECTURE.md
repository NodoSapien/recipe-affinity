# Arquitectura — recipe-affinity

> Generado en la Fase 0. Fuente de verdad del diseño: [`CLAUDE.md`](../CLAUDE.md).

## Principio rector

**Las skills orquestan; el dominio calcula.** Cada Claude Skill (`SKILL.md`) define el *cómo* y
pega piezas, pero toda la lógica determinista (normalizar scraping, puntuar afinidad, renderizar)
vive en **código** Python. Esto garantiza resultados reproducibles, no dependientes del modelo de
turno.

## Las tres capas

```
┌─────────────────────────────────────────────┐
│  SKILLS (SKILL.md) — orquestan, no calculan  │
│  recipe-fetcher → recipe-classifier →        │
│  recipe-page-builder                          │
└───────────────┬─────────────────────────────┘
                │ llaman a
┌───────────────▼─────────────────────────────┐
│  NÚCLEO DE DOMINIO (estable)                 │
│  Entidades: Recipe (+ Ingredient),           │
│             TasteProfile                      │
│  Puertos:   RecipeRepository, RecipeSource,  │
│             PageRenderer                      │
└───────────────┬─────────────────────────────┘
                │ implementados por
┌───────────────▼─────────────────────────────┐
│  ADAPTADORES (intercambiables)               │
│  FileRepository (hoy) → SupabaseRepo (Fase 4)│
│  JsonLdSource (Fase 1)                        │
│  AstroRenderer (Fase 3)                       │
└─────────────────────────────────────────────┘
```

### Regla de dependencias

Las flechas apuntan **hacia adentro**. `core/` (dominio + puertos) **no importa** `adapters/`,
ni Astro, ni librerías de scraping. Los adaptadores dependen del dominio, nunca al revés. Esta
regla se verifica de forma mecánica (los módulos de `core/` no contienen imports de `adapters`).

## Mapa de carpetas

| Carpeta | Rol | Estabilidad |
|---|---|---|
| `core/domain/` | Entidades (`Recipe`, `Ingredient`, `TasteProfile`) | Estable |
| `core/ports/` | Interfaces (`Protocol`) que el dominio expone | Estable |
| `adapters/` | Implementaciones concretas de los puertos | Intercambiable |
| `skills/` | Claude Skills que orquestan (Fases 1–3) | — |
| `app/` | App Astro (Fase 3) | — |
| `recipes/` | Fuente de verdad: una receta por archivo `.json` | Datos |

## Los puertos (contratos)

Todos se definen como `typing.Protocol` (tipado **estructural**): un adaptador cumple el contrato
por su forma, sin necesidad de importar el puerto. Esto mantiene las dependencias apuntando hacia
adentro de forma pura.

| Puerto | Método(s) | Implementado por | Fase |
|---|---|---|---|
| `RecipeRepository` | `save` / `get` / `list` / `exists` / `delete` | `FileRepository` | **0** (hoy) → `SupabaseRepository` (4) |
| `RecipeSource` | `fetch(url) -> Recipe` | `JsonLdSource` | 1 |
| `PageRenderer` | `render(recipe) -> str` | `AstroRenderer` | 3 |

## La decisión clave: "archivos hoy → BD mañana" como puerto

La persistencia se aísla detrás de `RecipeRepository`. Hoy el adaptador es `FileRepository`
(recetas en `recipes/<slug>.json`, escritura atómica, UTF-8). Al migrar a base de datos (Fase 4)
se escribe un `SupabaseRepository` que cumple el **mismo** puerto: **ninguna skill ni entidad de
dominio se reescribe**, solo se cambia qué adaptador se inyecta.

La clave natural de una receta es su `slug` (= nombre de archivo). La serialización JSON es 1:1
con el esquema de `CLAUDE.md` §3, con orden de claves estable para diffs limpios.

## Lo que NO existe todavía (por diseño)

- `core/domain/affinity.py` y el cálculo de `affinity_score` → **Fase 2**. `TasteProfile` ya existe
  como estructura de datos, pero sin método de puntuación.
- `JsonLdSource`, `AstroRenderer`, `SupabaseRepository` → sus puertos están definidos, pero los
  adaptadores llegan en sus Fases (1, 3, 4 respectivamente).
