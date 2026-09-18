#!/usr/bin/env python3
"""Render the approved 150-second film in resumable, bounded external batches.

--stills checks first/middle/last camera poses and renders one proof per shot.
The default renders/encodes all shots, but never changes the active Jekyll page.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cinematic_encoder",ROOT / "scripts/encode-journey-cinematic.py")
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wait_for_space(work, minimum):
    """Allow bounded OS cleanup after Blender exits, never relax the disk gate."""
    deadline = time.monotonic()+45
    while True:
        free = shutil.disk_usage(work).free/1024**3
        if free >= minimum:
            return free
        if time.monotonic() >= deadline:
            raise RuntimeError(f"Paused safely with {free:.2f} GiB free; full film requires {minimum} GiB")
        print(f"SPACE_WAIT {free:.2f} GiB; waiting for temporary resources to be released; no files deleted", flush=True)
        time.sleep(3)


def frozen_entry(frozen, shot, config):
    """Explicit approved footage reuse, never a forged current-code cache hit."""
    for artifact in frozen["artifacts"].values():
        assert sha(Path(artifact["path"]))==artifact["sha256"], "An approved clip or audit changed"
    entry=dict(frozen["entry"])
    assert (entry["id"],entry["seconds"],entry["start_seconds"])==(shot["id"],shot["seconds"],shot["start_seconds"])
    check_movie(Path(entry["movie"]),shot["seconds"],config)
    check_poses(json.loads(Path(entry["qa"]).read_text()),int(shot["seconds"]*config["fps"]))
    entry["approved_reuse"]={"movie_sha256":frozen["artifacts"]["movie"]["sha256"],"original_fingerprint":entry["fingerprint"]}
    return entry


def check_movie(path, seconds, config):
    data = common.probe(path)
    assert len(data["streams"]) == 1 and data["streams"][0]["codec_type"] == "video"
    stream = data["streams"][0]
    assert [stream["width"],stream["height"]] == config["resolution"]
    assert stream["r_frame_rate"] == f"{config['fps']}/1"
    assert int(stream["nb_frames"]) == int(seconds*config["fps"])
    assert abs(float(data["format"]["duration"])-seconds) < .002
    return data


def check_poses(metadata, expected):
    records = metadata["records"]
    assert len(records) == expected
    assert min(r["camera_clearance_m"] for r in records) >= 2.5
    assert len({tuple(r["vehicle_scale"]) for r in records}) == 1
    assert all(len(r["labels"]) == len(metadata["shot"]["endpoint_labels"]) for r in records)


def make_contact_pages(entries, directory):
    font = ImageFont.truetype(str(directory.parent / "font-body.ttf"),16)
    for start in range(0,len(entries),16):
        subset = entries[start:start+16]
        page = Image.new("RGB",(1280,4*270),common.PAPER)
        draw = ImageDraw.Draw(page)
        for i,entry in enumerate(subset):
            pic = Image.open(entry["proof"])
            pic.thumbnail((320,240))
            x,y = (i%4)*320,(i//4)*270
            page.paste(pic,(x,y))
            draw.text((x+5,y+242),entry["id"],font=font,fill=common.INK)
        page.save(directory / f"contact-{start//16+1}.jpg",quality=93)


def write_preview(directory, config):
    sample=config.get("approval_sample",False)
    video="journey-scenery-approval-sample.mp4" if sample else "journey-cinematic-film.mp4"
    poster="journey-scenery-approval-poster.jpg" if sample else "journey-cinematic-poster.jpg"
    title="Journey scenery · approval sample" if sample else "Switzerland &amp; the Dolomites"
    (directory / "preview.html").write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Switzerland &amp; the Dolomites — cinematic film</title>
<style>body{{margin:0;background:#f2ede0;color:#302f27;font:18px/1.5 Georgia,serif}}main{{max-width:960px;margin:24px auto;padding:0 18px}}h1{{font-size:26px}}video{{display:block;width:100%;max-width:96svh;margin:auto;aspect-ratio:4/3;border-radius:12px}}a{{color:#315a47}}p{{font-size:16px}}</style>
<main><h1>{title}</h1><video controls muted playsinline loop preload="none" poster="{poster}" aria-label="Illustrated Alpine scenery with named places, photo-inspired weather and two adult hikers"><source src="{video}" type="video/mp4"></video>
<p>{config['duration']} seconds · silent · {'approval sample only; current page and film are unchanged' if sample else 'local review before page replacement'}.</p><p><a href="{video}" download>Download MP4</a></p><details><summary>Terrain credits and sources</summary><p>Lake and forest outlines © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>. Individual trees, buildings, characters and weather are illustrative.</p><p>Produced using Copernicus WorldDEM-30 and WorldDEM-90 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.</p><p><a href="provenance.json">Sources and reconstruction notes</a> · <a href="https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM">Copernicus dataset licence</a></p></details></main></html>''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--blender",type=Path,required=True)
    parser.add_argument("--stills",action="store_true")
    parser.add_argument("--shots",nargs="+",help="Bounded proof/render subset; never finalizes an incomplete film")
    parser.add_argument("--prepare",action="store_true",help="Prepare missing data before rendering")
    parser.add_argument("--scenery-sample",action="store_true",help="Render only the configured isolated scenery sample")
    parser.add_argument("--scenery-film",action="store_true",help="Render the approved scenery revision in a separate full-film directory")
    parser.add_argument("--scenery-dir",default="cinematic-v3")
    args = parser.parse_args()
    work = args.work.resolve()
    assert work != ROOT and ROOT not in work.parents
    assert Path(args.scenery_dir).name==args.scenery_dir and args.scenery_dir.startswith("cinematic-v3")
    assert not (args.scenery_sample and args.scenery_film)
    directory = work / ("cinematic-v3-film" if args.scenery_film else args.scenery_dir if args.scenery_sample else "cinematic-film")
    if args.prepare:
        assert not args.scenery_film, "Prepare the scenery film explicitly with prepare-journey-scenery-film.py"
        common.command([sys.executable,ROOT / ("scripts/prepare-journey-scenery.py" if args.scenery_sample else "scripts/prepare-journey-film.py"),"--work",work,
            *(["--scenery-dir",args.scenery_dir] if args.scenery_sample else [])])
    payload = json.loads((directory / "film.json").read_text())
    config = payload["config"]
    assert config["approval_status"] == ("sample_only" if args.scenery_sample else "approved") and config["render_kind"] == "film"
    assert sum(s["seconds"] for s in config["shots"]) == config["duration"]
    assert config["duration"] == config["sample_duration"] if args.scenery_sample else config["duration"] == 150
    assert all(s["seconds"] > 0 and s["seconds"]*config["fps"] == int(s["seconds"]*config["fps"]) for s in config["shots"])
    if args.scenery_sample:
        assert config["approval_sample"] and config["full_duration"] == 150
    renderer = ROOT / "scripts/render-journey-cinematic.py"
    code = sha(renderer)+sha(ROOT / "scripts/render-journey-overview.py")+sha(ROOT / "scripts/encode-journey-cinematic.py")+sha(Path(__file__))
    if config.get("scenery"):
        code += sha(ROOT / "scripts/journey-scenery.py")+hashlib.sha256(json.dumps(config["scenery"],sort_keys=True).encode()).hexdigest()
    terrain_hashes = {key:sha(Path(value)) for key,value in payload["terrain_files"].items()}
    fonts = {kind+str(size):ImageFont.truetype(str(work / f"font-{kind}.ttf"),size) for kind,sizes in [("body",[22,36,44]),("display",[48])] for size in sizes}
    if args.shots:
        assert set(args.shots) <= {s["id"] for s in config["shots"]}
    entries,timings = [],[]
    for shot in config["shots"]:
        if shot["id"] in payload.get("frozen_shots",{}):
            entries.append(frozen_entry(payload["frozen_shots"][shot["id"]],shot,config))
            print(f"REUSE_APPROVED_CLIP {shot['id']}",flush=True)
            continue
        proof_sequence=bool(shot.get("proof_sequence") or config.get("scenery",{}).get("weather_profiles",{}).get(shot.get("weather_profile"),{}).get("mist_placement"))
        region = config["regions"][shot["region"]]
        signature = {"code":code,"shot":shot,"geometry":payload["shot_geometry"][shot["id"]],"lakes":payload["lakes"],
            "local_relief":config.get("seceda_relief"),
            "terrain":terrain_hashes[shot["region"]],"background":terrain_hashes.get(region.get("background")),
            "places":{key:payload["places"][key]["name"] for key in (shot["from_place"],shot["to_place"])},
            "render":{key:config[key] for key in ("duration","fps","resolution","samples","fade_seconds")}}
        fingerprint = hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()[:16]
        encoded = directory / "encoded" / shot["id"] / fingerprint
        encoded.mkdir(parents=True,exist_ok=True)
        movie,qa,proof = encoded / "shot.mp4",encoded / "qa.json",encoded / "proof.png"
        entry = {"id":shot["id"],"seconds":shot["seconds"],"start_seconds":shot["start_seconds"],"movie":str(movie),"proof":str(proof),"qa":str(qa),"fingerprint":fingerprint}
        entries.append(entry)
        if args.shots and shot["id"] not in args.shots:
            continue
        proof_edges=[encoded/"proof-00000.png",encoded/f"proof-{int(shot['seconds']*config['fps'])-1:05}.png"]
        if args.stills and proof.exists() and (encoded / "stills-qa.json").exists() and (not proof_sequence or all(p.exists() for p in proof_edges)):
            check_poses(json.loads((encoded / "stills-qa.json").read_text()),3)
            print(f"REUSE_PROOF {shot['id']}",flush=True)
            continue
        if not args.stills and movie.exists() and qa.exists():
            check_movie(movie,shot["seconds"],config)
            check_poses(json.loads(qa.read_text()),int(shot["seconds"]*config["fps"]))
            print(f"REUSE_MOVIE {shot['id']}",flush=True)
            continue
        free = wait_for_space(work, config["minimum_free_gib"])
        (directory / "state.json").write_text(json.dumps({"status":"proofs" if args.stills else "rendering","shot":shot["id"],"completed_frames":int(shot["start_seconds"]*config["fps"]),"total_frames":int(config["duration"]*config["fps"]),"free_gib":free},indent=2))
        started = time.monotonic()
        arguments = [args.blender,"--background","--factory-startup","--python-exit-code","1","--python",renderer,"--","--work",work,"--film","--shot",shot["id"]]
        if args.scenery_sample:
            arguments += ["--scenery-sample","--scenery-dir",args.scenery_dir]
        elif args.scenery_film:
            arguments += ["--scenery-film"]
        if args.stills:
            arguments += ["--still","--audit"]
            if proof_sequence:
                arguments.append("--proof-sequence")
        with (encoded / ("proof.log" if args.stills else "render.log")).open("w") as log:
            common.command(arguments,stdout=log,stderr=subprocess.STDOUT)
        raw = directory / "frames" / shot["id"]
        metadata = json.loads((raw / "screen-labels.json").read_text())
        check_poses(metadata,3 if args.stills else int(shot["seconds"]*config["fps"]))
        composed = raw / "composited"
        composed.mkdir(exist_ok=True)
        middle = int(shot["seconds"]*config["fps"])//2
        for record in metadata["records"]:
            filename = f"{record['frame']:05}.png"
            if args.stills and not proof_sequence and record["frame"] != middle:
                continue
            common.compose(raw / filename,composed / filename,record,metadata,payload,fonts,shot["start_seconds"])
            if record["frame"] in (0,middle,int(shot["seconds"]*config["fps"])-1):
                shutil.copy2(composed / filename,encoded / ("proof.png" if record["frame"] == middle else f"proof-{record['frame']:05}.png"))
        if not args.stills:
            common.command(["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate",config["fps"],"-i",composed / "%05d.png","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p","-an",movie])
            check_movie(movie,shot["seconds"],config)
        shutil.copy2(raw / "screen-labels.json",encoded / ("stills-qa.json" if args.stills else "qa.json"))
        # Remove only this shot's verified generated frame batches, never sources.
        for folder in (raw,composed):
            for path in folder.glob("[0-9][0-9][0-9][0-9][0-9].png"):
                path.unlink()
        elapsed = time.monotonic()-started
        timings.append({"shot":shot["id"],"seconds_spent":elapsed,"frames":(3 if proof_sequence else 1) if args.stills else int(shot["seconds"]*config["fps"])})
        (encoded / "benchmark.json").write_text(json.dumps(timings[-1],indent=2))
        print(f"{'PROOF' if args.stills else 'SHOT'}_READY {shot['id']} {elapsed:.1f}s",flush=True)
    (directory / "render-index.json").write_text(json.dumps(entries,indent=2))
    proofs = [entry for entry in entries if Path(entry["proof"]).exists()]
    make_contact_pages(proofs,directory)
    if args.stills or args.shots:
        print(f"BOUNDED_RENDER_FINISHED {len(proofs)} proofs; active film unchanged",flush=True)
        return
    for entry in entries:
        check_movie(Path(entry["movie"]),entry["seconds"],config)
    concat = directory / "concat.txt"
    concat.write_text("".join(f"file '{entry['movie']}'\n" for entry in entries))
    video = directory / ("journey-scenery-approval-sample.mp4" if args.scenery_sample else "journey-cinematic-film.mp4")
    common.command(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",concat,"-c","copy","-movflags","+faststart",video])
    if video.stat().st_size > config["video_limit_mib"]*1024**2:
        assert not config.get("preserve_frame_identity"), "Size limit exceeded: do not reencode frozen clips"
        compressed = directory / "journey-cinematic-sized.mp4"
        bitrate = int(config["video_limit_mib"]*1024**2*8/config["duration"]*.93)
        for pass_number in (1,2):
            common.command(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",video,"-c:v","libx264","-preset","slow","-b:v",bitrate,"-pass",pass_number,"-passlogfile",directory / "size-pass","-pix_fmt","yuv420p","-an","-movflags","+faststart",*(["-f","null","/dev/null"] if pass_number == 1 else [compressed])])
        compressed.replace(video)
    data = check_movie(video,config["duration"],config)
    assert video.stat().st_size <= config["video_limit_mib"]*1024**2
    common.command(["ffmpeg","-hide_banner","-loglevel","error","-i",video,"-f","null","-"])
    common.command(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",config["poster_seconds"],"-i",video,"-frames:v","1","-q:v","2",directory / ("journey-scenery-approval-poster.jpg" if args.scenery_sample else "journey-cinematic-poster.jpg")])
    metadata = {"duration":config["duration"],"frames":int(config["duration"]*config["fps"]),"fps":config["fps"],"resolution":config["resolution"],"bytes":video.stat().st_size,"sha256":sha(video),"shots":entries,"publication_status":"local_review_only"}
    (directory / "completed-film.json").write_text(json.dumps(metadata,indent=2))
    (directory / "state.json").write_text(json.dumps({"status":"render_complete_awaiting_local_review","frames":int(config["duration"]*config["fps"]),"video":str(video)},indent=2))
    write_preview(directory,config)
    print(f"FILM_READY_FOR_LOCAL_REVIEW {video}; no page or active media replaced",flush=True)


if __name__ == "__main__":
    main()
