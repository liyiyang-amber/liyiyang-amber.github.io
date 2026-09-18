#!/usr/bin/env python3
"""Render/compose only the 15-second approval sample, never the production film.

python3 scripts/encode-journey-cinematic.py --work SCRATCH --blender EXECUTABLE --stills
python3 scripts/encode-journey-cinematic.py --work SCRATCH --blender EXECUTABLE
Inspect the stills first. The second command renders five bounded shots and
encodes a silent sample in the external scratch directory. No GIF is generated.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PAPER = "#f2ede0"
INK = "#302f27"
COLORS = {"rail": "#315a47", "cable_car": "#39758e", "bus": "#aa6a2b", "rideshare": "#6f5968", "hike": "#b44f39"}


def command(arguments, **kwargs):
    subprocess.run([str(a) for a in arguments], check=True, **kwargs)


def probe(file):
    return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(file)]))


def text_lines(draw, value, font, width):
    lines, current = [], ""
    for word in value.split():
        proposed = (current+" "+word).strip()
        if current and draw.textlength(proposed, font=font) > width:
            lines.append(current)
            current = word
        else:
            current = proposed
    return lines+[current]


def boxes_intersect(a, b, margin=14):
    return not (a[2]+margin < b[0] or b[2]+margin < a[0] or a[3]+margin < b[1] or b[3]+margin < a[1])


def place_callouts(draw, labels, font):
    """Screen-space layout: clamp to safe area and separate the two endpoints."""
    used, result = [], []
    for index, label in enumerate(labels):
        lines = text_lines(draw, label["text"], font, 470)
        width = min(510, max(draw.textlength(line, font=font) for line in lines)+38)
        height = 39+len(lines)*49
        px, py = label["point"]
        x = min(max(px+24 if index == 0 else px-width-24, 30), 1250-width)
        y = min(max(py-height-34, 205), 830-height)
        candidates = [y, min(830-height, py+32), 210, 825-height]
        for candidate in candidates:
            box = (x, candidate, x+width, candidate+height)
            if not any(boxes_intersect(box, old) for old in used):
                break
        else:
            x = 30 if index == 0 else 1250-width
            box = (x, 210 if index == 0 else 825-height, x+width, 210+height if index == 0 else 825)
        used.append(box)
        result.append((label, box, lines))
    return result


def compose(source, destination, record, metadata, payload, fonts, sample_offset):
    frame = Image.open(source).convert("RGB")
    assert frame.size == (1280, 960)
    draw = ImageDraw.Draw(frame)
    shot, leg = metadata["shot"], metadata["leg"]
    film = payload["config"].get("render_kind") == "film"
    places = payload["places"] if film else {p["id"]: p for p in payload["journey"]["places"]}
    day = next((d for d in payload["journey"]["days"] if d["id"] == leg.get("day_id")),None)
    mode = {"rail": "TRAIN", "cable_car": "CABLE CAR", "hike": "HIKE", "rideshare": "CAR", "bus": "BUS"}[leg["mode"]]
    color = COLORS[leg["mode"]]
    if shot.get("weather") and not shot.get("atmosphere_3d"):
        # Original screen-space atmosphere; explicitly illustrative, not an
        # assertion of the weather at a particular time in June 2024.
        phase = record["weather_progress"]
        overlay = Image.new("RGBA",frame.size)
        weather = ImageDraw.Draw(overlay)
        opacity = int(120*min(1,max(0,(phase-.2)/.35)))
        for i in range(5):
            x = (i*310+phase*100)-80
            weather.ellipse((x,210+(i%2)*55,x+370,305+(i%2)*55),fill=(166,175,174,opacity))
        if phase > .63:
            for i in range(80):
                x = (i*149+record["time"]*80)%1280
                y = 200+(i*73+record["time"]*330)%665
                weather.line((x,y,x-8,y+28),fill=(110,137,145,130),width=2)
        frame = Image.alpha_composite(frame.convert("RGBA"),overlay).convert("RGB")
        draw = ImageDraw.Draw(frame)
    # Screen-space labels never tilt, cast shadows, or inherit perspective scaling.
    draw.rectangle((0, 0, 1280, 163), fill=PAPER)
    eyebrow = f"DAY {int(day['id'][-2:])}  ·  JUN {str(day['date'])[-2:]}  ·  {mode}" if day else "JUNE 15–24, 2024  ·  THROUGH THE ALPS"
    draw.text((40,17),eyebrow,font=fonts["body36"],fill=color)
    start = places[shot["from_place"]]["name"]
    end = places[shot["to_place"]]["name"]
    # Draw the arrow ourselves: the locally vendored Latin subset lacks its glyph.
    left_width = draw.textlength(start, font=fonts["display48"])
    right_width = draw.textlength(end, font=fonts["display48"])
    if not day:
        draw.text((40,66),"Switzerland & the Dolomites",font=fonts["display48"],fill=INK)
    elif left_width+right_width+100 <= 1200:
        draw.text((40, 66), start, font=fonts["display48"], fill=INK)
        ax = 40+left_width+24
        draw.line((ax, 101, ax+42, 101), fill=color, width=3)
        draw.line((ax+30, 93, ax+42, 101, ax+30, 109), fill=color, width=3)
        draw.text((ax+65, 66), end, font=fonts["display48"], fill=INK)
    else:
        draw.text((40, 66), "FROM  "+start, font=fonts["body36"], fill=INK)
        draw.text((40, 112), "TO      "+end, font=fonts["body36"], fill=INK)
    for label, box, lines in place_callouts(draw, record["labels"], fonts["body44"]):
        px, py = label["point"]
        px, py = min(max(px, 14), 1266), min(max(py, 182), 858)
        cx = min(max(px, box[0]+10), box[2]-10)
        cy = box[3] if py >= (box[1]+box[3])/2 else box[1]
        draw.line((px, py, cx, cy), fill=PAPER, width=7)
        draw.line((px, py, cx, cy), fill=color, width=3)
        draw.ellipse((px-7, py-7, px+7, py+7), fill=color, outline=PAPER, width=2)
        if shot.get("airport") or (film and not day):
            # An original airport symbol, never a flight path.
            ax,ay = px,py+30
            draw.ellipse((ax-24,ay-24,ax+24,ay+24),fill=PAPER,outline=color,width=2)
            draw.line((ax,ay-17,ax,ay+17),fill=color,width=4)
            draw.line((ax-17,ay+3,ax,ay-4,ax+17,ay+3),fill=color,width=4)
            draw.line((ax-8,ay+15,ax,ay+10,ax+8,ay+15),fill=color,width=3)
        draw.rounded_rectangle(box, radius=10, fill=PAPER, outline=color, width=2)
        label_kind = "DEPARTURE" if label["kind"] == "from" else "ARRIVAL"
        draw.text((box[0]+18, box[1]+7), label_kind, font=fonts["body22"], fill=color)
        for i, line in enumerate(lines):
            draw.text((box[0]+18, box[1]+30+i*49), line, font=fonts["body44"], fill=INK)
    if record["locator"]:
        px, py = record["locator"]
        if 15 < px < 1265 and 180 < py < 860:
            draw.ellipse((px-5, py-5, px+5, py+5), fill=color, outline=PAPER, width=2)
    draw.rectangle((0, 889, 1280, 960), fill=PAPER)
    duration = payload["config"]["duration" if film else "sample_duration"]
    production_timeline = payload["config"].get("production_timeline", False)
    if production_timeline:
        duration = payload["config"]["full_duration"]
        sample_offset = shot["original_start_seconds"]
    footer = f"DAY {int(day['id'][-2:]):02} / 10" if film and day else "JUNE 15–24, 2024" if film else f"VISUAL STUDY · {duration:g} SECONDS"
    if payload["config"].get("approval_sample") and not production_timeline:
        footer = f"SCENERY STUDY · {duration:g} SECONDS"
    if shot.get("weather"):
        footer = "ORTISEI · ILLUSTRATIVE WEATHER CHANGE"
    draw.text((40,904),footer,font=fonts["body22"],fill=INK)
    draw.text((565, 904), "Copernicus terrain · © OpenStreetMap contributors", font=fonts["body22"], fill=INK)
    progress = min(1,(sample_offset+record["time"]+1/payload["config"]["fps"])/duration)
    draw.line((40, 944, 1240, 944), fill="#d9d4c6", width=3)
    draw.line((40, 944, 40+1200*progress, 944), fill=color, width=3)
    if film and shot["id"] in ("opening","ending"):
        fade = payload["config"]["fade_seconds"]
        opacity = min(1,record["time"]/fade) if shot["id"] == "opening" else min(1,(shot["seconds"]-record["time"]-1/payload["config"]["fps"])/fade)
        frame = Image.blend(Image.new("RGB",frame.size,PAPER),frame,max(0,opacity))
    frame.save(destination, compress_level=2)


def validate_layout(work):
    font = ImageFont.truetype(str(work / "font-body.ttf"), 44)
    draw = ImageDraw.Draw(Image.new("RGB", (1280, 960)))
    for points in [[[-100, 20], [1400, 1100]], [[610, 400], [615, 405]], [[100, 800], [120, 790]]]:
        layouts = place_callouts(draw, [{"point": p, "text": name, "kind": kind} for p, name, kind in zip(points, ["Kandersteg", "Santa Maddalena, Val di Funes"], ["from", "to"])], font)
        boxes = [b for _, b, _ in layouts]
        assert all(0 <= b[0] < b[2] <= 1280 and 163 < b[1] < b[3] <= 889 for b in boxes)
        assert not boxes_intersect(boxes[0], boxes[1], margin=0)
    print("CINEMATIC_LABEL_LAYOUT_OK")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--blender", type=Path)
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--test-layout", action="store_true")
    args = parser.parse_args()
    work = args.work.resolve()
    assert work != ROOT and ROOT not in work.parents
    if args.test_layout:
        validate_layout(work)
        return
    if not args.blender:
        parser.error("--blender is required")
    config = json.loads((ROOT / "config/journey-cinematic.json").read_text())
    assert config["approval_status"] == "sample_only"
    free = shutil.disk_usage(work).free/1024**3
    if free < config["sample_minimum_free_gib"]:
        raise RuntimeError(f"Only {free:.2f} GiB free; need {config['sample_minimum_free_gib']} GiB before preparing/rendering the approval sample")
    command([sys_executable(), ROOT / "scripts/prepare-journey-cinematic.py", "--work", work])
    directory = work / "cinematic-v2"
    payload = json.loads((directory / "sample.json").read_text())
    renderer = ROOT / "scripts/render-journey-cinematic.py"
    digest = hashlib.sha256(renderer.read_bytes()+(directory / "sample.json").read_bytes()+Path(__file__).read_bytes()).hexdigest()[:12]
    encoded = directory / "encoded" / digest
    encoded.mkdir(parents=True, exist_ok=True)
    fonts = {kind+str(size): ImageFont.truetype(str(work / f"font-{kind}.ttf"), size)
             for kind, sizes in [("body", [22, 36, 44]), ("display", [48])] for size in sizes}
    offset = 0
    timings = []
    for shot in payload["config"]["sample_shots"]:
        movie = encoded / (shot["id"]+".mp4")
        if not args.stills and movie.exists() and abs(float(probe(movie)["format"]["duration"])-shot["seconds"]) < .02:
            offset += shot["seconds"]
            print(f"REUSE {shot['id']}", flush=True)
            continue
        started = time.monotonic()
        with (encoded / (shot["id"]+("-still" if args.stills else "")+".log")).open("w") as log:
            arguments = [args.blender, "--background", "--factory-startup", "--python", renderer, "--", "--work", work, "--shot", shot["id"]]
            if args.stills:
                arguments.append("--still")
            command(arguments, stdout=log, stderr=subprocess.STDOUT)
        raw = directory / "frames" / shot["id"]
        metadata = json.loads((raw / "screen-labels.json").read_text())
        assert len(metadata["records"]) == (1 if args.stills else shot["seconds"]*config["fps"])
        assert min(r["camera_clearance_m"] for r in metadata["records"]) >= 2.5
        scales = {tuple(r["vehicle_scale"]) for r in metadata["records"]}
        assert len(scales) == 1, "Vehicle size must never change with camera framing"
        composed = raw / "composited"
        composed.mkdir(exist_ok=True)
        for record in metadata["records"]:
            filename = f"{record['frame']:05}.png"
            compose(raw / filename, composed / filename, record, metadata, payload, fonts, offset)
        middle = metadata["records"][len(metadata["records"])//2]["frame"]
        shutil.copy2(composed / f"{middle:05}.png", encoded / (shot["id"]+".png"))
        if not args.stills:
            command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", config["fps"], "-i", composed / "%05d.png", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-an", movie])
            assert abs(float(probe(movie)["format"]["duration"])-shot["seconds"]) < .02
        shutil.copy2(raw / "screen-labels.json", encoded / (shot["id"]+"-qa.json"))
        # Only our numbered raw/composited frame batches; never source files.
        for folder in (raw, composed):
            for path in folder.glob("[0-9][0-9][0-9][0-9][0-9].png"):
                path.unlink()
        elapsed = time.monotonic()-started
        timings.append({"shot": shot["id"], "seconds_spent": elapsed, "rendered_frames": len(metadata["records"])})
        print(f"SAMPLE_SHOT_READY {shot['id']} {elapsed:.1f}s", flush=True)
        offset += shot["seconds"]
    (encoded / "benchmark.json").write_text(json.dumps(timings, indent=2))
    if args.stills:
        print(f"STILLS_FOR_REVIEW {encoded}")
        return
    concat = encoded / "concat.txt"
    concat.write_text("".join(f"file '{s['id']}.mp4'\n" for s in config["sample_shots"]))
    video = directory / "journey-cinematic-approval-sample.mp4"
    command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", concat,
             "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", video])
    data = probe(video)
    assert len(data["streams"]) == 1 and float(data["format"]["duration"]) == 15
    stream = data["streams"][0]
    assert (stream["width"], stream["height"], stream["r_frame_rate"]) == (1280, 960, "24/1")
    poster = directory / "journey-cinematic-approval-poster.jpg"
    command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "4", "-i", video, "-frames:v", "1", "-q:v", "2", poster])
    (directory / "sample.html").write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Journey cinematic sample — approval required</title>
<style>body{margin:0;background:#f2ede0;color:#302f27;font:18px/1.5 Georgia,serif}main{max-width:960px;margin:24px auto;padding:0 18px}h1{font-size:26px}video{display:block;width:100%;max-width:96svh;margin-inline:auto;aspect-ratio:4/3;border-radius:12px}a{color:#315a47}p{font-size:16px}</style>
<main><h1>Journey film · visual sample</h1><video controls muted playsinline preload="none" poster="journey-cinematic-approval-poster.jpg" aria-label="Fifteen-second style sample with named endpoints, low Alpine scenery, a small train and a cable car"><source src="journey-cinematic-approval-sample.mp4" type="video/mp4"></video><p>15 seconds · silent · style approval only. The existing journey page is unchanged.</p><p><a href="journey-cinematic-approval-sample.mp4" download>Download sample MP4</a></p><p>Terrain: Copernicus DEM; lake and forest outlines © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>. Individual trees, rocks and vehicles are original stylized illustrations.</p><details><summary>Terrain credits and sources</summary><p>Produced using Copernicus WorldDEM-30 and WorldDEM-90 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.</p><p><a href="provenance.json">Sources and reconstruction notes</a> · <a href="https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM">Copernicus dataset licence</a></p></details></main></html>''')
    print(f"APPROVAL_SAMPLE_READY {video}\nSTOP: await the user's visual approval before any full-film render or page replacement.")


def sys_executable():
    import sys
    return sys.executable


if __name__ == "__main__":
    main()
