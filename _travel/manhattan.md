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



<div class="music-player">
  <div class="player-card" style="background-image: url('/images/covers/Manhattan_cover.jpg')">
    <div class="background-blur"></div>
    <div class="player-overlay">
      <div class="player-controls">
        <div class="song-info">
          <p>Manhattan Waltzes - Johann Stauss II.</p>
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
    <source src="/audios/Manhattan_walzes.mp3" type="audio/mpeg">
  </audio>
</div>

<script>
document.querySelectorAll('.music-player').forEach(player => {
  const audio = player.querySelector('audio');
  const progressBar = player.querySelector('.progress-bar');
  const progressContainer = player.querySelector('.progress-container');
  const volumeSlider = player.querySelector('.volume-slider');
  
  // Initialize volume
  audio.volume = volumeSlider.value;

  // Play/Pause on click (excluding controls)
  player.addEventListener('click', (e) => {
    if (!e.target.closest('.progress-container') && !e.target.closest('.volume-control')) {
      audio.paused ? audio.play() : audio.pause();
    }
  });

  // Progress bar updates
  audio.addEventListener('timeupdate', () => {
    progressBar.style.width = `${(audio.currentTime / audio.duration) * 100}%`;
  });

  // Click to seek
  progressContainer.addEventListener('click', (e) => {
    const rect = progressContainer.getBoundingClientRect();
    audio.currentTime = ((e.clientX - rect.left) / rect.width) * audio.duration;
  });

  // Volume control
  volumeSlider.addEventListener('input', () => {
    audio.volume = volumeSlider.value;
  });
});
</script>



A year later, a friend insisted I listen to "Manhattan Walze" by Johann Strauss II. — that buoyant, spinning melody meant to soundtrack a city I’d only known as gridlock and grit. At first, it made no sense: how could a song so light, so untethered, belong to this jagged maze of scaffolding and honking cabs? Where was there room to waltz here???

But then I saw old Manhattan through the music:

- Gaslight flickering over cobblestones, horse-drawn carriages rattling down Broadway, still unpaved in places.
- Silk gowns swirling in the mirrored ballrooms of Fifth Avenue mansions, while tenement windows showed the silhouettes of garment workers bent over their needles.
- The first elevated trains screeching above streets thick with immigrants, the smell of roasting chestnuts battling coal smoke29.
- The last patches of countryside disappearing under waves of brownstones, the freshly-dug earth of Central Park still smelling of upturned soil.

Maybe the waltz wasn’t about the city as it is, but as it once dreamed of being — a place where, when night fell, the gas lamps would tame the chaos, the carriages would part, and two lovers could spin through the streets, past half-built skyscrapers, all the way to the park…

Before the concrete, before the noise—back when Manhattan was still a waltz.
