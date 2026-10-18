"""Isolated same-seed keyframe test. Never adopts takes or changes project state."""
import argparse, copy, json, time, urllib.request
from pathlib import Path
from workbench.providers import Production, run
from workbench.store import Store, atomic_json
from workbench.catalog import digest

p=argparse.ArgumentParser();p.add_argument('mode',choices=['submit','poll']);p.add_argument('shot',choices=['S07','S08']);p.add_argument('--clean-start',action='store_true');a=p.parse_args()
assert not a.clean_start or a.shot=='S07'
s=Store('/data/app/huanghaibin/soda');prod=Production(s)
root=s.root/'batches/s1e01-generation-review';root.mkdir(exist_ok=True)
sources={'S07':'j_9bb8fd3584c847cd','S08':'j_406de4f10cbb4b8c'}
guides={'S07':[(48,'S07-gesture-f48.png')], 'S08':[(67,'S08-book-released-f67.png'),(144,'S08-family-f144.png')]}
variant='clean-start-guide' if a.clean_start else 'guide-only'
folder=root/(a.shot+'-'+variant);folder.mkdir(exist_ok=True)
receipt=folder/'receipt.json'
if a.mode=='submit':
 if receipt.exists():
  print(receipt.read_text());raise SystemExit('Existing receipt retained. Poll it, do not resubmit.')
 src=s.root/'jobs'/sources[a.shot];g=json.loads((src/'shoot-graph.json').read_text());original=copy.deepcopy(g)
 changed_inputs=set()
 if a.clean_start:
  master=root/'S07-clean-start.png';assert master.is_file()
  g['6']['inputs']['image']=prod.input_file(master);changed_inputs.add('6')
  ref=next(n for n in g.values() if n['class_type']=='MiniMaxH3ReferenceToVideo')
  carrier=folder/'carrier.mp4'
  if not carrier.exists():
   run(['ffmpeg','-v','error','-n','-loop','1','-framerate','24','-i',master,'-i',src/a.shot/'carrier-audio.wav','-vf','scale=384:688:force_original_aspect_ratio=increase,crop=384:688,setsar=1','-frames:v',str(ref['inputs']['length']),'-c:v','libx264','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-ar','32000','-b:a','128k',carrier])
  for k,n in g.items():
   if n['class_type']=='LoadVideo':n['inputs']['file']=prod.input_file(carrier);changed_inputs.add(k)
 motion=next(k for k,n in g.items() if n['class_type']=='MiniMaxH3MotionContext')
 cond=next(k for k,n in g.items() if n['class_type']=='MiniMaxH3ReferenceToVideo')
 positive=g[motion]['inputs']['conditioning'];guide_records=[]
 for frame,name in guides[a.shot]:
  path=root/name;assert path.is_file(),str(path)
  image_id=str(max(map(int,g))+1);g[image_id]={'class_type':'LoadImage','inputs':{'image':prod.input_file(path)}}
  guide_id=str(max(map(int,g))+1);g[guide_id]={'class_type':'MiniMaxH3AddGuide','inputs':{'positive':positive,'vae':['4',0],'latent':[cond,1],'image':[image_id,0],'frame_idx':frame}}
  positive=[guide_id,0];guide_records.append({'frame':frame,'image':str(path),'sha256':digest(path),'node':guide_id})
 g[motion]['inputs']['conditioning']=positive
 for k,n in g.items():
  if n['class_type'] in ['SaveImage','SaveVideo']:
   n['inputs']['filename_prefix']='soda/s1e01-generation-review/'+a.shot+'-'+variant+'/'+k
 # Attribute only an additional visual guide: no prompt, seed, carrier or sampler edits.
 for k,n in original.items():
  if k not in changed_inputs and n['class_type'] not in ['MiniMaxH3MotionContext','SaveImage','SaveVideo']:assert n==g[k],k
 atomic_json(folder/'graph.json',g)
 atomic_json(folder/'experiment.json',{'source_job':sources[a.shot],'guides':guide_records,'prompt_seed_unchanged':True,'carrier_unchanged':not a.clean_start,'clean_start_master':str(master) if a.clean_start else None,'project_state_unchanged':True,'pixel_postprocessing':False})
 import uuid
 port=None
 for candidate in [8188,8189,8190,8191,8192]:
  try:
   q=prod.call(candidate,'/queue');info=prod.call(candidate,'/object_info/MiniMaxH3AddGuide')
   if not q.get('queue_running') and not q.get('queue_pending') and 'MiniMaxH3AddGuide' in info:port=candidate;break
  except OSError:continue
 if port is None:raise SystemExit('No idle enabled queue; nothing submitted.')
 q=prod.call(port,'/queue');assert not q.get('queue_running') and not q.get('queue_pending'),'Queue changed, nothing submitted'
 token=str(uuid.uuid4());r={'phase':'submitting','port':port,'prompt_id':token,'graph_sha256':digest(folder/'graph.json'),'created':time.time()};atomic_json(receipt,r)
 try:
  response=prod.call(port,'/prompt',{'prompt':g,'prompt_id':token,'client_id':token,'extra_data':{'soda_batch':'s1e01-generation-review','experiment':a.shot+'-'+variant}},timeout=60)
  r.update(phase='submitted',prompt_id=response['prompt_id']);atomic_json(receipt,r)
 except Exception as e:
  r.update(phase='rejected' if getattr(e,'code',0)==400 else 'submission_unknown');atomic_json(receipt,r);raise
 print(json.dumps(r));raise SystemExit
r=json.loads(receipt.read_text());hist=prod.call(r['port'],'/history/'+r['prompt_id'])
if r['prompt_id'] not in hist:
 q=prod.call(r['port'],'/queue');print(json.dumps({'phase':r['phase'],'prompt_id':r['prompt_id'],'in_queue':any(x[1]==r['prompt_id'] for x in q.get('queue_running',[])+q.get('queue_pending',[]))}));raise SystemExit
h=hist[r['prompt_id']];atomic_json(folder/'history.json',h)
if h.get('status',{}).get('status_str')!='success':
 r['phase']='failed';atomic_json(receipt,r);print(json.dumps(h.get('status'),ensure_ascii=False));raise SystemExit(1)
g=json.loads((folder/'graph.json').read_text());save=next(k for k,n in g.items() if n['class_type']=='SaveVideo')
files=[f for f in prod.output_files(h,save) if f.suffix=='.mp4'];assert len(files)==1
import shutil
raw=folder/'native-raw.mp4'
if not raw.exists():shutil.copy2(files[0],raw)
audio=json.loads((s.root/'jobs'/sources[a.shot]/a.shot/'audio-plan.json').read_text());out=folder/'take.mp4'
if not out.exists():
 run(['ffmpeg','-v','error','-n','-i',raw,'-i',audio['wave'],'-filter_complex',f'[0:v]trim=end_frame={audio["keep_frames"]},setpts=PTS-STARTPTS,fps=24[v]','-map','[v]','-map','1:a:0','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',out])
r.update(phase='completed',output=str(out),sha256=digest(out),keep_frames=audio['keep_frames'],seconds=audio['seconds']);atomic_json(receipt,r);print(json.dumps(r))
