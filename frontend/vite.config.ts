import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// CSP appliquée au seul build (l'index.html de dev doit rester compatible avec
// les préambules inline injectés par Vite/react-refresh). En mode bureau
// (Tauri), la CSP de tauri.conf.json reste la référence — celle-ci lui est
// alignée (même connexion locale, mêmes polices) et la renforce sans jamais
// l'affaiblir (additive).
const CSP_BUILD = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com data:",
  "img-src 'self' data: blob: http://localhost:* http://127.0.0.1:*",
  "connect-src 'self' http://localhost:* http://127.0.0.1:*",
  "object-src 'none'",
  "base-uri 'self'",
  "frame-ancestors 'none'",
  "form-action 'self'",
].join('; ')

function cspMetaBuild(): Plugin {
  return {
    name: 'inject-csp-meta-build',
    apply: 'build',
    transformIndexHtml(html) {
      return html.replace(
        '<head>',
        `    <meta http-equiv="Content-Security-Policy" content="${CSP_BUILD}" />\n    <head>`,
      )
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), cspMetaBuild()],
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
