'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const code = fs.readFileSync('assets/js/travel-journey.js', 'utf8');

async function setup(failure = null, routeFailure = false) {
  const state = { backgrounds: [], removals: 0, markers: 0, paths: 0, fits: 0, routeFetches: 0, attribution: '' };
  const status = { hidden: true, textContent: '' };
  const timers = new Map();
  const frameCallbacks = [];
  const mapHandlers = {};
  let zoom = 7;
  const events = {};
  const gl = { on(name, callback) { events[name] = callback; }, isStyleLoaded: () => true, areTilesLoaded: () => true };
  const element = attrs => ({
    getAttribute: name => attrs[name] ?? null,
    querySelector: () => null,
    classList: { toggle() {} },
  });
  const place = element({ 'data-place-id': 'kandersteg', 'data-latitude': '46.49', 'data-longitude': '7.67' });
  const route = element({ 'data-route-id': 'test-route', 'data-route-feature-id': 'test-feature',
    'data-route-status': 'mapped', 'data-route-mode': 'rail', 'data-route-day-id': 'day-01' });
  const toggle = { disabled: true };
  const mapElement = {
    addEventListener(name, callback) { mapHandlers[name] = callback; },
    getBoundingClientRect: () => ({ left: 0, top: 0, width: 600, height: 440 }),
  };
  const root = {
    getAttribute: name => name === 'data-map-worker-url' ? '/assets/vendor/maplibre-gl/5.24.0/maplibre-gl-csp-worker.js' : name === 'data-route-url' ? '/routes.geojson' : null,
    querySelector: selector => ({ '[data-travel-map]': mapElement, '[data-map-status]': status })[selector] || null,
    querySelectorAll: selector => ({ '[data-journey-place]': [place], '[data-journey-route]': [route],
      '[data-route-mode-toggle]': [toggle] })[selector] || [],
    addEventListener() {},
  };
  const bounds = { isValid: () => true, extend() { return this; }, getCenter: () => [46.49, 7.67] };
  const layers = new Set();
  const map = { on() {}, fitBounds() { state.fits++; }, hasLayer: layer => layers.has(layer),
    getZoom: () => zoom, getMinZoom: () => 1, getMaxZoom: () => 20,
    setZoomAround(anchor, target) { zoom = target; },
    getScaleZoom: (scale, start) => start + Math.log2(scale),
    removeLayer(layer) { layer.onRemove(); layers.delete(layer); state.removals++; }, attributionControl: { addAttribution(value) { state.attribution = value; } } };
  const L = {
    point: (x, y) => ({ x, y }),
    map(el, options) { assert.equal(el, mapElement); state.mapOptions = options; return map; },
    maplibreGL(options) {
      const layer = { options, onRemove() {},
        getMaplibreMap: () => failure === 'constructor' ? null : gl,
        getContainer: () => ({ remove() { state.containerRemoved = true; } }),
        addTo(target) {
          assert.equal(target, map);
          assert(state.fits > 0, 'Set the initial view before initializing the renderer');
          layers.add(this);
          if (failure === 'constructor') throw new Error('WebGL unavailable');
          return this;
        } };
      state.backgrounds.push(layer);
      return layer;
    },
    latLngBounds: () => bounds,
    divIcon: options => options,
    marker: () => ({ on() {}, addTo() { state.markers++; } }),
    geoJSON() {
      state.paths++;
      return { addTo() { layers.add(this); return this; }, getBounds: () => bounds,
        eachLayer(callback) { callback({ getElement: () => null, on() {} }); }, setStyle() {}, bringToFront() {} };
    },
  };
  if (failure === 'adapter') delete L.maplibreGL;
  const window = { L,
    GestureEvent: function () {},
    requestAnimationFrame(callback) { frameCallbacks.push(callback); return frameCallbacks.length; },
    cancelAnimationFrame() {},
    maplibregl: failure === 'runtime' ? undefined : { setWorkerUrl(url) { state.workerUrl = url; } },
    setTimeout(callback) { const id = timers.size + 1; timers.set(id, callback); return id; },
    clearTimeout(id) { timers.delete(id); }, innerWidth: 1440, matchMedia: () => ({ matches: false }), addEventListener() {},
    fetch: async () => {
      state.routeFetches++;
      return { ok: !routeFailure, json: async () => ({ type: 'FeatureCollection', features: [
        { type: 'Feature', properties: { id: 'test-feature' },
          geometry: { type: 'LineString', coordinates: [[7.67, 46.49], [7.68, 46.50]] } },
      ] }) };
    },
  };
  vm.runInNewContext(code, { window, document: { readyState: 'complete', querySelector: () => root,
    addEventListener() {} } });
  await new Promise(resolve => setImmediate(resolve));
  return { ...state, status, toggle, events, timers, mapHandlers, getZoom: () => zoom,
    flushFrames() { frameCallbacks.splice(0).forEach(callback => callback()); } };
}


