# Recetario Personal — Contexto del Proyecto (CLAUDE.md)

> Este archivo es la **fuente de verdad** para Claude Code y Cowork.
> Léelo completo antes de actuar. La fase de diseño está cerrada; aquí solo se ejecuta.

---

## 1. Qué es este proyecto

Un **recetario personal AI-first**. No es solo un repositorio de recetas: el sistema se
**alinea a los gustos del autor** (perfil de preferencias que puntúa cada receta) y expone
tres capacidades operadas por Claude Skills:

1. **Descargar** una receta desde internet (URL → receta estructurada).
2. **Clasificar** una receta (parámetros + afinidad contra los gustos).
3. **Generar** una página interactiva por receta (escalador de porciones, timers, checklist).

Autor / handle: `@Jrgil20`. Idioma del proyecto: **español**.

---

## 2. Principio rector: AI-first + Clean Architecture

> **Las skills orquestan; el dominio calcula.**

Cada skill (SKILL.md) define el *cómo* y pega piezas, pero la lógica determinista
(extraer parámetros, puntuar afinidad, normalizar scraping, renderizar) vive en **código**.
Esto garantiza resultados reproducibles, no dependientes del modelo de turno.

La decisión "archivos hoy → BD mañana" se implementa como un **puerto**: se define la
interfaz una vez y solo se cambia el adaptador al migrar. Ninguna skill se reescribe.

```
┌─────────────────────────────────────────────┐
│  SKILLS (SKILL.md) — orquestan, no calculan  │
│  recipe-fetcher → recipe-classifier →        │
│  recipe-page-builder                          │
└───────────────┬─────────────────────────────┘
                │ llaman a
┌───────────────▼─────────────────────────────┐
│  NÚCLEO DE DOMINIO (estable)                 │
│  Entidades: Recipe, TasteProfile             │
│  Puertos:   RecipeRepository, RecipeSource,  │
│             PageRenderer                      │
└───────────────┬─────────────────────────────┘
                │ implementados por
┌───────────────▼─────────────────────────────┐
│  ADAPTADORES (intercambiables)               │
│  FileRepository (hoy) → SupabaseRepo (luego) │
│  JsonLdSource (scraping)                      │
│  AstroRenderer (páginas)                      │
└─────────────────────────────────────────────┘
```

**Regla de dependencias:** las flechas apuntan hacia adentro. El dominio NO conoce a los
adaptadores ni a Astro; los adaptadores implementan los puertos del dominio.

---

## 3. Modelo de datos: esquema `Recipe`

Cada receta es un archivo `recipes/<slug>.json` con esta forma:

```jsonc
{
  "id": "uuid",
  "slug": "pasta-al-pesto",
  "title": "Pasta al pesto",
  "source_url": "https://...",
  "language": "es",
  "servings": 4,

  "ingredients": [
    { "name": "albahaca fresca", "amount": 60, "unit": "g" }
  ],
  "steps": ["Hervir la pasta...", "Triturar la albahaca..."],

  // --- Parámetros (clasifican y filtran) ---
  "time_total_min": 25,
  "time_active_min": 15,
  "difficulty": "media",          // baja | media | alta
  "cuisine": "italiana",
  "meal_type": "almuerzo",        // desayuno | almuerzo | cena | snack | postre
  "diet_tags": ["vegetariano"],
  "main_ingredients": ["albahaca", "pasta"],
  "techniques": ["hervido", "triturado"],
  "season": ["verano"],

  // --- Gustos ---
  "affinity_score": 0.0,          // calculado por el clasificador (0.0–1.0)
  "my_rating": null,              // feedback manual del autor (1–5 o null)
  "notes": "",

  // --- Sistema ---
  "created_at": "ISO-8601",
  "classified_at": "ISO-8601 | null",
  "tags": []
}
```

---

## 4. Modelo de gustos

Archivo `preferences.json` en la raíz:

```jsonc
{
  "loved_cuisines": ["italiana", "japonesa"],
  "avoided_ingredients": ["cilantro"],
  "diet_constraints": [],
  "weights": {                    // peso de cada dimensión en el score
    "cuisine": 0.3,
    "main_ingredients": 0.3,
    "diet_tags": 0.2,
    "difficulty": 0.1,
    "time": 0.1
  }
}
```

`affinity_score` = match ponderado entre los parámetros de la receta y este perfil.
**Fase inicial: estático.** Más adelante, `my_rating` ajusta los pesos → eso será un
puerto adicional `AffinityModel` (no implementar hasta que se pida).

---

## 5. Las tres Claude Skills (SKILL.md a construir)

Viven en `skills/<nombre>/SKILL.md`. Cada una es delgada: invoca scripts del dominio/adaptadores.

### `recipe-fetcher`  (URL → receta)
- **Input:** una URL de receta.
- **Hace:** descarga la página → extrae `schema.org/Recipe` (JSON-LD) vía el adaptador
  `JsonLdSource` → normaliza al esquema `Recipe` → guarda `recipes/<slug>.json`.
