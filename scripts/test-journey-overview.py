#!/usr/bin/env python3
"""Audit animation timing, route directions, coverage and prepared terrain."""
import argparse
import json
from pathlib import Path
import numpy as np


def directed_parts(leg, features, config):
    geometry = features[leg["feature_id"]]["geometry"]
    raw = geometry["coordinates"] if geometry["type"] == "MultiLineString" else [geometry["coordinates"]]
    parts = [np.array(part, dtype=float) for part in raw]
    options = config["playback"].get(leg["id"], {})
    for index in options.get("reverse_parts", []):
        parts[index] = parts[index][::-1]
    if options.get("reverse"):
        parts = [part[::-1] for part in parts[::-1]]
    if options.get("return"):
        parts += [part[::-1] for part in parts[::-1]]
        assert np.array_equal(parts[0][0], parts[-1][-1]), leg["id"]
    assert len(parts) == len(raw)*(2 if options.get("return") else 1)
    return parts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads((args.work / "journey.json").read_text())
    journey, config = data["journey"], data["config"]
    features = {f["properties"]["id"]: f for f in data["routes"]["features"]}
    assert len(journey["days"]) == 10 and len(journey["places"]) == 18
    assert len(journey["route_legs"]) == 29 and len(features) == 24
    assert len({leg["feature_id"] for leg in journey["route_legs"] if leg["mode"] == "hike"}) == 5
    assert config["opening_seconds"]+config["ending_seconds"]+sum(d["seconds"] for d in config["days"]) == 72
    assert config["resolution"] == [1280, 960] and config["fps"] == 24
    places = {place["id"]: place for place in journey["places"]}
    visited = {place for day in journey["days"] for place in day["place_ids"]}
    assert visited == set(places)
    start = config["opening_seconds"]
    chapter_ranges = []
    for day, camera in zip(journey["days"], config["days"]):
        assert day["id"] == camera["id"]
        legs = [leg for leg in journey["route_legs"] if leg["day_id"] == day["id"]]
        assert [leg["sequence"] for leg in legs] == list(range(1, len(legs)+1))
        region = config["regions"][camera["region"]]
        west, south, east, north = region["bounds"]
        for leg in legs:
            parts = directed_parts(leg, features, config)
            for part in parts:
                assert np.isfinite(part).all()
                assert (part[:, 0] >= west).all() and (part[:, 0] <= east).all(), leg["id"]
                assert (part[:, 1] >= south).all() and (part[:, 1] <= north).all(), leg["id"]
        first = places[day["place_ids"][0]]
        last = places[day["place_ids"][-1]]
        for point, place in [(directed_parts(legs[0], features, config)[0][0], first),
                             (directed_parts(legs[-1], features, config)[-1][-1], last)]:
            assert np.linalg.norm(point-[place["longitude"], place["latitude"]]) < .018, (day["id"], point, place["name"])
        chapter_ranges.append({"day": day["id"], "start": start, "end": start+camera["seconds"], "legs": len(legs)})
        start += camera["seconds"]
    assert start == 69
    for name in config["regions"]:
        terrain = np.load(args.work / f"terrain-{name}.npz")
        assert np.isfinite(terrain["z"]).all()
        # Regional coverage includes lowlands; a few metres below the vertical datum is valid.
        assert terrain["z"].min() >= -.5 and terrain["z"].max() <= 5
        assert (np.diff(terrain["x"]) > 0).all() and (np.diff(terrain["y"]) > 0).all()
        assert terrain["water"].max() == 255
    assert not json.loads((args.work / "provenance.json").read_text())["diagnostic_only"]
    print("OVERVIEW_COVERAGE_OK: 10 days, 18 places, 29 legs, 24 features, 5 hikes, 1728 frames")
    print(json.dumps(chapter_ranges, indent=2))


if __name__ == "__main__":
    main()
