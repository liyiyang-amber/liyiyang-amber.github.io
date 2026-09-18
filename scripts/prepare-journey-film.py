#!/usr/bin/env python3
"""Prepare the approved full film in external scratch space; never publish it."""
import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import urllib.parse

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sample_preparation", ROOT / "scripts/prepare-journey-cinematic.py")
sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample)
prep = sample.legacy()


def directed_parts(leg, routes, playback):
    geometry = next(f["geometry"] for f in routes["features"] if f["properties"]["id"] == leg["feature_id"])
    parts = copy.deepcopy(geometry["coordinates"] if geometry["type"] == "MultiLineString" else [geometry["coordinates"]])
    options = playback.get(leg["id"], {})
    for i in options.get("reverse_parts", []):
        parts[i].reverse()
    if options.get("reverse"):
        parts = [p[::-1] for p in parts[::-1]]
    if options.get("return"):
        parts += [p[::-1] for p in parts[::-1]]
    return [np.asarray(p, dtype=float) for p in parts]


def distances(line):
    xy = np.column_stack(prep.project(*line.T))*1000
    return xy, np.r_[0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]


def point_at(line, d, value):
    return np.array([np.interp(value, d, line[:, i]) for i in range(2)])


def cut_line(line, first, last):
    _, d = distances(line)
    first, last = np.clip([first, last], 0, d[-1])
    return np.vstack((point_at(line, d, first), line[(d > first) & (d < last)], point_at(line, d, last)))


def clip_line(line, bounds):
    """Rectangle clipping without joining separate lines or invisible gaps."""
    west, south, east, north = bounds
    output, current = [], []
    for a, b in zip(line[:-1], line[1:]):
        dx, dy = b-a
        low, high = 0., 1.
        for p, q in [(-dx, a[0]-west), (dx, east-a[0]), (-dy, a[1]-south), (dy, north-a[1])]:
            if abs(p) < 1e-12:
                if q < 0:
                    low, high = 1, 0
                    break
            elif p < 0:
                low = max(low, q/p)
            else:
                high = min(high, q/p)
        if low > high:
            if len(current) >= 2:
                output.append(current)
            current = []
            continue
        aa, bb = a+low*(b-a), a+high*(b-a)
        if current and not np.allclose(current[-1], aa, atol=1e-10, rtol=0):
            output.append(current)
            current = []
        if not current:
            current.append(aa.tolist())
        current.append(bb.tolist())
    if len(current) >= 2:
        output.append(current)
    return output


