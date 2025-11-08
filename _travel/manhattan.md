---
title: "Manhattan Travel Log"
layout: single
excerpt: "'Fresh out of f***s forever.'"
permalink: /memories/manhattan
date: 2024-06-10
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

<!-- 
<div class="music-player">
  <div class="player-card" style="background-image: url('/images/covers/Manhattan_cover.jpg')">
    <div class="background-blur"></div>
    <div class="player-overlay">
      <div class="player-controls">
        <div class="song-info">
          <p>Manhattan Waltzes - Johann Strauss II.</p>
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
  <audio class="audio-element">
    <source src="/audios/Manhattan_waltzes.mp3" type="audio/mpeg">
    Your browser does not support the audio element.
  </audio>
</div> -->

<div class="music-player" id="manhattan-player">
  <div class="player-card" style="background-image: url('{{ site.baseurl }}/images/covers/Manhattan_cover.jpg')">
    <div class="background-blur"></div>
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
  <audio class="audio-element" preload="metadata">
    <source src="{{ site.baseurl }}/audios/Manhattan_waltzes.mp3" type="audio/mpeg">
    Your browser does not support the audio element.
  </audio>
</div>

<script>
(function() {
  // Only initialize if not already initialized
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

  if (!audio) {
    console.error('Audio element not found in player');
    return;
  }

  console.log('🎵 Manhattan Music Player initialized');
  console.log('📂 Audio src:', audio.querySelector('source')?.src);
  console.log('⏸️ Audio readyState:', audio.readyState);

  // Initialize volume
  audio.volume = volumeSlider ? volumeSlider.value : 0.7;
  
  // Preload audio
  audio.load();

  // Add playing class management
  audio.addEventListener('play', () => {
    player.classList.add('playing');
    console.log('▶️ Playing');
  });

  audio.addEventListener('pause', () => {
    player.classList.remove('playing');
    console.log('⏸️ Paused');
  });

  audio.addEventListener('ended', () => {
    player.classList.remove('playing');
    console.log('⏹️ Ended');
  });

  // Function to toggle play/pause
  const togglePlayPause = (e) => {
    // Ignore clicks on controls
    if (e.target.closest('.progress-container') || e.target.closest('.volume-control')) {
      return;
    }
    
    e.preventDefault();
    e.stopPropagation();
    
    console.log('👆 Player clicked');
    
    if (audio.paused) {
      console.log('🎬 Attempting to play...');
      console.log('📊 Current state:', {
        readyState: audio.readyState,
        networkState: audio.networkState,
        src: audio.currentSrc
      });
      
      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            console.log('✅ Playback started successfully!');
          })
          .catch(error => {
            console.error('❌ Playback failed:', error);
            // Show user-friendly error
            alert('Unable to play audio. Please try clicking again or check your browser settings.');
          });
      }
    } else {
      console.log('⏸️ Pausing...');
      audio.pause();
    }
  };

  // Add event listeners with proper event handling
  playerCard.addEventListener('click', togglePlayPause);
  
  // Better mobile support
  playerCard.addEventListener('touchend', (e) => {
    e.preventDefault();
    togglePlayPause(e);
  }, { passive: false });

  // Progress bar updates
  audio.addEventListener('timeupdate', () => {
    if (audio.duration && isFinite(audio.duration)) {
      const progress = (audio.currentTime / audio.duration) * 100;
      progressBar.style.width = `${progress}%`;
    }
  });

  // Click to seek
  if (progressContainer) {
    const seekAudio = (e) => {
      e.stopPropagation();
      const rect = progressContainer.getBoundingClientRect();
      const clickX = (e.clientX || (e.touches && e.touches[0].clientX)) - rect.left;
      const clickRatio = Math.max(0, Math.min(1, clickX / rect.width));
      if (audio.duration && isFinite(audio.duration)) {
        audio.currentTime = clickRatio * audio.duration;
        console.log('⏩ Seeked to:', (clickRatio * 100).toFixed(1), '%');
      }
    };
    
    progressContainer.addEventListener('click', seekAudio);
    progressContainer.addEventListener('touchend', (e) => {
      e.preventDefault();
      seekAudio(e);
    }, { passive: false });
  }

  // Volume control
  if (volumeSlider) {
    const updateVolume = (e) => {
      e.stopPropagation();
      audio.volume = volumeSlider.value;
      console.log('🔊 Volume:', (audio.volume * 100).toFixed(0) + '%');
    };
    
    volumeSlider.addEventListener('input', updateVolume);
    volumeSlider.addEventListener('change', updateVolume);
    
    // Prevent propagation of click events
    volumeSlider.addEventListener('click', (e) => e.stopPropagation());
    volumeSlider.addEventListener('touchend', (e) => e.stopPropagation());
  }

  // Enhanced error handling
  audio.addEventListener('error', (e) => {
    console.error('❌ Audio error:', e);
    const err = audio.error;
    if (err) {
      const errorMessages = {
        1: 'MEDIA_ERR_ABORTED - Playback was aborted',
        2: 'MEDIA_ERR_NETWORK - Network error occurred',
        3: 'MEDIA_ERR_DECODE - Audio decoding failed',
        4: 'MEDIA_ERR_SRC_NOT_SUPPORTED - Audio format not supported or file not found'
      };
      console.error('Error code:', err.code, '-', errorMessages[err.code] || 'Unknown error');
      console.error('Audio src attempted:', audio.currentSrc);
    }
  });

  // Loading states logging
  audio.addEventListener('loadstart', () => console.log('📥 Loading started'));
  audio.addEventListener('loadedmetadata', () => console.log('✅ Metadata loaded, duration:', audio.duration, 's'));
  audio.addEventListener('loadeddata', () => console.log('✅ Data loaded'));
  audio.addEventListener('canplay', () => console.log('▶️ Can play'));
  audio.addEventListener('canplaythrough', () => console.log('✅ Can play through'));
  audio.addEventListener('stalled', () => console.warn('⚠️ Loading stalled'));
  audio.addEventListener('suspend', () => console.log('⏸️ Loading suspended'));
  audio.addEventListener('waiting', () => console.log('⏳ Waiting for data'));
  audio.addEventListener('playing', () => console.log('🎶 Actually playing now'));

  console.log('✅ Player setup complete');
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

