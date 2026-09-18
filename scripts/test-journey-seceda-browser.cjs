/* Isolated review player checks. No interception/replacement of website media. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('/Users/amber_test/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
async function main(){
  const [url,out]=process.argv.slice(2);
  assert(/^http:\/\/127\.0\.0\.1:\d+\/compare\.html$/.test(url));
  fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const reports=[];
  try {
    for(const [width,height] of [[1440,1000],[390,844]]){
      const context=await browser.newContext({viewport:{width,height},hasTouch:width===390,isMobile:width===390,reducedMotion:'reduce'});
      await context.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());
      const page=await context.newPage();
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      await page.goto(url,{waitUntil:'networkidle'});
      const video=page.locator('#after');
      await video.scrollIntoViewIfNeeded();
      assert(await video.evaluate(v=>v.paused&&v.controls&&v.muted&&v.loop&&v.playsInline));
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      await video.focus();await video.press('Space');
      await page.waitForFunction(()=>document.querySelector('#after').currentTime>.1);
      await video.press('Space');assert(await video.evaluate(v=>v.paused));
      const media=await video.evaluate(v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight,error:v.error?.message||null}));
      assert.equal(media.duration,12.5);assert.equal(media.width,1280);assert.equal(media.height,960);assert.equal(media.error,null);
      for(const [name,time] of [['summit',2],['mist',4.55],['revealed',6.6],['return',10]]){
        await video.evaluate((v,t)=>{v.currentTime=t},time);
        await page.waitForFunction(t=>{const v=document.querySelector('#after');return !v.seeking&&Math.abs(v.currentTime-t)<.04},time);
        await page.waitForTimeout(150);
        await video.screenshot({path:path.join(out,`${width}-${name}.png`)});
      }
      await video.evaluate(v=>{v.currentTime=0});
      await page.waitForFunction(()=>!document.querySelector('#after').seeking);
      await video.focus();await video.press('Space');
      await page.waitForFunction(()=>document.querySelector('#after').currentTime>12,{},{timeout:20000});
      await page.waitForFunction(()=>document.querySelector('#after').currentTime<1&&!document.querySelector('#after').paused);
      await video.press('Space');
      const rect=await video.boundingBox();assert(Math.abs(rect.width/rect.height-4/3)<.01);
      const download=await page.request.get(new URL('journey-scenery-approval-sample.mp4',url).href);
      assert(download.ok());
      assert.equal(errors.length,0,errors.join('\n'));
      reports.push({viewport:[width,height],...media,explicitPlayback:true,pause:true,loopReplay:true,overflow:false,downloadBytes:(await download.body()).length});
      await context.close();
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(out,'browser-checks.json'),JSON.stringify(reports,null,2));
  console.log('SECEDA_BROWSER_OK',JSON.stringify(reports));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
