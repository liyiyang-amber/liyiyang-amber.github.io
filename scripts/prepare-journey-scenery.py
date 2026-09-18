#!/usr/bin/env python3
"""Prepare only the revised 15-second look sample, reusing cached real terrain.

Never changes the approved story, itinerary, live media, or previous samples.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/journey-scenery.json"


def validate(config):
    assert config["approval_status"] == "sample_only"
    assert config["full_duration"] == 150 and config["sample_duration"] == 15
    assert sum(s["seconds"] for s in config["sample_shots"]) == 15
    assert sum(config["destination_seconds_by_day"]) == 45
    assert len({s["id"] for s in config["sample_shots"]}) == 4
    assert {p["id"] for p in config["walking_pair"]} == {"boy", "girl"}
    for shot in config["sample_shots"]:
        assert shot["weather_profile"] in config["weather_profiles"]
        assert (ROOT / shot["reference"]).is_file()
        for image in shot.get("additional_references", []):
            assert (ROOT / image).is_file()
        if shot.get("landmark"):
            assert shot["landmark"] in config["landmarks"]
    for landmark in config["landmarks"].values():
        assert landmark["source_url"].startswith("https://")
        assert len(landmark["lonlat"]) == 2 and landmark["coordinate_source"]
    mist=config["weather_profiles"]["changing-valley"].get("mist_placement")
    if mist:
        assert mist["kind"]=="upper-slopes"
        assert mist["zero_below_rise"]==.6 and mist["full_above_rise"]==.75
        assert 0<mist["ridge_approach_fraction"]<=1 and all(v>0 for v in mist["volume_scale_m"])


def prepare(work, scenery_dir="cinematic-v3", reuse_sample=None):
    config = json.loads(CONFIG.read_text())
    validate(config)
    assert work != ROOT and ROOT not in work.parents
    free = shutil.disk_usage(work).free / 1024**3
    if free < config["minimum_free_gib"]:
        raise RuntimeError(f"{free:.2f} GiB free; 8 GiB required. Nothing prepared or rendered.")
    source = work / "cinematic-film/film.json"
    if not source.is_file():
        raise RuntimeError("The existing approved-film terrain cache is required; no implicit downloads.")
    payload = json.loads(source.read_text())
    existing = {s["id"]: s for s in payload["config"]["shots"]}
    geometry, shots, start = {}, [], 0
    for patch in config["sample_shots"]:
        shot = {**copy.deepcopy(existing[patch["base_shot"]]), **patch}
        shot["start_seconds"] = start
        shot["atmosphere_3d"] = True
        shot["show_route"] = False
        shot["endpoint_labels"] = []
        shot.pop("camera_axes", None)
        start += shot["seconds"]
        shots.append(shot)
        geometry[shot["id"]] = payload["shot_geometry"][patch["base_shot"]]
    payload["config"].update(approval_status="sample_only", duration=15, render_kind="film",
        full_duration=150, shots=shots, poster_seconds=2.5, minimum_free_gib=8,
        scenery=config, approval_sample=True, fade_seconds=0.35)
    payload["shot_geometry"] = geometry
    for path in payload["terrain_files"].values():
        assert Path(path).is_file(), path
    provenance = payload["provenance"]
    provenance.update(status="revised_scenery_sample_awaiting_approval",
        note="Real Copernicus terrain and OSM water/forest outlines; photo-guided original landmark models, snow masks and weather are illustrative, not surveyed buildings or historical weather measurements.",
        landmarks=config["landmarks"], scenery_config_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        source_photo_hashes={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
            for s in shots for p in [s["reference"], *s.get("additional_references", [])]})
    assert Path(scenery_dir).name==scenery_dir and scenery_dir.startswith("cinematic-v3")
    destination = work / scenery_dir
    if reuse_sample:
        reuse_sample=reuse_sample.resolve()
        assert reuse_sample!=destination.resolve()
        old=json.loads((reuse_sample/"film.json").read_text())
        completed=json.loads((reuse_sample/"completed-film.json").read_text())
        assert completed["duration"]==15 and completed["frames"]==360
        digest=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        assert digest(reuse_sample/"journey-scenery-approval-sample.mp4")==completed["sha256"]
        previous_config=copy.deepcopy(config)
        previous_config["weather_profiles"]["changing-valley"].pop("mist_placement")
        assert previous_config==old["config"]["scenery"], "Reuse is permitted only for this isolated Ortisei mist correction"
        frozen={}
        for shot in shots:
            if shot["id"]=="v3-ortisei-atmosphere":
                continue
            assert shot==next(s for s in old["config"]["shots"] if s["id"]==shot["id"])
            assert geometry[shot["id"]]==old["shot_geometry"][shot["id"]]
            entry=next(e for e in completed["shots"] if e["id"]==shot["id"])
            artifacts={key:{"path":entry[key],"sha256":digest(Path(entry[key]))} for key in ("movie","proof","qa")}
            stills=Path(entry["proof"]).parent/"stills-qa.json"
            artifacts["stills_qa"]={"path":str(stills),"sha256":digest(stills)}
            frozen[shot["id"]]={"entry":entry,"artifacts":artifacts}
        payload["frozen_shots"]=frozen
        provenance["reused_approved_sample"]={"directory":str(reuse_sample),"movie_sha256":completed["sha256"],
            "payload_sha256":digest(reuse_sample/"film.json"),"provenance_sha256":digest(reuse_sample/"provenance.json"),
            "completed_sha256":digest(reuse_sample/"completed-film.json"),"shots":frozen}
    destination.mkdir(exist_ok=True)
    (destination / "film.json").write_text(json.dumps(payload, ensure_ascii=False))
    (destination / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
    print(f"SCENERY_SAMPLE_PREPARED {destination}: 15s/360 frames; production remains 150s/3600 frames")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--scenery-dir", default="cinematic-v3")
    parser.add_argument("--reuse-sample", type=Path, help="Freeze the three approved non-Ortisei clips from a completed sample")
    args = parser.parse_args()
    if args.validate_only:
        validate(json.loads(CONFIG.read_text()))
        print("SCENERY_CONFIG_OK: four shots, photo references, verified landmark sources, two adult hikers")
    else:
        if not args.work:
            parser.error("--work is required")
        prepare(args.work.resolve(),args.scenery_dir,args.reuse_sample)
