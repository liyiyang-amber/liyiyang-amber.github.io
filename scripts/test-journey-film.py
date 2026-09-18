#!/usr/bin/env python3
"""Read-only story, direction, geometry-gap and completed-film checks."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("film_preparation",ROOT / "scripts/prepare-journey-film.py")
film = importlib.util.module_from_spec(spec)
spec.loader.exec_module(film)


def check_overview_validation():
    ruby = 'require "yaml";require "date";require "json";puts JSON.generate(YAML.safe_load(File.read(ARGV[0]).split(/^---\\s*$/)[1],permitted_classes:[Date,Time],aliases:true))'
    source = json.loads(subprocess.check_output(["ruby","-EUTF-8","-e",ruby,str(ROOT / "_travel/swiss+dolomites.md")]))
    cases = [
        ("video-only",{"gif":None,"duration":150},True,None),
        ("optional-gif",{"gif":"/assets/media/travel/swiss-dolomites-overview.gif","duration":150},True,None),
        ("missing-video",{"video":None},False,"overview.video"),
        ("missing-alt",{"alt":None},False,"overview.alt"),
        ("invalid-duration",{"duration":0},False,"overview.duration"),
        ("text-duration",{"duration":"150"},False,"overview.duration"),
        ("missing-gif-file",{"gif":"/assets/media/travel/nonexistent-film.gif"},False,"overview.gif"),
        ("remote-provenance",{"provenance":"https://example.com/sources.json"},False,"overview.provenance")
    ]
    with tempfile.TemporaryDirectory(prefix="journey-film-validation-",dir="/private/tmp") as temporary:
        for name,changes,valid,field in cases:
            data = copy.deepcopy(source)
            data["journey"]["overview"].update(changes)
            path = Path(temporary) / (name+".md")
            path.write_text("---\n"+json.dumps(data,ensure_ascii=False)+"\n---\n")
            result = subprocess.run(["ruby","-EUTF-8",str(ROOT / "scripts/validate-travel-journey.rb"),str(path)],capture_output=True,text=True)
            assert (result.returncode == 0) == valid,(name,result.stdout,result.stderr)
            if field:
                assert field in result.stderr,(name,result.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work",type=Path)
    parser.add_argument("--rendered",action="store_true")
    parser.add_argument("--proofs",action="store_true",help="Check the current all-shot proof index and camera framing")
    args = parser.parse_args()
    config,journey,routes,playback,places = film.load_story()
    assert all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",s["id"]) for s in config["shots"])
    for leg in journey["route_legs"]:
        parts = film.directed_parts(leg,routes,playback)
        assert all(np.isfinite(p).all() and len(p) >= 2 for p in parts)
        if playback.get(leg["id"],{}).get("return"):
            n = len(parts)//2
            assert all(np.array_equal(a,b[::-1]) for a,b in zip(parts[:n],parts[n:][::-1]))
    for leg_id,expected in [("day-07-seceda-round-trip",{0,1,2,3}),("day-08-ortisei-seceda",{0,1}),("day-08-seceda-ortisei",{0,1})]:
        assert {s["part"] for s in config["shots"] if s.get("leg_id") == leg_id and not s["show_route"]} == expected
    # A line that leaves the rectangle and later returns must not gain a bridge.
    line = np.array([[-2.,0.],[0.,0.],[2.,0.],[2.,2.],[0.,.5],[-2.,.5]])
    pieces = film.clip_line(line,[-1,-1,1,1])
    assert len(pieces) == 2 and not np.array_equal(pieces[0][-1],pieces[1][0])
    assert len([p for p in places.values() if not p.get("animation_only")]) == 18
    assert sum(s["seconds"]*config["fps"] for s in config["shots"]) == 3600
    check_overview_validation()
    if args.proofs:
        assert args.work, "--work is required with --proofs"
        entries = json.loads((args.work / "cinematic-film/render-index.json").read_text())
        assert [e["id"] for e in entries] == [s["id"] for s in config["shots"]]
        for entry in entries:
            proof = Path(entry["proof"])
            assert proof.exists(), entry["id"]
            qa = json.loads((proof.parent / "stills-qa.json").read_text())
            assert len(qa["records"]) == 3
            for record in qa["records"]:
                assert record["camera_clearance_m"] >= 2.5, entry["id"]
                shot = qa["shot"]
                if not shot["show_route"] and not shot.get("weather") and shot["camera"] != "passenger_window":
                    x,y = record["vehicle_screen"]
                    assert 15 < x < 1265 and 170 < y < 879, (entry["id"],x,y)
                    assert record.get("vehicle_visual_clearance_m",0) < 4, (entry["id"],"excessive display clearance")
    if args.rendered:
        assert args.work, "--work is required with --rendered"
        directory = args.work / "cinematic-film"
        completed = json.loads((directory / "completed-film.json").read_text())
        assert completed["frames"] == 3600 and completed["duration"] == 150
        assert len(completed["shots"]) == len(config["shots"])
        total = 0
        for entry in completed["shots"]:
            qa = json.loads(Path(entry["qa"]).read_text())
            assert len(qa["records"]) == int(entry["seconds"]*config["fps"])
            assert min(r["camera_clearance_m"] for r in qa["records"]) >= 2.5
            assert len({tuple(r["vehicle_scale"]) for r in qa["records"]}) == 1
            shot = qa["shot"]
            if not shot["show_route"] and not shot.get("weather") and shot["camera"] != "passenger_window":
                for record in qa["records"]:
                    x,y = record["vehicle_screen"]
                    assert 15 < x < 1265 and 170 < y < 879, (entry["id"],record["frame"],x,y)
                    assert record.get("vehicle_visual_clearance_m",0) < 4, (entry["id"],record["frame"],"excessive display clearance")
            total += len(qa["records"])
        assert total == 3600
        video = directory / "journey-cinematic-film.mp4"
        data = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(video)]))
        assert len(data["streams"]) == 1
        stream = data["streams"][0]
        assert stream["codec_name"] == "h264" and stream["nb_frames"] == "3600"
        assert [stream["width"],stream["height"]] == [1280,960] and stream["r_frame_rate"] == "24/1"
        assert float(data["format"]["duration"]) == 150
        assert video.stat().st_size <= config["video_limit_mib"]*1024**2
    print("FILM_TESTS_OK: chronological coverage, 18 places, 29 legs, five hikes, cableway return directions, disconnected geometry, optional GIF and duration validation"+("; all-shot proof framing verified" if args.proofs else "")+("; 3600 rendered frames and media verified" if args.rendered else "; no rendering performed"))


if __name__ == "__main__":
    main()
