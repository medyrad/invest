import {defineConfig} from '@playwright/test';
export default defineConfig({
 testDir:'./tests/browser',testMatch:/core-fix-01\.spec\.ts/,workers:1,timeout:90000,retries:0,
 outputDir:'test-results/core-fix-01',reporter:[['list'],['json',{outputFile:'test-results/core-fix-01-results.json'}]],
 use:{baseURL:'http://127.0.0.1:3108',viewport:{width:1440,height:1000},actionTimeout:15000,trace:'off',launchOptions:{executablePath:'/usr/bin/google-chrome'}},
});
