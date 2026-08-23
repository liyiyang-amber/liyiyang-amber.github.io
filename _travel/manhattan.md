---
title: "Manhattan Travel Log"
layout: single
excerpt: "'Fresh out of f***s forever.'"
permalink: /memories/manhattan
date: 2024-06-10
github_updated_at: 2026-08-04T01:08:17-04:00
header:
  overlay_image: covers/Manhattan_cover.jpg
  overlay_filter: 0.25
---

**2024.06.06 – 2024.06.09 Location: Manhattan, NYC, USA**

**Rain, Steel, and the Ghosts of Old New York**

The city greeted me with its usual chaos—endless customs lines, subway delays — the scenery shifting from drowsy countryside to the soot-stained underworld of Wall Street. New York’s subway really earns its title as the world’s worst. Rain and sun fought for dominance, a sticky, familiar humidity like Hangzhou’s, but layered with 3D urine, weed, and steam rising from sewer grates. Jet lag clung to me like a second skin.

But then, the steakhouse spinach—creamy, garlicky, perfect—and the buildings. God, the buildings. When the sun finally broke through, Manhattan turned into a postcard: sharp-edged towers against a blue so bright it hurt.


**Edge & The Sunset That Almost Made Me Forgive NYC**

From Edge, the city unfolded like a living thing—steel veins, glass skin, the Hudson a shimmering wound — its skyline aflame where the sun drowned in the river. For the first time, I didn’t hate New York. Later, MoMA’s white cubes and Summit’s dizzying mirrors made art feel like a game I wasn’t sure I was winning. But then, sunset. The sun bled red over New Jersey, and for a second, I understood why people stay.


**Wall Street Bulls, Tiny Islands, and Central Park’s Golden Hour**

The Charging Bull stood polished by a thousand hopeful hands (may we all get rich). I walked Little Island, then the long march uptown — past Vessel’s skeletal curves, through Central Park, where the light turned the grass to gold. Dappled shadows stretched like memories of carriages and gas lamps that might’ve once danced here. (Ha! The "twenty-minute effect of a garden.")

<div class="music-player" id="manhattan-player">
  <div class="player-card" style="background-image: url('{{ '/images/covers/Manhattan_cover.jpg' | relative_url }}')">
    <div class="background-blur"></div>
    <button class="play-toggle" type="button" aria-label="Play Manhattan Waltzes" aria-pressed="false">
      <span class="play-icon" aria-hidden="true">▶</span>
      <span class="screen-reader-text play-status">Play</span>
    </button>
    <div class="player-overlay">
      <div class="player-controls">
        <div class="song-info">
          <p>Manhattan Waltzes – Johann Strauss II.</p>
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
    <source src="{{ '/audios/Manhattan_waltzes.mp3' | relative_url }}" type="audio/mpeg">
    Your browser does not support the audio element.
  </audio>
</div>

<script>
(function() {
  const player = document.getElementById('manhattan-player');
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
    playToggle.setAttribute('aria-label', isPlaying ? 'Pause Manhattan Waltzes' : 'Play Manhattan Waltzes');

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
        console.warn('Manhattan audio playback failed. Showing native controls.', error);
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



A year later, a friend insisted I listen to "Manhattan Walze" by Johann Strauss II. — that buoyant, spinning melody meant to soundtrack a city I’d only known as gridlock and grit. At first, it made no sense: how could a song so light, so untethered, belong to this jagged maze of scaffolding and honking cabs? Where was there room to waltz here???

But then I saw old Manhattan through the music:

- Gaslight flickering over cobblestones, horse-drawn carriages rattling down Broadway, still unpaved in places.
- Silk gowns swirling in the mirrored ballrooms of Fifth Avenue mansions, while tenement windows showed the silhouettes of garment workers bent over their needles.
- The first elevated trains screeching above streets thick with immigrants, the smell of roasting chestnuts battling coal smoke29.
- The last patches of countryside disappearing under waves of brownstones, the freshly-dug earth of Central Park still smelling of upturned soil.

Maybe the waltz wasn’t about the city as it is, but as it once dreamed of being — a place where, when night fell, the gas lamps would tame the chaos, the carriages would part, and two lovers could spin through the streets, past half-built skyscrapers, all the way to the park…

Before the concrete, before the noise—back when Manhattan was still a waltz.
