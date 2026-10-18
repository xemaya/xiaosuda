"""Assemble approved retakes; mix a quiet original music bed. No GPU calls."""
import copy,json,sys,threading,subprocess,wave
from pathlib import Path
import numpy as np
from workbench.store import Store,atomic_json,now
from workbench.catalog import digest
from workbench.providers import run,probe,tool
from workbench import finishing
sys.path.insert(0,str(Path(__file__).resolve().parent));import captions_v4
s=Store('/data/app/huanghaibin/soda');pid='p_5e6ea50dd70a4026';f=s.root/'batches/s1e01-soft-bgm';receipt=f/'assembly.json'
assert (f/'bgm-soft.wav').is_file()
if receipt.exists():
 r=json.loads(receipt.read_text());job=s.job(r['job_id'])
 if job['status']=='succeeded':print((f/'delivery.json').read_text());raise SystemExit
 raise SystemExit('Original job exists; inspect and resume its saved artifacts, never enqueue twice: '+job['id'])
p=s.project(pid);assert p['revision']==84,'Project changed: inspect current state before adopting accepted retakes'
atomic_json(f/'source-project.json',p)
# The user approved these native retakes with “很好”, then requested only BGM.
p=s.adopt(pid,p['revision'],'a_a80c4ec48a024ecd')
p=s.accept(pid,p['revision'],'board')
for aid in ['a_96a0d7c86d014c4a','a_11d7ab46b4c84a1f']:p=s.adopt(pid,p['revision'],aid)
job=s.enqueue(pid,p['revision'],'assemble','s1e01-soft-bgm-20261017',{'operator_profile':str(f/'captions_v4.py'),'bgm':str(f/'bgm-soft.wav'),'approved_native_retakes':['a_96a0d7c86d014c4a','a_11d7ab46b4c84a1f']})
atomic_json(receipt,{'job_id':job['id'],'project_revision':p['revision'],'phase':'enqueued'})
with s.tx() as c:
 row=c.execute('select status,doc,payload from jobs where id=?',(job['id'],)).fetchone();assert row['status']=='queued','Worker already claimed; retain existing job, do not double-run'
 doc=json.loads(row['doc']);doc.update(status='running',progress='合成已认可重拍镜头，加入轻声背景音乐',updated=now());c.execute('update jobs set status=?,doc=?,updated=? where id=?',('running',json.dumps(doc,ensure_ascii=False),now(),job['id']));job={**doc,'payload':json.loads(row['payload'])}
folder=s.root/'jobs'/job['id']
try:
 captions_v4.install();base=finishing.assemble(s,job,threading.Event())
 assert base['frames']==1112
 original_mix=folder/'final-audio.wav';assert digest(original_mix)==digest(s.root/'jobs/j_7cec99780cc14ccb/final-audio.wav'),'Original spoken/sfx mix changed'
 assert digest(folder/'captions.ass')==digest(s.root/'jobs/j_7cec99780cc14ccb/captions.ass'),'Caption style/text/timing changed'
 s.progress(job['id'],'画面已合成，轻声混音并核对音量')
 mix=folder/'final-audio-with-bgm.wav';duck=folder/'bgm-ducked.wav'
 filters='[1:a][0:a]sidechaincompress=threshold=0.04:ratio=2:attack=50:release=700:knee=4:makeup=1:detection=rms[m];[m]asplit=2[bed][bedcopy];[0:a][bed]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[out]'
 run(['ffmpeg','-v','error','-n','-i',original_mix,'-i',f/'bgm-soft.wav','-filter_complex',filters,'-map','[out]','-ar','32000','-ac','2','-c:a','pcm_s16le',mix,'-map','[bedcopy]','-ar','32000','-ac','2','-c:a','pcm_s16le',duck])
 with wave.open(str(mix),'rb') as w:data=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2');assert w.getframerate()==32000 and w.getnchannels()==2
 assert int(np.max(np.abs(data.astype(np.int32))))<32767,'Clipped mix; stop and reduce music, do not alter source voices'
 out=folder/'hi-soda-s1e01-soft-bgm.mp4'
 run(['ffmpeg','-v','error','-n','-i',s.asset(base['id'])['path'],'-i',mix,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-video_track_timescale','12288','-movflags','+faststart',out])
 def video_hash(path):
  return subprocess.check_output([tool('ffmpeg'),'-v','error','-i',str(path),'-map','0:v:0','-c:v','copy','-f','hash','-hash','sha256','-']).decode().strip()
 assert video_hash(out)==video_hash(s.asset(base['id'])['path']),'Picture stream changed while adding music'
 meta=probe(out);v=next(x for x in meta['streams'] if x['codec_type']=='video');assert v['nb_frames']=='1112' and v['avg_frame_rate']=='24/1' and v['r_frame_rate']=='24/1'
 manifest=copy.deepcopy(base['manifest']);manifest.update(bgm={'title':'Soda Sunny Steps','source':'Original note arrangement, local Apple GM instrument rendering','score':str(f/'score.json'),'raw_sha256':digest(f/'bgm-raw.wav'),'soft_sha256':digest(f/'bgm-soft.wav'),'base_loudness_lufs_approx':-32,'voice_ducking':'ratio2,50ms attack,700ms release','fade_in_seconds':.8,'fade_out_seconds':2.733333,'voice_gain':1,'lyrics':False},caption_profile={'english':46,'chinese':42,'safe_width':620},original_voice_sfx_pcm_identical_before_music=True,picture_bitstream_unchanged_when_mixing=True,human_acceptance='pending')
 a=s.add_asset(pid,'final',out,{'name':'S1E01 · 自我介绍 · 轻声BGM版','job_id':job['id'],'board_version':p['board_version'],'setting_version':p['setting_version'],'frames':1112,'seconds':float(meta['format']['duration']),'manifest':manifest,'review':'candidate'})
 report={'asset_id':a['id'],'job_id':job['id'],'url':'https://soda.buplayground.cn/'+a['url'],'path':str(out),'sha256':a['sha256'],'frames':1112,'fps':24,'seconds':a['seconds'],'music_title':'Soda Sunny Steps','source_takes':p['adopted_takes'],'source_mix_unchanged':True,'captions_unchanged':True,'picture_bitstream_unchanged_when_mixing':True,'human_acceptance':'pending'}
 atomic_json(folder/'final-manifest-with-bgm.json',manifest);atomic_json(folder/'result.json',a);atomic_json(f/'delivery.json',report);s.progress(job['id'],'轻声BGM版完成，待审片',status='succeeded',result_assets=[a['id']]);atomic_json(receipt,{'job_id':job['id'],'phase':'completed','final_asset':a['id']});print(json.dumps(report,ensure_ascii=False),flush=True)
except Exception as e:
 s.progress(job['id'],'本地合成需核对，原素材和混音保留',status='needs_attention',error=str(e));raise
