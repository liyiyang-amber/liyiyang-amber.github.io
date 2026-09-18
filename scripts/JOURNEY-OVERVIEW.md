# Switzerland / Dolomites overview

## Seceda sculpted ridge revision — approval sample only

The installed 150-second film remains unchanged. The six-shot Seceda revision
uses `config/journey-seceda.json` and writes to `cinematic-v3-seceda-sculpted`
outside the repository. The previous Seceda sample is also preserved and hashed.
The user explicitly approved photo-guided artistic geometry refinement: this is
not a new high-resolution survey. A six-metre replacement mesh trims the broad
DEM shoulders into asymmetric blades, preserving measured crest anchors,
height scale, boundary seams, and a 30 m corridor around mapped routes. The source
DEM files remain byte-identical. Layered clouds retain valley and summit mist
after the foreground reveal has cleared. Day 7 remains clear.

```sh
python3 scripts/prepare-journey-seceda.py --work /absolute/scratch
python3 scripts/test-journey-seceda.py --work /absolute/scratch
python3 scripts/encode-journey-film.py --work /absolute/scratch --blender /path/to/Blender --scenery-sample --scenery-dir cinematic-v3-seceda-sculpted --stills
# Inspect all proof frames before motion rendering:
python3 scripts/test-journey-seceda.py --work /absolute/scratch --proofs
python3 scripts/encode-journey-film.py --work /absolute/scratch --blender /path/to/Blender --scenery-sample --scenery-dir cinematic-v3-seceda-sculpted
python3 scripts/test-journey-seceda.py --work /absolute/scratch --rendered --decode-baseline
python3 scripts/preview-journey-seceda.py --work /absolute/scratch
```

Preparation uses the existing local NumPy/SciPy runtime; Blender does not need
SciPy. No downloaded images are embedded into the film. Their original paths
and SHA-256 hashes are retained as reference provenance. At least 8 GiB free is
required before preparation/rendering. Sample duration is 12.5 seconds / 300
frames, not the earlier fixed 15 seconds. Do not assemble or install the full
film until this specific sample is approved. The assembly helper requires its
explicit approved checksum and verifies all 3,300 unchanged decoded frames.

## Approved scenery revision — full-film preparation in progress

The earlier temporary cache subsequently disappeared. The user explicitly
authorized rebuilding the full film. The replacement cache now lives outside
both the repository and `/tmp`, under the app's writable visualization workspace
in `journey-film-render/`. Blender 4.5.13 is restored from the official disk image,
SHA-256 `663ce944257c61ff1d6aa09e15c8f57bbd8d59023adb2fa7edde33a9ed960b53`,
and mounted read-only. Terrain and map sources are downloaded and hashed again.

When the historical sample bytes are unavailable, explicitly pass
`--recover-missing-sample` to the scenery-film preparation and test commands.
This uses the retained, user-approved `config/journey-scenery.json` and records
the cache loss and rebuild authorization in provenance. It does **not** claim to
have reverified the unavailable sample's historical checksum. New proofs and
full-frame validation are still required before replacing the website film.

The user approved the corrected upper-slope-mist sample, then requested the full
render to continue. `config/journey-scenery-film.json` now specifies 68 shots,
150 seconds / 3,600 frames, and 47 seconds of destination-focused scenery within
the original day budgets. It inherits the approved four scene treatments,
including Ortisei's four-second transition, and uses the walking pair on all five
hikes. Additional original castle, clock-tower, chalet, flag, boat and waterfall
models require rendered proof review before motion rendering.

