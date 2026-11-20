module.exports = {
  testDir: '/evidence',
  testMatch: 'browser-report.spec.ts',
  timeout: 120000,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['junit', {outputFile: '/evidence/browser-report.xml'}]],
  outputDir: '/tmp/fix-02-browser-artifacts',
  use: {
    baseURL: 'http://127.0.0.1:3118',
    viewport: {width: 1440, height: 1000},
    reducedMotion: 'reduce',
    trace: 'off',
  },
};
