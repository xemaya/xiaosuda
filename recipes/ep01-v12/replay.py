#!/usr/bin/env python3
"""Replay the accepted v12 inputs and edit without changing the original job."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
MANIFEST = json.loads((HERE / "manifest.json").read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    errors = []
    files = [(HERE / a["path"], a["sha256"]) for a in MANIFEST["assets"]]
    files += [(PROJECT / a["path"], a["sha256"]) for a in MANIFEST["references"]]
    files += [(PROJECT / s["approved_output"], s["approved_sha256"])
              for s in MANIFEST["shots"].values()]
    files += [(HERE / "runtime" / name, sha)
              for name, sha in MANIFEST["runtime_sha256"].items()]
    files += [(HERE / name, sha) for name, sha in MANIFEST["graph_sha256"].items()]
    for path, sha in files:
        if not path.is_file() or digest(path) != sha:
            errors.append(str(path))
    if errors:
        raise SystemExit("Missing or changed frozen files:\n" + "\n".join(errors))
    print(f"Verified {len(files)} frozen inputs, graphs, runtime files and accepted outputs.")


def ffmpeg(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", *args], check=True)


def carriers(out):
    specs = [
        ("carrier1.mp4", "k1-quiz-916.png", 9.0,
         [("e1_00_quiz", 500), ("e1_02", 5780)]),
        ("carrier2.mp4", "k2-verdict-916.png", 5.2,
         [("e1_03", 500), ("e1_04", 2820)]),
        ("carrier3.mp4", "k3-teach-916.png", 10.2,
         list(zip([f"e2_{i:02d}" for i in range(1, 7)],
                  [250, 1900, 3840, 5680, 7560, 8680]))),
        ("practice-carrier.mp4", "practice-firstframe.png", 10.2,
         list(zip([f"e3_{i:02d}" for i in range(1, 7)],
                  [560, 2280, 3480, 4960, 6480, 7200]))),
    ]
    results = []
    for name, image, seconds, lines in specs:
        args = ["-loop", "1", "-t", str(seconds), "-i", str(HERE / "assets" / image)]
        for clip, _ in lines:
            args += ["-i", str(HERE / "assets/tts" / (clip + ".mp3"))]
        filters = ["[0:v]scale=384:688,setsar=1[v]"]
        for i, (_, delay) in enumerate(lines, 1):
            filters.append(f"[{i}:a]adelay={delay}|{delay}[a{i}]")
        mix = "".join(f"[a{i}]" for i in range(1, len(lines) + 1))
        filters.append(f"{mix}amix=inputs={len(lines)}:normalize=0,apad=whole_dur={seconds}[ao]")
        # The old practice carrier explicitly selected 128k AAC; the other
        # three used ffmpeg's AAC default. Keep that historical difference.
        audio = ["-b:a", "128k"] if name == "practice-carrier.mp4" else []
        pixel = [] if name == "practice-carrier.mp4" else ["-pix_fmt", "yuv420p"]
        target = out / name
        ffmpeg(args + ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[ao]",
                       "-c:v", "libx264", "-crf", "20", *pixel, "-r", "24",
                       "-c:a", "aac", *audio, "-shortest", str(target)])
        results.append({"file": name, "byte_equal": digest(target) == digest(HERE / "assets" / name)})
    (out / "carrier-check.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    if not all(r["byte_equal"] for r in results):
        raise SystemExit("Carrier bytes differ; inspect ffmpeg version and historical settings.")


def assemble(out):
    shots = MANIFEST["shots"]
    verdict = PROJECT / shots["verdict"]["approved_output"]
    padded = out / "shot2pinf.mp4"
    ffmpeg(["-i", str(verdict), "-vf", "tpad=stop_mode=clone:stop_duration=0.5",
            "-af", "apad=whole_dur=5.6667", "-c:v", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "aac", str(padded)])
    inputs = [PROJECT / shots["quiz"]["approved_output"], padded,
              PROJECT / shots["teach"]["approved_output"],
              PROJECT / shots["practice"]["approved_output"]]
    args = []
    for path in inputs:
        args += ["-i", str(path)]
    graph = (
        "[0:v]settb=AVTB[v0];[1:v]settb=AVTB[v1];"
        "[2:v]settb=AVTB[v2];[3:v]settb=AVTB[v3];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[vabc];"
        "[0:a][1:a][2:a]concat=n=3:v=0:a=1[aabc];"
        "[vabc][v3]xfade=transition=slideup:duration=0.5:offset=24.7084[v];"
        "[aabc][3:a]acrossfade=d=0.5[a]"
    )
    target = out / "v12-nosub.mp4"
    ffmpeg(args + ["-filter_complex", graph, "-map", "[v]", "-map", "[a]",
                   "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", str(target)])
    original = PROJECT / MANIFEST["references"][0]["path"]
    result = {"byte_equal": digest(target) == digest(original),
              "replay_sha256": digest(target), "approved_sha256": digest(original)}
    (out / "assembly-check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["byte_equal"]:
        raise SystemExit("Assembly bytes differ; inspect media before claiming a match.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["verify", "carriers", "assemble"])
    parser.add_argument("--out", type=Path, help="New output directory; never overwrite the accepted job")
    args = parser.parse_args()
    verify()
    if args.action != "verify":
        if not args.out:
            parser.error("--out is required")
        out = args.out.resolve()
        if out == HERE or PROJECT / "jobs/1015-v11-keychain" in (out, *out.parents):
            parser.error("Choose a new replay directory outside the accepted job")
        out.mkdir(parents=True, exist_ok=True)
        {"carriers": carriers, "assemble": assemble}[args.action](out)


if __name__ == "__main__":
    main()
