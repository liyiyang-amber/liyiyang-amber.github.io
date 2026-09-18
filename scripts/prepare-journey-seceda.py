#!/usr/bin/env python3
"""Isolated six-shot Seceda study; preserve the installed film and 62 clips."""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/journey-seceda.json"
EXPECTED = {"d07-seceda": 1.5, "d07-summit": 1, "d08-seceda-lift": 2,
            "d08-pieralongia-out": 4, "d08-pieralongia-return": 3, "d08-loop-arrival": 1}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_recipe(recipe):
    assert recipe["approval_status"] == "sample_only"
    assert {k: v["seconds"] for k, v in recipe["shots"].items()} == EXPECTED
    assert Path(recipe["directory"]).name == recipe["directory"] and recipe["directory"].startswith("cinematic-v3-")
    assert all((ROOT / name).is_file() for name in recipe["references"])
    assert recipe["ridge_geometry"]["protected_path_m"] >= 30
    assert recipe["weather_profiles"]["seceda-reveal"]["reveal_seconds"] == 2
    for shot in recipe["shots"].values():
        assert shot["weather_profile"] in recipe["weather_profiles"]
        assert shot["ridge_camera"]["lens_mm"] > 0


def prepare(work):
    work = work.resolve()
    assert work != ROOT and ROOT not in work.parents
    recipe = read(CONFIG)
    validate_recipe(recipe)
    if shutil.disk_usage(work).free < 8*1024**3:
        raise RuntimeError("At least 8 GiB free is required; nothing prepared")
    source = work / "cinematic-v3-film"
    original = read(source / "film.json")
    completed = read(source / "completed-film.json")
    assert completed["frames"] == 3600 and completed["duration"] == 150
    assert sha(source / "journey-cinematic-film.mp4") == completed["sha256"]
    assert sha(ROOT / "assets/media/travel/swiss-dolomites-cinematic.mp4") == completed["sha256"]
    destination = work / recipe["directory"]
    destination.mkdir(exist_ok=True)
    baseline_path = destination / "preservation-baseline.json"
    protected = ["_travel/swiss+dolomites.md", "assets/data/travel/swiss-dolomites-routes.geojson",
        "assets/media/travel/swiss-dolomites-cinematic.mp4", "assets/media/travel/swiss-dolomites-cinematic-poster.jpg",
        "assets/data/travel/swiss-dolomites-cinematic-provenance.json"]
    baseline = {
        "installed": {p: sha(ROOT/p) for p in protected},
        "source_payload": {"path": str(source/"film.json"), "sha256": sha(source/"film.json")},
        "source_movie": {"path": str(source/"journey-cinematic-film.mp4"), "sha256": completed["sha256"]},
        "photos": {p: sha(ROOT/p) for p in recipe["references"]},
        "terrain": {k: {"path": p, "sha256": sha(Path(p))} for k,p in original["terrain_files"].items()},
        "unchanged_shots": {}
    }
    previous = work / recipe["previous_revision"]
    preserved = [previous / name for name in ("film.json", "completed-film.json", "journey-scenery-approval-sample.mp4", "journey-scenery-approval-poster.jpg", "provenance.json", "preservation-baseline.json", "render-index.json")]
    for entry in read(previous / "completed-film.json")["shots"]:
        preserved.extend(Path(entry[k]) for k in ("movie", "proof", "qa"))
    baseline["previous_revision"] = {str(p):sha(p) for p in preserved}
    for shot in original["config"]["shots"]:
        if shot["id"] in EXPECTED:
            continue
        entry = next(e for e in completed["shots"] if e["id"] == shot["id"])
        baseline["unchanged_shots"][shot["id"]] = {"entry": entry, "shot": shot,
            "geometry": original["shot_geometry"][shot["id"]],
            "artifacts": {k: {"path": entry[k], "sha256": sha(Path(entry[k]))} for k in ("movie", "proof", "qa")}}
    assert len(baseline["unchanged_shots"]) == 62
    if baseline_path.exists():
        assert read(baseline_path) == baseline, "Protected inputs changed; do not silently reset the baseline"
    else:
        baseline_path.write_text(json.dumps(baseline, ensure_ascii=False, indent=2))
    payload = copy.deepcopy(original)
    config = payload["config"]
    config["scenery"]["weather_profiles"].update(copy.deepcopy(recipe["weather_profiles"]))
    spec = importlib.util.spec_from_file_location("seceda_relief", ROOT / "scripts/journey-seceda-terrain.py")
    sculpt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sculpt)
    lines = [line for sid in EXPECTED for line in original["shot_geometry"][sid]["lines"]]
    relief = destination / "seceda-relief.npz"
    relief_audit = sculpt.prepare(original["terrain_files"]["gardena"], recipe["ridge_geometry"], lines, relief)
    config["seceda_relief"] = {"path":str(relief), "sha256":sha(relief), "audit":relief_audit}
    (destination / "relief-audit.json").write_text(json.dumps(relief_audit, indent=2))
    shots, start, geometry = [], 0, {}
    for old in original["config"]["shots"]:
        if old["id"] not in EXPECTED:
            continue
        patch = copy.deepcopy(recipe["shots"][old["id"]])
        assert old["seconds"] == patch["seconds"]
        shot = {**copy.deepcopy(old), **patch}
        shot.update(original_start_seconds=old["start_seconds"], start_seconds=start,
            show_route=False, endpoint_labels=[], reference=recipe["references"][0],
            additional_references=recipe["references"][1:], proof_sequence=True)
        shot["ridge_camera"]["target"] = copy.deepcopy(recipe["ridge_target"])
        geometry[old["id"]] = copy.deepcopy(original["shot_geometry"][old["id"]])
        if "travel_fraction" in patch:
            # Select another scenic stretch of the SAME directed mapped loop;
            # public route geometry and walking speed/direction are unchanged.
            line = geometry[old["id"]]["lines"][0]
            geometry[old["id"]]["travel"] = copy.deepcopy(line)
            scale = math.pi/180*6371008.8
            length = sum(math.hypot((b[0]-a[0])*scale*math.cos(math.radians(47)),(b[1]-a[1])*scale) for a,b in zip(line,line[1:]))
            shot["fraction"] = shot["source_fraction"] = patch["travel_fraction"]
            shot["source_interval_m"] = [length*shot["fraction"],length*shot["fraction"]+shot["seconds"]*shot["speed_mps"]]
        shot.pop("camera_axes", None)
        shot["camera"] = "ridge_panorama"
        start += shot["seconds"]
        shots.append(shot)
    assert start == 12.5
    config.update(approval_status="sample_only", approval_sample=True, duration=start, sample_duration=start,
        full_duration=150, shots=shots, poster_seconds=7, minimum_free_gib=8, samples=48,
        revision_kind="seceda", preserve_frame_identity=True, production_timeline=True)
    payload.pop("frozen_shots", None)
    payload["shot_geometry"] = geometry
    payload["provenance"].update(status="seceda_sample_awaiting_approval", seceda_recipe_sha256=sha(CONFIG),
        preservation_baseline_sha256=sha(baseline_path), modified_shots=list(EXPECTED),
        source_photo_hashes=baseline["photos"], protected_site_hashes=baseline["installed"],
        seceda_relief=config["seceda_relief"],
        visual_reference_attachments=[{"path":p,"sha256":sha(Path(p)) if Path(p).is_file() else None,"status":"local_file_available" if Path(p).is_file() else "Visible in user message; original file missing, checksum unavailable"} for p in recipe.get("visual_reference_attachments",[])],
        note="Seceda-only photo-guided artistic relief, not higher-resolution survey or photogrammetry. Source DEMs are untouched; local shoulders are carved while measured crest anchors, heights, geographic route corridors and public geometry stay fixed. Valley and summit clouds remain after the reveal. The previous sample and 62 original clips are frozen; approval is still required.")
    attachments=payload["provenance"]["visual_reference_attachments"]
    if all(a["sha256"] for a in attachments):
        recorded=destination/"reference-attachment-hashes.json"
        if recorded.exists():
            assert read(recorded)==attachments,"Reference attachments changed after being recorded"
        else:
            recorded.write_text(json.dumps(attachments,ensure_ascii=False,indent=2))
    (destination/"film.json").write_text(json.dumps(payload, ensure_ascii=False))
    (destination/"provenance.json").write_text(json.dumps(payload["provenance"], ensure_ascii=False, indent=2))
    print(f"SECEDA_PREPARED {destination}: six shots, {start}s/300 frames; 62 protected clips; installed film unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    prepare(parser.parse_args().work)
