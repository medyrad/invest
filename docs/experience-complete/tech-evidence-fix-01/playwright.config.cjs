const {defineConfig} = require('../../../.tools/pw-min/node_modules/@playwright/test');

module.exports = defineConfig({
  testDir: __dirname,
  testMatch: 'capture-fixed-slots.spec.cjs',
  timeout: 120_000,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['junit', {outputFile: `${__dirname}/browser-results.xml`}]],
  outputDir: `${__dirname}/browser-artifacts`,
  use: {launchOptions: {executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}},
});
