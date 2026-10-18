import copy,json,uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from workbench.app import create_app
from workbench.store import Store
from workbench.domain import validate_setting,validate_board,Conflict
from workbench.catalog import STYLE_ID

def setting():return {'title':'饼干分享','logline':'小苏打问萌鸡能否分享饼干。','premise':'暖光客厅中，两个伙伴把请求和分享演成小日常。','style_id':STYLE_ID,'cast':[{'character_id':'xiaosuda','story_role':'请求饼干'},{'character_id':'mengji-gege','story_role':'分享饼干'}],'scenes':[{'id':'scene-1','name':'暖光客厅','setting':'窗边地毯，保持角色原有服装。','lighting':'暖光','props':['饼干'],'cast_ids':['xiaosuda','mengji-gege'],'reference_scene_id':'living-room'}],'beats':[{'summary':'小苏打提出请求，萌鸡同意。','scene_id':'scene-1'}],'dialogue':[{'id':'d1','speaker_id':'xiaosuda','text':'Can I have a cookie?','translation':'我可以吃一块饼干吗？','emotion':'好奇','speed':1},{'id':'d2','speaker_id':'mengji-gege','text':'Sure!','translation':'当然！','emotion':'温暖','speed':1}],'notes':[],'unresolved_characters':[]}
def board():return {'summary':'固定机位内完成两句问答与递饼干。','shots':[{'id':'S01','scene_id':'scene-1','character_ids':['xiaosuda','mengji-gege'],'seconds':8,'beat':'请求与分享','action':'小苏打抬头询问，萌鸡自然递出饼干，双方依次开口。','camera':'固定中景','dialogue_ids':['d1','d2'],'continuation':False,'transition':'cut','prompt_en':'Fixed camera, plush original characters. Dog asks, chick answers. Exact original dialogue.'}],'notes':[]}
def create(store):return store.import_scripts([{'title':'饼干分享','script':'小苏打：Can I have a cookie?\n萌鸡：Sure!'}],str(uuid.uuid4()))[0]['id']
def prepare(store,pid):
 p=store.project(pid);p=store.update(pid,p['revision'],{'setting':setting()});p=store.accept(pid,p['revision'],'setting');return p

@pytest.fixture
def client(tmp_path):
 app=create_app(tmp_path/'data',auth='off',run_worker=False)
 with TestClient(app,base_url='http://localhost') as client:yield client

def test_fixed_roster_is_server_enforced(client):
 c=client.get('/api/catalog').json();assert len(c['characters'])==7 and c['style']['locked']
 r=client.post('/api/projects/batch',json={'scripts':[{'title':'bad','script':'熊猫说话','cast_ids':['panda']}],'request_key':'unknown-cast-001'})
 assert r.status_code==400 and '人物库' in r.json()['detail']
 r=client.post('/api/projects/batch',json={'scripts':[{'title':'bad','script':'x','style_id':'anime'}],'request_key':'unknown-style-01'})
 assert r.status_code==422

def test_batch_is_idempotent_and_key_cannot_mutate(client):
 body={'scripts':[{'title':'一','script':'小苏打：Hi!'},{'title':'二','script':'萌鸡：Hello!'}],'request_key':'import-stable-001'}
 a=client.post('/api/projects/batch',json=body);b=client.post('/api/projects/batch',json=body)
 assert a.status_code==b.status_code==200 and a.json()==b.json() and len(client.get('/api/projects').json())==2
 body['scripts'][0]['script']='changed';assert client.post('/api/projects/batch',json=body).status_code==409

def test_revisions_preserve_accepted_history_and_invalidate_downstream(tmp_path):
 s=Store(tmp_path);pid=create(s);p=prepare(s,pid);vid=p['setting_version'];p=s.update(pid,p['revision'],{'script':'小苏打：新台词'})
 assert not p['setting_accepted'] and not p['board_accepted'] and not p['scene_masters']
 with s.connection() as c:assert c.execute('SELECT COUNT(*) FROM versions WHERE id=?',(vid,)).fetchone()[0]==1
 with pytest.raises(Conflict):s.update(pid,p['revision']-1,{'title':'cannot overwrite'})

def test_only_own_current_scene_can_be_adopted(tmp_path):
 s=Store(tmp_path);a=create(s);b=create(s);p=prepare(s,a);q=prepare(s,b);img=tmp_path/'image.png';img.write_bytes(b'not-a-real-image-for-provenance-test')
 item=s.add_asset(a,'scene',img,{'scene_id':'scene-1','setting_version':p['setting_version']})
 with pytest.raises(ValueError):s.adopt(b,q['revision'],item['id'])
 p=s.update(a,p['revision'],{'setting':setting()});p=s.accept(a,p['revision'],'setting')
 with pytest.raises(Conflict):s.adopt(a,p['revision'],item['id'])

