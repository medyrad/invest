module.exports = {
  testDir: '/checks',
  testMatch: '*.spec.ts',
  testIgnore: 'visual.spec.ts',
  timeout: 150000,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['junit', {outputFile: '/retest/browser-independent.xml'}]],
  outputDir: '/retest/browser-independent-artifacts',
  use: {
    baseURL: 'http://127.0.0.1:3109',
    viewport: {width: 1440, height: 1000},
    reducedMotion: 'reduce',
    trace: 'retain-on-failure',
  },
};
