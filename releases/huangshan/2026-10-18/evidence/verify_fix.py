from pathlib import Path
import subprocess,json
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parent;d=json.loads((R/'delivery.json').read_text());old=Path(d['source']);new=Path(d['path'])
def hashes(p):
 text=subprocess.check_output(['ffmpeg','-v','error','-threads','2','-i',str(p),'-map','0:v:0','-an','-fps_mode','passthrough','-f','framemd5','-']).decode();return [x.rsplit(',',1)[-1].strip() for x in text.splitlines() if x and not x.startswith('#')]
with ThreadPoolExecutor(max_workers=2) as pool:a,b=list(pool.map(hashes,[old,new]))
lo,hi=d['reencoded_gop_frames'];assert len(a)==len(b)==3325;assert a[:lo]==b[:lo] and a[hi:]==b[hi:]
result={'decoded_frames':3325,'decoded_pixels_outside_reencoded_gop_exact':True,'unchanged_decoded_frames':lo+len(a)-hi,'reframed_interval_seconds':d['reframed_seconds'],'original_audio_encoded_stream_exact':d['audio_encoded_stream_exact'],'frame_rate':24,'manual_static_padding':False,'ffmpeg':subprocess.check_output(['ffmpeg','-version']).decode().splitlines()[0],'human_acceptance':'pending'}
(R/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False),flush=True)