def test_dialogue_coverage_and_speakers_are_validated():
 s=validate_setting(setting(),['xiaosuda','mengji-gege']);b=board();assert validate_board(b,s)['shots'][0]['dialogue_ids']==['d1','d2']
 b['shots'][0]['dialogue_ids']=['d1','d1']
 with pytest.raises(ValueError,match='恰好'):validate_board(b,s)
 b=board();b['shots'][0]['character_ids']=['xiaosuda']
 with pytest.raises(ValueError,match='说话者'):validate_board(b,s)
 b=board();b['shots'][0]['continuation']=True
 with pytest.raises(ValueError,match='连续镜头'):validate_board(b,s)
 s=setting();s['cast'][0]['character_id']='panda'
 with pytest.raises(ValueError):validate_setting(s,['xiaosuda','mengji-gege'])

def test_tasks_are_frozen_and_idempotent(tmp_path):
 s=Store(tmp_path);pid=create(s);p=s.project(pid);j=s.enqueue(pid,p['revision'],'setting','job-exact-key-001');same=s.enqueue(pid,p['revision'],'setting','job-exact-key-001');assert j['id']==same['id']
 with pytest.raises(Conflict):s.enqueue(pid,p['revision'],'setting','other-key-002')
 job=s.claim(['setting']);assert job['payload']['project']['script']==p['script'];s.update(pid,p['revision'],{'script':'changed while writer runs'})
 s.complete_text(job,validate_setting(setting(),p['cast_ids']));p=s.project(pid)
 assert p['setting'] is None and p['versions'] and p['jobs'][0]['status']=='succeeded'

def test_csrf_and_local_mode_are_enforced(client):
 assert client.post('/api/projects/batch',headers={'Origin':'https://untrusted.example'},json={'scripts':[{'title':'x','script':'x'}],'request_key':'csrf-test-001'}).status_code==403
 assert client.get('/api/health',headers={'Host':'public.example'}).status_code==403
 assert client.get('/api/catalog/media/../../../etc/passwd').status_code in [400,404]

def test_production_uses_frozen_picture_only_graph():
 from workbench.providers import load_continuity
 c=load_continuity();g,r=c.new_graph('canonical.png');one=c.append_take(g,r,carrier='a.mp4',prompt='Original first take',keep_frames=178,seed=1,prefix='test/a',first_anchor=True);two=c.append_take(g,r,carrier='b.mp4',prompt='Original next take',keep_frames=100,seed=2,prefix='test/b',context_images=one['visible_images'])
 contexts=[n['inputs'] for n in g.values() if n['class_type']=='MiniMaxH3MotionContext']
 assert contexts[1]['context_frames']==one['visible_images']
 assert all(not any(k in n for k in ['context_audio','context_latent','audio_vae']) for n in contexts)
 assert two['context_frames']==22

def test_recovery_queries_original_gpu_receipt_without_resubmission(tmp_path):
 import threading
 from workbench.providers import Production
 from workbench.store import atomic_json
 s=Store(tmp_path);pid=create(s);p=s.project(pid);j=s.enqueue(pid,p['revision'],'setting','recovery-test-001');job=s.claim(['setting']);graph={'1':{'class_type':'Example','inputs':{}}}
 from workbench.domain import fingerprint
 folder=s.root/'jobs'/job['id'];atomic_json(folder/'saved-receipt.json',{'phase':'submitted','port':8188,'prompt_id':'original-prompt-id','client_id':'original-client','graph_hash':fingerprint(graph)})
 prod=Production(s);calls=[]
 def fake(port,path,body=None,timeout=15):
  calls.append((path,body));return {'original-prompt-id':{'status':{'status_str':'success'},'outputs':{}}}
 prod.call=fake
 result=prod.run_graph(job,graph,'saved','Example',threading.Event())
 assert result['status']['status_str']=='success' and all(body is None for _,body in calls)
 assert calls[0][0]=='/history/original-prompt-id'
 s.progress(j['id'],'服务暂停，原GPU任务回执已保留',status='needs_attention');s.recover();assert s.job(j['id'])['status']=='queued'

