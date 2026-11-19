module.exports = {
  testDir: '/checks',
  testMatch: 'visual.spec.ts',
  timeout: 180000,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['junit', {outputFile: '/retest/browser-visual.xml'}]],
  outputDir: '/retest/browser-visual-artifacts',
  use: {baseURL: 'http://127.0.0.1:3109', reducedMotion: 'reduce', trace: 'retain-on-failure'},
};
