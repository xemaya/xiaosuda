#!/usr/bin/env python3
"""MiniMax H3 命令行出片(ComfyUI API)。按官方 video_minimax_h3_* 模板接线。
例: h3run.py --prompt "..." --unet minimax_h3_fl2va_pruned_fp8_scaled.safetensors --lora minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors:1
    --unet 以 .gguf 结尾走 UnetLoaderGGUF;--ref/--refvideo 走 Ref2VA。
    --pose 动作视频:SDPose 提骨骼 -> Fun ControlNet Union 控制动作(--pose-raw 表示给的已经是骨骼视频)。"""
import argparse, json, time, urllib.request, uuid, os, shutil

from director_receipt import submit as director_submit, completed as director_completed

ap = argparse.ArgumentParser()
ap.add_argument("--receipt", help="导演台任务回执路径(可选)")
ap.add_argument("--prompt")
ap.add_argument("--prompt-file", help="从文件读提示词,免引号转义")
ap.add_argument("--unet", default="minimax_h3_fl2va_pruned_fp8_scaled.safetensors")
ap.add_argument("--clip", default="qwen3-vl-32b-ultra-heretic-minimax-h3-q6_k.gguf")
ap.add_argument("--lora", action="append", default=[], help="name:strength,可多次")
ap.add_argument("--ref", action="append", default=[], help="参考图(已在 input 目录),走 Ref2VA")
ap.add_argument("--first", help="首帧图(input 目录),走 I2V")
ap.add_argument("--last", help="尾帧图(input 目录)")
ap.add_argument("--prev-latent", help="上一段的 AV latent(output 目录下相对路径),Motion Context 续镜,画面和声音真延续;不要再给 --first")
ap.add_argument("--save-latent", help="保存本段 AV latent 的前缀(output 目录下),供下一段续镜")
ap.add_argument("--refvideo", action="append", default=[], help="参考视频(input 目录),走 Ref2VA,正文用 <Video 1>")
ap.add_argument("--pose", help="动作视频(input 目录),提骨骼后用 ControlNet 控制动作")
ap.add_argument("--pose-raw", action="store_true", help="--pose 给的已经是骨骼/控制视频,不再提取")
ap.add_argument("--control-strength", type=float, default=1.0)
ap.add_argument("--pose-threshold", type=float, default=0.2, help="骨骼点置信度阈值,越低骨骼越全也越容易有误检")
ap.add_argument("--controlnet", default="minimax_h3_fun_controlnet_union_2.0_pruned_bf16.safetensors")
ap.add_argument("--save-control", action="store_true", help="另存一份提取出的骨骼视频,方便检查")
ap.add_argument("--w", type=int, default=864); ap.add_argument("--h", type=int, default=480)
ap.add_argument("--sec", type=float, default=5); ap.add_argument("--steps", type=int, default=8)
ap.add_argument("--sampler", default="res_multistep"); ap.add_argument("--scheduler", default="simple")
ap.add_argument("--seed", type=int, default=42); ap.add_argument("--port", type=int, default=8188)
ap.add_argument("--prefix", default="h3/test")
a = ap.parse_args()
if a.prompt_file:
    a.prompt = open(a.prompt_file, encoding="utf-8").read().strip()
if not a.prompt:
    ap.error("需要 --prompt 或 --prompt-file")
if a.prev_latent and a.first:
    ap.error("--prev-latent 续镜时不要再给 --first(钉住的头部已决定开头)")

x = max(5, round(a.sec * 24)) + (22 if a.prev_latent else 0)   # 续镜多采 22 帧,补 Trim 去掉的钉住头部
length = x + (5 - x % 17) % 17   # 模板里的 17k+5 帧对齐
P, nid = {}, [0]
def node(cls, **inp):
    nid[0] += 1; P[str(nid[0])] = {"class_type": cls, "inputs": inp}; return str(nid[0])

unet = node("UnetLoaderGGUF", unet_name=a.unet) if a.unet.endswith(".gguf") else node("UNETLoader", unet_name=a.unet, weight_dtype="default")
model = [unet, 0]
for l in a.lora:
    name, s = l.rsplit(":", 1)
    model = [node("LoraLoaderModelOnly", model=model, lora_name=name, strength_model=float(s)), 0]
clip = node("CLIPLoaderGGUFMiniMaxH3", clip_name=a.clip, vision_name="qwen3vl_32b_minimax_h3_visual_bf16.safetensors") if a.clip.endswith(".gguf") else node("CLIPLoader", clip_name=a.clip, type="minimax", device="default")
vv = node("VAELoader", vae_name="minimax_h3_video_vae_fp16.safetensors")
va = node("VAELoader", vae_name="minimax_h3_audio_vae_fp32.safetensors")

def video_frames(fname, dur):
    """LoadVideo -> 截取前 dur 秒 -> (IMAGE, AUDIO)"""
    v = node("Video Slice", video=[node("LoadVideo", file=fname), 0], start_time=0.0, duration=dur, strict_duration=False)
    c = node("GetVideoComponents", video=[v, 0])
    return [c, 0], [c, 1]

