"""Run the user's approved five-scene image batch through the existing workbench."""
from pathlib import Path
import json,time
from workbench.store import Store,atomic_json
from workbench.domain import fingerprint
PID='p_5e6ea50dd70a4026'
store=Store('/data/app/huanghaibin/soda')
receipt=store.root/'batches'/'s1e01-scene-masters-v1.json'
project=store.project(PID)
if receipt.exists():
 batch=json.loads(receipt.read_text())
 assert batch['setting_version']==project['setting_version'],'Setting changed; keep existing batch and receipts'
else:
 assert project['revision']==4 and len(project['setting']['scenes'])==5,'Approved version changed; review before submitting'
 batch={'project_id':PID,'setting_version':project['setting_version'],'setting_hash':fingerprint(project['setting']),'human_approval':'2026-10-16 审稿OK，开始出图','jobs':{},'assets':{}}
 atomic_json(receipt,batch)
if not project['setting_accepted']:
 project=store.accept(PID,project['revision'],'setting')
 print(json.dumps({'event':'setting_accepted','revision':project['revision']},ensure_ascii=False),flush=True)
for scene in project['setting']['scenes']:
 current=store.project(PID)
 assert current['setting_version']==batch['setting_version'],'Setting changed during batch; stop without overwriting'
 sid=scene['id']
 if sid not in batch['jobs']:
  task=store.enqueue(PID,current['revision'],'scene','s1e01-scene-masters-v1-'+sid,{'scene_id':sid})
  batch['jobs'][sid]=task['id'];atomic_json(receipt,batch)
 jid=batch['jobs'][sid];last=None;deadline=time.monotonic()+2400
 while True:
  task=store.job(jid);status=task['status']
  if (status,task['progress'])!=last:
   print(json.dumps({'scene':sid,'name':scene['name'],'job_id':jid,'status':status,'progress':task['progress'],'prompt_id':task.get('prompt_id')},ensure_ascii=False),flush=True);last=(status,task['progress'])
  if status=='succeeded':
   assets=[store.asset(aid,PID) for aid in task['result_assets']]
   batch['assets'][sid]=assets;atomic_json(receipt,batch)
   print(json.dumps({'scene':sid,'event':'image_saved','assets':[{'id':a['id'],'path':a['path'],'sha256':a['sha256']} for a in assets]},ensure_ascii=False),flush=True)
   break
  if status in ['failed','needs_attention','cancelled']:
   batch['stopped']={'scene':sid,'status':status,'error':task.get('error')};atomic_json(receipt,batch)
   raise RuntimeError(json.dumps(batch['stopped'],ensure_ascii=False))
  if time.monotonic()>deadline:raise TimeoutError('Original task receipt preserved; no resubmission: '+jid)
  time.sleep(4)
batch['complete']=True;atomic_json(receipt,batch)
print(json.dumps({'event':'batch_complete','receipt':str(receipt),'candidate_count':sum(len(a) for a in batch['assets'].values()),'auto_adopted':False}),flush=True)
