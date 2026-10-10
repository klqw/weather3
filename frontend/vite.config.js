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
      input: {
        "location-dates": "src/location-dates.jsx",
        "weather-app": "src/weather-app.jsx",
        "extreme-details": "src/extreme-details.jsx"
      },
      output: {
        entryFileNames: "[name].js"
      }
    }
  }
})
