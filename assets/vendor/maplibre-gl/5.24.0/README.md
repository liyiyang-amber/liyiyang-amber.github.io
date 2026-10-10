# maplibre-gl 5.24.0

Source: https://registry.npmjs.org/maplibre-gl/-/maplibre-gl-5.24.0.tgz

npm integrity: `sha512-ALyFxgtd5R+65UqZ/++lOqwWcC0SNho9c27fYSyLmG7AfnAul2o46F05aDJGPbFU57wos9dgcIySHs0Xe6ia3A==`

Files copied unchanged from the verified npm package.
MapLibre uses the CSP bundle with a separately hosted worker.

## Journey map setup

The journey uses OpenFreeMap's standard Liberty style with the existing Leaflet
1.9.4 map and the locally hosted Leaflet adapter 0.1.3. No API key, account, or
development configuration override is needed. Run the normal Jekyll preview:

```sh
env LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 bundle exec jekyll serve
```

MapLibre's runtime, worker, CSS, and the adapter load only on journey pages.
The style, tiles, fonts, and sprites load from OpenFreeMap. Keep OpenFreeMap,
OpenMapTiles, and OpenStreetMap attribution visible. The public service has no
uptime guarantee. Integration: https://openfreemap.org/quick_start/#using-leaflet

If WebGL or map resources fail, the notice preserves access to the Leaflet routes,
markers, and complete itinerary. Reload after a resource error to retry. Slow
successful loads and restored WebGL contexts recover without hiding route errors.

Regression check: `node scripts/test-travel-map-background.cjs` from the repo root.

SHA-256:

- `maplibre-gl-csp.js`: `a1f1847bac64aa00acbf80fbb79b2c5af24d8eecaaa5e2ad14080fab81f1de95`
- `maplibre-gl-csp-worker.js`: `f950e7b15c49c8b9c7bb52136df2a2df2f6f03b83b8927774573fc98b067f7f0`
- `maplibre-gl.css`: `ab1e70d59ec40465bae7e7030da2f3ccf28133fd502e62bd598eefbadfd7a732`
- `LICENSE.txt`: `ee5fc05a0677eaf69601d2c7db0d9ecd6cc27c3abc1d0733bc9ed34707cf8ef2`
