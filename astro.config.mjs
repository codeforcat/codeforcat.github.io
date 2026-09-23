import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://code4cat.org",
  output: "static",
  build: {
    format: "file"
  }
});
