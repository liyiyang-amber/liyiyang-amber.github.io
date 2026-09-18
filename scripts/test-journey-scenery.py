#!/usr/bin/env python3
"""Approval-sample checks; never renders or modifies the journey page."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work",type=Path)
    parser.add_argument("--proofs",action="store_true")
    parser.add_argument("--rendered",action="store_true")
    parser.add_argument("--scenery-dir",default="cinematic-v3")
    args=parser.parse_args()
    preparation=module("scenery_preparation","scripts/prepare-journey-scenery.py")
    config=json.loads(preparation.CONFIG.read_text())
    preparation.validate(config)
    film=module("film_story","scripts/prepare-journey-film.py")
    story,journey,*_=film.load_story()
    assert story["duration"]==150 and story["fps"]*story["duration"]==3600
    assert all(a<=b for a,b in zip(config["destination_seconds_by_day"],story["day_seconds"]))
    assert len(journey["days"])==10 and len(journey["places"])==18 and len(journey["route_legs"])==29
    assert len([leg for leg in journey["route_legs"] if leg["mode"]=="hike"])==5
    # The sample preparation must never replace the current approved film/page.
    assert hashlib.sha256((ROOT/"assets/media/travel/swiss-dolomites-cinematic.mp4").read_bytes()).hexdigest()=="9e106bb8b9b6b2ecea6a07613475f0a17d827c14166edaed5876510d9623f863"
    assert hashlib.sha256((ROOT/"_travel/swiss+dolomites.md").read_bytes()).hexdigest()=="28e10dd19c6be90813765b981b81244eaf9f0b70d36959df8914404966c600f3"
    if args.proofs or args.rendered:
        assert args.work
        directory=args.work/args.scenery_dir
        payload=json.loads((directory/"film.json").read_text())
        assert payload["config"]["scenery"]==config, "Prepared scenery is stale; rerun preparation after meeting the disk-space gate"
        assert payload["config"]["approval_status"]=="sample_only"
        assert payload["config"]["duration"]==15 and len(payload["config"]["shots"])==4
        assert payload["config"]["samples"]==48 and payload["config"]["minimum_free_gib"]>=8
        provenance=payload["provenance"]
        assert hashlib.sha256((ROOT/"config/journey-film.json").read_bytes()).hexdigest()==provenance["story_sha256"]
        for photo,expected in provenance["source_photo_hashes"].items():
            assert hashlib.sha256((ROOT/photo).read_bytes()).hexdigest()==expected, f"Source photo changed: {photo}"
        encoder=module("scenery_encoder","scripts/encode-journey-film.py")
        if payload.get("frozen_shots"):
            reuse=provenance["reused_approved_sample"]
            original=Path(reuse["directory"])
            assert encoder.sha(original/"journey-scenery-approval-sample.mp4")==reuse["movie_sha256"]
            assert encoder.sha(original/"film.json")==reuse["payload_sha256"]
            assert encoder.sha(original/"provenance.json")==reuse["provenance_sha256"]
            assert encoder.sha(original/"completed-film.json")==reuse["completed_sha256"]
            assert set(payload["frozen_shots"])=={s["id"] for s in config["sample_shots"][:-1]}
        entries=json.loads((directory/"render-index.json").read_text())
        assert [e["id"] for e in entries]==[s["id"] for s in config["sample_shots"]]
        for entry,shot in zip(entries,config["sample_shots"]):
            if shot["id"] in payload.get("frozen_shots",{}):
                render_shot=next(s for s in payload["config"]["shots"] if s["id"]==shot["id"])
                encoder.frozen_entry(payload["frozen_shots"][shot["id"]],render_shot,payload["config"])
            proof=Path(entry["proof"])
            assert proof.is_file()
            qa=json.loads((Path(entry["qa"]) if args.rendered else proof.parent/"stills-qa.json").read_text())
            encoder.check_poses(qa,int(shot["seconds"]*24) if args.rendered else 3)
            if shot["id"]=="v3-ortisei-atmosphere" and config["weather_profiles"]["changing-valley"].get("mist_placement"):
                assert (proof.parent/"proof-00000.png").is_file() and (proof.parent/"proof-00095.png").is_file()
                for record in qa["records"]:
                    assert len(record["mist_bands"])==4
                    for band in record["mist_bands"]:
                        base,crest=band["church_elevation_m"],band["ridge_elevation_m"]
                        assert crest>base+100
                        assert abs(band["zero_below_m"]-(base+.6*(crest-base)))<1e-5
                        assert abs(band["full_above_m"]-(base+.75*(crest-base)))<1e-5
                        assert abs(band["shader_zero_below_m"]-band["zero_below_m"])<.001
                        assert abs(band["shader_full_above_m"]-band["full_above_m"])<.001
                        assert [p[1] for p in band["mask_probes"]]==[0,0,0,.5,1]
                        assert band["center_m"][2]+band["scale_m"][2]*.5>band["full_above_m"]
            for record in qa["records"]:
                assert record["atmosphere_3d"]
                assert len(record["walkers"])==(2 if shot["show_pair"] else 0)
                for walker in record["walkers"]:
                    expected=next(p for p in config["walking_pair"] if p["id"]==walker["id"])
                    assert walker["height_m"]==expected["height_m"]
                    assert any(foot["stance"] for foot in walker["feet"])
                    assert all(abs(foot["sole_clearance_m"])<1e-6 for foot in walker["feet"] if foot["stance"])
            if args.rendered:
                encoder.check_movie(Path(entry["movie"]),shot["seconds"],payload["config"])
        if args.rendered:
            encoder.check_movie(directory/"journey-scenery-approval-sample.mp4",15,payload["config"])
    print("SCENERY_TESTS_OK: sample approval gate, original film/page unchanged, four scenes, two hikers; full story remains 150s/3600 frames")


if __name__=="__main__":
    main()
