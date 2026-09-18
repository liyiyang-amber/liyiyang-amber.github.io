#!/usr/bin/env python3
"""Validate the approved scenery revision without changing site files or media."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/"scripts"/filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--proofs", action="store_true")
    parser.add_argument("--rendered", action="store_true")
    parser.add_argument("--shots", nargs="+", help="Check a bounded subset, not a completed film")
    parser.add_argument("--recover-missing-sample", action="store_true")
    args = parser.parse_args()
    preparation = module("scenery_film_preparation", "prepare-journey-scenery-film.py")
    preparation.prepare(args.work, validate_only=True, recover_missing_sample=args.recover_missing_sample)
    if not (args.proofs or args.rendered):
        print("SCENERY_FILM_STATIC_TESTS_OK; rendering and visual checks remain pending")
        return
    directory = args.work/preparation.DIRECTORY
    payload = json.loads((directory/"film.json").read_text())
    preparation.validate(payload)
    provenance, config = payload["provenance"], payload["config"]
    assert preparation.sha(preparation.CONFIG) == provenance["scenery_recipe_sha256"]
    # Capture the actual user-edited site at preparation, not an old hard-coded
    # whole-page hash that rejects unrelated approved edits made between runs.
    for path, expected in provenance["protected_site_hashes"].items():
        assert preparation.sha(ROOT/path) == expected, f"Site file changed during render: {path}"
    for path, expected in provenance["source_photo_hashes"].items():
        assert preparation.sha(ROOT/path) == expected, f"Source photograph changed: {path}"
    for name, expected in provenance["terrain_mesh_hashes"].items():
        assert preparation.sha(Path(payload["terrain_files"][name])) == expected
    encoder = module("scenery_film_encoder", "encode-journey-film.py")
    entries = json.loads((directory/"render-index.json").read_text())
    assert [e["id"] for e in entries] == [s["id"] for s in config["shots"]]
    if args.shots:
        assert set(args.shots) <= {s["id"] for s in config["shots"]}
    checked = 0
    for entry, shot in zip(entries, config["shots"]):
        if args.shots and shot["id"] not in args.shots:
            continue
        proof = Path(entry["proof"])
        assert proof.is_file(), shot["id"]
        qa = json.loads((Path(entry["qa"]) if args.rendered else proof.parent/"stills-qa.json").read_text())
        expected = int(shot["seconds"]*24) if args.rendered else 3
        encoder.check_poses(qa, expected)
        for record in qa["records"]:
            assert record["atmosphere_3d"] == bool(shot.get("atmosphere_3d"))
            assert len(record["walkers"]) == (2 if shot.get("show_pair") else 0)
            for walker in record["walkers"]:
                person = next(p for p in config["scenery"]["walking_pair"] if p["id"] == walker["id"])
                assert walker["height_m"] == person["height_m"]
                assert any(foot["stance"] for foot in walker["feet"])
                assert all(abs(f["sole_clearance_m"]) < 1e-6 for f in walker["feet"] if f["stance"])
            if shot["id"] == "d07-ortisei-weather":
                assert len(record["mist_bands"]) == 4
                for band in record["mist_bands"]:
                    base, crest = band["church_elevation_m"], band["ridge_elevation_m"]
                    assert crest > base+100
                    assert abs(band["shader_zero_below_m"]-(base+.6*(crest-base))) < .001
                    assert abs(band["shader_full_above_m"]-(base+.75*(crest-base))) < .001
                    assert [p[1] for p in band["mask_probes"]] == [0, 0, 0, .5, 1]
            if record["vehicle_visible"]:
                x, y = record["vehicle_screen"]
                assert 15 < x < 1265 and 170 < y < 879, (shot["id"], x, y)
                assert record["vehicle_visual_clearance_m"] < 4
        if args.rendered:
            encoder.check_movie(Path(entry["movie"]), shot["seconds"], config)
        checked += expected
    if args.rendered and not args.shots:
        assert checked == 3600
        movie = directory/"journey-cinematic-film.mp4"
        encoder.check_movie(movie, 150, config)
        assert movie.stat().st_size <= 35*1024**2
    print(f"SCENERY_FILM_TESTS_OK: {checked} {'rendered frames' if args.rendered else 'proof poses'}; visual review still required")


if __name__ == "__main__":
    main()
