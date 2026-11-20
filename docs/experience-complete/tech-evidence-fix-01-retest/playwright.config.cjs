const {defineConfig} = require('../../../.tools/pw-min/node_modules/@playwright/test');

module.exports = defineConfig({
  testDir: __dirname,
  testMatch: 'browser-retest.spec.cjs',
  timeout: 120_000,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['junit', {outputFile: `${__dirname}/browser-results.xml`}]],
  outputDir: `${__dirname}/browser-artifacts`,
});
