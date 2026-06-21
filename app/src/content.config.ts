import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const recipes = defineCollection({
  // Astro v6: loader obligatorio. Lee *.json desde recipes/ (fuera de app/).
  loader: glob({ pattern: "**/*.json", base: "../recipes" }),
  schema: z.object({
    id: z.string(),
    slug: z.string(),
    title: z.string(),
    source_url: z.string().url().nullable().optional(),
    language: z.string().default("es"),
    servings: z.number().int().min(1).default(1),
    ingredients: z.array(
      z.object({
        name: z.string(),
        amount: z.number().nullable().optional(),
        unit: z.string().nullable().optional(),
      })
    ).default([]),
    steps: z.array(z.string()).default([]),
    time_total_min: z.number().int().nullable().optional(),
    time_active_min: z.number().int().nullable().optional(),
    difficulty: z.enum(["baja", "media", "alta"]).nullable().optional(),
    cuisine: z.string().nullable().optional(),
    meal_type: z.enum(["desayuno", "almuerzo", "cena", "snack", "postre"]).nullable().optional(),
    diet_tags: z.array(z.string()).default([]),
    main_ingredients: z.array(z.string()).default([]),
    techniques: z.array(z.string()).default([]),
    season: z.array(z.string()).default([]),
    affinity_score: z.number().min(0).max(1).default(0),
    my_rating: z.number().int().min(1).max(5).nullable().optional(),
    notes: z.string().default(""),
    created_at: z.string(),
    classified_at: z.string().nullable().optional(),
    tags: z.array(z.string()).default([]),
  }),
});

export const collections = { recipes };