def test_saved_tts_audio_recovers_without_second_api_call(tmp_path,monkeypatch):
 import subprocess,wave
 from workbench.providers import Production,tool
 from workbench.store import atomic_json
 from workbench.domain import fingerprint
 s=Store(tmp_path);pid=create(s);p=s.project(pid);j=s.enqueue(pid,p['revision'],'setting','tts-recovery-001');job=s.claim(['setting']);folder=s.root/'jobs'/job['id']/'S01';folder.mkdir()
 line=setting()['dialogue'][0]
 raw=folder/(line['id']+'.mp3')
 subprocess.run([tool('ffmpeg'),'-v','error','-f','lavfi','-i','sine=frequency=300:duration=0.2','-c:a','libmp3lame',str(raw)],check=True)
 h=fingerprint({'line':line,'voice':'Cute_Elf','pitch':0,'model':'speech-02-hd'})
 atomic_json(folder/(line['id']+'-tts.json'),{'phase':'audio_received','hash':h})
 monkeypatch.setattr('urllib.request.urlopen',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Must not call voice API again')))
 path=Production(s).speech(job,line,folder)
 with wave.open(str(path),'rb') as f:assert f.getframerate()==32000 and f.getnchannels()==2
 assert json.loads((folder/(line['id']+'-tts.json')).read_text())['recovered_from_saved_audio']

def test_series_roster_names_mimi_and_legacy_aliases(client):
 c=client.get('/api/catalog').json();chars={x['id']:x for x in c['characters']}
 assert c['series']['max_seconds']==300 and c['series']['format']=='少儿英语情景剧'
 assert [chars[x]['english_name'] for x in ['xiaosuda','mengji-gege','mianyang-jiejie','niu-baba','long-mama','xiaomi-mimi']]==['Soda','Jacky','Angela','Dad','Mom','Mimi']
 assert 'Chick' in chars['mengji-gege']['aliases'] and 'Baking Soda' in chars['xiaosuda']['aliases']
 assert chars['xiaomi-mimi']['available'] and not chars['xiaomi-mimi']['voice_ready'] and chars['xiaomi-mimi']['pronouns']=='she/her'
 assert '技术样片' in c['reference_episode']['title']
 r=client.post('/api/projects/batch',json={'scripts':[{'title':'全员候选','script':'Soda: Hi!'}],'request_key':'all-seven-cast-001'})
 assert r.status_code==200 and len(client.get('/api/projects/'+r.json()[0]['id']).json()['cast_ids'])==7
 assert client.get('/api/catalog/media/series-bible').status_code==200


def long_board(seconds):
 b=board();b['shots']=[]
 for i,n in enumerate(seconds):
  shot=board()['shots'][0];shot.update(id=f'S{i+1:03}',seconds=n,dialogue_ids=['d1','d2'] if i==0 else [])
  b['shots'].append(shot)
 return b


def test_five_minute_budget_includes_op_intertitles_and_frame_rounding():
 s=setting()
 b=long_board([10]*29+[8]);assert len(validate_board(b,s)['shots'])==30
 b['shots'][1]['transition']='practice_time'
 with pytest.raises(ValueError,match='5分钟'):validate_board(b,s)
 b=long_board([10]*29+[10]);assert validate_board(b,s,{'op':False})
 with pytest.raises(ValueError,match='5分钟'):validate_board(b,s,{'op':True})
 b=long_board([2]*149);assert len(validate_board(b,s)['shots'])==149
 b['shots'][-1]['seconds']=2.001
 with pytest.raises(ValueError,match='5分钟'):validate_board(b,s)


def test_mimi_voice_blocks_before_any_paid_or_gpu_request(tmp_path,monkeypatch):
 import threading
 from workbench.providers import Production
 s=Store(tmp_path);prod=Production(s)
 monkeypatch.setattr('workbench.providers.require_tools',lambda:{})
 monkeypatch.setattr(prod,'speech',lambda *a:pytest.fail('Must not submit voice before Mimi audition'))
 monkeypatch.setattr(prod,'run_graph',lambda *a:pytest.fail('Must not submit GPU before Mimi audition'))
 p={'setting':{'dialogue':[{'id':'d1','speaker_id':'xiaomi-mimi','text':'Hi!'}]},'board':{'shots':[{'id':'S01','dialogue_ids':['d1']}]}}
 job={'id':'voice-block-test','payload':{'project':p,'extra':{}}}
 with pytest.raises(ValueError,match='小咪'):prod.shoot(job,threading.Event())


def test_camera_framing_idle_actions_and_scene_identity():
 s=setting();s['scenes'][0].update(framing='wide',idle_actions={'mengji-gege':'在旁边搭积木，被叫到时抬头回应'})
 checked=validate_setting(s,['xiaosuda','mengji-gege']);b=board();b['shots'][0]['framing']='wide'
 assert validate_board(b,checked)['shots'][0]['framing']=='wide'
 b['shots'][0]['framing']='close_up'
 with pytest.raises(ValueError,match='新机位主图'):validate_board(b,checked)
 s['scenes'][0]['idle_actions']['xiaomi-mimi']='看书'
 with pytest.raises(ValueError,match='当前场景'):validate_setting(s,['xiaosuda','mengji-gege'])


def test_pull_down_is_postproduction_not_native_continuation():
 from workbench.domain import episode_frames
 s=setting();b=long_board([5,5]);b['shots'][1]['transition']='pull_down'
 checked=validate_board(b,s)
 assert episode_frames(checked['shots'])==240+48-8
 b['shots'][1]['continuation']=True
 with pytest.raises(ValueError,match='连续表演'):validate_board(b,s)
 b['shots'][0]['transition']='pull_down'
 with pytest.raises(ValueError,match='首镜前'):validate_board(b,s)


def test_pull_down_blocks_voice_overlap():
 from workbench.finishing import pull_down_audio
 from workbench.domain import NeedsAttention
 take={'keep_frames':48,'audio':{'turns':[{'start':.4,'end':1.6}]}}
 out=pull_down_audio(b'\0'*(64000*4),b'\0'*(64000*4),take,take)
 assert len(out)==(128000-round(32000/3))*4
 unsafe=copy.deepcopy(take);unsafe['audio']['turns'][0]['end']=1.9
 with pytest.raises(NeedsAttention,match='覆盖原对白'):pull_down_audio(b'\0'*(64000*4),b'\0'*(64000*4),unsafe,take)


def test_pull_down_real_media_frames_captions_and_original_voice(tmp_path):
 import wave,threading,subprocess,hashlib
 import numpy as np
 from workbench.finishing import assemble
 from workbench.providers import tool,probe
 root=tmp_path/'data';folder=root/'jobs'/'media-test';folder.mkdir(parents=True)
 assets={}
 for i,color in enumerate(['red','blue'],1):
  video=tmp_path/f'{i}.mp4'
  # Real moving inputs: a white stripe advances each frame over a colored stage.
  channel="if(lt(abs(X-N*3),8),255,0)"
  geq=f"geq=r='255':g='{channel}':b='{channel}'" if i==1 else f"geq=r='{channel}':g='{channel}':b='255'"
  subprocess.run([tool('ffmpeg'),'-v','error','-f','lavfi','-i',f'color={color}:s=160x288:r=24:d=2','-vf',geq,'-frames:v','48','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
  audio=tmp_path/f'{i}.wav';samples=np.zeros((64000,2),dtype='<i2');samples[12800:51200]=i*1000
  with wave.open(str(audio),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(32000);f.writeframes(samples.tobytes())
  assets[f'a{i}']={'id':f'a{i}','path':str(video),'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'board_version':'b1','master_id':f'm{i}','shot_id':f'S0{i}','keep_frames':48,'audio':{'wave':str(audio),'turns':[{'text':f'Line {i}','translation':f'第{i}句','start':.4,'end':1.6}]}}
 class MediaStore:
  def __init__(self):self.root=root
  def asset(self,aid,pid):return assets[aid]
  def add_asset(self,pid,kind,path,metadata):return {'path':str(path),**metadata}
 shots=[{'id':'S01','scene_id':'scene1','continuation':False,'transition':'cut'},{'id':'S02','scene_id':'scene2','continuation':False,'transition':'pull_down'}]
 p={'id':'p-test','title':'下拉转场本地验收','board':{'shots':shots},'adopted_takes':{'S01':'a1','S02':'a2'},'board_version':'b1','setting_version':'s1','scene_masters':{'scene1':'m1','scene2':'m2'},'packaging':{'op':False}}
 result=assemble(MediaStore(),{'id':'media-test','payload':{'project':p}},threading.Event())
 meta=probe(result['path']);v=next(x for x in meta['streams'] if x['codec_type']=='video')
 assert int(v['nb_frames'])==88 and v['avg_frame_rate']=='24/1'
 assert '00:00:02,067' in (folder/'captions.srt').read_text()
 with wave.open(str(folder/'final-audio.wav'),'rb') as f:out=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').reshape(-1,2)
 assert np.all(out[12800:51200]==1000)
 second_start=64000-round(32000/3)+12800
 assert np.all(out[second_start:second_start+38400]==2000)
 assert result['manifest']['transitions']==[{'shot_id':'S02','kind':'pull_down'}]
 # Halfway through the wipe: new blue stage is above, old red stage below.
 frame=subprocess.check_output([tool('ffmpeg'),'-v','error','-i',result['path'],'-vf','select=eq(n\\,44),scale=16:32','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
 rgb=np.frombuffer(frame,dtype=np.uint8).reshape(32,16,3)
 assert int(rgb[3,8,2])>int(rgb[3,8,0])+100
 assert int(rgb[28,8,0])>int(rgb[28,8,2])+100


def test_pull_down_after_cut_keeps_cfr_and_expected_frame_count(tmp_path):
 import subprocess
 from workbench.finishing import picture_chain
 from workbench.providers import tool,probe
 paths=[]
 for color in ['red','blue']:
  p=tmp_path/(color+'.mp4');subprocess.run([tool('ffmpeg'),'-v','error','-f','lavfi','-i',f'color={color}:s=64x112:r=24:d=2','-c:v','libx264','-pix_fmt','yuv420p',str(p)],check=True);paths.append(str(p))
 entries=[{'path':paths[i%2],'frames':48,'transition':t} for i,t in enumerate(['cut','cut','pull_down','cut'])]
 args,filters,index=picture_chain(entries);out=tmp_path/'chain.mp4'
 subprocess.run([tool('ffmpeg'),'-v','error']+args+['-filter_complex_threads','1','-filter_complex',';'.join(filters),'-map','[body0]','-c:v','libx264','-pix_fmt','yuv420p',str(out)],check=True)
 v=next(s for s in probe(out)['streams'] if s['codec_type']=='video')
 assert int(v['nb_frames'])==184 and v['avg_frame_rate']=='24/1'


def test_long_bilingual_subtitles_render_inside_safe_margins(tmp_path):
 import subprocess,numpy as np
 from workbench.finishing import caption_header,caption_content,wrap_caption,caption_font
 from workbench.providers import tool
 line={'text':"This is my big brother, Jacky. He's a cheerful little chick.",'translation':'这是我的哥哥奇奇，他是一只开朗又喜欢搭积木的小鸡。'}
 for key,size in [('text',38),('translation',34)]:
  rows=wrap_caption(line[key],size)
  assert ''.join(rows).replace(' ','')==line[key].replace(' ','')
  assert all(caption_font(size).getlength(row)<=620 for row in rows)
 ass=tmp_path/'long.ass';ass.write_text(caption_header()+'Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,'+caption_content(line)+'\n')
 data=subprocess.check_output([tool('ffmpeg'),'-v','error','-f','lavfi','-i','color=black:s=768x1376:r=24:d=2','-vf',f'ass={ass}:fontsdir={Path(__file__).resolve().parents[2]/"recipes/plush-dialogue-v14/assets"}','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
 rgb=np.frombuffer(data,dtype=np.uint8).reshape(1376,768,3);ys,xs=np.where(rgb.max(axis=2)>180)
 assert len(xs)>1000 and xs.min()>=60 and xs.max()<=708
 assert ys.min()>950 and ys.max()<1300


def test_retake_reuses_exact_original_voice_without_new_api_request(tmp_path,monkeypatch):
 import wave,hashlib
 from workbench.providers import Production
 from workbench.domain import fingerprint
 from workbench.store import atomic_json
 s=Store(tmp_path);pid=create(s);source=tmp_path/'jobs'/'old-shoot'/'S03';source.mkdir(parents=True)
 line=setting()['dialogue'][0];original=source/'d1.wav'
 with wave.open(str(original),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(32000);f.writeframes(b'\x01\x00'*32000)
 atomic_json(source/'d1-tts.json',{'phase':'completed','hash':fingerprint({'line':line,'voice':'Cute_Elf','pitch':0,'model':'speech-02-hd'}),'sha256':hashlib.sha256(original.read_bytes()).hexdigest()})
 monkeypatch.setattr(s,'job',lambda jid:{'project_id':pid,'kind':'shoot','status':'succeeded','cancel_requested':False})
 monkeypatch.setattr('urllib.request.urlopen',lambda *a,**kw:pytest.fail('Must reuse existing audio without billing'))
 folder=tmp_path/'new-take';folder.mkdir();prod=Production(s)
 job={'id':'new-shoot','project_id':pid,'payload':{'extra':{'reuse_audio_job_id':'old-shoot'}}}
 actual=prod.speech(job,line,folder);assert actual.read_bytes()==original.read_bytes()
 other=tmp_path/'mismatch';other.mkdir()
 with pytest.raises(ValueError,match='未发起新的计费请求'):prod.speech(job,{**line,'text':'Different text'},other)
