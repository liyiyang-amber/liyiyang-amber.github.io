/* Native controls remain the fallback when JavaScript or autoplay is unavailable. */
(function () {
  'use strict';
  var video = document.querySelector('[data-travel-overview]');
  if (!video) return;
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var visible = false;
  var manuallyPaused = false;
  var automaticPause = false;
  var automaticPlay = false;
  var explicitlyPlaying = false;
  var canAutoplay = 'IntersectionObserver' in window;

  function pauseAutomatically() {
    if (video.paused) return;
    automaticPause = true;
    video.pause();
  }

  function updatePlayback() {
    if (!visible || document.hidden) {
      pauseAutomatically();
    } else if (!manuallyPaused && (canAutoplay || explicitlyPlaying) && (!reducedMotion.matches || explicitlyPlaying) && video.paused) {
      automaticPlay = true;
      var playback = video.play();
      if (playback && playback.catch) playback.catch(function () { automaticPlay = false; });
    }
  }

  video.addEventListener('pause', function () {
    if (automaticPause) automaticPause = false;
    else { manuallyPaused = true; explicitlyPlaying = false; }
  });
  video.addEventListener('play', function () {
    if (automaticPlay) automaticPlay = false;
    else { manuallyPaused = false; explicitlyPlaying = true; }
    if (!visible || document.hidden) pauseAutomatically();
  });
  document.addEventListener('visibilitychange', updatePlayback);
  function motionChanged() {
    if (reducedMotion.matches) {
      explicitlyPlaying = false;
      pauseAutomatically();
    } else updatePlayback();
  }
  if (reducedMotion.addEventListener) reducedMotion.addEventListener('change', motionChanged);
  else reducedMotion.addListener(motionChanged);
  if (canAutoplay) {
    new IntersectionObserver(function (entries) {
      visible = entries[0].isIntersecting && entries[0].intersectionRatio >= 0.35;
      updatePlayback();
    }, { threshold: [0, 0.35] }).observe(video);
  } else {
    // Older browsers keep native, user-initiated playback only.
    visible = true;
  }
}());
