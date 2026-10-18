"""Two durable lanes: script writing never waits behind a GPU render."""
import fcntl,threading,time,traceback
from .providers import Writer,Production
from .finishing import assemble
from .domain import NeedsAttention
from .store import atomic_json

class Worker:
 def __init__(self,store,writer=None,production=None):
  self.store=store;self.writer=writer or Writer();self.production=production or Production(store,self.writer);self.stop_event=threading.Event();self.threads=[];self.lease=None
 def start(self):
  self.lease=(self.store.root/'worker.lock').open('a')
  try:fcntl.flock(self.lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:self.lease.close();self.lease=None;return
  self.store.recover();self.stop_event.clear()
  for name,kinds in [('writer',['setting','board']),('production',['voices','scene','shoot','assemble'])]:
   t=threading.Thread(target=self.loop,args=(kinds,),daemon=True,name='soda-'+name);t.start();self.threads.append(t)
 def stop(self):
  self.stop_event.set()
  for t in self.threads:t.join(timeout=2)
  if self.lease:self.lease.close();self.lease=None
 def loop(self,kinds):
  while not self.stop_event.is_set():
   job=self.store.claim(kinds)
   if not job:self.stop_event.wait(.8);continue
   folder=self.store.root/'jobs'/job['id']
   try:
    if job['kind'] in ['setting','board']:
     result=self.writer.stage(job,self.store)
     if self.store.job(job['id'])['cancel_requested']:
      atomic_json(folder/'cancelled-result.json',result);self.store.progress(job['id'],'结果已保存，取消采用',status='cancelled')
     else:self.store.complete_text(job,result)
    else:
     if job['kind']=='voices':result=self.production.voices(job,self.stop_event)
     elif job['kind']=='scene':result=self.production.scene(job,self.stop_event)
     elif job['kind']=='shoot':result=self.production.shoot(job,self.stop_event)
     else:result=assemble(self.store,job,self.stop_event)
     atomic_json(folder/'result.json',result)
     cancelled=self.store.job(job['id'])['cancel_requested'];self.store.progress(job['id'],'制作结果已保存，请预览并选择采用' if not cancelled else '原任务结果已保存，取消采用',status='succeeded' if not cancelled else 'cancelled',result_assets=[a['id'] for a in result] if isinstance(result,list) else [result['id']])
   except NeedsAttention as e:
    self.store.progress(job['id'],str(e),status='queued' if self.stop_event.is_set() else 'needs_attention',error=None if self.stop_event.is_set() else str(e));(folder/'error.txt').write_text(traceback.format_exc())
   except Exception as e:
    message=str(e)[:1200] or '任务未完成，输入和历史产物已保留';self.store.progress(job['id'],message,status='failed',error=message);(folder/'error.txt').write_text(traceback.format_exc())
