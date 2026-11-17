import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/browser',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [['list'], ['json', { outputFile: 'test-results/results.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:3109', trace: 'retain-on-failure',
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {},
  },
  projects: [
    { name: 'mobile-360', grepInvert: /@desktop/, use: { viewport: { width: 360, height: 800 } } },
    { name: 'tablet-768', grepInvert: /@desktop/, use: { viewport: { width: 768, height: 1000 } } },
    { name: 'mobile-390', grepInvert: /@desktop/, use: { viewport: { width: 390, height: 844 } } },
    { name: 'desktop-1440', use: { viewport: { width: 1440, height: 1000 } } },
  ],
  webServer: {
    command: 'npm run start',
    env: { PORT: '3109', HOSTNAME: '127.0.0.1' },
    url: 'http://127.0.0.1:3109',
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
