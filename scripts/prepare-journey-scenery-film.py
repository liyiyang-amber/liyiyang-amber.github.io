#!/usr/bin/env python3
"""Apply the approved scenery direction to cached film geometry, never publish.

This deliberately does not rebuild routes, download terrain, or overwrite either
sample or the original film cache. New map anchors are verified against the small
cached OSM responses; all local inputs and protected site files are hashed.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/journey-scenery-film.json"
DIRECTORY = "cinematic-v3-film"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def landmark_data(work):
    sources = []
    result = {}
    files = [
        ("scenery-landmarks-swiss.json", "https://overpass.osm.ch/api/interpreter"),
        ("scenery-brixen-tower.json", "https://www.openstreetmap.org/api/0.6/way/231738203/full.json")]
    for filename, url in files:
        path = work / "cache" / filename
        data = read(path)
        assert not data.get("remark"), data.get("remark")
        sources.append({"file": filename, "url": url, "sha256": sha(path),
                        "osm_timestamp": data.get("osm3s", {}).get("timestamp_osm_base")})
        for element in data["elements"]:
            point = element.get("center", element)
            if "lon" in point:
                result[element["id"]] = [point["lon"], point["lat"]]
            elif element["type"] == "way" and filename.endswith("tower.json"):
                points = [result[n] for n in dict.fromkeys(element["nodes"])]
                result[element["id"]] = [sum(p[k] for p in points)/len(points) for k in (0, 1)]
    landmarks = {}
    for key, osm_id, model, rotation in [
        ("spiez-castle", 212739946, "castle", -20),
        ("interlaken-church", 202410138, "gothic-church", 5),
        ("lauterbrunnen-church", 230551186, "gothic-church", 0),
        ("brixen-tower", 231738203, "clock-tower", 0),
        ("staubbachfall", 948595022, "waterfall", 0)]:
        landmarks[key] = {"lonlat": result[osm_id], "model": model, "rotation_degrees": rotation,
            "source_url": f"https://www.openstreetmap.org/{'node' if model == 'waterfall' else 'way'}/{osm_id}",
            "coordinate_source": "OSM geometry/centroid; original illustrative model, not a surveyed building"}
    return landmarks, sources


def prepare(work, validate_only=False, recover_missing_sample=False):
    recipe = read(CONFIG)
    assert recipe["approval_status"] == "approved" and recipe["duration"] == 150
    assert work != ROOT and ROOT not in work.parents
    free = shutil.disk_usage(work).free / 1024**3
    if free < 8 and not validate_only:
        raise RuntimeError(f"Paused: {free:.2f} GiB free; 8 GiB required")
    approved = work / "cinematic-v3-upper-mist"
    sample_movie = approved / "journey-scenery-approval-sample.mp4"
    if sample_movie.is_file():
        assert sha(sample_movie) == recipe["approved_sample_sha256"]
        scenery = copy.deepcopy(read(approved / "film.json")["config"]["scenery"])
        approval_evidence = {"status": "approved_sample_bytes_verified", "sha256": sha(sample_movie)}
    else:
        if not recover_missing_sample:
            raise RuntimeError("Approved sample cache is missing. Explicit --recover-missing-sample is required to rebuild the user-approved design from the retained configuration.")
        scenery = read(ROOT / "config/journey-scenery.json")
        approval_evidence = {
            "status": "user_authorized_rebuild_after_temporary_cache_loss",
            "historical_sample_sha256": recipe["approved_sample_sha256"],
            "historical_sample_bytes_available": False,
            "retained_design_sha256": sha(ROOT / "config/journey-scenery.json"),
            "note": "User approved upper-slope mist and then explicitly requested rebuilding the full film after the temporary cache disappeared. This is a new render, not verified reuse of the lost sample."}
    source = work / "cinematic-film/film.json"
    payload = read(source)
    anchors, sources = landmark_data(work)
    scenery["landmarks"].update(anchors)
    scenery["place_anchors"] = {k: [p["longitude"], p["latitude"]] for k, p in payload["places"].items()}
    # Static town shots use the cloudy palette without replaying the transition.
    scenery["weather_profiles"]["town-clear"] = copy.deepcopy(scenery["weather_profiles"]["clear-lake"])
    scenery["weather_profiles"]["town-clear"]["cloud_density"] = .0008
    old_shots = {s["id"]: s for s in payload["config"]["shots"]}
    geometry = payload["shot_geometry"]
    shots = []
    for old in payload["config"]["shots"]:
        for insertion in recipe["insertions"]:
            if insertion.get("before") == old["id"]:
                shots.append({**copy.deepcopy(old_shots[insertion["base_shot"]]), **insertion})
                geometry[insertion["id"]] = copy.deepcopy(geometry[insertion["base_shot"]])
        shots.append(copy.deepcopy(old))
        for insertion in recipe["insertions"]:
            if insertion.get("after") == old["id"]:
                shots.append({**copy.deepcopy(old_shots[insertion["base_shot"]]), **insertion})
                geometry[insertion["id"]] = copy.deepcopy(geometry[insertion["base_shot"]])
    legs = {l["id"]: l for l in payload["journey"]["route_legs"]}
    start = 0
    for shot in shots:
        sid = shot["id"]
        shot["seconds"] = recipe["duration_overrides"].get(sid, shot["seconds"])
        shot["start_seconds"] = start
        start += shot["seconds"]
        mode = legs.get(shot.get("leg_id"), {}).get("mode")
        if shot["region"] in recipe["region_profiles"]:
            profile, photo = recipe["region_profiles"][shot["region"]]
            shot.update(weather_profile=profile, reference="images/swiss_do/"+photo,
                        atmosphere_3d=True, full_scenery=True,
                        show_pair=mode == "hike" and not shot["show_route"])
            shot["scenery"] = "trail" if mode == "hike" else "transport"
        if sid in ("d04-mannlichen-arrival", "d09-plateau-arrival"):
            shot["scenery"] = "lift-station"
            shot["station_lonlat"] = geometry[sid]["anchors"]["to"]
        destination = recipe["destinations"].get(sid)
        if destination:
            shot["destination_focus"] = True
            if destination.get("approved_shot"):
                patch = next(s for s in scenery["sample_shots"] if s["id"] == destination["approved_shot"])
                shot.update({k: copy.deepcopy(v) for k, v in patch.items() if k not in ("id", "base_shot", "seconds")})
                shot.pop("camera_axes", None)
                shot["full_scenery"] = False  # Preserve the approved props/composition.
            else:
                shot.update({k: v for k, v in destination.items() if k not in ("offset_m", "look_offset_m", "reference")})
                shot["reference"] = "images/swiss_do/"+destination["reference"]
                if destination.get("offset_m"):
                    shot["camera"] = "destination_panorama"
                    shot["destination_camera"] = {"offset_m": destination["offset_m"],
                        "look_offset_m": destination["look_offset_m"], "drift_m": [2, 0, 0]}
                    shot["lens_mm"] = 34
                    shot["show_pair"] = False
                    shot["weather_profile"] = "town-clear" if sid == "d10-ortisei-departure" else shot["weather_profile"]
                    shot.pop("camera_axes", None)
            shot["show_route"] = False
            shot["endpoint_labels"] = []
        if shot.get("landmark") in ("interlaken-church", "lauterbrunnen-church"):
            shot["full_scenery"] = True
        assert shot["seconds"]*24 == int(shot["seconds"]*24)
    payload["config"].update(shots=shots, scenery=scenery, duration=150,
        approval_status="approved", scenery_revision=True, approval_sample=False,
        minimum_free_gib=8, poster_seconds=22, scenery_recipe=recipe)
    assert start == 150, start
    validate(payload)
    if validate_only:
        print(f"SCENERY_FILM_STORY_OK: {len(shots)} shots, 150s/3600 frames, {recipe['destination_seconds']}s destinations; no files written")
        return
    protected = ["_travel/swiss+dolomites.md", "assets/data/travel/swiss-dolomites-routes.geojson",
                 "assets/media/travel/swiss-dolomites-cinematic.mp4", "assets/media/travel/swiss-dolomites-cinematic-poster.jpg"]
    provenance = payload["provenance"]
    provenance.update(status="approved_scenery_revision_local_render",
        note="Real Copernicus terrain and OSM shoreline/forest/landmark anchors. Models, snow distribution and weather are original photo-guided illustrations, not photogrammetry or a historic weather timeline.",
        parent_payload_sha256=sha(source), scenery_recipe_sha256=sha(CONFIG),
        approved_sample_sha256=recipe["approved_sample_sha256"], landmarks=scenery["landmarks"],
        approval_evidence=approval_evidence,
        protected_site_hashes={p: sha(ROOT/p) for p in protected},
        source_photo_hashes={p: sha(ROOT/p) for s in shots for p in [s.get("reference"), *s.get("additional_references", [])] if p})
    provenance["sources"] += sources
    directory = work / DIRECTORY
    directory.mkdir(exist_ok=True)
    (directory/"film.json").write_text(json.dumps(payload, ensure_ascii=False))
    (directory/"provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
    print(f"SCENERY_FILM_PREPARED {len(shots)} shots, 150s/3600 frames, {recipe['destination_seconds']}s destinations; {free:.2f} GiB free", flush=True)


def validate(payload):
    config, journey = payload["config"], payload["journey"]
    shots = config["shots"]
    assert len(journey["days"]) == 10 and len(journey["places"]) == 18
    legs = {l["id"]: l for l in journey["route_legs"]}
    assert len(legs) == 29
    assert {s["leg_id"] for s in shots if s.get("leg_id")} == set(legs)
    assert len({s["id"] for s in shots}) == len(shots)
    assert sum(s["seconds"] for s in shots) == config["duration"] == 150
    assert config["fps"] == 24 and config["resolution"] == [1280, 960] and config["samples"] == 48
    assert sum(s["seconds"] for s in shots if s.get("destination_focus")) == config["scenery_recipe"]["destination_seconds"]
    assert sum(s["seconds"] for s in shots if not s["show_route"])/150 >= .7
    day_totals = {d["id"]: 0 for d in journey["days"]}
    previous = -1
    for shot in shots:
        if shot.get("leg_id"):
            index = list(legs).index(shot["leg_id"])
            assert index >= previous
            previous = index
            day_totals[legs[shot["leg_id"]]["day_id"]] += shot["seconds"]
        if shot.get("reference"):
            assert (ROOT/shot["reference"]).is_file(), shot["reference"]
    assert list(day_totals.values()) == config["day_seconds"], day_totals
    hikes = {l["id"] for l in legs.values() if l["mode"] == "hike"}
    assert len(hikes) == 5 and {s["leg_id"] for s in shots if s.get("show_pair")} == hikes
    for leg, expected in [("day-07-seceda-round-trip", {0, 1, 2, 3}), ("day-08-ortisei-seceda", {0, 1}), ("day-08-seceda-ortisei", {0, 1})]:
        assert {s["source_part"] for s in shots if s.get("leg_id") == leg and "source_part" in s} == expected
    weather = next(s for s in shots if s["id"] == "d07-ortisei-weather")
    assert weather["seconds"] == 4 and weather["weather_profile"] == "changing-valley"
    for path in payload["terrain_files"].values():
        assert Path(path).is_file()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true", help="Read-only storyboard checks; never prepares or renders")
    parser.add_argument("--recover-missing-sample", action="store_true", help="Explicitly authorized rebuild from retained approved configuration after cache loss")
    args = parser.parse_args()
    prepare(args.work.resolve(), args.validate_only, args.recover_missing_sample)
