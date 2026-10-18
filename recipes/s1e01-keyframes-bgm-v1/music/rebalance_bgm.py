"""Final loudness QA revision: reduce only music by another 7 dB."""
from pathlib import Path
import copy,json,subprocess,wave
import numpy as np
from workbench.store import Store,atomic_json
from workbench.providers import run,tool,probe
from workbench.catalog import digest
s=Store('/data/app/huanghaibin/soda');f=s.root/'batches/s1e01-soft-bgm';src=json.loads((f/'delivery.json').read_text());folder=s.root/'jobs'/src['job_id'];old=s.asset(src['asset_id']);voice=folder/'final-audio.wav';music=f/'bgm-soft-v2.wav';mix=folder/'final-audio-with-bgm-v2.wav';duck=folder/'bgm-ducked-v2.wav';out=folder/'hi-soda-s1e01-soft-bgm-v2.mp4'
if not music.exists():run(['ffmpeg','-v','error','-n','-i',f/'bgm-soft.wav','-af','volume=-7dB','-c:a','pcm_s16le',music])
if not mix.exists():run(['ffmpeg','-v','error','-n','-i',voice,'-i',music,'-filter_complex','[1:a][0:a]sidechaincompress=threshold=0.04:ratio=2:attack=50:release=700:knee=4:makeup=1:detection=rms[m];[m]asplit=2[bed][bedcopy];[0:a][bed]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[out]','-map','[out]','-ar','32000','-ac','2','-c:a','pcm_s16le',mix,'-map','[bedcopy]','-ar','32000','-ac','2','-c:a','pcm_s16le',duck])
def read(path):
 with wave.open(str(path),'rb') as w:return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(float)/32768
v,b,m=read(voice),read(duck),read(mix);n=min(len(v),len(b));v=v[:n];b=b[:n];mask=np.mean(v*v,axis=1)>.0001;mask[:64000]=False
qa={'music_under_active_voice_db_relative':round(float(10*np.log10(np.mean(b[mask]**2)/np.mean(v[mask]**2))),2),'mixed_peak_dbfs':round(float(20*np.log10(np.max(np.abs(m)))),2),'source_voice_gain':1,'clipped_samples':int(np.sum(np.abs(m)>=32767/32768)),'additional_music_gain_db':-7}
assert qa['music_under_active_voice_db_relative'] < -14 and qa['clipped_samples']==0
if not out.exists():run(['ffmpeg','-v','error','-n','-i',old['path'],'-i',mix,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-video_track_timescale','12288','-movflags','+faststart',out])
def vh(path):return subprocess.check_output([tool('ffmpeg'),'-v','error','-i',str(path),'-map','0:v:0','-c:v','copy','-f','hash','-hash','sha256','-']).decode().strip()
assert vh(out)==vh(old['path']);p=s.project(old['project_id']);assert p['adopted_takes']==src['source_takes']
vstream=next(x for x in probe(out)['streams'] if x['codec_type']=='video');assert vstream['nb_frames']=='1112' and vstream['avg_frame_rate']=='24/1'
manifest=copy.deepcopy(old['manifest']);manifest['bgm'].update(soft_sha256=digest(music),soft_path=str(music),base_loudness_lufs_approx=-39,qa=qa);manifest['source_candidate']=old['id']
meta={k:copy.deepcopy(val) for k,val in old.items() if k not in ['id','project_id','kind','path','created','sha256','url']};meta.update(manifest=manifest,source_asset_id=old['id'],name='S1E01 · 自我介绍 · 轻声BGM定稿候选')
a=s.add_asset(p['id'],'final',out,meta);report={**src,'asset_id':a['id'],'url':'https://soda.buplayground.cn/'+a['url'],'path':str(out),'sha256':a['sha256'],'mix_qa':qa,'previous_candidate':old['id']}
atomic_json(f/'delivery-v2.json',report);atomic_json(folder/'bgm-qa-v2.json',qa);atomic_json(folder/'final-manifest-with-bgm-v2.json',manifest);s.progress(src['job_id'],'轻声BGM版完成，配乐已按人声下调，待审片',status='succeeded',result_assets=[old['id'],a['id']]);print(json.dumps(report,ensure_ascii=False))
