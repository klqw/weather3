import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [
    react()
  ],

  build: {
    outDir: "../static/react",
    emptyOutDir: true,

    rollupOptions: {
      input: "src/location-dates.jsx",

      output: {
        entryFileNames: "location-dates.js"
      }
    }
  }
})