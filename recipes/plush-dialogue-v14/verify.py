"""Read-only verification of the accepted v14 recipe and source artifact."""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / "frozen-files.json").read_text())
for name, record in manifest.items():
    path = HERE / name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
        raise SystemExit(f"Frozen recipe file missing or changed: {name}")
recipe = json.loads((HERE / "recipe.json").read_text())
video = HERE / recipe["accepted_video"]["path"]
if hashlib.sha256(video.read_bytes()).hexdigest() != recipe["accepted_video"]["sha256"]:
    raise SystemExit("Accepted v14 video changed")
from continuity import example_graph
graph = example_graph()
motions = [n["inputs"] for n in graph.values() if n["class_type"] == "MiniMaxH3MotionContext"]
assert len(motions) == 2
assert sum("context_frames" in m for m in motions) == 1
assert not any(any(k in m for k in ("context_audio", "context_latent", "audio_vae")) for m in motions)
print(f"Verified {len(manifest)} frozen files, the user-accepted video, and picture-only continuation wiring.")
