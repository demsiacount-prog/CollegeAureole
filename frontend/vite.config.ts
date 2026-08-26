import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // Pas de manualChunks dans build.rollupOptions : le découpage forcé plaçait
  // les helpers CommonJS (__commonJSMin) dans un chunk applicatif, créant un
  // cycle entre chunks (query-vendor → api → query-vendor). React plantait alors
  // à l'évaluation des modules ("__commonJSMin is not a function") → écran noir
  // au démarrage. Rollup découpe seul, sans cycle.
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:3000',
        changeOrigin: true,
      },
      '/uploads': {
        target: process.env.VITE_API_TARGET || 'http://localhost:3000',
        changeOrigin: true,
      },
    },
  },
})
