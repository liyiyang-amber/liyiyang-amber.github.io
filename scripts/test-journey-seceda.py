#!/usr/bin/env python3
"""Seceda isolation, timing, terrain, character and sample-media checks."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/"scripts"/filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def framedigests(path):
    value = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-f", "framemd5", "-"], text=True)
    return [line.rsplit(",", 1)[1].strip() for line in value.splitlines() if line and not line.startswith("#")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--proofs", action="store_true")
    parser.add_argument("--rendered", action="store_true")
    parser.add_argument("--decode-baseline", action="store_true")
    parser.add_argument("--candidate-film", type=Path, help="After approval, verify a separately reassembled film outside the six revised intervals")
    args = parser.parse_args()
    prep = load_module("seceda_preparation", "prepare-journey-seceda.py")
    recipe = prep.read(prep.CONFIG)
    prep.validate_recipe(recipe)
    directory = args.work/recipe["directory"]
    baseline = prep.read(directory/"preservation-baseline.json")
    payload = prep.read(directory/"film.json")
    original = prep.read(Path(baseline["source_payload"]["path"]))
    config = payload["config"]
    assert config["approval_status"] == "sample_only" and config["approval_sample"]
    assert config["duration"] == config["sample_duration"] == 12.5
    assert config["fps"] == 24 and config["resolution"] == [1280,960] and config["samples"] == 48
    assert config["minimum_free_gib"] >= 8 and config["full_duration"] == 150
    assert config["production_timeline"], "Approved clip reuse needs production labels, not sample-only overlays"
    assert {s["id"]:s["seconds"] for s in config["shots"]} == prep.EXPECTED
    assert sum(s["seconds"] for s in config["shots"])*24 == 300
    assert payload["journey"] == original["journey"] and payload["routes"] == original["routes"]
    assert len(original["journey"]["days"]) == 10 and len(original["journey"]["places"]) == 18
    assert len(original["journey"]["route_legs"]) == 29
    assert sum(l["mode"] == "hike" for l in original["journey"]["route_legs"]) == 5
    shared = copy.deepcopy(config["scenery"])
    for name in recipe["weather_profiles"]:
        shared["weather_profiles"].pop(name)
    assert shared == original["config"]["scenery"], "Shared scenery must stay unchanged"
    for group in ("installed", "photos"):
        for path, expected in baseline[group].items():
            assert prep.sha(ROOT/path) == expected, path
    for artifact in [baseline["source_movie"], baseline["source_payload"], *baseline["terrain"].values()]:
        assert prep.sha(Path(artifact["path"])) == artifact["sha256"], artifact["path"]
    for frozen in baseline["unchanged_shots"].values():
        for artifact in frozen["artifacts"].values():
            assert prep.sha(Path(artifact["path"])) == artifact["sha256"], artifact["path"]
    for path,expected in baseline["previous_revision"].items():
        assert prep.sha(Path(path)) == expected, path
    relief = config["seceda_relief"]
    assert prep.sha(Path(relief["path"])) == relief["sha256"]
    audit = relief["audit"]
    assert audit["height_scale"] == 1 and audit["maximum_raising_m"] == 0
    assert audit["anchor_error_m"] < 1e-6
    assert audit["seam_error_m"] == audit["path_height_error_m"] == 0
    assert audit["protected_path_m"] >= 30 and max(audit["spacing_m"]) < 6.1
    assert all(abs(a["render_height_m"]-a["source_height_m"]) < 1e-6 for a in audit["anchors"])
    local = np.load(relief["path"])
    assert np.isfinite(local["z"]).all()
    assert len(baseline["unchanged_shots"]) == 62
    for shot in config["shots"]:
        old = next(s for s in original["config"]["shots"] if s["id"] == shot["id"])
        assert (shot["seconds"],shot["original_start_seconds"],shot["speed_mps"],shot["from_place"],shot["to_place"]) == (old["seconds"],old["start_seconds"],old["speed_mps"],old["from_place"],old["to_place"])
        geometry = copy.deepcopy(payload["shot_geometry"][shot["id"]])
        if "travel_fraction" in shot:
            assert geometry["travel"] == geometry["lines"][0]
            assert shot["fraction"] == recipe["shots"][shot["id"]]["travel_fraction"]
            assert 0 < shot["fraction"] < 1 and shot["source_interval_m"][1] > shot["source_interval_m"][0]
            geometry["travel"] = original["shot_geometry"][shot["id"]]["travel"]
        assert geometry == original["shot_geometry"][shot["id"]]
    assert prep.sha(prep.CONFIG) == payload["provenance"]["seceda_recipe_sha256"]
    for reference in payload["provenance"]["visual_reference_attachments"]:
        assert reference["sha256"] and prep.sha(Path(reference["path"]))==reference["sha256"]
    if args.decode_baseline or args.candidate_film:
        digests = {sid:framedigests(Path(v["entry"]["movie"])) for sid,v in baseline["unchanged_shots"].items()}
        assert sum(map(len, digests.values())) == 3300
        full = framedigests(Path(baseline["source_movie"]["path"]))
        assert len(full) == 3600
        for sid,frozen in baseline["unchanged_shots"].items():
            first = int(frozen["shot"]["start_seconds"]*24)
            assert full[first:first+len(digests[sid])] == digests[sid], sid
        output = directory/"frozen-frame-digests.json"
        if output.exists():
            assert prep.read(output) == digests
        else:
            output.write_text(json.dumps(digests, indent=2))
        print("FROZEN_DECODE_OK: 3300 decoded frames from 62 unchanged clips")
        if args.candidate_film:
            encoder = load_module("seceda_candidate_encoder", "encode-journey-film.py")
            encoder.check_movie(args.candidate_film,150,config)
            assert args.candidate_film.stat().st_size <= 35*1024**2
            candidate = framedigests(args.candidate_film)
            assert len(candidate) == 3600
            for sid,frozen in baseline["unchanged_shots"].items():
                first = int(frozen["shot"]["start_seconds"]*24)
                assert candidate[first:first+len(digests[sid])] == digests[sid], sid
            print("CANDIDATE_REUSE_OK: every frame outside the six Seceda intervals is identical")
    if args.proofs or args.rendered:
        encoder = load_module("seceda_encoder", "encode-journey-film.py")
        entries = prep.read(directory/"render-index.json")
        assert [e["id"] for e in entries] == [s["id"] for s in config["shots"]]
        total = 0
        for entry,shot in zip(entries, config["shots"]):
            expected = int(shot["seconds"]*24) if args.rendered else 3
            qa = prep.read(Path(entry["qa"]) if args.rendered else Path(entry["proof"]).parent/"stills-qa.json")
            for key,value in shot.items():
                assert qa["shot"].get(key) == value, (shot["id"], "Stale rendered parameter", key)
            encoder.check_poses(qa, expected)
            total += expected
            for record in qa["records"]:
                assert record["ridge_camera"] and record["atmosphere_3d"]
                assert record["seceda_relief"] == relief["sha256"]
                clouds = {c["group"]:c for c in record["ridge_cloud_groups"]}
                if shot["id"].startswith("d07"):
                    assert not clouds
                else:
                    assert clouds["valley"]["density"] > 0 and clouds["summit"]["density"] > 0
                walkers = record["walkers"]
                assert len(walkers) == (2 if shot.get("show_pair") else 0)
                camera = np.array(record["ridge_camera"]["position_m"])
                forward = np.array(record["ridge_camera"]["target_m"])-camera
                forward /= np.linalg.norm(forward)
                right = np.cross(forward,[0,0,1]); right /= np.linalg.norm(right)
                up = np.cross(right,forward)
                for walker in walkers:
                    definition = next(p for p in config["scenery"]["walking_pair"] if p["id"] == walker["id"])
                    assert walker["height_m"] == definition["height_m"]
                    assert any(f["stance"] for f in walker["feet"])
                    assert all(abs(f["sole_clearance_m"]) < 1e-6 for f in walker["feet"] if f["stance"])
                    relative = np.array(walker["position"])+[0,0,walker["height_m"]/2]-camera
                    depth = np.dot(relative,forward)
                    assert depth > 2
                    factor = shot["ridge_camera"]["lens_mm"]/36*1280/depth
                    x,y = 640+factor*np.dot(relative,right),480-factor*np.dot(relative,up)
                    assert 15<x<1265 and 174<y<882, (shot["id"],walker["id"],x,y)
                if shot["id"] == "d08-pieralongia-out":
                    expected_density = 0 if record["time"] >= 2 else 1-(record["time"]/2)**2*(3-record["time"])
                    assert abs(record["ridge_reveal_density_fraction"]-expected_density)<1e-6
                    assert abs(clouds["reveal"]["density"]-.022*expected_density)<1e-6
                else:
                    assert record["ridge_reveal_density_fraction"] is None
            if args.rendered:
                encoder.check_movie(Path(entry["movie"]), shot["seconds"], config)
        if args.rendered:
            encoder.check_movie(directory/"journey-scenery-approval-sample.mp4",12.5,config)
            assert total == 300
        print(f"SECEDA_POSES_OK: {total} {'frames' if args.rendered else 'proof poses'}")
    print("SECEDA_TESTS_OK: six scoped shots, 62 protected clips, preserved previous sample/installed film/source DEM/photos/itinerary; artistic relief anchors and paths fixed; sample approval still required")


if __name__ == "__main__":
    main()
