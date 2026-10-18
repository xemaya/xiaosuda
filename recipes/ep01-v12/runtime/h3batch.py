#!/usr/bin/env python3
"""批量出片:解析提示词文件 -> 分到空闲 GPU 并行跑 h3run.py。

用法(一般由本地 gen.sh 调用):
  h3batch.py --file prompts.txt --batch NAME [--gpus auto|0,1,2] [--img-prefix P] [--dry-run]

提示词文件格式见 games/4090/prompts.example.txt。
"""
import argparse, json, os, queue, random, re, subprocess, sys, threading, time

HOME = "/home/huanghaibin"
DATA = "/data/app/huanghaibin"
TURBO_FL2V = "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"
TURBO_REF = "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors"

# 预设:base x mode。nsfw LoRA 可用 @lora 覆盖、@nsfw off 关掉
PRESETS = {
    ("fp8", "fl2va"): dict(unet="minimax_h3_fl2va_pruned_fp8_scaled.safetensors", turbo=TURBO_FL2V,
                           nsfw=["SexGod_NaughtyTimes_v3_rank64_pruned_NOADALN.safetensors"],
                           steps=8, sampler="res_multistep", scheduler="simple"),
    ("gguf", "fl2va"): dict(unet="minimax_h3_fl2va-Q8_0.gguf", turbo=TURBO_FL2V,
                            nsfw=["SexGod_NaughtyTimes_v3_rank64_unpruned.safetensors"],
                            steps=8, sampler="res_multistep", scheduler="simple"),
    ("fp8", "ref"): dict(unet="minimax_h3_ref2va_pruned_fp8_scaled.safetensors", turbo=TURBO_REF,
                         nsfw=["AfterMidnight_ref2va_h3_sexytime_rank64-v1.2.safetensors"],
                         steps=4, sampler="euler", scheduler="beta"),  # AfterMidnight 必须 euler+beta
}
DEFAULTS = {"size": "768x1344", "sec": "5", "base": "fp8", "nsfw": "on", "nsfw_strength": "1", "n": "1", "seed": "random"}


def parse(path):
    """--- 分块;@key value 是参数;第一个只有参数没正文的块 = 全局默认。"""
    blocks, cur = [], []
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.strip() == "---":
            blocks.append(cur); cur = []
        else:
            cur.append(line)
    blocks.append(cur)
    glob, jobs = dict(DEFAULTS), []
    for b in blocks:
        opts, multi, text = {}, {"ref": [], "lora": [], "refvideo": []}, []
        for line in b:
            s = line.strip()
            if s.startswith("#") or s.startswith("```"):  # 注释;写手输出常带的 markdown 代码块标记
                continue
            m = re.match(r"^@(\w+)\s*(.*)$", s)
            if m:
                k, v = m.group(1).lower(), m.group(2).strip()
                (multi[k].append(v) if k in multi else opts.__setitem__(k, v))
            else:
                text.append(line)
        prompt = "\n".join(text).strip()
        if not prompt:
            glob.update(opts)
            for k in multi:
                if multi[k]: glob[k] = multi[k]
            continue
        o = {**glob, **opts}
        for k in multi:
            o[k] = multi[k] or glob.get(k, [])
        o["prompt"] = prompt
        o["_file"] = path
        jobs.append(o)
    return jobs


def expand(job, idx, img_prefix):
    lb_text = job.get("lookbook")
    if job.get("lookbook_file"):
        lb_text = open(f"{DATA}/input/{img_prefix}{job['lookbook_file']}", encoding="utf-8").read().strip()
    lb_as = job.get("lookbook_as", "first").lower()
    if lb_text and lb_as == "ref":
        job = {**job, "ref": job.get("ref", []) + ["__LOOKBOOK__"]}
    mode = "ref" if (job.get("ref") or job.get("refvideo")) else "fl2va"
    p = PRESETS.get((job["base"], mode))
    if p is None:
        raise SystemExit(f"第 {idx} 条:不支持 base={job['base']} + {mode}(参考图模式只有 fp8)")
    w, h = map(int, job["size"].lower().split("x"))
    if w % 32 or h % 32:
        raise SystemExit(f"第 {idx} 条:尺寸 {w}x{h} 要是 32 的倍数(H3 latent 按 16x2 切块,848x1216 这种会 shape 报错)")
    loras = [f"{p['turbo']}:1"]
    if job["nsfw"].lower() != "off":
        names = job.get("lora") or p["nsfw"]
        for n in names:
            loras.append(n if ":" in n else f"{n}:{job['nsfw_strength']}")
    out = []
    for k in range(int(job["n"])):
        seed = random.randint(0, 2**31 - 1) if job["seed"] == "random" else int(job["seed"]) + k
        out.append(dict(idx=idx, prompt=job["prompt"], mode=mode, unet=job.get("unet", p["unet"]), loras=loras,
                        ref=[r if r == "__LOOKBOOK__" else img_prefix + r for r in job.get("ref", [])],
                        lookbook=lb_text, lookbook_as=lb_as,
                        lookbook_seed=int(job["lookbook_seed"]) if job.get("lookbook_seed") else None,
                        lookbook_steps=int(job.get("lookbook_steps", 40)),
                        first=(img_prefix + job["first"]) if job.get("first") else None,
                        last=(img_prefix + job["last"]) if job.get("last") else None,
                        refvideo=[img_prefix + r for r in job.get("refvideo", [])],
                        pose=(img_prefix + job["pose"]) if job.get("pose") else None,
                        pose_raw=job.get("pose_raw", "off").lower() in ("on", "1", "true", "yes"),
                        control_strength=float(job.get("control_strength", 1)),
                        pose_threshold=float(job.get("pose_threshold", 0.2)),
                        w=w, h=h, sec=float(job["sec"]), steps=int(job.get("steps", p["steps"])),
                        mute=job.get("mute", "off"),
                        sampler=job.get("sampler", p["sampler"]), scheduler=job.get("scheduler", p["scheduler"]),
                        seed=seed))
    return out


