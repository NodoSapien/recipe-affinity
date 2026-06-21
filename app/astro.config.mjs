// @ts-check
import { defineConfig } from "astro/config";

export default defineConfig({
  output: "static",
  // Las skills Python escriben JSONs en src/content/recipes/; Astro los consume aquí.
  // Al migrar a Supabase (Fase 4) se añade un loader externo sin cambiar las páginas.
});
