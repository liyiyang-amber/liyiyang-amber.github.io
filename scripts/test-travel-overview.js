/* Dependency-free regression tests for native-video progressive enhancement. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const code = fs.readFileSync('assets/js/travel-overview.js', 'utf8');

function setup(reduced, observerSupported = true) {
  const listeners = {};
  const docListeners = {};
  let onIntersection;
  let onMotion;
  const preference = { matches: reduced, addEventListener: (_, fn) => { onMotion = fn; } };
  const video = {
    paused: true, plays: 0,
    addEventListener: (type, fn) => { listeners[type] = fn; },
    play() { this.plays++; this.paused = false; listeners.play(); return Promise.resolve(); },
    pause() { this.paused = true; listeners.pause(); }
  };
  const document = { hidden: false, querySelector: () => video, addEventListener: (type, fn) => { docListeners[type] = fn; } };
  const window = { matchMedia: () => preference };
  function IntersectionObserver(fn) { onIntersection = fn; this.observe = () => {}; }
  if (observerSupported) window.IntersectionObserver = IntersectionObserver;
  vm.runInNewContext(code, { document, window, IntersectionObserver });
  return {
    video,
    visible(value) { onIntersection([{ isIntersecting: value, intersectionRatio: value ? .7 : 0 }]); },
    hidden(value) { document.hidden = value; docListeners.visibilitychange(); },
    motion(value) { preference.matches = value; onMotion(); }
  };
}

const normal = setup(false);
assert.equal(normal.video.plays, 0, 'no eager playback');
normal.visible(true);
assert.equal(normal.video.paused, false);
normal.visible(false);
assert.equal(normal.video.paused, true);
normal.visible(true);
assert.equal(normal.video.paused, false, 'resume viewport-driven pause');
normal.video.pause();
normal.visible(false); normal.visible(true);
normal.hidden(true); normal.hidden(false);
assert.equal(normal.video.paused, true, 'respect manual pause across visibility changes');
normal.video.play();
normal.hidden(true); normal.hidden(false);
assert.equal(normal.video.paused, false, 'manual replay re-enables visibility handling');
normal.motion(true);
assert.equal(normal.video.paused, true, 'new reduced-motion preference pauses autoplay');
normal.visible(false); normal.visible(true);
assert.equal(normal.video.paused, true);
normal.video.play();
assert.equal(normal.video.paused, false, 'explicit reduced-motion playback remains available');

const reduced = setup(true);
reduced.visible(true);
assert.equal(reduced.video.plays, 0, 'reduced motion starts on the poster');
reduced.video.play();
reduced.visible(false); reduced.visible(true);
assert.equal(reduced.video.paused, false);
reduced.video.pause(); reduced.visible(false); reduced.visible(true);
assert.equal(reduced.video.paused, true);

const legacy = setup(false, false);
assert.equal(legacy.video.plays, 0, 'without an observer keep native controls only');
legacy.hidden(true); legacy.hidden(false);
assert.equal(legacy.video.plays, 0, 'tab visibility must not start playback in the legacy fallback');
legacy.video.play();
assert.equal(legacy.video.paused, false);
console.log('OVERVIEW_PLAYBACK_TESTS_OK');