if a.pose:
    frames, _ = video_frames(a.pose, a.sec)
    if a.pose_raw:
        control = frames
    else:  # 官方模板的 SDPose 多人骨骼提取子图
        sdp = node("CheckpointLoaderSimple", ckpt_name="sdpose_wholebody_fp16.safetensors")
        small = node("ResizeImageMaskNode", input=frames, resize_type="scale longer dimension",
                     **{"resize_type.longer_size": 1024}, scale_method="lanczos")
        boxes = node("RTDETR_detect", model=[node("UNETLoader", unet_name="rt_detr_v4-x-hgnet_fp16.safetensors", weight_dtype="default"), 0],
                     image=[small, 0], threshold=min(0.5, a.pose_threshold + 0.1), class_name="person", max_detections=2)
        kp = node("SDPoseKeypointExtractor", model=[sdp, 0], vae=[sdp, 2], image=[small, 0], batch_size=16, bboxes=[boxes, 0])
        control = [node("SDPoseDrawKeypoints", keypoints=[kp, 0], draw_body=True, draw_hands=True, draw_face=True, draw_feet=True,
                        stick_width=4, face_point_size=2, score_threshold=a.pose_threshold, draw_head=True), 0]
        if a.save_control:  # 缩到输出尺寸再存(长边 1024 缩出来可能是奇数高,H.264 编不了)
            prev = node("ResizeImageMaskNode", input=control, resize_type="scale dimensions",
                        **{"resize_type.width": a.w, "resize_type.height": a.h, "resize_type.crop": "center"}, scale_method="lanczos")
            node("SaveVideo", video=[node("CreateVideo", images=[prev, 0], fps=24.0), 0], filename_prefix=a.prefix + "_pose",
                 format="auto", **{"format.codec": "auto"})
    model = [node("MiniMaxH3FunControlNetApply", model=model, model_patch=[node("ModelPatchLoader", name=a.controlnet), 0],
                  vae=[vv, 0], strength=a.control_strength, start_percent=0.0, end_percent=1.0, control_video=control), 0]

if a.ref or a.refvideo:
    refs = {f"ref_images.ref_image_{i}": [node("LoadImage", image=r), 0] for i, r in enumerate(a.ref)}  # ref_image_0 = <Picture 1>
    for i, rv in enumerate(a.refvideo):  # ref_video_0 = <Video 1>,原声一并作为该视频的音轨
        im, au = video_frames(rv, 15.0)
        refs[f"ref_videos.ref_video_{i}"] = im
        refs[f"ref_video_audios.ref_video_audio_{i}"] = au
    cond = node("MiniMaxH3ReferenceToVideo", clip=[clip, 0], vae=[vv, 0], audio_vae=[va, 0], prompt=a.prompt, width=a.w, height=a.h, length=length, ref_image_size="match", **refs)
else:
    extra = {"first_frame": [node("LoadImage", image=a.first), 0]} if a.first else {}
    if a.last:
        extra["last_frame"] = [node("LoadImage", image=a.last), 0]
    cond = node("MiniMaxH3ImageToVideo", clip=[clip, 0], vae=[vv, 0], prompt=a.prompt, width=a.w, height=a.h, length=length, **extra)
cond_pos = [cond, 0]
if a.last and (a.ref or a.refvideo):  # ref2va 分支:用 AddGuide 把尾帧钉到最后一帧(frame_idx=-1)
    cond_pos = [node("MiniMaxH3AddGuide", positive=cond_pos, vae=[vv, 0], latent=[cond, 1],
                     image=[node("LoadImage", image=a.last), 0], frame_idx=-1), 0]
mc_in = dict(conditioning=cond_pos, vae=[vv, 0], latent=[cond, 1], context_length="22", audio_context_length=24)
if a.prev_latent:
    mc_in["context_latent"] = [node("MiniMaxH3MotionContextLoadLatent", latent_path=a.prev_latent, clip_index=1), 0]
mc = node("MiniMaxH3MotionContext", **mc_in)   # 无 context_latent 时直通,trim_frames=0
guider = node("BasicGuider", model=model, conditioning=[mc, 0])
sig = node("BasicScheduler", model=model, scheduler=a.scheduler, steps=a.steps, denoise=1.0)
samp = node("SamplerCustomAdvanced", noise=[node("RandomNoise", noise_seed=a.seed), 0], guider=[guider, 0],
            sampler=[node("KSamplerSelect", sampler_name=a.sampler), 0], sigmas=[sig, 0], latent_image=[cond, 1])
img = node("VAEDecode", samples=[samp, 0], vae=[vv, 0])
aud = node("VAEDecodeAudio", samples=[samp, 0], vae=[va, 0])
trim = node("MiniMaxH3MotionContextTrim", images=[img, 0], trim_frames=[mc, 1], audio=[aud, 0], fps=24.0, match_tail=True)
vid = node("CreateVideo", images=[trim, 0], fps=24.0, audio=[trim, 1])
node("SaveVideo", video=[vid, 0], filename_prefix=a.prefix, format="auto", **{"format.codec": "auto"})
if a.save_latent:
    node("MiniMaxH3MotionContextSaveLatent", latent=[samp, 0], filename_prefix=a.save_latent, clip_index=1)

base = f"http://127.0.0.1:{a.port}"
def call(path, data=None):
    req = urllib.request.Request(base + path, data=json.dumps(data).encode() if data else None, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))
try:
    pid = director_submit(call, P, a.receipt, a.port)
except urllib.error.HTTPError as e:
    print(e.read().decode()[:3000]); raise SystemExit(1)
t0 = time.time(); print(f"queued {pid} {a.w}x{a.h} {length}f {a.steps}steps", flush=True)
while True:
    time.sleep(3)
    h = call(f"/history/{pid}")
    if pid in h:
        st = h[pid]["status"]
        if st.get("status_str") != "success":
            print(json.dumps(st)[:3000]); raise SystemExit(1)
        files = [f for o in h[pid]["outputs"].values() for k in o.values() if isinstance(k, list) for f in k if isinstance(f, dict) and "filename" in f]
        paths = [os.path.join(f.get('subfolder',''), f['filename']) for f in files]
        director_completed(a.receipt, paths)
        print(f"DONE {time.time()-t0:.1f}s", paths); break
