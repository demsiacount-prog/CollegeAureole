import { defineConfig } from '@playwright/test'

// Base unique collegeaureole (dev + tests). Le démarrage du backend d'e2e
// vide le schéma public via psql puis Alembic le recrée au démarrage.

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
        `set -a && . ./.env && set +a`,
        `psql "$DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"`,
        `venv/bin/uvicorn main:app --host 127.0.0.1 --port 3001`,
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
