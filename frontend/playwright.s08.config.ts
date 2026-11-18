import {defineConfig} from '@playwright/test';
export default defineConfig({
 testDir:'./tests/browser',testMatch:['s08.spec.ts','s08-fix-01.spec.ts','core.spec.ts'],grep:/S08|core shared provider/,
 fullyParallel:false,workers:1,retries:0,
 reporter:[['list'],['json',{outputFile:'test-results/s08-results.json'}]],
 use:{baseURL:process.env.INVEST_BROWSER_URL||'http://127.0.0.1:3108',viewport:{width:1440,height:1000},launchOptions:{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||'/usr/bin/google-chrome'},trace:'retain-on-failure'},
});
