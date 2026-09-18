#!/usr/bin/env python3
"""Prepare the approval sample without changing the active journey or film.

--validate-only is read-only and works before the disk-space prerequisite is met.
All generated data live under WORK/cinematic-v2; existing v1 caches are reused.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/journey-cinematic.json"


def legacy():
    spec = importlib.util.spec_from_file_location("journey_preparation", ROOT / "scripts/prepare-journey-overview.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_inputs():
    config = json.loads(CONFIG.read_text())
    ruby = 'require "yaml";require "date";require "json";puts JSON.generate(YAML.safe_load(File.read(ARGV[0]).split(/^---\\s*$/)[1],permitted_classes:[Date,Time],aliases:true))'
    source = ROOT / "_travel/swiss+dolomites.md"
    journey = json.loads(subprocess.check_output(["ruby", "-EUTF-8", "-e", ruby, str(source)]))["journey"]
    routes = json.loads((ROOT / journey["route_geojson"].lstrip("/")).read_text())
    playback = json.loads((ROOT / "assets/data/travel/swiss-dolomites-overview.json").read_text())["playback"]
    assert len(journey["days"]) == 10 and len(journey["places"]) == 18
    assert len(journey["route_legs"]) == 29 and len(routes["features"]) == 24
    assert len({l["feature_id"] for l in journey["route_legs"] if l["mode"] == "hike"}) == 5
    assert len(config["day_seconds"]) == 10
    assert config["opening_seconds"] + sum(config["day_seconds"]) + config["ending_seconds"] == config["duration"] == 150
    assert sum(s["seconds"] for s in config["sample_shots"]) == config["sample_duration"] == 15
    assert config["duration"] * config["fps"] == 3600
    assert config["resolution"] == [1280, 960] and config["samples"] == 48
    places = {p["id"]: p for p in journey["places"]}
    legs = {l["id"]: l for l in journey["route_legs"]}
    features = {f["properties"]["id"]: f for f in routes["features"]}
    ids = set()
    for shot in config["sample_shots"]:
        assert shot["id"] not in ids
        ids.add(shot["id"])
        assert shot["from_place"] in places and shot["to_place"] in places, shot
        leg = legs[shot["leg_id"]]
        assert leg["feature_id"] in features and shot["region"] in config["regions"]
        assert 0 <= shot["fraction"] < 1 and 0 < shot["speed_mps"] <= 20
        assert shot["camera"].endswith("aerial") == shot["show_route"]
    assert sum(s["seconds"] for s in config["sample_shots"] if not s["show_route"]) / 15 >= .7
    return config, journey, routes, playback


def require_space(work, gib):
    free = shutil.disk_usage(work).free / 1024**3
    if free < gib:
        raise RuntimeError(f"{free:.2f} GiB free; at least {gib} GiB required. No rendering or downloads started.")


def point_distance(point, coordinates, prep):
    xy = np.column_stack(prep.project(*np.asarray(coordinates).T)) * 1000
    a, delta = xy[:-1], np.diff(xy, axis=0)
    t = np.clip(np.sum((point-a)*delta, axis=1)/np.maximum(np.sum(delta*delta, axis=1), 1e-9), 0, 1)
    return float(np.linalg.norm(a+t[:, None]*delta-point, axis=1).min())


def sample_distance(xy, distance):
    lengths = np.r_[0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
    return np.array([np.interp(distance, lengths, xy[:, i]) for i in range(xy.shape[1])])


def verify_rail(shot, coords, elevation, prep, cache):
    """Choose a short interval on positively identified, above-ground OSM rail."""
    path = cache / "cinematic-thun-rail.json"
    query = '[out:json][timeout:60];way["railway"="rail"](46.63,7.69,46.72,7.88);out geom;'
    import urllib.parse
    url = "https://overpass.osm.ch/api/interpreter?" + urllib.parse.urlencode({"data": query})
    prep.fetch(url, path, timeout=75)
    response = json.loads(path.read_text())
    if response.get("remark"):
        raise ValueError("Incomplete railway verification response")
    ways = [w for w in response["elements"] if len(w.get("geometry", [])) >= 2]
    xy = np.column_stack(prep.project(*np.asarray(coords).T))*1000
    length = np.linalg.norm(np.diff(xy, axis=0), axis=1).sum()
    for fraction in [shot["fraction"], .50, .45, .60, .40, .65, .35, .70]:
        distances = fraction*length + np.linspace(0, shot["seconds"]*shot["speed_mps"]+55, 9)
        points = np.array([sample_distance(xy, d) for d in distances])
        chosen = []
        for point in points:
            nearest = sorted((point_distance(point, [(p["lon"], p["lat"]) for p in w["geometry"]], prep), i) for i, w in enumerate(ways))
            if not nearest or nearest[0][0] > 30:
                break
            way = ways[nearest[0][1]]
            tags = way.get("tags", {})
            if any(tags.get(k, "no") not in ("no", "0", "false") for k in ("tunnel", "bridge", "covered")):
                break
            chosen.append(way["id"])
        if len(chosen) != len(points):
            continue
        lon, lat = prep.unproject(points[:, 0]/1000, points[:, 1]/1000)
        z = elevation.sample(lon, lat, 30)*1000
        if np.max(np.abs(np.diff(z)) / np.maximum(np.diff(distances), 1)) > .075:
            continue
        shot["fraction"] = fraction
        return {"source_url": url, "osm_way_ids": sorted(set(chosen)), "fraction": fraction,
                "checked_length_m": float(distances[-1]-distances[0]),
                "note": "Close shot uses above-ground rail; DEM heights remain an illustrated surface, not surveyed track elevations."}
    raise ValueError("No safe above-ground rail sample found; inspect geometry before rendering")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    config, journey, routes, playback = read_inputs()
    if args.validate_only:
        print("CINEMATIC_CONFIG_OK: 150s / 3600 frames; 15s approval sample; 10 days, 18 places, 29 legs, 5 hikes")
        return
    if not args.work:
        parser.error("--work is required for preparation")
    work = args.work.resolve()
    assert work != ROOT and ROOT not in work.parents
    assert config["approval_status"] == "sample_only"
    require_space(work, config["sample_minimum_free_gib"])
    prep = legacy()
    destination = work / "cinematic-v2"
    destination.mkdir(exist_ok=True)
    cache = work / "cache"
    elevation = prep.Elevation(cache)
    # These existing sources are reused; only missing files are fetched.
    polygons = prep.load_landcover(cache)
    features = {f["properties"]["id"]: f for f in routes["features"]}
    legs = {l["id"]: l for l in journey["route_legs"]}
    audits = []
    for shot in config["sample_shots"]:
        if shot.get("verify_surface_rail"):
            geometry = features[legs[shot["leg_id"]]["feature_id"]]["geometry"]
            coords = geometry["coordinates"] if geometry["type"] == "LineString" else geometry["coordinates"][shot["part"]]
            audits.append(verify_rail(shot, coords, elevation, prep, cache))
    for name, region in config["regions"].items():
        west, south, east, north = region["bounds"]
        xmin, ymin = prep.project(west, south)
        xmax, ymax = prep.project(east, north)
        xs = np.linspace(xmin, xmax, math.ceil((xmax-xmin)/.030)+1)
        ys = np.linspace(ymin, ymax, math.ceil((ymax-ymin)/.030)+1)
        xx, yy = np.meshgrid(xs, ys)
        lon, lat = prep.unproject(xx, yy)
        z = elevation.sample(lon, lat, 30)
        masks = prep.land_mask(polygons, xs, ys)
        np.savez_compressed(destination / f"terrain-{name}.npz", x=xs, y=ys, z=z, **masks)
        print(f"SCENIC_TERRAIN {name}: {z.shape}; <=30m spacing", flush=True)
    lakes = []
    for kind, rings in polygons:
        if kind != "water":
            continue
        for ring, hole in rings:
            if hole:
                continue
            xy = np.column_stack(prep.project([p["lon"] for p in ring], [p["lat"] for p in ring]))
            area = abs(np.sum(xy[:-1, 0]*xy[1:, 1]-xy[1:, 0]*xy[:-1, 1]))/2
            if area < .015:
                continue  # Do not turn subpixel ponds into giant regional lakes.
            center = np.mean(xy, axis=0)
            if not (7.6 <= prep.unproject(*center)[0] <= 8.1):
                continue
            ring_z = elevation.sample(np.array([p["lon"] for p in ring]), np.array([p["lat"] for p in ring]), 30)
            lakes.append({"xy": xy.tolist(), "height": float(np.percentile(ring_z, 10))+.0006})
    (destination / "sample.json").write_text(json.dumps({"config": config, "journey": journey, "routes": routes, "playback": playback, "lakes": lakes}, ensure_ascii=False))
    provenance = {"status": "approval_sample_only", "accessed_on": datetime.date.today().isoformat(),
        "source": "Copernicus GLO-30 / 2021; OpenStreetMap land cover; original stylized foreground detail",
        "sources": prep.SOURCES, "surface_rail_audits": audits,
        "configuration_sha256": hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        "route_sha256": hashlib.sha256(json.dumps(routes, sort_keys=True).encode()).hexdigest()}
    (destination / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
    print(f"SAMPLE_PREPARED {destination}")


if __name__ == "__main__":
    main()
