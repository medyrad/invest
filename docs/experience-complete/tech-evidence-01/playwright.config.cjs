module.exports={
  testDir:'/checks',testMatch:['design-capture.spec.ts'],timeout:180000,workers:1,retries:0,
  reporter:[['list'],['junit',{outputFile:'/evidence/design-browser.xml'}]],
  outputDir:'/evidence/browser-artifacts',
  use:{viewport:{width:1440,height:1000},reducedMotion:'reduce',trace:'off'}
};
