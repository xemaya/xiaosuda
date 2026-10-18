"""Accepted v14 graph wiring, reusable for a new scene or a new continuation.

This module builds JSON only. It never submits GPU jobs or uploads assets.
Carriers are static HD-master loops with the CURRENT take's intended audio.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECIPE = json.loads((HERE / "recipe.json").read_text())


def aligned_frames(frames):
    return frames + (5 - frames % 17) % 17


def add_node(graph, kind, **inputs):
    key = str(max(map(int, graph), default=0) + 1)
    graph[key] = {"class_type": kind, "inputs": inputs}
    return key


def new_graph(master_image):
    graph, roles = {}, {}
    models = RECIPE["models"]
    unet = add_node(graph, "UNETLoader", unet_name=models["unet"], weight_dtype="default")
    model = add_node(graph, "LoraLoaderModelOnly", model=[unet, 0], lora_name=models["lora"],
                     strength_model=models["lora_strength"])
    roles["model"] = [model, 0]
    roles["clip"] = [add_node(graph, "CLIPLoaderGGUFMiniMaxH3", clip_name=models["clip"],
                              vision_name=models["vision"]), 0]
    roles["video_vae"] = [add_node(graph, "VAELoader", vae_name=models["video_vae"]), 0]
    roles["audio_vae"] = [add_node(graph, "VAELoader", vae_name=models["audio_vae"]), 0]
    roles["master"] = [add_node(graph, "LoadImage", image=master_image), 0]
    roles["sampler"] = [add_node(graph, "KSamplerSelect", sampler_name=RECIPE["render"]["sampler"]), 0]
    return graph, roles


def select_visible(graph, images, keep_frames):
    """Use this selected stream as the NEXT take's context source."""
    if keep_frames < 1:
        raise ValueError("keep_frames must be positive")
    return [add_node(graph, "ImageFromBatch", image=images, batch_index=0, length=keep_frames), 0]


def append_take(graph, roles, *, carrier, prompt, keep_frames, seed, prefix,
                context_images=None, first_anchor=False, anchors=(), raw_frames=None):
    if not 1 <= keep_frames <= 243:
        raise ValueError("Keep each delivered take within the accepted ~10-second range")
    if context_images is not None and first_anchor:
        raise ValueError("Motion context owns the head; do not also pin a still at frame 0")
    render = RECIPE["render"]
    overlap = render["context_frames"] if context_images is not None else 0
    length = aligned_frames(keep_frames + overlap) if raw_frames is None else raw_frames
    if length % 17 != 5 or length < keep_frames + overlap or length > 362:
        raise ValueError("Invalid H3 aligned length")
    video = add_node(graph, "LoadVideo", file=carrier)
    sliced = add_node(graph, "Video Slice", video=[video, 0], start_time=0.0,
                      duration=15.0, strict_duration=False)
    parts = add_node(graph, "GetVideoComponents", video=[sliced, 0])
    cond = add_node(graph, "MiniMaxH3ReferenceToVideo", clip=roles["clip"],
                    vae=roles["video_vae"], audio_vae=roles["audio_vae"], prompt=prompt,
                    width=render["width"], height=render["height"], length=length,
                    ref_image_size="match", **{"ref_images.ref_image_0": roles["master"],
                    "ref_videos.ref_video_0": [parts, 0],
                    "ref_video_audios.ref_video_audio_0": [parts, 1]})
    positive = [cond, 0]
    for frame in ([0] if first_anchor else []) + list(anchors):
        if not 0 <= frame < length:
            raise ValueError("Anchor is outside the raw take")
        guide = add_node(graph, "MiniMaxH3AddGuide", positive=positive,
                         vae=roles["video_vae"], latent=[cond, 1], image=roles["master"], frame_idx=frame)
        positive = [guide, 0]
    context = {"context_frames": context_images} if context_images is not None else {}
    motion = add_node(graph, "MiniMaxH3MotionContext", conditioning=positive,
                      vae=roles["video_vae"], latent=[cond, 1],
                      context_length=str(render["context_frames"]), audio_context_length=24, **context)
    # Deliberately absent: context_audio, context_latent and context audio_vae.
    guider = add_node(graph, "BasicGuider", model=roles["model"], conditioning=[motion, 0])
    scheduler = add_node(graph, "BasicScheduler", model=roles["model"], scheduler=render["scheduler"],
                         steps=render["steps"], denoise=1.0)
    noise = add_node(graph, "RandomNoise", noise_seed=seed)
    sample = add_node(graph, "SamplerCustomAdvanced", noise=[noise, 0], guider=[guider, 0],
                      sampler=roles["sampler"], sigmas=[scheduler, 0], latent_image=[cond, 1])
    decoded = add_node(graph, "VAEDecode", samples=[sample, 0], vae=roles["video_vae"])
    audio = add_node(graph, "VAEDecodeAudio", samples=[sample, 0], vae=roles["audio_vae"])
    trimmed = add_node(graph, "MiniMaxH3MotionContextTrim", images=[decoded, 0],
                       trim_frames=[motion, 1], audio=[audio, 0], fps=24.0, match_tail=True)
    visible = select_visible(graph, [trimmed, 0], keep_frames)
    movie = add_node(graph, "CreateVideo", images=[trimmed, 0], audio=[trimmed, 1], fps=24.0)
    save = add_node(graph, "SaveVideo", video=[movie, 0], filename_prefix=prefix,
                    format="auto", **{"format.codec": "auto"})
    return {"raw_images": [decoded, 0], "delivered_images": [trimmed, 0],
            "visible_images": visible, "audio": [trimmed, 1], "save_node": save,
            "raw_frames": length, "context_frames": overlap, "keep_frames": keep_frames}


def roles_from_v14(graph):
    """Bind an archived v14 graph, preserving its node IDs and server cache."""
    expected = {"1": "UNETLoader", "2": "LoraLoaderModelOnly", "3": "CLIPLoaderGGUFMiniMaxH3",
                "4": "VAELoader", "5": "VAELoader", "6": "LoadImage", "17": "KSamplerSelect"}
    for key, kind in expected.items():
        if graph.get(key, {}).get("class_type") != kind:
            raise ValueError(f"Not a matching frozen v14 graph: node {key}")
    if graph["1"]["inputs"]["unet_name"] != RECIPE["models"]["unet"]:
        raise ValueError("Model differs from the accepted recipe")
    return {"model": ["2", 0], "clip": ["3", 0], "video_vae": ["4", 0],
            "audio_vae": ["5", 0], "master": ["6", 0], "sampler": ["17", 0]}


def example_graph():
    graph, roles = new_graph("scene-master.png")
    middle = append_take(graph, roles, carrier="native-carrier.mp4",
                         prompt=(HERE / "accepted/native-prompt.txt").read_text(),
                         keep_frames=243, seed=871602711, prefix="batches/recipe-example/middle", first_anchor=True)
    tail = append_take(graph, roles, carrier="continuation-carrier.mp4",
                       prompt=(HERE / "accepted/continuation-prompt.txt").read_text(),
                       keep_frames=178, seed=909285593, prefix="batches/recipe-example/tail",
                       context_images=middle["visible_images"])
    assert (middle["raw_frames"], tail["raw_frames"], tail["context_frames"]) == (243, 209, 22)
    return graph


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Write an offline example graph; no upload or render")
    args = parser.parse_args()
    with args.out.open("x") as f:
        json.dump(example_graph(), f, ensure_ascii=False, indent=2)
        f.write("\n")