def port_up(port):
    r = subprocess.run(["ss", "-ltn", f"sport = :{port}"], capture_output=True, text=True)
    return f":{port}" in r.stdout


def pick_gpus(spec):
    q = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True).stdout.split("\n")
    used = {int(a): int(b) for a, b in (l.split(",") for l in q if l.strip())}
    # auto 时避开留给别的服务的卡(默认 GPU3 = Qwen-Image 实例,GPU5 = 提示词写手),可用环境变量 H3_AVOID_GPUS 改
    avoid = {int(x) for x in os.environ.get("H3_AVOID_GPUS", "3,5").split(",") if x.strip()}
    cand = [g for g in sorted(used) if g not in avoid] if spec == "auto" else [int(x) for x in spec.split(",")]
    # 我们自己的实例占着显存也算可用;别人占着(>1.5G 且不是我们的端口)就跳过
    return [g for g in cand if port_up(8188 + g) or used.get(g, 0) < 1500]


def queue_len(port):
    """实例队列里正在跑+排队的任务数;连不上返回 None"""
    try:
        import urllib.request
        q = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/queue", timeout=5))
        return len(q.get("queue_running", [])) + len(q.get("queue_pending", []))
    except Exception:
        return None


def ensure_instance(g):
    port = 8188 + g
    if not port_up(port):
        subprocess.run([f"{HOME}/bin/comfy.sh", str(g)], check=True)
    for _ in range(120):
        try:
            import urllib.request
            urllib.request.urlopen(f"http://127.0.0.1:{port}/object_info/CLIPLoaderGGUFMiniMaxH3", timeout=5)
            return True
        except Exception:
            time.sleep(3)
    return False


LB_LOCK, LB_DONE, LB_JOB_LOCKS = threading.Lock(), {}, {}


