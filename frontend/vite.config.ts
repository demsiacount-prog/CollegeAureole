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
  build: {
    rollupOptions: {
      output: {
        // Séparer les bibliothèques stables en chunks réutilisables : le
        // navigateur ne les re-télécharge pas lors d'un déploiement applicatif,
        // et les pages se chargent plus vite (parallélisme + cache).
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('react-router') || id.includes('react-dom') || id.includes('/react/')) return 'react-vendor'
          if (id.includes('@tanstack') || id.includes('/axios/')) return 'query-vendor'
          if (id.includes('/recharts/') || id.includes('/d3-') || id.includes('/redux/')) return 'charts-vendor'
          if (id.includes('/lucide-react/')) return 'icons'
          return 'vendor'
        },
      },
    },
  },
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
