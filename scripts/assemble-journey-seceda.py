#!/usr/bin/env python3
"""After explicit user approval, assemble six new clips plus 62 frozen clips.

This script does not render, replace website media, or publish. The required
sample checksum identifies the specific sample the user approved; do not invoke
it as an alternative to obtaining that visual approval.
"""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/"scripts"/filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--approved-sample-sha256", required=True,
        help="Checksum of the specific sample explicitly approved by the user")
    args = parser.parse_args()
    work = args.work.resolve()
    assert work != ROOT and ROOT not in work.parents
    prep = module("seceda_assembly_prep", "prepare-journey-seceda.py")
    encoder = module("seceda_assembly_encoder", "encode-journey-film.py")
    tests = module("seceda_assembly_tests", "test-journey-seceda.py")
    sample_dir = work/prep.read(prep.CONFIG)["directory"]
    sample = prep.read(sample_dir/"film.json")
    sample_index = prep.read(sample_dir/"completed-film.json")
    baseline = prep.read(sample_dir/"preservation-baseline.json")
    assert args.approved_sample_sha256 == sample_index["sha256"] == prep.sha(sample_dir/"journey-scenery-approval-sample.mp4")
    assert sample_index["frames"] == 300 and sample_index["duration"] == 12.5
    assert sample["config"]["production_timeline"]
    assert sample["provenance"]["seceda_recipe_sha256"] == prep.sha(prep.CONFIG)
    assert sample["provenance"]["preservation_baseline_sha256"] == prep.sha(sample_dir/"preservation-baseline.json")
    for path,expected in baseline["installed"].items():
        assert prep.sha(ROOT/path) == expected, f"Installed media or page changed: {path}"
    for artifact in [baseline["source_payload"],baseline["source_movie"],*baseline["terrain"].values()]:
        assert prep.sha(Path(artifact["path"])) == artifact["sha256"]
    if shutil.disk_usage(work).free < 8*1024**3:
        raise RuntimeError("At least 8 GiB free required before assembly")
    candidate = copy.deepcopy(prep.read(Path(baseline["source_payload"]["path"])))
    candidate["config"]["scenery"] = copy.deepcopy(sample["config"]["scenery"])
    candidate["config"]["seceda_relief"] = copy.deepcopy(sample["config"]["seceda_relief"])
    replacements = {s["id"]:s for s in sample["config"]["shots"]}
    entries,shots = [],[]
    for old in candidate["config"]["shots"]:
        sid = old["id"]
        if sid in replacements:
            shot = copy.deepcopy(replacements[sid])
            shot["start_seconds"] = old["start_seconds"]
            entry = copy.deepcopy(next(e for e in sample_index["shots"] if e["id"] == sid))
            entry["approved_reuse"] = {"sample_sha256":sample_index["sha256"],
                "clip_sha256":prep.sha(Path(entry["movie"])),"sample_start_seconds":entry["start_seconds"]}
            entry["start_seconds"] = old["start_seconds"]
            candidate["shot_geometry"][sid] = copy.deepcopy(sample["shot_geometry"][sid])
        else:
            frozen = baseline["unchanged_shots"][sid]
            assert old == frozen["shot"] and candidate["shot_geometry"][sid] == frozen["geometry"]
            for artifact in frozen["artifacts"].values():
                assert prep.sha(Path(artifact["path"])) == artifact["sha256"]
            shot = old
            entry = copy.deepcopy(frozen["entry"])
            entry["approved_reuse"] = {"parent_movie_sha256":baseline["source_movie"]["sha256"],
                "clip_sha256":frozen["artifacts"]["movie"]["sha256"]}
        encoder.check_movie(Path(entry["movie"]),shot["seconds"],candidate["config"])
        entries.append(entry);shots.append(shot)
    assert len(entries) == 68 and sum(s["seconds"] for s in shots) == 150
    candidate["config"].update(shots=shots,approval_status="approved",approval_sample=False,duration=150,revision_kind="seceda",preserve_frame_identity=True)
    destination = work/(sample_dir.name+"-approved")
    destination.mkdir(exist_ok=True)
    provenance = candidate["provenance"]
    provenance.update(status="approved_seceda_revision_local_assembly",approved_sample_sha256=sample_index["sha256"],
        parent_installed_sha256=baseline["source_movie"]["sha256"],seceda_recipe_sha256=prep.sha(prep.CONFIG),
        modified_shots=list(prep.EXPECTED),unchanged_clips=62,
        source_photo_hashes=sample["provenance"]["source_photo_hashes"],
        visual_reference_attachments=sample["provenance"]["visual_reference_attachments"],
        seceda_relief=sample["config"]["seceda_relief"],
        note=sample["provenance"]["note"],
        assembly_note="Lossless stream-copy assembly. All 3300 frames outside the six Seceda intervals verified against the installed parent film. Poster unchanged.")
    concat = destination/"concat.txt"
    assert all("'" not in e["movie"] for e in entries)
    concat.write_text("".join(f"file '{e['movie']}'\n" for e in entries))
    video = destination/"journey-cinematic-film.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy","-movflags","+faststart",str(video)],check=True)
    encoder.check_movie(video,150,candidate["config"])
    assert video.stat().st_size <= 35*1024**2, "Do not reencode the unchanged clips to fit a size target"
    parent_frames = tests.framedigests(Path(baseline["source_movie"]["path"]))
    frames = tests.framedigests(video)
    assert len(frames) == len(parent_frames) == 3600
    for entry in entries:
        first,count = int(entry["start_seconds"]*24),int(entry["seconds"]*24)
        expected = tests.framedigests(Path(entry["movie"])) if entry["id"] in replacements else parent_frames[first:first+count]
        assert frames[first:first+count] == expected, entry["id"]
    shutil.copy2(ROOT/"assets/media/travel/swiss-dolomites-cinematic-poster.jpg",destination/"journey-cinematic-poster.jpg")
    (destination/"film.json").write_text(json.dumps(candidate,ensure_ascii=False))
    (destination/"provenance.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2))
    (destination/"render-index.json").write_text(json.dumps(entries,indent=2))
    (destination/"completed-film.json").write_text(json.dumps({"duration":150,"frames":3600,"fps":24,"resolution":[1280,960],"bytes":video.stat().st_size,"sha256":prep.sha(video),"shots":entries,"publication_status":"local_review_only"},indent=2))
    encoder.write_preview(destination,candidate["config"])
    print("SECEDA_APPROVED_ASSEMBLY_READY",video,"; installed site unchanged")


if __name__ == "__main__":
    main()