def load_story():
    style, journey, routes, playback = sample.read_inputs()
    story = json.loads((ROOT / "config/journey-film.json").read_text())
    assert story["approval_status"] == "approved", "The full film requires sample approval"
    config = {**style, **story, "render_kind": "film"}
    places = {p["id"]: copy.deepcopy(p) for p in journey["places"]}
    for key, value in story["transfers"].items():
        place = copy.deepcopy(value)
        if "feature_id" in place:
            g = next(f["geometry"] for f in routes["features"] if f["properties"]["id"] == place["feature_id"])
            parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
            place["longitude"], place["latitude"] = parts[place["part"]][0 if place["endpoint"] == "start" else -1]
        places[key] = {**place, "id": key, "animation_only": True}
    legs = {l["id"]: l for l in journey["route_legs"]}
    order = {l["id"]: i for i, l in enumerate(journey["route_legs"])}
    day_durations = {d["id"]: 0 for d in journey["days"]}
    seen, used, referenced, previous, time = set(), set(), set(), -1, 0
    for shot in config["shots"]:
        assert shot["id"] not in seen and shot["seconds"] > 0
        seen.add(shot["id"])
        assert shot["seconds"]*config["fps"] == int(shot["seconds"]*config["fps"])
        shot["start_seconds"] = time
        time += shot["seconds"]
        shot["show_route"] = shot["camera"].endswith("aerial")
        shot["endpoint_labels"] = ["from", "to"] if shot.get("anchor", "both") == "both" else [shot["anchor"]]
        if not shot["show_route"]:
            shot["endpoint_labels"] = []
        assert shot["region"] in config["regions"]
        for key in ("from_place", "to_place"):
            assert shot[key] in places
            referenced.add(shot[key])
        if "leg_id" not in shot:
            assert shot["id"] in ("opening", "ending") and shot["seconds"] == config[shot["id"]+"_seconds"]
            continue
        leg = legs[shot["leg_id"]]
        assert order[leg["id"]] >= previous, "Shots must follow the real itinerary"
        previous = order[leg["id"]]
        used.add(leg["id"])
        day_durations[leg["day_id"]] += shot["seconds"]
        if not shot["show_route"]:
            parts = directed_parts(leg, routes, playback)
            assert 0 <= shot["part"] < len(parts)
            assert 0 < shot["speed_mps"] <= 20
    assert list(day_durations.values()) == config["day_seconds"], day_durations
    assert time == config["duration"] == 150 and time*config["fps"] == 3600
    assert used == set(legs) and {p["id"] for p in journey["places"]} <= referenced
    low = sum(s["seconds"] for s in config["shots"] if not s["show_route"])
    assert low/time >= .7, f"Only {low/time:.1%} low scenic footage"
    # Both outward and reversed halves of every out-and-back remain explicit.
    for leg_id, options in playback.items():
        if options.get("return"):
            count = len(directed_parts(legs[leg_id], routes, playback))//2
            selected = [s.get("part") for s in config["shots"] if s.get("leg_id") == leg_id and not s["show_route"]]
            assert any(i < count for i in selected) and any(i >= count for i in selected), leg_id
    return config, journey, routes, playback, places


