#!/usr/bin/env python3
"""Render bounded EEVEE chapters and publish verified, silent local media.

python3 scripts/encode-journey-overview.py --work /scratch --blender /path/to/Blender
Use --chapters day-02 for an isolated full-resolution motion sample. Encoded
chapters are resumed only when the renderer/configuration/data fingerprint agrees.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def command(args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, **kwargs)


def probe(path):
    return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument("--chapters", nargs="+")
    args = parser.parse_args()
    work = args.work.resolve()
    assert ROOT != work and ROOT not in work.parents
    config = json.loads((work / "journey.json").read_text())["config"]
    provenance = json.loads((work / "provenance.json").read_text())
    assert not provenance.get("diagnostic_only"), "Scenery data are incomplete; do not render release chapters."
    chapters = [("opening", 3)] + [(d["id"], d["seconds"]) for d in config["days"]] + [("ending", 3)]
    renderer = ROOT / "scripts/render-journey-overview.py"
    digest = hashlib.sha256(renderer.read_bytes()+(work / "journey.json").read_bytes()+(work / "provenance.json").read_bytes()).hexdigest()
    cache = work / "encoded" / digest[:12]
    cache.mkdir(parents=True, exist_ok=True)
    for chapter, duration in chapters:
        if args.chapters and chapter not in args.chapters:
            continue
        movie = cache / f"{chapter}.mp4"
        if movie.exists() and abs(float(probe(movie)["format"]["duration"])-duration) < .02:
            print(f"REUSE {chapter}", flush=True)
            continue
        if shutil.disk_usage(work).free < 1500*1024**2:
            raise RuntimeError("Less than 1.5 GiB free; stop before allocating a frame batch.")
        started = time.monotonic()
        log = cache / f"{chapter}.log"
        with log.open("w") as stream:
            command([args.blender, "--background", "--factory-startup", "--python", renderer,
                     "--", "--work", work, "--chapter", chapter], stdout=stream, stderr=subprocess.STDOUT)
        frames = work / "frames" / chapter
        assert len(list(frames.glob("[0-9][0-9][0-9][0-9][0-9].png"))) == duration*24
        command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "24", "-i", frames / "%05d.png",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-an", movie])
        assert abs(float(probe(movie)["format"]["duration"])-duration) < .02
        # Save a representative proof frame; remove only this renderer's numbered PNGs.
        shutil.copy2(frames / f"{duration*12:05}.png", cache / f"{chapter}.png")
        for frame in frames.glob("[0-9][0-9][0-9][0-9][0-9].png"):
            frame.unlink()
        print(f"ENCODED {chapter}: {duration}s in {time.monotonic()-started:.1f}s; temporary frames cleared", flush=True)
    if args.chapters:
        print(f"Samples: {cache}")
        return
    concat = cache / "concat.txt"
    concat.write_text("".join(f"file '{chapter}.mp4'\n" for chapter, _ in chapters))
    staging = work / "release"
    staging.mkdir(exist_ok=True)
    video = staging / "swiss-dolomites-overview.mp4"
    command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", concat,
             "-vf", "fade=t=in:st=0:d=0.3:color=0xf2ede0,fade=t=out:st=71.5:d=0.5:color=0xf2ede0",
             "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-maxrate", "2100k", "-bufsize", "4200k",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", video])
    metadata = probe(video)
    assert len(metadata["streams"]) == 1 and abs(float(metadata["format"]["duration"])-72) < .02
    stream = metadata["streams"][0]
    assert (stream["width"], stream["height"], stream["r_frame_rate"]) == (1280, 960, "24/1")
    assert video.stat().st_size <= 20*1024**2
    poster = staging / "swiss-dolomites-overview-poster.jpg"
    command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "10", "-i", video, "-frames:v", "1", "-q:v", "2", poster])
    gif = staging / "swiss-dolomites-overview.gif"
    # Keep the complete timeline. Palette tuning precedes any change beyond the
    # explicitly approved 480 x 360 / 8 fps fallback (never reduced further).
    for width, fps, colors, dither in [(640, 10, 160, "bayer:bayer_scale=3"),
                                      (480, 8, 128, "bayer:bayer_scale=5"),
                                      (480, 8, 96, "none")]:
        palette = cache / "palette.png"
        scale = f"fps={fps},scale={width}:-1:flags=lanczos"
        command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-vf", scale+f",palettegen=max_colors={colors}:stats_mode=diff", "-frames:v", "1", palette])
        command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-i", palette,
                 "-filter_complex", f"[0:v]{scale}[s];[s][1:v]paletteuse=dither={dither}:diff_mode=rectangle",
                 "-loop", "0", gif])
        if gif.stat().st_size <= 35*1024**2:
            break
    assert gif.stat().st_size <= 35*1024**2
    assert abs(float(probe(gif)["format"]["duration"])-72) < .15
    provenance["render"] = {"blender": "4.5.13 LTS", "renderer": "EEVEE", "duration_seconds": 72,
        "resolution": [1280, 960], "fps": 24, "audio": False, "vertical_exaggeration": 1,
        "projection": "Local equirectangular, origin 9 E / 47 N, kilometres",
        "render_grid_metres": {"overview": 980.0, "oeschinensee": 32.4, "jungfrau": 79.6, "dolomites": 100.5, "gardena": 39.5},
        "renderer_sha256": hashlib.sha256(renderer.read_bytes()).hexdigest(),
        "weather": "Illustrative recollection only; not a historical weather reconstruction"}
    provenance["media"] = [{"file": file.name, "bytes": file.stat().st_size, "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}
                           for file in [video, gif, poster]]
    provenance["gif"] = {"width": width, "height": width*3//4, "fps": fps,
                         "palette_colors": colors, "dither": dither, "duration_seconds": 72}
    destination = ROOT / "assets/media/travel"
    destination.mkdir(parents=True, exist_ok=True)
    for file in [video, gif, poster]:
        shutil.copy2(file, destination / file.name)
    (ROOT / "assets/data/travel/swiss-dolomites-overview-provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(provenance["media"], indent=2))


if __name__ == "__main__":
    main()
