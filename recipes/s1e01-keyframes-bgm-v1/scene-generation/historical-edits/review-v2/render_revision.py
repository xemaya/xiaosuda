from pathlib import Path
import json,time
from workbench.store import Store,atomic_json
s=Store('/data/app/huanghaibin/soda');folder=s.root/'batches/s1e01-review-v2';receipt=folder/'revision.json';r=json.loads(receipt.read_text());assert r['ready']
for sid in r['remaining_shots']:
 p=s.project(r['project_id']);assert p['board_version']==r['board_version'],'Project changed in parallel'
 if sid not in r['jobs']:
  j=s.enqueue(p['id'],p['revision'],'shoot','s1e01-review-v2-'+sid,{'shot_id':sid,'reuse_audio_job_id':r['old_shoot_job_id']});r['jobs'][sid]=j['id'];atomic_json(receipt,r)
 last=None;deadline=time.monotonic()+2400
 while True:
  j=s.job(r['jobs'][sid]);state=(j['status'],j['progress'])
  if state!=last:print(json.dumps({'shot':sid,'job':j['id'],'status':j['status'],'progress':j['progress'],'prompt_id':j.get('prompt_id'),'error':j.get('error')},ensure_ascii=False),flush=True);last=state
  if j['status']=='succeeded':break
  if j['status'] in ['failed','needs_attention','cancelled']:raise RuntimeError('原任务回执已保留：'+json.dumps({k:j.get(k) for k in ['id','status','error']},ensure_ascii=False))
  if time.monotonic()>deadline:raise TimeoutError('原任务仍保留，不重复提交：'+j['id'])
  time.sleep(5)
r['rendered']=True;atomic_json(receipt,r);print(json.dumps({'event':'revision_render_complete','jobs':r['jobs']},ensure_ascii=False),flush=True)
