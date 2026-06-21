# Skill: `recipe-classifier`

> **Las skills orquestan; el dominio calcula.** Este archivo describe el *qué* y el *cómo* de la
> orquestación. Toda la lógica determinista (normalización, puntuación) vive en código Python.

## Propósito

Enriquecer una receta existente con:

1. **Normalización** de parámetros que la fuente no proveyó (`main_ingredients`, `meal_type`,
   `difficulty`).
2. **`affinity_score`** (0.0–1.0): qué tanto encaja la receta con los gustos del autor
   (`preferences.json`).
3. **`classified_at`**: marca de tiempo ISO-8601 de la última clasificación.

## Rúbrica de puntuación (determinista)

`affinity_score = Σ(weight[dim] × match[dim]) / Σ(weight[dim])`

| Dimensión | Peso (default) | Regla de match |
|---|---|---|
| `cuisine` | 0.30 | 1.0 si en `loved_cuisines`; 0.0 si no; 0.5 si desconocida |
| `main_ingredients` | 0.30 | fracción de ingredientes que NO son `avoided_ingredients` |
| `diet_tags` | 0.20 | fracción de `diet_constraints` satisfechas (1.0 si sin restricciones) |
| `difficulty` | 0.10 | baja→1.0 · media→0.8 · alta→0.5 · None→0.7 |
| `time` | 0.10 | ≤30 min→1.0 · escala lineal → ≥120 min→0.2 · None→0.6 |

Los pesos se leen de `preferences.json` y pueden modificarse sin tocar el código.
La implementación es `core/domain/affinity.py`.

## Heurísticas de normalización

Rellena solo si el campo es `null`/vacío (nunca sobreescribe):

- `main_ingredients` → últimas palabras de los primeros 5 ingredientes.
- `meal_type` → inferido del tiempo total: ≤20 min→desayuno · ≤60→almuerzo · >60→cena.
- `difficulty` → inferida del tiempo activo (o total): ≤20 min→baja · ≤45→media · >45→alta.

## Uso

```bash
# Clasificar una sola receta:
python skills/recipe-classifier/classify_recipe.py pasta-al-pesto

# Clasificar todas las recetas del repositorio:
python skills/recipe-classifier/classify_recipe.py --all
```

## Encadenamiento

En el flujo completo la skill `recipe-fetcher` llama a este script automáticamente. También puede
invocarse de forma independiente para re-clasificar recetas cuando `preferences.json` cambia.

## Archivos del dominio involucrados

| Archivo | Rol |
|---|---|
| `core/domain/affinity.py` | Cálculo del score (sin side-effects) |
| `core/domain/recipe.py` | Entidad `Recipe` |
| `core/domain/taste_profile.py` | Entidad `TasteProfile` |
| `adapters/file_repository.py` | Lectura/escritura de `recipes/<slug>.json` |
| `preferences.json` | Perfil de gustos (pesos y listas) |