- **Librería recomendada:** `recipe-scrapers` (Python) — soporta cientos de sitios y tiene
  fallback genérico a JSON-LD. Confirmar viabilidad en Fase 1.
- **Encadena con:** `recipe-classifier`.
- **Determinismo:** la extracción y normalización son código; la skill solo orquesta.

### `recipe-classifier`  (receta → receta enriquecida)
- **Input:** una receta (recién descargada o existente).
- **Hace:** normaliza parámetros faltantes → calcula `affinity_score` contra `preferences.json`
  → asigna `tags` y categorías → escribe `classified_at`.
- **Determinismo:** la rúbrica de puntuación se documenta dentro del SKILL.md para que sea
  consistente entre ejecuciones.

### `recipe-page-builder`  (receta → página)
- **Input:** una receta.
- **Hace:** genera la entrada de la colección de contenido de Astro **y** exporta el HTML
  estático. La página incluye: escalador de porciones, timers por paso, checklist de ingredientes.
- **Determinismo:** plantilla fija; los datos vienen del JSON de la receta.

---

## 6. Stack técnico

- **Núcleo de dominio + adaptadores + lógica de skills:** **Python**.
  (Mejor ecosistema para scraping/JSON-LD; es el lenguaje más fuerte del autor.)
- **App web:** **Astro**.
  - Content collections = recetas en archivos (encaja con "archivos primero").
  - Export estático nativo = cubre "exporta páginas".
  - Islands (React o vanilla) = catálogo con filtros + interactividad por receta.
  - Al migrar a Supabase, Astro lee vía loader → solo cambia el adaptador del repositorio.
- **Puente:** las skills (Python) escriben en `app/src/content/recipes/`; Astro consume eso.

> Si se prefiere **Next.js** en vez de Astro, cambiarlo aquí antes de empezar la Fase 3.
> El resto de la arquitectura no se ve afectada.

---

## 7. Estructura del repositorio

```
recetario/
├── CLAUDE.md                      # este archivo
├── README.md
├── pyproject.toml                 # dominio/adaptadores/skills (Python)
├── preferences.json               # gustos del autor
├── recipes/                       # fuente de verdad (fase archivos)
│   └── *.json
├── core/
│   ├── domain/
│   │   ├── recipe.py              # entidad Recipe
│   │   ├── taste_profile.py
│   │   └── affinity.py           # cálculo del score
│   └── ports/
│       ├── recipe_repository.py  # interfaz (Protocol/ABC)
│       ├── recipe_source.py
│       └── page_renderer.py
├── adapters/
│   ├── file_repository.py        # HOY
│   ├── supabase_repository.py    # Fase 4
│   ├── jsonld_source.py          # scraping
│   └── astro_renderer.py
├── skills/
│   ├── recipe-fetcher/SKILL.md
│   ├── recipe-classifier/SKILL.md
│   └── recipe-page-builder/SKILL.md
├── app/                          # Astro
│   ├── src/content/recipes/
│   ├── src/pages/
│   └── astro.config.mjs
├── docs/
│   └── ARCHITECTURE.md           # generado en Fase 0
└── ai-usage/                     # registro de uso de IA (@Jrgil20)
    └── *.json
```

---

## 8. Roadmap de construcción

| Fase | Entregable | Criterio de "hecho" |
|------|-----------|---------------------|
| **0** | Scaffold + entidad `Recipe` + `TasteProfile` + puertos + `FileRepository` + `docs/ARCHITECTURE.md` | Se puede crear/leer/listar recetas desde `recipes/*.json` con tests verdes |
| **1** | Skill `recipe-fetcher` + adaptador `JsonLdSource` | Una URL real produce un `recipes/<slug>.json` válido |
| **2** | Skill `recipe-classifier` + `preferences.json` | Cada receta obtiene `affinity_score` reproducible |
| **3** | Skill `recipe-page-builder` + app Astro | Catálogo con filtros + página interactiva por receta + export estático |
| **4** | Adaptador `SupabaseRepository` | Migración a BD cambiando solo el adaptador; skills intactas |

---

## 9. Convenciones

- **Idioma:** código y comentarios en español; nombres de símbolos en inglés está OK.
- **Clean Architecture:** dependencias hacia adentro; el dominio no importa adaptadores.
- **Skills delgadas:** ninguna lógica de cálculo dentro del SKILL.md; siempre delega a código.
- **Tests:** cada puerto/adaptador con tests; el cálculo de afinidad con casos fijos.
- **Git:** commits atómicos por fase; autor `@Jrgil20`.
- **Registro de uso de IA:** al cerrar cada fase, escribir un JSON en `ai-usage/` (herramienta,
  qué generó, qué modificó el humano) siguiendo el patrón habitual del autor.

---

## 10. Cómo arrancar (para el agente)

1. **No escribas código aún.** Primero propón tu plan de la **Fase 0** y espera confirmación.
2. Sigue el roadmap fase por fase; no adelantes fases.
3. Al terminar cada fase, resume qué hiciste y actualiza `ai-usage/`.