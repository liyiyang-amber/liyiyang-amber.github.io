---
title: "White Dress"
excerpt: "'You were my man, felt like I got this.'"
permalink: /memories/white_dress
date: 2026-06-01
header:
  overlay_image: covers/Wd_cover.jpg
  overlay_filter: 0.25
---

<div class="music-player" id="white-dress-player">
  <div class="player-card" style="background-image: url('{{ '/images/covers/Wd_cover.jpg' | relative_url }}')">
    <div class="background-blur"></div>
    <button class="play-toggle" type="button" aria-label="Play Succession" aria-pressed="false">
      <span class="play-icon" aria-hidden="true">▶</span>
      <span class="screen-reader-text play-status">Play</span>
    </button>
    <div class="player-overlay">
      <div class="player-controls">
        <div class="song-info">
          <p>Succession</p>
        </div>
        <div class="volume-control">
          <span>♪</span>
          <input type="range" class="volume-slider" min="0" max="1" step="0.01" value="0.7">
        </div>
      </div>
      <div class="progress-container">
        <div class="progress-bar"></div>
      </div>
    </div>
  </div>
  <audio class="audio-element fallback-audio" controls preload="metadata">
    <source src="{{ '/audios/Succession.mp3' | relative_url }}" type="audio/mpeg">
    Your browser does not support the audio element.
  </audio>
</div>

<script>
(function() {
  const player = document.getElementById('white-dress-player');
  if (!player || player.dataset.initialized === 'true') {
    return;
  }
  player.dataset.initialized = 'true';

  const audio = player.querySelector('.audio-element');
  const progressBar = player.querySelector('.progress-bar');
  const progressContainer = player.querySelector('.progress-container');
  const volumeSlider = player.querySelector('.volume-slider');
  const playerCard = player.querySelector('.player-card');
  const playToggle = player.querySelector('.play-toggle');
  const playIcon = player.querySelector('.play-icon');
  const playStatus = player.querySelector('.play-status');

  if (!audio || !playerCard || !playToggle) {
    return;
  }

  player.classList.add('is-enhanced');
  audio.controls = false;

  const updatePlayState = () => {
    const isPlaying = !audio.paused && !audio.ended;
    player.classList.toggle('playing', isPlaying);
    playToggle.setAttribute('aria-pressed', String(isPlaying));
    playToggle.setAttribute('aria-label', isPlaying ? 'Pause Succession' : 'Play Succession');

    if (playIcon) {
      playIcon.textContent = isPlaying ? '❚❚' : '▶';
    }

    if (playStatus) {
      playStatus.textContent = isPlaying ? 'Pause' : 'Play';
    }
  };

  const showNativeFallback = () => {
    player.classList.remove('is-enhanced', 'playing');
    player.classList.add('playback-error');
    audio.controls = true;
  };

  const playAudio = () => {
    if (audio.ended) {
      audio.currentTime = 0;
    }

    const playPromise = audio.play();
    if (playPromise && typeof playPromise.catch === 'function') {
      playPromise.catch((error) => {
        console.warn('Succession audio playback failed. Showing native controls.', error);
        showNativeFallback();
      });
    }
  };

  const togglePlayPause = (event) => {
    if (!player.classList.contains('is-enhanced')) {
      return;
    }

    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    if (audio.paused || audio.ended) {
      playAudio();
    } else {
      audio.pause();
    }
  };

  const updateProgress = () => {
    if (progressBar && audio.duration && isFinite(audio.duration)) {
      progressBar.style.width = `${(audio.currentTime / audio.duration) * 100}%`;
    }
  };

  if (volumeSlider) {
    const initialVolume = Number(volumeSlider.value);
    audio.volume = Number.isNaN(initialVolume) ? 0.7 : initialVolume;
  }

  audio.load();

  audio.addEventListener('play', updatePlayState);
  audio.addEventListener('pause', updatePlayState);
  audio.addEventListener('ended', updatePlayState);
  audio.addEventListener('timeupdate', updateProgress);
  audio.addEventListener('loadedmetadata', updateProgress);
  audio.addEventListener('error', showNativeFallback);

  playToggle.addEventListener('click', togglePlayPause);
  playerCard.addEventListener('click', (event) => {
    const target = event.target;
    if (target instanceof Element && target.closest('.progress-container, .volume-control, .play-toggle, .fallback-audio')) {
      return;
    }

    togglePlayPause(event);
  });

  if (progressContainer) {
    progressContainer.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();

      const rect = progressContainer.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickRatio = Math.max(0, Math.min(1, clickX / rect.width));

      if (audio.duration && isFinite(audio.duration)) {
        audio.currentTime = clickRatio * audio.duration;
        updateProgress();
      }
    });
  }

  if (volumeSlider) {
    const updateVolume = (e) => {
      e.stopPropagation();
      audio.volume = Number(volumeSlider.value);
    };

    volumeSlider.addEventListener('input', updateVolume);
    volumeSlider.addEventListener('change', updateVolume);
    volumeSlider.addEventListener('click', (e) => e.stopPropagation());
  }

  updatePlayState();
})();
</script>







When I listened to that song — Austerlitz – Allegro Moderato, from Succession — I linked it immediately to Lana Del Rey's 'White Dress'.

Not the lyrics, not the melody. The feeling. That ache of something lost, something you didn't even know you were holding until your hands were empty.

The faded old days. The naive and young ages. That summer when I was nineteen...