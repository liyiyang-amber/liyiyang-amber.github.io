#!/usr/bin/env python3
"""Prepare real Copernicus terrain and OSM land cover outside the site checkout.

Dependencies: numpy, Pillow, fonttools (including its Brotli WOFF2 decoder), Ruby.
Usage: python3 scripts/prepare-journey-overview.py --work /absolute/scratch/path
Only source data referenced by this journey are downloaded. Downloads are cached,
hashed and recorded; intermediate data never belong in the published assets.
"""

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import math
from pathlib import Path
import subprocess
import shutil
import time
import urllib.parse
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "assets/data/travel/swiss-dolomites-overview.json"
MANIFEST = ROOT / "_travel/swiss+dolomites.md"
RADIUS = 6371.0088
SOURCES = []


def project(lon, lat):
    return ((np.asarray(lon) - 9) * math.pi / 180 * RADIUS * math.cos(math.radians(47)),
            (np.asarray(lat) - 47) * math.pi / 180 * RADIUS)


def unproject(x, y):
    return (np.asarray(x) / (math.pi / 180 * RADIUS * math.cos(math.radians(47))) + 9,
            np.asarray(y) / (math.pi / 180 * RADIUS) + 47)


def fetch(url, destination, post=None, attempts=3, timeout=150):
    if not destination.exists():
        if shutil.disk_usage(destination.parent).free < 8*1024**3:
            raise RuntimeError("8 GiB free required before downloading render assets")
        for attempt in range(attempts):
            try:
                print(f"SOURCE_FETCH {destination.name} attempt {attempt+1}/{attempts}", flush=True)
                req = urllib.request.Request(url, data=post,
                    headers={"User-Agent": "AmberJourneyOverview/1.0 (local cartographic render)"})
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    payload = response.read()
                destination.write_bytes(payload)
                print(f"SOURCE_READY {destination.name} {len(payload)} bytes", flush=True)
                break
            except Exception:
                if attempt == attempts-1:
                    raise
                time.sleep(2 + attempt * 3)
    SOURCES.append({"url": url, "file": destination.name,
                    "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
    return destination


class Elevation:
    def __init__(self, cache):
        self.cache = cache
        self.tiles = {}

    def tile(self, lat, lon, resolution):
        key = (lat, lon, resolution)
        if key not in self.tiles:
            code = "10" if resolution == 30 else "30"
            name = f"Copernicus_DSM_COG_{code}_N{lat:02}_00_E{lon:03}_00_DEM"
            url = f"https://copernicus-dem-{resolution}m.s3.amazonaws.com/{name}/{name}.tif"
            path = fetch(url, self.cache / f"{name}.tif")
            with Image.open(path) as image:
                scale = image.tag_v2[33550]
                tie = image.tag_v2[33922]
                array = np.asarray(image, dtype=np.float32).copy()
            self.tiles[key] = array, scale, tie
        return self.tiles[key]

    def sample(self, lon, lat, resolution):
        lon, lat = np.broadcast_arrays(lon, lat)
        output = np.zeros(lon.shape, dtype=np.float32)
        lat_index, lon_index = np.floor(lat).astype(int), np.floor(lon).astype(int)
        for south, west in set(zip(lat_index.flat, lon_index.flat)):
            select = (lat_index == south) & (lon_index == west)
            array, scale, tie = self.tile(south, west, resolution)
            # GeoTIFF tiepoint describes the upper-left raster edge.
            u = np.clip((lon[select] - tie[3]) / scale[0] - 0.5, 0, array.shape[1] - 1.001)
            v = np.clip((tie[4] - lat[select]) / scale[1] - 0.5, 0, array.shape[0] - 1.001)
            i, j = u.astype(int), v.astype(int)
            a, b = u - i, v - j
            output[select] = ((1-a)*(1-b)*array[j, i] + a*(1-b)*array[j, i+1]
                              + (1-a)*b*array[j+1, i] + a*b*array[j+1, i+1])
        if not np.isfinite(output).all() or output.min() < -500:
            raise ValueError("Missing or invalid elevation values")
        return output / 1000


def polygon_rings(element):
    # Country-limited Overpass mirrors can return null nodes for parts outside
    # their coverage. Reject the incomplete polygon, never bridge missing nodes.
    geometries = [element.get("geometry", [])] + [m.get("geometry", []) for m in element.get("members", [])]
    if any(p is None or "lon" not in p or "lat" not in p for g in geometries for p in g):
        return []
    if element["type"] == "way":
        geom = element.get("geometry", [])
        return [(geom, False)] if len(geom) > 3 and geom[0] == geom[-1] else []
    segments = {"outer": [], "inner": []}
    for member in element.get("members", []):
        geom = member.get("geometry", [])
        role = member.get("role") or "outer"
        if member["type"] == "way" and role in segments and len(geom) > 1:
            segments[role].append(list(geom))
    rings = []
    for role, remaining in segments.items():
        while remaining:
            ring = remaining.pop()
            while ring[0] != ring[-1]:
                found = False
                for i, segment in enumerate(remaining):
                    if segment[0] == ring[-1]:
                        ring.extend(segment[1:])
                    elif segment[-1] == ring[-1]:
                        ring.extend(segment[-2::-1])
                    elif segment[-1] == ring[0]:
                        ring = segment[:-1] + ring
                    elif segment[0] == ring[0]:
                        ring = segment[:0:-1] + ring
                    else:
                        continue
                    remaining.pop(i)
                    found = True
                    break
                if not found:
                    break
            if len(ring) > 3 and ring[0] == ring[-1]:
                rings.append((ring, role == "inner"))
    return rings


def load_landcover(cache):
    documents = []
    for name, bounds in [("swiss", (46.38, 7.52, 46.82, 8.19)),
                         ("dolomites", (46.42, 11.41, 46.89, 12.24)),
                         ("regional-lakes", (45.6, 5.5, 48.9, 12.7))]:
        bbox = ",".join(map(str, bounds))
        query = f'[out:json][timeout:150];(nwr["natural"="water"]({bbox});nwr["natural"="wood"]({bbox});nwr["landuse"="forest"]({bbox}););out geom;'
        if name == "regional-lakes":
            query = f'[out:json][timeout:60];nwr["natural"="water"]["name"~"Léman|Genfersee|Bodensee|Zürichsee|Walensee|Thunersee|Brienzersee"]({bbox});out geom;'
        post = urllib.parse.urlencode({"data": query}).encode()
        path = cache / f"osm-{name}.json"
        if not path.exists() and shutil.disk_usage(cache).free < 8*1024**3:
            raise RuntimeError("8 GiB free required before downloading map data")
        endpoints = (["https://overpass.osm.ch/api/interpreter"] if name != "dolomites" else []) + ["https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass-api.de/api/interpreter"]
        for endpoint in endpoints:
            try:
                print(f"OSM {name}: {endpoint}", flush=True)
                url = endpoint + "?" + post.decode()
                if not path.exists():
                    subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--max-time", "75", url, "--output", str(path)], check=True)
                SOURCES.append({"url": url, "file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
                data = json.loads(path.read_text())
                if data.get("remark"):
                    raise ValueError(data["remark"])
                incomplete = [f"{e['type']}/{e['id']}" for e in data.get("elements", [])
                    if any(p is None for g in [e.get("geometry", [])]+[m.get("geometry", []) for m in e.get("members", [])] for p in g)]
                if incomplete:
                    SOURCES[-1]["omitted_incomplete_polygons"] = incomplete
                    print(f"OSM incomplete polygons omitted, not connected: {incomplete}", flush=True)
                documents.append(data)
                break
            except Exception as error:
                print(f"OSM endpoint unavailable: {error}", flush=True)
                if path.exists():
                    path.unlink()  # Only this script's invalid temporary response.
                if endpoint == endpoints[-1]:
                    raise
    polygons = []
    seen = set()
    for data in documents:
        for e in data.get("elements", []):
            key = (e["type"], e["id"])
            if key in seen:
                continue
            seen.add(key)
            tags = e.get("tags", {})
            kind = "water" if tags.get("natural") == "water" else "forest"
            rings = polygon_rings(e)
            if rings:
                polygons.append((kind, rings))
    return polygons


def land_mask(polygons, xs, ys):
    w, h = len(xs), len(ys)
    images = {key: Image.new("L", (w, h)) for key in ("water", "forest")}
    for kind, rings in polygons:
        layer = Image.new("L", (w, h))
        draw = ImageDraw.Draw(layer)
        for ring, hole in sorted(rings, key=lambda pair: pair[1]):
            x, y = project([p["lon"] for p in ring], [p["lat"] for p in ring])
            if max(x) < xs[0] or min(x) > xs[-1] or max(y) < ys[0] or min(y) > ys[-1]:
                continue
            points = list(zip((x-xs[0])/(xs[-1]-xs[0])*(w-1), (y-ys[0])/(ys[-1]-ys[0])*(h-1)))
            draw.polygon(points, fill=0 if hole else 255)
        from PIL import ImageChops
        images[kind] = ImageChops.lighter(images[kind], layer)
    return {k: np.asarray(v.filter(ImageFilter.GaussianBlur(.9 if k == "forest" else .45))) for k, v in images.items()}


def prepare_labels(work, journey):
    """Rasterize the existing fonts without Blender's font-outline tessellation artifacts."""
    directory = work / "labels"
    directory.mkdir(exist_ok=True)
    def font(kind, size):
        return ImageFont.truetype(str(work / f"font-{kind}.ttf"), size)
    colors = {"rail": "#315a47", "cable_car": "#39758e", "bus": "#aa6a2b", "rideshare": "#6f5968", "hike": "#b44f39"}
    for entry in [{"id": "opening"}, *journey["route_legs"], {"id": "ending"}]:
        page = Image.new("RGBA", (1280, 960))
        draw = ImageDraw.Draw(page)
        draw.rectangle((0, 0, 1280, 228), fill="#f2ede0")
        draw.rectangle((0, 840, 1280, 960), fill="#f2ede0")
        day = int(entry["day_id"][-2:]) if "day_id" in entry else 10 if entry["id"] == "ending" else 0
        if "day_id" in entry:
            mode = entry["mode"]
            date = next(d["date"] for d in journey["days"] if d["id"] == entry["day_id"])
            eyebrow = f"DAY {day:02}  /  JUN {date[-2:]}  /  " + {"cable_car": "CABLE CAR", "rideshare": "CAR"}.get(mode, mode.upper())
            title = entry["label"].split(" via ")[0].split(" by ")[0].replace(", Val di Funes", "").replace("panoramic viewpoint", "viewpoint")
            subtitle = "A walk above the turquoise lake" if day == 2 else "Across the Alps, through Bern and Zürich" if day == 5 else "Ortisei: sunshine, cloud and rain in a moment" if day == 7 else "Follow the journey, one place at a time"
        else:
            mode = "rail"
            eyebrow = "JUNE 15–24, 2024  /  THROUGH THE ALPS"
            title = "Switzerland & the Dolomites" if day == 0 else "Ten days. A thousand memories."
            subtitle = "Geneva Airport / the Swiss Alps / the Dolomites / Munich Airport"
        title = title.replace("→", "/").replace("↔", "/")
        draw.text((70, 34), eyebrow, font=font("body", 36), fill=colors[mode])
        size = 57
        while draw.textlength(title, font=font("display", size)) > 1140:
            size -= 1
        draw.text((70, 80), title, font=font("display", size), fill="#302f27")
        draw.text((70, 165), subtitle, font=font("body", 27), fill="#302f27")
        for i in range(10):
            draw.text((70+i*120, 870), f"{i+1:02}", font=font("body", 24), fill="#315a47" if i < day else "#817563")
        draw.text((70, 911), "Real Alpine terrain · Copernicus DEM · © OpenStreetMap contributors", font=font("body", 18), fill="#302f27")
        page.save(directory / f"{entry['id']}.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--terrain-only", action="store_true", help="Diagnostic terrain samples only; not a release render")
    args = parser.parse_args()
    work = args.work.resolve()
    import sys
    sys.path.insert(0, str(work / "python-packages"))
    if ROOT == work or ROOT in work.parents:
        parser.error("Use a scratch directory outside the repository")
    cache = work / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG.read_text())
    subprocess.run(["ruby", "-EUTF-8", str(ROOT / "scripts/validate-travel-journey.rb"), str(MANIFEST)], check=True)
    ruby = 'require "yaml"; require "json"; require "date"; text=File.read(ARGV[0]); puts JSON.generate(YAML.safe_load(text.split(/^---\\s*$/)[1], permitted_classes:[Date,Time], aliases:true))'
    manifest = json.loads(subprocess.check_output(["ruby", "-EUTF-8", "-e", ruby, str(MANIFEST)]))
    journey = manifest["journey"]
    routes_path = ROOT / journey["route_geojson"].lstrip("/")
    routes = json.loads(routes_path.read_text())
    assert sum(d["seconds"] for d in config["days"]) + config["opening_seconds"] + config["ending_seconds"] == 72
    assert [d["id"] for d in config["days"]] == [d["id"] for d in journey["days"]]
    assert len(journey["places"]) == 18 and len(journey["route_legs"]) == 29
    unknown = set(config["playback"]) - {leg["id"] for leg in journey["route_legs"]}
    assert not unknown, f"Unknown playback legs: {unknown}"
    (work / "journey.json").write_text(json.dumps({"journey": journey, "routes": routes, "config": config}, ensure_ascii=False))
    elevation = Elevation(cache)
    needed = set()
    for region in config["regions"].values():
        west, south, east, north = region["bounds"]
        for lat in range(math.floor(south), math.floor(north)+1):
            for lon in range(math.floor(west), math.floor(east)+1):
                needed.add((lat, lon, region["dem"]))
    print(f"Preparing {len(needed)} Copernicus tiles", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda tile: elevation.tile(*tile), sorted(needed)))
    print("Fetching OSM water and forest outlines", flush=True)
    polygons = [] if args.terrain_only else load_landcover(cache)
    for name, region in config["regions"].items():
        west, south, east, north = region["bounds"]
        xmin, ymin = project(west, south)
        xmax, ymax = project(east, north)
        step = max(region["dem"]/1000, max(xmax-xmin, ymax-ymin)/(region["max_grid"]-1))
        xs = np.linspace(xmin, xmax, math.ceil((xmax-xmin)/step)+1)
        ys = np.linspace(ymin, ymax, math.ceil((ymax-ymin)/step)+1)
        xx, yy = np.meshgrid(xs, ys)
        lon, lat = unproject(xx, yy)
        z = elevation.sample(lon, lat, region["dem"])
        masks = land_mask(polygons, xs, ys)
        np.savez_compressed(work / f"terrain-{name}.npz", x=xs, y=ys, z=z, **masks)
        print(f"Terrain {name}: {z.shape}, {step*1000:.1f}m render grid from GLO-{region['dem']}", flush=True)
    for key, filename in [("display", "playfair-display-latin-variable.woff2"),
                          ("body", "source-sans-3-latin-variable.woff2")]:
        font = TTFont(ROOT / "assets/fonts/travel-journey" / filename)
        from fontTools.varLib.instancer import instantiateVariableFont
        font = instantiateVariableFont(font, {"wght": 600})
        font.flavor = None
        font.save(work / f"font-{key}.ttf")
    prepare_labels(work, journey)
    provenance = {"diagnostic_only": args.terrain_only, "accessed_on": datetime.date.today().isoformat(),
        "elevation": "Copernicus GLO-30 and GLO-90, AWS COG distribution / 2021 release",
        "land_cover": "OpenStreetMap current water and forest polygons; ODbL 1.0",
        "terrain_credit": "produced using Copernicus WorldDEM-30 and WorldDEM-90 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved",
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "routes_sha256": hashlib.sha256(routes_path.read_bytes()).hexdigest(),
        "configuration_sha256": hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        "sources": sorted(SOURCES, key=lambda s: s["file"])}
    (work / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
    print("Prepared journey, terrain, land cover, fonts and provenance", flush=True)


if __name__ == "__main__":
    main()
