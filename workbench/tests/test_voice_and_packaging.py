import json,threading,wave,copy
import numpy as np
import pytest
from workbench.store import Store
from workbench.providers import Production,run,probe
from workbench.domain import fingerprint,validate_board,normalize_packaging
from workbench.finishing import assemble
from workbench.catalog import PROJECT
from workbench.tests.test_workbench import create,prepare,setting,board


def wav(path,seconds=2,freq=440):
 samples=(np.sin(np.arange(round(seconds*32000))*2*np.pi*freq/32000)*1000).astype('<i2')
 with wave.open(str(path),'wb') as f:
  f.setnchannels(2);f.setsampwidth(2);f.setframerate(32000);f.writeframes(np.repeat(samples[:,None],2,axis=1).tobytes())
 return path


def test_prepared_voice_reuses_exact_line_without_api_and_changed_line_does_not(tmp_path,monkeypatch):
 s=Store(tmp_path);pid=create(s);p=prepare(s,pid)
 line=p['setting']['dialogue'][0];voice=wav(tmp_path/'prepared.wav')
 h=fingerprint({'line':line,'voice':'Cute_Elf','pitch':0,'model':'speech-02-hd'})
 a=s.add_asset(pid,'voice',voice,{'name':'prepared','tts_hash':h})
 job=s.enqueue(pid,p['revision'],'voices','voice-prep-reuse-001');job=s.claim(['voices'])
 folder=s.root/'jobs'/job['id']/'exact';folder.mkdir()
 monkeypatch.setattr('urllib.request.urlopen',lambda *a,**kw:pytest.fail('Prepared voice must not make another API call'))
 prod=Production(s);monkeypatch.setattr(prod,'key',lambda:'')
 path=prod.speech(job,line,folder)
 assert path.read_bytes()==voice.read_bytes()
 assert json.loads((folder/(line['id']+'-tts.json')).read_text())['reused_voice_asset']==a['id']
 changed={**line,'text':'Different original line.'};other=folder/'changed';other.mkdir()
 with pytest.raises(ValueError,match='未就绪'):prod.speech(job,changed,other)


def test_voice_stage_checks_every_speaker_before_first_paid_request(tmp_path,monkeypatch):
 s=Store(tmp_path);pid=create(s);p=prepare(s,pid);job=s.enqueue(pid,p['revision'],'voices','voice-preflight-001');job=s.claim(['voices'])
 job['payload']['project']['setting']['dialogue'].append({'id':'d3','speaker_id':'xiaomi-mimi','text':'Hello'})
 prod=Production(s);monkeypatch.setattr(prod,'speech',lambda *a:pytest.fail('No voice requests before roster preflight'))
 with pytest.raises(ValueError,match='小咪'):prod.voices(job,threading.Event())


def two_shots():
 b=board();first=b['shots'][0];first.update(seconds=2,dialogue_ids=['d1'])
 second=copy.deepcopy(first);second.update(id='S02',dialogue_ids=['d2']);b['shots'].append(second);return b


def test_cold_open_position_requires_real_shot_and_enabled_op():
 b=two_shots();assert validate_board(b,setting(),{'op':True,'op_after_shot':'S01'})
 with pytest.raises(ValueError,match='片头位置'):validate_board(b,setting(),{'op':True,'op_after_shot':'missing'})
 with pytest.raises(ValueError,match='片头位置'):normalize_packaging({'op':False,'op_after_shot':'S01'})


def test_real_cold_open_compiler_keeps_original_audio_and_shifts_only_later_captions(tmp_path):
 s=Store(tmp_path);pid=create(s);p=prepare(s,pid)
 image=tmp_path/'master.png';image.write_bytes(b'provenance-only-fixture')
 master=s.add_asset(pid,'scene',image,{'scene_id':'scene-1','setting_version':p['setting_version']});p=s.adopt(pid,p['revision'],master['id'])
 p=s.update(pid,p['revision'],{'board':two_shots(),'packaging':{'op':True,'op_after_shot':'S01'}});p=s.accept(pid,p['revision'],'board')
 waves=[]
 for i,(shot,color) in enumerate(zip(p['board']['shots'],['red','blue'])):
  video=tmp_path/f'take-{i}.mp4';audio=wav(tmp_path/f'voice-{i}.wav',freq=440+220*i);waves.append(audio)
  run(['ffmpeg','-v','error','-n','-f','lavfi','-i',f'color=c={color}:s=768x1376:r=24','-frames:v','48','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',video])
  line=p['setting']['dialogue'][i]
  take=s.add_asset(pid,'take',video,{'shot_id':shot['id'],'scene_id':'scene-1','master_id':master['id'],'board_version':p['board_version'],'keep_frames':48,'audio':{'wave':str(audio),'turns':[{**line,'start':.4,'end':1.4}]},'context_dependency':None})
  p=s.adopt(pid,p['revision'],take['id'])
 j=s.enqueue(pid,p['revision'],'assemble','cold-open-media-001');job=s.claim(['assemble']);result=assemble(s,job,threading.Event())
 assert result['frames']==144 and result['manifest']['op_after_shot']=='S01'
 video=probe(s.asset(result['id'])['path']);v=next(x for x in video['streams'] if x['codec_type']=='video')
 assert v['nb_frames']=='144' and v['avg_frame_rate']=='24/1'
 folder=s.root/'jobs'/j['id'];captions=(folder/'captions.srt').read_text()
 assert '00:00:00,400 --> 00:00:01,400' in captions and '00:00:04,400 --> 00:00:05,400' in captions
 def samples(path):
  with wave.open(str(path),'rb') as f:return f.readframes(f.getnframes())
 audio=samples(folder/'final-audio.wav');op=samples(PROJECT/'assets/op/hi-soda-motion/hi-soda-op.wav')
 assert audio==samples(waves[0])+op+samples(waves[1])
