const path = require('node:path');
const root = path.resolve(__dirname, '../../..');
const { defineConfig } = require(path.join(root, 'frontend/node_modules/@playwright/test'));
module.exports = defineConfig({
  testDir: __dirname, testMatch: 'late.spec.ts', workers: 1, retries: 0,
  reporter: [['list']], outputDir: path.join(root, '.tools/test-s05-a1-02/output'),
  use: { baseURL: 'http://127.0.0.1:3109', viewport: { width: 1440, height: 1000 },
    trace: 'off', launchOptions: { executablePath: '/usr/bin/google-chrome' } },
});
