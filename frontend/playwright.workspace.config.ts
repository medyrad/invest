import path from 'node:path';
import { defineConfig } from '@playwright/test';

const root = path.resolve(__dirname, '..');
export default defineConfig({
  testDir: './tests/browser',
  testMatch: 'workspace.spec.ts',
  workers: 1,
  retries: 0,
  reporter: [['list'], ['json', { outputFile: process.env.A1_RESULTS_FILE || path.join(root, '.tools/s05-a1/browser-review.json') }]],
  outputDir: path.join(root, '.tools/s05-a1/browser-review-output'),
  use: {
    baseURL: process.env.A1_BASE_URL || 'http://127.0.0.1:3109',
    viewport: { width: Number(process.env.A1_WIDTH || 1440), height: 1000 },
    trace: 'off',
    launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/usr/bin/google-chrome' },
  },
});
