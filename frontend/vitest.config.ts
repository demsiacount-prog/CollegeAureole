import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Configuration séparée de vite.config.ts (dédiée au build) pour ne pas lui
// ajouter de dépendance à vitest. Les tests e2e Playwright restent séparés
// (test:e2e) : ceci ne couvre que les tests unitaires/composants rapides.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    exclude: ['**/node_modules/**', '**/e2e/**', '**/src-tauri/**'],
  },
})