New landmark anchors are checked against cached OSM records (Swiss Overpass and
the White Tower's individual OSM API record). Small houses, vineyard rows and
boats remain explicitly illustrative. No website content, route, photo manifest,
production media or earlier sample has been replaced.

The separate output directory is `SCRATCH/cinematic-v3-film`. On 2026-09-18,
the terrain cache and full-film payload were rebuilt with more than 8 GiB free.
All 68 proofs pass the 204 first/middle/last camera, walking-pair and upper-mist
pose checks. Visual review corrected the Spiez, Lauterbrunnen, Mürren, Wengen
and Brixen camera compositions. Full motion rendering has started, but this is
not yet a completed replacement film. The encoder checks the 8 GiB threshold before each batch,
allowing up to 45 seconds for temporary system resources to be released without
deleting any files or lowering the threshold.

With at least 8 GiB free (append `--recover-missing-sample` to preparation/tests
when rebuilding after the explicitly authorized historical cache loss):

```sh
python3 scripts/test-journey-scenery-film.py --work /absolute/scratch
python3 scripts/prepare-journey-scenery-film.py --work /absolute/scratch
python3 scripts/encode-journey-film.py --work /absolute/scratch --blender /path/to/Blender --scenery-film --stills
python3 scripts/test-journey-scenery-film.py --work /absolute/scratch --proofs
# Inspect all proofs and resolve visual issues before the motion batches:
python3 scripts/encode-journey-film.py --work /absolute/scratch --blender /path/to/Blender --scenery-film
python3 scripts/test-journey-scenery-film.py --work /absolute/scratch --rendered
```

Use `--shots ID...` for bounded proof/render/test subsets. Do not edit rendering
code during active batches. The original sample tests contain historical site
hashes; the new full-film checks instead capture the current user-edited page at
preparation and verify it stays untouched throughout rendering.

## Ortisei upper-slope mist correction

Only the four-second Ortisei shot changes. Its `mist_placement` profile locates
the visible ridge from the unchanged camera using cached terrain, places volumes
over the upper forest, and applies a world-elevation smoothstep to both volume
density and ambient fill. Mist is zero below 60% of the church-to-ridge rise and
fully enabled above 75%; cloud drift cannot move this elevation cutoff.

The revision uses a separate `cinematic-v3-upper-mist` directory. The original
sample remains intact. Explicit `frozen_shots` entries retain the original
fingerprints and SHA-256 hashes of all three approved clips and their audits;
they are not presented as renders made with the revised code. Preparation rejects
reuse if any scenery settings beyond Ortisei's placement have changed, and the
encoder verifies the frozen artifacts before reusing them. Only Ortisei renders.

```sh
python3 scripts/prepare-journey-scenery.py --work /absolute/scratch --scenery-dir cinematic-v3-upper-mist --reuse-sample /absolute/scratch/cinematic-v3
python3 scripts/encode-journey-film.py --work /absolute/scratch --blender /path/to/Blender --scenery-sample --scenery-dir cinematic-v3-upper-mist --stills
python3 scripts/test-journey-scenery.py --work /absolute/scratch --scenery-dir cinematic-v3-upper-mist --proofs
# Inspect beginning, midpoint and end proofs before rendering the 96 frames:
python3 scripts/encode-journey-film.py --work /absolute/scratch --blender /path/to/Blender --scenery-sample --scenery-dir cinematic-v3-upper-mist
python3 scripts/test-journey-scenery.py --work /absolute/scratch --scenery-dir cinematic-v3-upper-mist --rendered
```

The resulting sample still totals 15 seconds / 360 frames. The production film
and page remain unchanged, pending approval of the corrected sample. Do not use
the original sample's directory as this revision's output or alter rendering code
while a batch is running.

The corrected sample was rendered on 2026-09-16: 1,251,824 bytes, SHA-256
`e58845fb8a86a279932921919fc67c0add541121eb0265bd793442098a3e30db`.
Only Ortisei's 96 motion frames were rendered (approximately 11 minutes).
The first 264 decoded frames have the same frame-checksum digest in both samples:
`67cef30390730813e2ebf4e7260a293d4fc85a763a662d2bd1091d755bf3a397`.
All frames passed the pose/elevation-mask checks; the three reused clips and the
original sample, production film, page and photo references retained their hashes.
Native playback and pause, 390px/1440px layout and zero page overflow were checked.
The correction remains a review sample, not approval to replace the full film.

## Revised scenery sample: approval still required

`config/journey-scenery.json` specifies a separate 15-second, four-shot study:
Oeschinensee and two adult hikers (5s), Männlichen snow/sunlight (3s), Santa
Maddalena church/meadow (3s), and Ortisei's changing atmosphere (4s). It does
not authorize replacing or rendering the full 150-second film. The existing
film, poster, page manifest, route geometry and previous sample remain intact.

`scripts/journey-scenery.py` supplies original landmark models, photo-guided
regional snow masks, bounded 3D cloud/mist volumes, and two physically sized
walkers. Church anchors come from the official municipal/tourism map links
recorded in the configuration. Surrounding houses are illustrative. The
weather is photo-inspired, not a reconstructed historical timeline; there
is no snowfall. Blender's default 100 m volumetric cutoff is explicitly
extended for mountain-scale clouds, with volume shadows enabled.

```sh
python3 scripts/prepare-journey-scenery.py --validate-only
python3 scripts/test-journey-scenery.py
python3 scripts/prepare-journey-scenery.py --work /absolute/scratch
python3 scripts/encode-journey-film.py --work /absolute/scratch --blender /path/to/Blender --scenery-sample --stills
python3 scripts/test-journey-scenery.py --work /absolute/scratch --proofs
# Visually approve the corrected stills internally before motion rendering:
python3 scripts/encode-journey-film.py --work /absolute/scratch --blender /path/to/Blender --scenery-sample
python3 scripts/test-journey-scenery.py --work /absolute/scratch --rendered
```

The revised workflow requires the existing `cinematic-film/film.json` and its
cached terrain, writes only to `SCRATCH/cinematic-v3`, and requires **8 GiB free
before preparation and every render batch**, including sample batches. No
new DEM downloads or dependencies are needed. First/middle/last pose audits
check camera clearance; the revised checks additionally validate both walkers,
their independent stance-foot contact, sample-only authorization, and unchanged
production media/page hashes. Tests reject stale prepared scenery.

The sample is named `journey-scenery-approval-sample.mp4`, inside the isolated
`cinematic-v3` directory, with a matching poster and `preview.html`. It remains
a 15-second approval artifact, not the production film. Do not change renderer/configuration
while a batch is running. The planned full-film allocation reserves 45 seconds
for destination-forward views within the unchanged day budgets; that story
revision and the full render remain gated on approval of this new sample.

The revised approval sample was rendered locally on 2026-09-16: 15 seconds,
360 frames, 1280×960, 24 fps, silent H.264, 1,298,024 bytes (1.24 MiB).
Its SHA-256 is `8200c41b03283ea51ab36f809a917a8397b3fbc2c8239a45a64224a4cec3cb34`.
The four motion batches took approximately 37 minutes in total, including scene
setup, rendering and per-shot encoding. All 360 pose records and the final media
passed validation; source-photo, production-film and page hashes were unchanged.
Native playback/pause/resume, the 390px and laptop layouts, map-to-place focus,
day/route dialogs and gallery keyboard scrolling were checked locally. The sample
preview requires explicit playback and has no JavaScript or autoplay. Approval
of this revised sample is still required before the full-film scenery revision.

## Approved 150-second cinematic film

The user approved the 15-second visual sample. `config/journey-film.json` now
provides 65 chronological shots, totaling 150 seconds / 3,600 frames at 24 fps.
It reuses the sample's 48-sample EEVEE style and fixed physical vehicle sizes.
74.5% of the timeline uses low scenic views. All 18 places, 29 route legs, five
hikes, and outward/return cableway stages are covered. Transfers are animation
labels only; the map manifest and route geometry remain unchanged.

The full film was rendered and locally integrated on 2026-09-16:
`assets/media/travel/swiss-dolomites-cinematic.mp4` is a silent 1280×960 H.264
MP4, 150 seconds / 3,600 frames, 14,762,281 bytes (14.08 MiB). Its SHA-256 is
`9e106bb8b9b6b2ecea6a07613475f0a17d827c14166edaed5876510d9623f863`.
The matching `swiss-dolomites-cinematic-poster.jpg` and local cinematic provenance
JSON are referenced by `journey.overview`. Duration comes from the metadata;
GIF and provenance links are optional. The former MP4, poster and GIF remain
untouched, but the active journey no longer advertises or loads the GIF.
Every rendered frame passed camera-clearance, fixed-scale and applicable model
framing checks. This is a local build, not a deployment.

```sh
python3 scripts/test-journey-film.py
python3 scripts/prepare-journey-film.py --work /absolute/scratch
python3 scripts/encode-journey-film.py --work /absolute/scratch --blender /path/to/Blender --stills
python3 scripts/test-journey-film.py --work /absolute/scratch --proofs
python3 scripts/encode-journey-film.py --work /absolute/scratch --blender /path/to/Blender
python3 scripts/test-journey-film.py --work /absolute/scratch --rendered
```

Full-film preparation and each render batch require **8 GiB free**. The encoder
keeps per-shot caches, verifies camera poses and media before removing only its
own numbered frames, and never publishes to the site. `--shots ID...` supports
bounded proof or motion checks. Review every proof and the completed film before
changing active page metadata. Sources, terrain, proofs, videos, and progress
live in `SCRATCH/cinematic-film/`. No GIF is generated. The original sample,
current video, and previous GIF are not removed by these commands.

Do not edit the renderer, compositor, encoder, story configuration, or prepared
payload during an active render. Stop the batch before changes and rerun
preparation; the fingerprinted cache then resumes only matching shots. Proof
checks cover first/middle/last camera poses, screen framing, endpoint callouts,
fixed model scales, and excessive visual ground clearance. Two low rail shots
use passenger-style scenery views; regional rail orientation uses a small
locator rather than enlarging the train. At remote patch boundaries the detailed
mesh blends into the lighter background terrain to avoid visible seams.

Close rail and road shots use positive OSM surface checks; ambiguous bridge or
tunnel intervals are rejected. Disconnected geometry is clipped separately,
never connected with invented tracks. Local detail samples Copernicus at 30 m;
distant backdrops are lighter. Ortisei's brief weather treatment is illustrative.

## Retained approval-sample workflow

The v2 direction is specified in `config/journey-cinematic.json`: a 150-second
video-only film with perspective cameras and physically sized cartoon transport.
The sample's original purpose was style approval before replacing the active
film. Its encoder deliberately has no full-film or GIF command.
Intermediate frames, lake/forest data, geometry checks and the sample remain in
the external scratch directory. No new dependencies are needed.

```sh
python3 scripts/prepare-journey-cinematic.py --validate-only
python3 scripts/encode-journey-cinematic.py --work /absolute/scratch --test-layout
python3 scripts/encode-journey-cinematic.py --work /absolute/scratch --blender /path/to/Blender --stills
python3 scripts/encode-journey-cinematic.py --work /absolute/scratch --blender /path/to/Blender
```

The user-approved sample commands refuse to run below 6 GiB free; the full-film
prerequisite remains 8 GiB. The validation commands do not render or download
anything. Inspect all five stills
before the motion sample. Labels are composed in screen space after rendering;
their point anchors come from camera-projected geographic endpoints. The source
route is not altered. A close railway shot requires a positive OpenStreetMap
above-ground check; ambiguous tunnels/bridges stop preparation. Foreground detail
is illustrative and does not claim centimetre-accurate terrain or individual trees.

The approved full-film workflow is documented above. These sample commands never
replace the active film. Do not treat the sample as the completed replacement.

## Retained 72-second film workflow

Local-only, reproducible Blender EEVEE rendering. The former page version used a
silent MP4, poster and downloadable GIF, never terrain or rendering libraries. Optional
`journey.overview` metadata enables the component; other journeys are unchanged.

## Inputs and dependencies

- `_travel/swiss+dolomites.md`: existing chronological itinerary, 18 places and 29 route legs.
- `assets/data/travel/swiss-dolomites-routes.geojson`: 24 existing route features, including five hikes.
- `assets/data/travel/swiss-dolomites-overview.json`: 72-second camera/chapter timing and explicit playback directions.
- Blender **4.5.13 LTS**, EEVEE; Python with NumPy, Pillow, fontTools and Brotli;
  Ruby for safe YAML parsing; FFmpeg / ffprobe.
- Existing local Playfair Display / Source Sans 3 fonts. Labels are rasterized
  from those fonts before rendering, avoiding Blender font-tessellation defects.

Use the official Blender build, verify its published checksum, and keep the app,
source downloads and intermediate frames in a dedicated scratch directory outside
the repository. Start with at least **8 GiB free**. Do not delete personal or
tracked files to make room. The encoder stops if available scratch space drops
below 1.5 GiB and removes only its own numbered PNG batches after verified encoding.

```sh
python3 scripts/prepare-journey-overview.py --work /absolute/scratch
/path/to/Blender --background --factory-startup --python scripts/render-journey-overview.py -- --work /absolute/scratch --chapter day-02 --sample
/path/to/Blender --background --factory-startup --python scripts/render-journey-overview.py -- --work /absolute/scratch --chapter day-02 --limit 24
python3 scripts/encode-journey-overview.py --work /absolute/scratch --blender /path/to/Blender
node scripts/test-travel-overview.js
env LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 ruby scripts/validate-travel-journey.rb _travel/swiss+dolomites.md
env LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 bundle exec jekyll build
```

`--terrain-only` is diagnostic and cannot be encoded as a release. Downloaded
responses are cached and SHA-256 hashes recorded. Encoding resumes completed
chapters only under a matching input/renderer fingerprint. Inspect sample stills
and motion before committing to the full 1,728-frame render. A frame takes roughly
one second on the development laptop; this is a rendering benchmark, not a promise
for other hardware. No soundtrack or third-party vehicle models are used.

## Geographic accuracy and credits

- Elevation: [Copernicus GLO-30 / GLO-90](https://registry.opendata.aws/copernicus-dem/),
  AWS cloud-optimized GeoTIFF distribution, **2021 release**. Heights are displayed
  at their physical scale in a local equirectangular projection (origin 9° E / 47° N).
  Source resolution is 30 m for scenic chapters and 90 m for regional chapters;
  the lightweight render meshes sample at roughly 32–101 m and 980 m respectively.
  This is real terrain, not photogrammetry, satellite imagery, or exact cliff geometry.
- [OpenStreetMap](https://www.openstreetmap.org/copyright) provides current lake and
  forest outlines. Forest detail is used in scenic chapters, generalized away in
  regional views. Lake outlines are retained. Data are under ODbL 1.0; response
  source URLs, retrieval dates and hashes are in the provenance JSON.
- Existing route reconstructions and source notes remain in the page's route lists.
  Train positions follow physical railway geometry, not verified historical train
  operations. Overlay height is visual clearance, not tunnel, bridge or GPX altitude.
- Disconnected route parts remain disconnected. Playback changes camera position
  across gaps and never adds a fictitious connecting railway. Reversed legs and
  outward/return corridors are explicit in configuration, not inferred from labels.
- The Ortisei sunshine/cloud/rain passage is illustrative, not an exact weather
  chronology. Airport symbols do not introduce unsupplied flights.
- Original cartoon vehicles and the scenery palette reference the supplied
  Oeschinensee and Seceda photographs; no personal photographs are uploaded.

Required adapted-terrain credit: Produced using Copernicus WorldDEM-30 and
WorldDEM-90 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018
provided under COPERNICUS by the European Union and ESA; all rights reserved.
See the [dataset licence and attribution guidance](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).

## Page behavior

Native controls, `muted`, `playsinline`, `loop`, and a poster work without
JavaScript. With JavaScript, playback starts at 35% visibility; leaving the
viewport or hiding the tab pauses it. A manual pause persists. Reduced motion
never starts playback without an explicit play action. If supplied, an optional
GIF is only an anchor download, not an embedded image; this journey has no GIF
link. The ordinary map, galleries and journal anchors
are independent of this enhancement.