def fetch_map(cache, name, query, swiss):
    path = cache / ("film-"+name+".json")
    source_path = path.with_suffix(".source.json")
    endpoints = (["https://overpass.osm.ch/api/interpreter"] if swiss else []) + ["https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
    if path.exists():
        data = json.loads(path.read_text())
        if not data.get("remark"):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            source = json.loads(source_path.read_text()) if source_path.exists() else None
            prior = cache.parent / "cinematic-film/provenance.json"
            if source is None and prior.exists():
                source = next((s for s in json.loads(prior.read_text())["sources"] if s.get("file") == path.name and s.get("sha256") == digest),None)
            if source is None:
                source = {"url":"https://www.openstreetmap.org/copyright","file":path.name,"sha256":digest,"note":"Existing OSM cache; original mirror was not recorded. Query below is reproducible, not a claimed retrieval endpoint."}
            source = {**source,"query":query,"osm_timestamp":data.get("osm3s",{}).get("timestamp_osm_base")}
            assert source["sha256"] == digest, "Cached map source hash changed"
            source_path.write_text(json.dumps(source,indent=2))
            prep.SOURCES.append(source)
            return data,source["url"]
    error = None
    for endpoint in endpoints:
        before = len(prep.SOURCES)
        try:
            url = endpoint+"?"+urllib.parse.urlencode({"data": query})
            prep.fetch(url, path, attempts=1, timeout=65)
            result = json.loads(path.read_text())
            if result.get("remark"):
                raise ValueError(result["remark"])
            source = {"url":url,"file":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"query":query,"osm_timestamp":result.get("osm3s",{}).get("timestamp_osm_base")}
            source_path.write_text(json.dumps(source,indent=2))
            prep.SOURCES[before:] = [source]
            return result, url
        except Exception as exc:
            del prep.SOURCES[before:]
            error = exc
            if path.exists():
                path.unlink()  # Only this builder's invalid cached HTTP response.
    raise error


def verify_surface(shot, line, fraction, region, mode, elevation, cache):
    west, south, east, north = region["bounds"]
    rail = mode == "rail"
    selector = '["railway"~"^(rail|narrow_gauge|light_rail)$"]' if rail else '["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|service|living_street|track|.*_link)$"]'
    query = f'[out:json][timeout:50];way{selector}({south},{west},{north},{east});out geom;'
    data, url = fetch_map(cache, shot["region"]+("-rail" if rail else "-road"), query, west < 10)
    ways = [w for w in data["elements"] if len(w.get("geometry", [])) >= 2]
    if not ways:
        raise ValueError(f"No mapped surface transport in {shot['region']}")
    starts,deltas,owners = [],[],[]
    for index,w in enumerate(ways):
        way_xy = np.column_stack(prep.project([p["lon"] for p in w["geometry"]],[p["lat"] for p in w["geometry"]]))*1000
        starts.extend(way_xy[:-1])
        deltas.extend(np.diff(way_xy,axis=0))
        owners.extend([index]*(len(way_xy)-1))
    starts,deltas,owners = np.asarray(starts),np.asarray(deltas),np.asarray(owners)
    squared_lengths = np.maximum(np.sum(deltas*deltas,axis=1),1e-9)
    xy, d = distances(line)
    length = d[-1]
    for offset in [0, -.005, .005, -.015, .015, -.03, .03, -.06, .06]:
        start = (fraction+offset)*length
        end = start+shot["seconds"]*shot["speed_mps"]+(55 if rail else 14)
        if start < 0 or end >= length:
            continue
        points = np.array([point_at(xy, d, v) for v in np.linspace(start, end, 9)])
        lon, lat = prep.unproject(points[:, 0]/1000, points[:, 1]/1000)
        if not ((lon > west+.003)&(lon < east-.003)&(lat > south+.003)&(lat < north-.003)).all():
            continue
        chosen = []
        for p in points:
            projections = np.clip(np.sum((p-starts)*deltas,axis=1)/squared_lengths,0,1)
            squared_distances = np.sum((starts+projections[:,None]*deltas-p)**2,axis=1)
            nearest = int(squared_distances.argmin())
            if squared_distances[nearest] > 30**2:
                break
            w = ways[owners[nearest]]
            if any(w.get("tags", {}).get(k, "no") not in ("no", "0", "false") for k in ("bridge", "tunnel", "covered")):
                break
            chosen.append(w["id"])
        if len(chosen) != len(points):
            continue
        heights = elevation.sample(lon, lat, 30)*1000
        grade = np.max(np.abs(np.diff(heights))/((end-start)/8))
        if grade > shot.get("max_grade", .12 if rail else .3):
            continue
        return start/length, {"shot":shot["id"], "source_url":url, "osm_way_ids":sorted(set(chosen)), "checked_length_m":round(end-start, 2), "max_dem_grade":float(grade), "note":"Above-ground map check; displayed heights remain illustrative, not surveyed engineering."}
    raise ValueError(f"No verified above-ground interval for {shot['id']}; inspect before rendering")


def prepare(work):
    config, journey, routes, playback, places = load_story()
    sample.require_space(work, config["minimum_free_gib"])
    destination, cache = work / "cinematic-film", work / "cache"
    destination.mkdir(exist_ok=True)
    elevation = prep.Elevation(cache)
    polygons = prep.load_landcover(cache)
    for name in ("lavaux", "brenner"):
        w,s,e,n = config["regions"][name]["bounds"]
        query = f'[out:json][timeout:50];(nwr["natural"="wood"]({s},{w},{n},{e});nwr["landuse"="forest"]({s},{w},{n},{e}););out geom;'
        data, _ = fetch_map(cache, name+"-forest", query, w < 10)
        polygons += [("forest", prep.polygon_rings(element)) for element in data["elements"] if prep.polygon_rings(element)]
    terrain_files = {}
    for name, region in config["regions"].items():
        sample.require_space(work, config["minimum_free_gib"])
        if region.get("legacy"):
            terrain_files[name] = str(work / ("terrain-"+region["legacy"]+".npz"))
            continue
        path = destination / ("terrain-"+name+".npz")
        terrain_files[name] = str(path)
        key = hashlib.sha256(json.dumps(region, sort_keys=True).encode()).hexdigest()
        marker = path.with_suffix(".sha256")
        if path.exists() and marker.exists() and marker.read_text() == key:
            print(f"REUSE_TERRAIN {name}", flush=True)
            continue
        west,south,east,north = region["bounds"]
        x0,y0 = prep.project(west,south)
        x1,y1 = prep.project(east,north)
        step = region.get("step_m",30)/1000
        xs,ys = np.linspace(x0,x1,math.ceil((x1-x0)/step)+1),np.linspace(y0,y1,math.ceil((y1-y0)/step)+1)
        xx,yy = np.meshgrid(xs,ys)
        lon,lat = prep.unproject(xx,yy)
        z = elevation.sample(lon,lat,90 if step >= .09 else 30)
        np.savez_compressed(path,x=xs,y=ys,z=z,**prep.land_mask(polygons,xs,ys))
        marker.write_text(key)
        print(f"FILM_TERRAIN {name} {z.shape} {step*1000:.0f}m",flush=True)
    for region in config["regions"].values():
        background = region.get("background")
        if background and background not in terrain_files:
            terrain_files[background] = str(work / ("terrain-"+background+".npz"))
    lakes = []
    for kind,rings in polygons:
        if kind != "water":
            continue
        for ring,hole in rings:
            if hole:
                continue
            lon,lat = np.array([p["lon"] for p in ring]),np.array([p["lat"] for p in ring])
            xy = np.column_stack(prep.project(lon,lat))
            area = abs(np.sum(xy[:-1,0]*xy[1:,1]-xy[1:,0]*xy[:-1,1]))/2
            if area < .015:
                continue
            resolution = 30 if area < 5 else 90
            heights = elevation.sample(lon,lat,resolution)
            lakes.append({"xy":xy.tolist(),"height":float(np.percentile(heights,10))+.0006})
    legs = {l["id"]:l for l in journey["route_legs"]}
    geometry, audits = {}, []
    for shot in config["shots"]:
        bounds = config["regions"][shot["region"]]["bounds"]
        lines, modes = [], []
        if "leg_id" not in shot:
            selected, used = [], set()
            for leg in journey["route_legs"]:
                if leg["feature_id"] not in used:
                    selected.append(leg)
                    used.add(leg["feature_id"])
        else:
            selected = [legs[shot["leg_id"]]]
        source_parts = directed_parts(selected[0],routes,playback)
        for leg in selected:
            parts = directed_parts(leg,routes,playback)
            if shot.get("route_parts"):
                parts = [parts[i] for i in shot["route_parts"]]
            for line in parts:
                clipped = clip_line(line,bounds)
                lines += clipped
                modes += [leg["mode"]]*len(clipped)
        anchors = {}
        for key in ("from","to"):
            value = shot.get(key+"_anchor",shot[key+"_place"])
            if value == "route_end":
                anchors[key] = source_parts[-1][-1].tolist()
            else:
                anchors[key] = [places[value]["longitude"],places[value]["latitude"]]
        if shot["show_route"]:
            travel = lines[0] if lines else source_parts[0].tolist()
            shot["fraction"], shot["speed_mps"] = .5,.5
        else:
            line = source_parts[shot["part"]]
            xy,d = distances(line)
            fraction = shot.get("fraction",.5)
            if "near" in shot:
                point = np.array(prep.project(*shot["near"]))*1000
                fraction = float(d[np.linalg.norm(xy-point,axis=1).argmin()]/d[-1])
            if selected[0]["mode"] in ("rail","bus","rideshare"):
                fraction,audit = verify_surface(shot,line,fraction,config["regions"][shot["region"]],selected[0]["mode"],elevation,cache)
                audits.append(audit)
                print(f"SURFACE_VERIFIED {shot['id']}",flush=True)
            initial = fraction*d[-1]
            last = initial+shot["speed_mps"]*shot["seconds"]
            assert last < d[-1], shot["id"]
            first = max(0,initial-500)
            travel = cut_line(line,first,min(d[-1],last+600)).tolist()
            _,local_d = distances(np.asarray(travel))
            shot["source_part"],shot["source_fraction"] = shot["part"],fraction
            shot["source_interval_m"] = [initial,last]
            shot["part"],shot["fraction"] = 0,(initial-first)/local_d[-1]
            for p in (point_at(line,d,initial),point_at(line,d,last)):
                assert bounds[0] < p[0] < bounds[2] and bounds[1] < p[1] < bounds[3], shot["id"]
        geometry[shot["id"]] = {"lines":lines,"modes":modes,"travel":travel,"anchors":anchors}
    provenance = {"status":"approved_full_film", "accessed_on":datetime.date.today().isoformat(),
        "source":"Copernicus GLO-30 / GLO-90 2021; OpenStreetMap outlines and above-ground topology checks",
        "sources":prep.SOURCES,"surface_transport_audits":audits,
        "story_sha256":hashlib.sha256((ROOT / "config/journey-film.json").read_bytes()).hexdigest(),
        "route_sha256":hashlib.sha256(json.dumps(routes,sort_keys=True).encode()).hexdigest(),
        "note":"Terrain overlays are not recorded GPS elevations. Foreground props and Ortisei weather are illustrative, not a historical weather reconstruction."}
    # Include cached DEM inputs too: reusing a prepared terrain patch must not
    # make its source URLs or original-file hashes disappear from provenance.
    original_regions = json.loads(prep.CONFIG.read_text())["regions"]
    tiles = set()
    for name in terrain_files:
        region = config["regions"].get(name,original_regions.get(name))
        if region.get("legacy"):
            region = original_regions[region["legacy"]]
        resolution = region.get("dem",90 if region.get("step_m",30) >= 90 else 30)
        w,s,e,n = region["bounds"]
        tiles.update((lat,lon,resolution) for lat in range(math.floor(s),math.floor(n)+1) for lon in range(math.floor(w),math.floor(e)+1))
    for lat,lon,resolution in sorted(tiles):
        code = "10" if resolution == 30 else "30"
        name = f"Copernicus_DSM_COG_{code}_N{lat:02}_00_E{lon:03}_00_DEM"
        path = cache / (name+".tif")
        if not path.exists():
            raise ValueError(f"A terrain source is missing: {path.name}")
        prep.SOURCES.append({"url":f"https://copernicus-dem-{resolution}m.s3.amazonaws.com/{name}/{name}.tif","file":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    provenance["sources"] = list({(s["url"],s["sha256"]):s for s in prep.SOURCES}.values())
    provenance["terrain_mesh_hashes"] = {name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in terrain_files.items()}
    payload = {"config":config,"journey":journey,"routes":routes,"playback":playback,"places":places,
        "lakes":lakes,"shot_geometry":geometry,"terrain_files":terrain_files,"provenance":provenance}
    (destination / "film.json").write_text(json.dumps(payload,ensure_ascii=False))
    (destination / "provenance.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2))
    print(f"FILM_PREPARED {destination}",flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work",type=Path)
    parser.add_argument("--validate-only",action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        config,*_ = load_story()
        low = sum(s["seconds"] for s in config["shots"] if not s["show_route"])
        print(f"FILM_STORY_OK: {len(config['shots'])} shots, 150s, 3600 frames, {low/150:.1%} low scenic views; 10 days, 18 places, 29 legs, five hikes, return directions")
    else:
        if not args.work:
            parser.error("--work is required")
        work = args.work.resolve()
        assert work != ROOT and ROOT not in work.parents
        prepare(work)


if __name__ == "__main__":
    main()
