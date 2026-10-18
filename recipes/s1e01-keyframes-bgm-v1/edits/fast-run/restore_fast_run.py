from pathlib import Path
import copy,json,shutil,wave
import numpy as np
from workbench.store import Store,atomic_json
from workbench.providers import run,probe
from workbench.catalog import digest
from workbench.domain import validate_board
s=Store('/data/app/huanghaibin/soda');pid='p_5e6ea50dd70a4026';folder=s.root/'batches/s1e01-review-v3';folder.mkdir(exist_ok=True)
receipt=folder/'revision.json'
if receipt.exists():
 print(receipt.read_text());raise SystemExit
p=s.project(pid);assert p['revision']==38 and p['board_version']=='v_fd55ce4c0e854ec6','Project changed; preserve parallel changes'
source=copy.deepcopy(p);atomic_json(folder/'source-project-v2.json',source)
a=s.asset('a_5e2f2806475f4a3e',pid);b=s.asset('a_402a53e21ece40f4',pid)
for take in [a,b]:assert digest(take['path'])==take['sha256']
# Remove S03's silent frames 72..119; keep the approved original S04 run at 1x speed.
frames=192;out=folder/'S03-restored-fast-run.mp4';wav=folder/'S03-original-audio.wav'
parts=[]
for take,n in [(a,72),(b,120)]:
 with wave.open(take['audio']['wave'],'rb') as f:
  assert f.getframerate()==32000 and f.getnchannels()==2 and f.getsampwidth()==2
  raw=f.readframes(f.getnframes());parts.append(raw[:round(n/24*32000)*4])
with wave.open(str(wav),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(32000);f.writeframes(b''.join(parts))
# No speech is cut. Removed region must be actual digital silence.
with wave.open(a['audio']['wave'],'rb') as f:raw=f.readframes(f.getnframes())
assert not np.frombuffer(raw[3*32000*4:],dtype='<i2').any()
if not out.exists():run(['ffmpeg','-v','error','-n','-i',a['path'],'-i',b['path'],'-i',wav,'-filter_complex','[0:v]trim=end_frame=72,setpts=PTS-STARTPTS[v0];[1:v]trim=end_frame=120,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2:v=1:a=0,fps=24[v]','-map','[v]','-map','2:a:0','-c:v','libx264','-threads','3','-preset','fast','-crf','16','-pix_fmt','yuv420p','-r','24','-fps_mode','cfr','-c:a','aac','-b:a','128k','-movflags','+faststart',out])
v=next(x for x in probe(out)['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==192 and v['avg_frame_rate']=='24/1'
turns=copy.deepcopy(a['audio']['turns'])
for t in copy.deepcopy(b['audio']['turns']):t['start']+=3;t['end']+=3;turns.append(t)
board=copy.deepcopy(p['board'])
for shot in board['shots']:
 if shot['id']=='S03':shot.update(seconds=8,beat='保留V1原速快跑，去掉起跑前2秒等待',action='复用V1雪地介绍前72帧及原快跑完整120帧。第一句结束后立刻蓄力起跑，保留原版腾空奔跑、快速移位与自然收住；不慢放、不重生成。',prompt_en=b['prompt_en'],dialogue_gap_seconds=round(3.4-2.95421875,6))
board['summary']='S1E01审片V3：仅恢复V1原速快跑并剪掉其前2秒静音等待；沿用V2特写开场、字幕安全边距及哥哥比例，其他6段表演原样保留。'
board['notes']=['雪地素材：V1 S03帧0..71 + V1 S04帧0..119，原速剪辑；删除S03末尾48帧静音等待。','原快跑含腾空、位移、制动完整保留，未新增生成、变速、补帧或淡融。','其余6段V2表演、全部8句原声及V2字幕格式保留。','本版为待审候选，保留V1和V2。']
board=validate_board(board,p['setting'],p['packaging'])
p=s.update(pid,p['revision'],{'board':board});p=s.accept(pid,p['revision'],'board')
reused={}
for shot in board['shots']:
 old=s.asset(source['adopted_takes'][shot['id']],pid)
 metadata={k:copy.deepcopy(val) for k,val in old.items() if k not in ['id','project_id','created','url','sha256','path','kind']}
 metadata.update(name=shot['id']+' · V3',board_version=p['board_version'],review='candidate')
 if shot['id']=='S03':
  path=out;metadata.update(keep_frames=192,audio={'keep_frames':192,'seconds':8,'wave':str(wav),'turns':turns},context_dependency=None,tail_frames=b['tail_frames'],source_asset_ids=[a['id'],b['id']],edit={'source_ranges':[{'id':a['id'],'start_frame':0,'end_frame_exclusive':72},{'id':b['id'],'start_frame':0,'end_frame_exclusive':120}],'speed':1,'removed_silent_frames':48},reuse_reason='用户要求恢复V1快跑，仅剪掉等待',prompt_en=b['prompt_en'])
 else:
  path=folder/(shot['id']+'-unchanged.mp4');shutil.copy2(old['path'],path);metadata.update(source_asset_id=old['id'],reuse_reason='V2表演逐字节保留')
 asset=s.add_asset(pid,'take',path,metadata)
 if shot['id']!='S03':assert asset['sha256']==old['sha256']
 p=s.adopt(pid,p['revision'],asset['id']);reused[shot['id']]=asset['id']
j=s.enqueue(pid,p['revision'],'assemble','s1e01-review-v3-restore-original-fast-run')
r={'project_id':pid,'source_revision':38,'board_version':p['board_version'],'adopted_takes':reused,'assembly_job_id':j['id'],'snow_frames':192,'original_run_speed':1,'removed_wait_seconds':2,'human_acceptance':'pending'}
atomic_json(receipt,r);print(json.dumps(r,ensure_ascii=False))
