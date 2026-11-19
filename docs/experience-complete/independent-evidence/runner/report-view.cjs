const {chromium}=require('@playwright/test');
(async()=>{const b=await chromium.launch();for(const width of [1440,390]){const p=await b.newPage({viewport:{width,height:1000}});await p.goto('file:///evidence/first-download.html');await p.screenshot({path:`/evidence/download-view-${width}.png`,fullPage:true});await p.close();}await b.close()})();
