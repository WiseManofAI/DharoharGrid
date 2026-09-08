import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  // Relative base so the build works wherever it's linked from (this repo
  // links to it as a static build at Discover/dist/index.html, not served
  // from the domain root).
  base: './',
  plugins: [react()],
})
