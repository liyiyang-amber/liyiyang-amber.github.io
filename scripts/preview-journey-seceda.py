#!/usr/bin/env python3
"""Make an external before/after review, never touch the installed film."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    recipe = json.loads((Path(__file__).resolve().parents[1]/"config/journey-seceda.json").read_text())
    directory = args.work/recipe["directory"]
    baseline = json.loads((directory/"preservation-baseline.json").read_text())
    assert sha(Path(baseline["source_movie"]["path"])) == baseline["source_movie"]["sha256"]
    payload = json.loads((directory/"film.json").read_text())
    completed = json.loads((args.work/"cinematic-v3-film/completed-film.json").read_text())
    originals = [next(e for e in completed["shots"] if e["id"]==s["id"]) for s in payload["config"]["shots"]]
    concat = directory/"before-concat.txt"
    assert all("'" not in e["movie"] for e in originals)
    concat.write_text("".join(f"file '{e['movie']}'\n" for e in originals))
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy","-movflags","+faststart",str(directory/"before-seceda.mp4")],check=True)
    subprocess.run(["ffmpeg","-v","error","-y","-ss","7","-i",str(directory/"before-seceda.mp4"),"-frames:v","1","-q:v","2",str(directory/"before-poster.jpg")],check=True)
    (directory/"before-provenance.json").write_text(json.dumps({"parent_movie":baseline["source_movie"],"method":"Lossless concatenation of the six original encoded clips", "duration":12.5,"frames":300,"clips":{e["id"]:sha(Path(e["movie"])) for e in originals},"sha256":sha(directory/"before-seceda.mp4")},indent=2))
    if recipe.get("previous_revision"):
        previous = args.work/recipe["previous_revision"]
        for source,target in [("journey-scenery-approval-sample.mp4","before-seceda.mp4"),("journey-scenery-approval-poster.jpg","before-poster.jpg")]:
            expected=baseline["previous_revision"][str(previous/source)]
            assert sha(previous/source)==expected
            shutil.copy2(previous/source,directory/target)
            assert sha(directory/target)==expected
        (directory/"before-provenance.json").write_text(json.dumps({"method":"Byte-for-byte copy of previous Seceda review sample", "source":str(previous/"journey-scenery-approval-sample.mp4"),"sha256":sha(directory/"before-seceda.mp4")},indent=2))
    (directory/"compare.html").write_text('''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Seceda · ridge panorama review</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f2ede0;color:#302f27;font:17px/1.5 Georgia,serif}main{max-width:1320px;margin:32px auto;padding:0 20px}h1{font-size:clamp(28px,4vw,42px);margin:0 0 8px}h2{font-size:21px;margin:0 0 10px}.eyebrow{font:12px Arial,sans-serif;text-transform:uppercase;letter-spacing:.18em;color:#315a47}p{max-width:850px}.comparison{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin:26px 0}section{min-width:0}video{display:block;width:100%;aspect-ratio:4/3;background:#ded8c8;border-radius:12px}a{color:#315a47}button{font:inherit;border:1px solid #315a47;border-radius:6px;padding:9px 16px;color:#315a47;background:transparent;cursor:pointer}button:focus-visible,a:focus-visible{outline:3px solid #b44f39;outline-offset:4px}.note{color:#665f50;font-size:15px}@media(max-width:760px){main{margin:22px auto;padding:0 12px}.comparison{grid-template-columns:1fr;gap:28px}.revised{grid-row:1}}
</style><main><p class="eyebrow">Isolated approval sample</p><h1>Seceda: the ridge, revealed</h1>
<p>12.5 seconds · six replacement shots. Sharper blades and flowing left-hand cliffs; Day 8 reveals the main crest over two seconds while valley and summit clouds remain. The installed 150-second film is unchanged.</p>
<button id="play-both" type="button">Restart and play both</button>
<div class="comparison"><section><h2>Before · previous Seceda sample</h2><video id="before" controls muted playsinline loop preload="none" poster="before-poster.jpg" aria-label="Previous Seceda review sample"><source src="before-seceda.mp4" type="video/mp4"></video></section>
<section class="revised"><h2>After · proposed Seceda revision</h2><video id="after" controls muted playsinline loop preload="none" poster="journey-scenery-approval-poster.jpg" aria-label="Revised Seceda ridge panoramas and two-second mist reveal"><source src="journey-scenery-approval-sample.mp4" type="video/mp4"></video></section></div>
<p><a href="journey-scenery-approval-sample.mp4" download>Download the revised MP4</a> · <a href="provenance.json">Sources and revision notes</a></p>
<p class="note">The other 62 clips and previous sample remain untouched. This is an original, photo-guided artistic reconstruction over Copernicus terrain—not a new high-resolution survey. Local shoulders are carved into sharper ridges; measured crest anchors, overall scale and the 30-metre walking-path corridor stay fixed. No source photograph is inserted into the film. The progress strip retains the original full-film positions for later lossless clip reuse.</p>
<p class="note">Terrain: Copernicus WorldDEM-30/90 © DLR e.V. and Airbus Defence and Space, provided under COPERNICUS by the EU and ESA. Map outlines © OpenStreetMap contributors.</p></main>
<script>document.getElementById('play-both').addEventListener('click',()=>{for(const video of document.querySelectorAll('video')){video.currentTime=0;video.play().catch(()=>{});}});</script></html>''')
    print("SECEDA_REVIEW_READY", directory/"compare.html")


if __name__ == "__main__":
    main()
