/* Local Chromium verification. Run only against the supplied localhost preview. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

async function main() {
  const [url, output, packageRoot] = process.argv.slice(2);
  assert(url && /^http:\/\/127\.0\.0\.1:\d+\//.test(url), 'A local preview URL is required');
  assert(output && packageRoot, 'Output directory and bundled Node package root are required');
  const { chromium } = require(path.join(packageRoot, 'playwright'));
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  const report = [];
  try {
    for (const [width, height, motion, javascript] of [[1440, 900, 'reduce', true], [390, 844, 'reduce', true], [1440, 900, 'no-preference', true], [390, 844, 'reduce', false]]) {
      const context = await browser.newContext({ viewport: { width, height },
        isMobile: width === 390, hasTouch: width === 390, reducedMotion: motion, javaScriptEnabled: javascript });
      // No analytics or third-party media requests; also exercise tile failure.
      await context.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1'
        ? route.continue() : route.abort());
      const page = await context.newPage();
      const requests = [];
      const errors = [];
      page.on('request', request => requests.push(new URL(request.url()).pathname));
      page.on('pageerror', error => errors.push(error.message));
      const wait = async (fn, arg) => {
        const until = Date.now() + 30000;
        while (Date.now() < until) {
          if (await page.evaluate(fn, arg)) return;
          await page.waitForTimeout(100);
        }
        throw new Error('Timed out: ' + fn);
      };
      await page.goto(url, { waitUntil: 'networkidle' });
      assert.equal(await page.locator('video').count(), 0);
      assert.equal(await page.locator('script[src*="travel-overview.js"]').count(), 0);
      assert(!requests.some(p => p.endsWith('.mp4') || p.includes('cinematic-poster')));
      const link = page.locator('#travel-map-instructions #travel-overview-title');
      assert.equal(await link.innerText(), 'Click to see the overview route video');
      assert.equal(await link.getAttribute('target'), null);
      const videoURL = new URL(await link.getAttribute('href'), url);
      await link.scrollIntoViewIfNeeded();
      assert(await link.isVisible());
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({ path: path.join(output, `map-${width}-${motion}-${javascript}.png`) });
      if (width === 390) await link.tap();
      else { await link.focus(); await link.press('Enter'); }
      await page.waitForURL(videoURL.href);
      assert.equal(context.pages().length, 1);
      assert.equal(await page.locator('.sidebar, [data-travel-map], script[src*="leaflet"], link[href*="leaflet"], script[src*="travel-journey.js"]').count(), 0);
      assert.equal(await page.locator('script[src*="travel-overview.js"]').count(), 1);
      assert.equal(await page.locator('.masthead, .page__footer').count(), 2);
      assert(!(await page.locator('#travel-overview-description').innerText()).includes('sources are below'));
      const video = page.locator('video').first();
      await video.scrollIntoViewIfNeeded();
      const state = await video.evaluate(v => ({ paused: v.paused, controls: v.controls,
        muted: v.muted, inline: v.playsInline, loop: v.loop,
        w: v.getBoundingClientRect().width, h: v.getBoundingClientRect().height }));
      assert(state.controls && state.muted && state.inline && state.loop);
      assert(Math.abs(state.w / state.h - 4 / 3) < 0.01);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
      if (motion === 'reduce') {
        assert(state.paused);
        await video.focus();
        if (javascript) await video.press('Space');
        else { const box = await video.boundingBox(); await video.click({ position: { x: 25, y: box.height - 49 } }); }
      }
      await wait(() => document.querySelector('video').currentTime > 0.1);
      const media = await video.evaluate(v => ({ duration: v.duration, width: v.videoWidth,
        height: v.videoHeight, error: v.error && v.error.message }));
      assert.equal(media.duration, 150);
      assert.equal(media.width, 1280); assert.equal(media.height, 960); assert.equal(media.error, null);
      await video.focus(); await video.press('Space');
      assert(await video.evaluate(v => v.paused));
      await page.locator('.page__footer').scrollIntoViewIfNeeded();
      await video.scrollIntoViewIfNeeded();
      await page.waitForTimeout(400);
      assert(await video.evaluate(v => v.paused), 'Respect manual pause after scrolling');
      await video.evaluate(v => { v.currentTime = 113.25; });
      await wait(() => !document.querySelector('video').seeking);
      await page.screenshot({ path: path.join(output, `film-${width}-${motion}-${javascript}.png`) });
      await video.evaluate(v => { v.currentTime = 149.6; });
      await wait(() => !document.querySelector('video').seeking);
      await video.focus(); await video.press('Space');
      await wait(() => document.querySelector('video').currentTime < 1.5 && !document.querySelector('video').paused);
      await video.press('Space');
      const download = page.locator('a[download]').filter({ hasText: 'Download MP4' });
      const downloaded = await context.request.get(new URL(await download.getAttribute('href'), url).href);
      assert(downloaded.ok());
      assert((await downloaded.body()).equals(fs.readFileSync(path.join(__dirname, '../assets/media/travel/swiss-dolomites-cinematic.mp4'))));
      await page.locator('[data-journey-return]').click();
      await page.waitForURL(u => u.hash === '#travel-map-instructions' && u.pathname === new URL(url).pathname);
      assert.equal(await page.locator('video').count(), 0);
      const places = page.locator('[data-place-id]');
      if (await places.count()) {
        assert.equal(await places.count(), 18);
        const heading = page.locator('#journey-place-kandersteg [data-place-name]');
        await page.locator('a[href="#journey-place-kandersteg"]').first().click();
        assert(new URL(page.url()).hash === '#journey-place-kandersteg');
        await heading.waitFor({ state: 'visible' });
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
        assert(await page.locator('#journey-place-kandersteg .gallery-item').count() >= 4);
      }
      let routePointerClose = null;
      if (javascript) {
        await page.locator('[data-day-trigger]').first().click();
        assert(await page.locator('[data-day-dialog]').evaluate(d => d.open));
        await page.keyboard.press('Escape');
        assert(!(await page.locator('[data-day-dialog]').evaluate(d => d.open)));
        await page.locator('[data-route-trigger]').first().click();
        assert(await page.locator('[data-route-dialog]').evaluate(d => d.open));
        try {
          await page.locator('[data-route-dialog] [data-dialog-close]').click({ timeout: 2000 });
          routePointerClose = true;
        } catch (error) {
          if (!error.message.includes('intercepts pointer events')) throw error;
          // Report this existing dialog issue rather than changing unrelated styling.
          routePointerClose = false;
          await page.screenshot({ path: path.join(output, `route-close-overlap-${width}-${motion}.png`) });
          console.warn('ROUTE_CLOSE_POINTER_OVERLAP', width, motion, '; verifying Escape dismissal separately');
          await page.keyboard.press('Escape');
        }
        assert(!(await page.locator('[data-route-dialog]').evaluate(d => d.open)));
      }
      const gallery = page.locator('#journey-place-kandersteg .gallery-container');
      await gallery.scrollIntoViewIfNeeded();
      assert(await gallery.evaluate(el => {
        if (el.scrollWidth <= el.clientWidth) return false;
        el.scrollLeft = 50;
        return el.scrollLeft > 0;
      }), 'Kandersteg gallery remains horizontally scrollable');
      assert.equal(errors.length, 0, errors.join('\n'));
      report.push({ viewport: [width, height], ...state, ...media,
        reduced_motion: motion === 'reduce', javascript, pause: true, loop_replay: true, horizontal_overflow: false,
        main_page_media_requests: false, video_page_leaflet: false, navigation: 'same-tab',
        route_pointer_close: routePointerClose,
        blocked_external_resources: true, places: await places.count() });
      await context.close();
    }
  } finally { await browser.close(); }
  fs.writeFileSync(path.join(output, 'browser-checks.json'), JSON.stringify(report, null, 2));
  console.log('FILM_BROWSER_TESTS_OK', JSON.stringify(report));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
