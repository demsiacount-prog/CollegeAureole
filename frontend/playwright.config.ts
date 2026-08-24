import { defineConfig } from '@playwright/test'

// Base PostgreSQL dédiée aux tests e2e, recréée vide à chaque exécution.
// Connexion par socket Unix (auth peer) : aucun mot de passe dans ce fichier.
const E2E_DB = 'collegeaureole_e2e'

export default defineConfig({
  testDir: './e2e',
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  webServer: [
    {
      command: [
        `dropdb --if-exists --force ${E2E_DB}`,
        `createdb ${E2E_DB}`,
        `DATABASE_URL='postgresql:///${E2E_DB}' venv/bin/uvicorn main:app --host 127.0.0.1 --port 3001`,
      ].join(' && '),
      cwd: '../backend',
      url: 'http://localhost:3001/api/setup/status',
      reuseExistingServer: false,
      timeout: 90_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: 'VITE_API_TARGET=http://localhost:3001 npm run dev -- --port 5174 --strictPort',
      cwd: '.',
      url: 'http://localhost:5174',
      reuseExistingServer: false,
      timeout: 90_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: 'VITE_API_TARGET=http://localhost:3001 npm run dev -- --port 5173 --strictPort',
      cwd: '.',
      url: 'http://localhost:5173',
      reuseExistingServer: false,
      timeout: 90_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
  use: {
    headless: true,
    viewport: { width: 1440, height: 900 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'initialisation',
      testMatch: /initialisation-wizard\.spec\.ts/,
      use: { baseURL: 'http://localhost:5174' },
    },
    {
      name: 'default',
      testMatch: /.*\.spec\.ts/,
      testIgnore: /(initialisation-wizard|final-purge)\.spec\.ts/,
      use: { baseURL: 'http://localhost:5173' },
      deps: ['initialisation'],
    },
    {
      name: 'final',
      testMatch: /final-purge\.spec\.ts/,
      use: { baseURL: 'http://localhost:5174' },
      deps: ['default'],
    },
  ],
})