def make_lookbook(t, port, batch, outdir):
    """Qwen-Image-2.1 出定妆照(目标尺寸 1.5 倍,16 对齐)-> 精确缩到视频尺寸放进 input。返回 input 里的文件名。"""
    with LB_LOCK:
        jl = LB_JOB_LOCKS.setdefault(t["idx"], threading.Lock())
    with jl:
        if t["idx"] in LB_DONE:
            return LB_DONE[t["idx"]]
        qw, qh = (round(t["w"] * 1.5 / 16) * 16, round(t["h"] * 1.5 / 16) * 16)
        seed = t["lookbook_seed"] if t["lookbook_seed"] is not None else random.randint(0, 2**31 - 1)
        pf = f"{outdir}/.lb{t['idx']}.txt"
        open(pf, "w", encoding="utf-8").write(t["lookbook"])
        cmd = [sys.executable, f"{HOME}/bin/qi21run.py", "--port", str(port), "--prompt-file", pf, "--w", str(qw), "--h", str(qh),
               "--steps", str(t["lookbook_steps"]), "--seed", str(seed), "--prefix", f"batches/{batch}/lookbook_{t['idx']:02d}_s{seed}"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        m = re.search(r"'([^']+\.png)'", r.stdout)
        if not m:
            raise RuntimeError("定妆照失败: " + (r.stdout + r.stderr)[-800:])
        src = m.group(1) if m.group(1).startswith("/") else f"{DATA}/output/{m.group(1)}"
        name = f"{batch}__lookbook_{t['idx']:02d}.png"
        from PIL import Image
        Image.open(src).convert("RGB").resize((t["w"], t["h"]), Image.LANCZOS).save(f"{DATA}/input/{name}")
        print(f"定妆照 [{t['idx']:02d}] {qw}x{qh} seed={seed} -> {os.path.basename(src)}", flush=True)
        LB_DONE[t["idx"]] = name
        return name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True); ap.add_argument("--batch", required=True)
    ap.add_argument("--gpus", default="auto"); ap.add_argument("--img-prefix", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    tasks = [t for i, j in enumerate(parse(a.file), 1) for t in expand(j, i, a.img_prefix)]
    outdir = f"{DATA}/output/batches/{a.batch}"
    os.makedirs(outdir, exist_ok=True)
    for t in tasks:
        print(f"[{t['idx']:02d}] {t['mode']} {t['w']}x{t['h']} {t['sec']}s {t['steps']}步 seed={t['seed']} "
              f"lora={[l.split(':')[0][:28] for l in t['loras']]} ref={t['ref']} refvideo={t['refvideo']} pose={t['pose']} lookbook={'yes(' + t['lookbook_as'] + ')' if t['lookbook'] else 'no'} | {t['prompt'][:60]!r}", flush=True)
    if a.dry_run:
        return
    gpus = pick_gpus(a.gpus)
    # 排序:空闲的已开实例(模型在内存,免冷启) > 空卡新开实例 > 正忙的实例(只能排队)
    def rank(g):
        if not port_up(8188 + g): return 1
        return 0 if not queue_len(8188 + g) else 2
    gpus = sorted(gpus, key=rank)[:len(tasks)]
    if not gpus:
        raise SystemExit("没有空闲 GPU")
    print(f"共 {len(tasks)} 条,用 GPU {gpus}", flush=True)

    q = queue.Queue()
    for t in tasks: q.put(t)
    lock, results, t0 = threading.Lock(), [], time.time()

    def worker(g):
        if not ensure_instance(g):
            print(f"GPU{g} 实例起不来,跳过", flush=True); return
        while True:
            try: t = q.get_nowait()
            except queue.Empty: return
            if t["lookbook"]:
                try:
                    lb = make_lookbook(t, 8188 + g, a.batch, outdir)
                except Exception as e:
                    with lock:
                        results.append({**t, "gpu": g, "ok": False, "sec_used": 0, "files": [], "error": str(e)})
                    print(f"FAIL [{t['idx']:02d}] GPU{g} {e}", flush=True); continue
                t = {**t, "ref": [lb if r == "__LOOKBOOK__" else r for r in t["ref"]]}
                if t["lookbook_as"] != "ref":
                    t["first"] = lb
            pf = f"{outdir}/.p{t['idx']}_{t['seed']}.txt"
            open(pf, "w", encoding="utf-8").write(t["prompt"])
            cmd = [sys.executable, f"{HOME}/bin/h3run.py", "--port", str(8188 + g), "--prompt-file", pf,
                   "--unet", t["unet"], "--w", str(t["w"]), "--h", str(t["h"]), "--sec", str(t["sec"]),
                   "--steps", str(t["steps"]), "--sampler", t["sampler"], "--scheduler", t["scheduler"],
                   "--seed", str(t["seed"]), "--prefix", f"batches/{a.batch}/{t['idx']:02d}_s{t['seed']}"]
            for l in t["loras"]: cmd += ["--lora", l]
            for r in t["ref"]: cmd += ["--ref", r]
            if t["first"]: cmd += ["--first", t["first"]]
            if t["last"]: cmd += ["--last", t["last"]]
            for r in t["refvideo"]: cmd += ["--refvideo", r]
            if t["pose"]:
                cmd += ["--pose", t["pose"], "--control-strength", str(t["control_strength"]),
                        "--pose-threshold", str(t["pose_threshold"]), "--save-control"]
                if t["pose_raw"]: cmd.append("--pose-raw")
            s = time.time()
            r = subprocess.run(cmd, capture_output=True, text=True)
            if "DONE" not in r.stdout and re.search(r"Connection (reset|refused)|RemoteDisconnected", r.stdout + r.stderr):
                # 实例中途被重启/挂了:拉起来重试一次
                print(f"GPU{g} 实例中断,重新拉起后重试 [{t['idx']:02d}]", flush=True)
                if ensure_instance(g):
                    r = subprocess.run(cmd, capture_output=True, text=True)
            dt = time.time() - s
            ok = "DONE" in r.stdout
            files = re.findall(r"'([^']+\.mp4)'", r.stdout)
            with lock:
                results.append({**t, "gpu": g, "ok": ok, "sec_used": round(dt, 1), "files": files,
                                "error": None if ok else (r.stdout + r.stderr)[-1500:]})
                n = len(results)
            print(f"{'OK  ' if ok else 'FAIL'} [{t['idx']:02d}] GPU{g} {dt:.0f}s ({n}/{len(tasks)}) "
                  f"{files[0] if files else (r.stdout + r.stderr).strip()[-300:]}", flush=True)

    ths = [threading.Thread(target=worker, args=(g,)) for g in gpus]
    for th in ths: th.start()
    for th in ths: th.join()
    with open(f"{outdir}/manifest.jsonl", "w", encoding="utf-8") as f:
        for r in sorted(results, key=lambda x: (x["idx"], x["seed"])):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    ok = sum(r["ok"] for r in results)
    print(f"BATCH_DONE {ok}/{len(tasks)} 成功,总耗时 {time.time()-t0:.0f}s -> {outdir}", flush=True)


if __name__ == "__main__":
    main()