(async () => {
  for (const failure of ['runtime', 'adapter', 'constructor']) {
    const state = await setup(failure);
    assert.equal(state.status.hidden, false);
    assert.match(state.status.textContent, /map background is unavailable/);
    assert.equal(state.markers, 1, 'Markers survive renderer failures');
    assert.equal(state.paths, 2, 'Route foreground and outline survive renderer failures');
    assert.equal(state.toggle.disabled, false);
    assert(state.fits > 0);
    assert.equal(state.mapOptions.maxZoom, 20);
    assert.equal(state.mapOptions.minZoom, 1);
    if (failure === 'constructor') {
      assert.equal(state.removals, 1, 'Remove a partially initialized adapter');
      assert.equal(state.containerRemoved, true);
    }
  }
  const state = await setup();
  assert.equal(state.backgrounds.length, 1);
  assert.equal(state.backgrounds[0].options.style, 'https://tiles.openfreemap.org/styles/liberty');
  assert.equal(state.backgrounds[0].options.interactive, false);
  assert.match(state.workerUrl, /^\/assets\/vendor\/maplibre-gl\//);
  for (const provider of ['OpenFreeMap', 'OpenMapTiles', 'OpenStreetMap']) assert(state.attribution.includes(provider));
  state.events.load();
  assert.equal(state.status.hidden, true);
  assert.equal(state.timers.size, 0);
  state.events.error();
  state.events.idle();
  assert.equal(state.status.hidden, false, 'An idle renderer does not prove failed resources recovered');
  assert.match(state.status.textContent, /map background is unavailable/);

  const slow = await setup();
  [...slow.timers.values()][0]();
  assert.equal(slow.status.hidden, false);
  slow.events.load();
  assert.equal(slow.status.hidden, true, 'A slow successful load recovers');
  slow.events.webglcontextlost();
  slow.events.idle();
  assert.equal(slow.status.hidden, false);
  slow.events.webglcontextrestored();
  slow.events.idle();
  assert.equal(slow.status.hidden, true, 'A restored context recovers');

  const failedRoutes = await setup(null, true);
  for (const event of ['load', 'error', 'idle', 'webglcontextlost', 'webglcontextrestored', 'idle']) {
    failedRoutes.events[event]();
    assert.equal(failedRoutes.status.hidden, false);
    assert.match(failedRoutes.status.textContent, /route layers could not be loaded/);
  }
  assert.equal(failedRoutes.markers, 1);
  assert.equal(failedRoutes.toggle.disabled, true);
  const pinch = await setup();
  const wheel = { ctrlKey: true, deltaY: -120, deltaMode: 0, clientX: 300, clientY: 220,
    preventDefault() {}, stopPropagation() {} };
  pinch.mapHandlers.wheel({ ...wheel, ctrlKey: false });
  pinch.flushFrames();
  assert.equal(pinch.getZoom(), 7, 'Ordinary scrolling does not zoom');
  pinch.mapHandlers.wheel(wheel);
  pinch.flushFrames();
  assert.equal(pinch.getZoom(), 9, 'Trackpad pinch zooms around the pointer');
  pinch.mapHandlers.gesturestart(wheel);
  pinch.mapHandlers.gesturechange({ ...wheel, scale: 2 });
  assert.equal(pinch.getZoom(), 10, 'Safari pinch gestures preserve scale');
  pinch.mapHandlers.gesturechange({ ...wheel, scale: 2 ** 30 });
  assert.equal(pinch.getZoom(), 20, 'Pinch respects the zoom limit');
  console.log('LIBERTY_MAP_CHECKS_OK: renderer failures, partial cleanup, routes, attribution, slow load, context recovery, route-error precedence, trackpad pinch');
})().catch(error => { console.error(error); process.exitCode = 1; });
