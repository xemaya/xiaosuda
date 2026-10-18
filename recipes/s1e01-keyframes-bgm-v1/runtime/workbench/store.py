"""Independent SQLite/WAL state, immutable revisions, idempotent jobs and assets."""
from contextlib import contextmanager
from pathlib import Path
import copy,json,os,sqlite3,time,uuid,hashlib
from .domain import Conflict,fingerprint,cast_ids,text,validate_setting,validate_board,normalize_packaging
from .catalog import STYLE_ID,CHARACTERS

def uid(prefix):return prefix+'_'+uuid.uuid4().hex[:16]
def now():return time.time()
def atomic_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,path)

class Store:
 def __init__(self,root):
  self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True);self.db=self.root/'state.sqlite'
  with self.connection() as c:
   c.executescript('''PRAGMA journal_mode=WAL;
   CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,doc TEXT NOT NULL,updated REAL NOT NULL);
   CREATE TABLE IF NOT EXISTS versions(id TEXT PRIMARY KEY,project_id TEXT NOT NULL,stage TEXT NOT NULL,doc TEXT NOT NULL,created REAL NOT NULL);
   CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,project_id TEXT NOT NULL,kind TEXT NOT NULL,status TEXT NOT NULL,request_key TEXT NOT NULL UNIQUE,payload TEXT NOT NULL,doc TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL);
   CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY,project_id TEXT NOT NULL,kind TEXT NOT NULL,path TEXT NOT NULL,doc TEXT NOT NULL,created REAL NOT NULL);
   CREATE TABLE IF NOT EXISTS requests(key TEXT PRIMARY KEY,hash TEXT NOT NULL,response TEXT NOT NULL);
   ''')
 @contextmanager
 def connection(self):
  c=sqlite3.connect(self.db,timeout=20);c.row_factory=sqlite3.Row
  try:yield c;c.commit()
  except BaseException:c.rollback();raise
  finally:c.close()
 @contextmanager
 def tx(self):
  with self.connection() as c:c.execute('BEGIN IMMEDIATE');yield c
 def _project(self,c,pid):
  r=c.execute('SELECT doc FROM projects WHERE id=?',(pid,)).fetchone()
  if not r:raise KeyError('作品不存在')
  return json.loads(r['doc'])
 def _save(self,c,p):
  p['revision']+=1;p['updated']=now();c.execute('UPDATE projects SET doc=?,updated=? WHERE id=?',(json.dumps(p,ensure_ascii=False),p['updated'],p['id']))
 def _revision(self,p,revision):
  if p['revision']!=revision:raise Conflict('内容已在别处更新，请刷新后再操作，当前编辑不会被自动覆盖')
 def list(self):
  with self.connection() as c:
   result=[]
   for row in c.execute('SELECT doc FROM projects ORDER BY updated DESC'):
    p=json.loads(row['doc']);result.append({**{k:p[k] for k in ['id','title','revision','status','created','updated','cast_ids','style_id','setting_accepted','board_accepted']},'script_excerpt':p['script'][:100],'scene_count':len((p['setting'] or {}).get('scenes',[])),'shot_count':len((p['board'] or {}).get('shots',[]))})
   return result
 def project(self,pid):
  with self.connection() as c:
   p=self._project(c,pid);p['jobs']=[json.loads(r['doc']) for r in c.execute('SELECT doc FROM jobs WHERE project_id=? ORDER BY created DESC LIMIT 30',(pid,))]
   p['assets']=[json.loads(r['doc']) for r in c.execute('SELECT doc FROM assets WHERE project_id=? ORDER BY created',(pid,))]
   p['versions']=[{'id':r['id'],'stage':r['stage'],'created':r['created']} for r in c.execute('SELECT id,stage,created FROM versions WHERE project_id=? ORDER BY created DESC',(pid,))]
   return p
 def import_scripts(self,scripts,key):
  if not 1<=len(scripts)<=50:raise ValueError('每批导入1–50份剧本')
  signature=fingerprint(scripts)
  with self.tx() as c:
   r=c.execute('SELECT * FROM requests WHERE key=?',(key,)).fetchone()
   if r:
    if r['hash']!=signature:raise Conflict('同一请求编号对应了不同内容')
    return json.loads(r['response'])
   result=[]
   for item in scripts:
    title=text(item.get('title','未命名剧本'),'标题',120);script=text(item.get('script'),'剧本',100000);selected=cast_ids(item.get('cast_ids',[c['id'] for c in CHARACTERS]))
    p={'id':uid('p'),'title':title,'script':script,'script_hash':fingerprint(script),'cast_ids':selected,'style_id':STYLE_ID,'revision':1,'created':now(),'updated':now(),'setting':None,'setting_version':None,'setting_accepted':False,'board':None,'board_version':None,'board_accepted':False,'scene_masters':{},'adopted_takes':{},'final_asset':None,'status':'draft','packaging':{'op':True},'history':[]}
    c.execute('INSERT INTO projects VALUES(?,?,?)',(p['id'],json.dumps(p,ensure_ascii=False),p['updated']));result.append({'id':p['id'],'title':title})
   c.execute('INSERT INTO requests VALUES(?,?,?)',(key,signature,json.dumps(result,ensure_ascii=False)));return result
 def update(self,pid,revision,fields):
  with self.tx() as c:
   p=self._project(c,pid);self._revision(p,revision)
   if 'title' in fields:p['title']=text(fields['title'],'标题',120)
   changed=False
   for k in ['script','cast_ids']:
    if k in fields and fields[k]!=p[k]:
     p[k]=text(fields[k],'剧本',100000) if k=='script' else cast_ids(fields[k]);changed=True
   if changed:
    p['script_hash']=fingerprint(p['script']);p['setting_accepted']=False;p['board_accepted']=False;p['status']='draft';p['final_asset']=None;p['scene_masters']={};p['adopted_takes']={}
   if 'setting' in fields:
    p['setting']=validate_setting(fields['setting'],p['cast_ids']);p['setting_source_hash']=p['script_hash'];p['setting_version']=self._version(c,pid,'setting',p['setting']);p['setting_accepted']=False;p['board_accepted']=False;p['status']='setting';p['final_asset']=None;p['scene_masters']={};p['adopted_takes']={}
   if 'board' in fields:
    if not p['setting_accepted']:raise ValueError('请先确认剧情设定')
    p['board']=validate_board(fields['board'],p['setting'],fields.get('packaging',p['packaging']));p['board_setting_version']=p['setting_version'];p['board_version']=self._version(c,pid,'board',p['board']);p['board_accepted']=False;p['status']='board';p['final_asset']=None;p['adopted_takes']={}
   if 'packaging' in fields:
    packaging=normalize_packaging(fields['packaging'])
    if p['board']:validate_board(p['board'],p['setting'],packaging)
    if packaging!=p['packaging']:p['final_asset']=None
    p['packaging']=packaging
   self._save(c,p)
  return self.project(pid)
 def _version(self,c,pid,stage,doc):
  vid=uid('v');c.execute('INSERT INTO versions VALUES(?,?,?,?,?)',(vid,pid,stage,json.dumps(doc,ensure_ascii=False),now()));return vid
 def accept(self,pid,revision,stage):
  with self.tx() as c:
   p=self._project(c,pid);self._revision(p,revision)
   if stage=='setting':
    if not p['setting']:raise ValueError('请先生成剧情设定')
    validate_setting(p['setting'],p['cast_ids'])
    if p.get('setting_source_hash')!=p['script_hash']:raise Conflict('剧本已修改，请重新拆解或编辑保存设定后确认')
    if p['setting'].get('unresolved_characters'):raise ValueError('请先将剧本里的未匹配人物映射为库内角色')
    p['setting_accepted']=True;p['status']='setting'
   elif stage=='board':
    if not p['setting_accepted'] or not p['board']:raise ValueError('请先生成分镜')
    validate_board(p['board'],p['setting'],p['packaging']);
    if p.get('board_setting_version')!=p['setting_version']:raise Conflict('设定已更新，请重新设计或编辑保存分镜后确认')
    self._require_masters(p);p['board_accepted']=True;p['status']='ready_to_shoot'
   else:raise ValueError('确认阶段无效')
   self._save(c,p)
  return self.project(pid)
 def _require_masters(self,p):
  missing=[s['name'] for s in p['setting']['scenes'] if s['id'] not in p['scene_masters']]
  if missing:raise ValueError('请先为这些场景采用主图：'+'、'.join(missing))
 def enqueue(self,pid,revision,kind,key,extra=None):
  extra=extra or {};signature=fingerprint({'pid':pid,'kind':kind,'extra':extra,'revision':revision})
  with self.tx() as c:
   old=c.execute('SELECT doc,payload FROM jobs WHERE request_key=?',(key,)).fetchone()
   if old:
    doc=json.loads(old['doc'])
    if json.loads(old['payload']).get('request_signature')!=signature:raise Conflict('同一任务编号不能提交不同请求')
    return doc
   p=self._project(c,pid);self._revision(p,revision)
   if c.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running','waiting_gpu','submitted')",(pid,)).fetchone():raise Conflict('本片已有任务，请等待结果；不会重复提交')
   if kind not in ['setting','voices','scene','board','shoot','assemble']:raise ValueError('任务类型无效')
   if kind!='setting' and not p['setting_accepted']:raise ValueError('请先确认剧情设定')
   if kind=='scene' and extra.get('scene_id') not in {s['id'] for s in p['setting']['scenes']}:raise ValueError('场景不存在')
   if kind in ['board','shoot','assemble']:self._require_masters(p)
   if kind in ['shoot','assemble'] and not p['board_accepted']:raise ValueError('请先确认分镜')
   if kind in ['shoot','assemble']:validate_board(p['board'],p['setting'],p['packaging'])
   if kind=='shoot' and extra.get('shot_id') and extra['shot_id'] not in {s['id'] for s in p['board']['shots']}:raise ValueError('镜头不存在')
   if kind=='assemble' and any(s['id'] not in p['adopted_takes'] for s in p['board']['shots']):raise ValueError('请先为每个镜头采用一个拍摄版本')
   jid=uid('j');doc={'id':jid,'project_id':pid,'kind':kind,'status':'queued','progress':'等待执行','created':now(),'updated':now(),'cancel_requested':False,'error':None,'extra':extra}
   payload={'project':p,'extra':extra,'request_signature':signature}
   c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?)',(jid,pid,kind,'queued',key,json.dumps(payload,ensure_ascii=False),json.dumps(doc,ensure_ascii=False),now(),now()))
   (self.root/'jobs'/jid).mkdir(parents=True);atomic_json(self.root/'jobs'/jid/'input.json',payload)
   return doc
 def claim(self,kinds):
  with self.tx() as c:
   row=c.execute("SELECT id,doc,payload FROM jobs WHERE status='queued' AND kind IN ("+','.join('?'*len(kinds))+") ORDER BY created LIMIT 1",kinds).fetchone()
   if not row:return None
   d=json.loads(row['doc']);d.update(status='running',progress='开始处理',updated=now());c.execute('UPDATE jobs SET status=?,doc=?,updated=? WHERE id=?',('running',json.dumps(d,ensure_ascii=False),now(),d['id']))
   return {**d,'payload':json.loads(row['payload'])}
 def job(self,jid):
  with self.connection() as c:
   r=c.execute('SELECT doc,payload FROM jobs WHERE id=?',(jid,)).fetchone()
   if not r:raise KeyError('任务不存在')
   return {**json.loads(r['doc']),'payload':json.loads(r['payload'])}
 def progress(self,jid,message,status=None,**extra):
  with self.tx() as c:
   row=c.execute('SELECT doc FROM jobs WHERE id=?',(jid,)).fetchone();d=json.loads(row['doc'])
   if d.get('progress')==message and (not status or d.get('status')==status) and all(d.get(k)==v for k,v in extra.items()):return
   d.update(progress=message,updated=now(),**extra)
   if status:d['status']=status
   c.execute('UPDATE jobs SET status=?,doc=?,updated=? WHERE id=?',(d['status'],json.dumps(d,ensure_ascii=False),now(),jid))
 def complete_text(self,job,result):
  stage=job['kind'];pid=job['project_id']
  with self.tx() as c:
   p=self._project(c,pid);snap=job['payload']['project'];vid=self._version(c,pid,stage,result)
   same=(p['script_hash']==snap['script_hash'] and p['cast_ids']==snap['cast_ids'] and (stage!='board' or p['setting_version']==snap['setting_version']))
   if same:
    p[stage]=result;p[stage+'_version']=vid;
    if stage=='setting':p['setting_source_hash']=snap['script_hash']
    else:p['board_setting_version']=snap['setting_version']
    p[stage+'_accepted']=False;p['status']=stage
    if stage=='setting':p['board_accepted']=False;p['scene_masters']={};p['adopted_takes']={}
    self._save(c,p)
  self.progress(job['id'],'已生成，请检查后确认' if same else '生成期间输入已变，结果保留在历史版本，未覆盖当前内容',status='succeeded',result_version=vid)
 def add_asset(self,pid,kind,path,metadata):
  path=Path(path).resolve()
  if not path.is_relative_to(self.root):raise ValueError('制作素材必须位于本工作台数据目录')
  if not path.is_file():raise ValueError('制作产物尚未写完')
  doc={**metadata,'id':uid('a'),'project_id':pid,'kind':kind,'created':now(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'url':None};doc['url']='api/media/'+doc['id']
  with self.tx() as c:
   existing=c.execute('SELECT doc FROM assets WHERE project_id=? AND kind=? AND path=?',(pid,kind,str(path))).fetchone()
   if existing:
    old=json.loads(existing['doc'])
    if old['sha256']!=doc['sha256']:raise ValueError('历史素材文件被修改，不能覆盖旧版本')
    return old
   c.execute('INSERT INTO assets VALUES(?,?,?,?,?,?)',(doc['id'],pid,kind,str(path),json.dumps(doc,ensure_ascii=False),now()))
  return doc
 def asset(self,aid,pid=None):
  with self.connection() as c:r=c.execute('SELECT * FROM assets WHERE id=?',(aid,)).fetchone()
  if not r or (pid and r['project_id']!=pid):raise ValueError('素材不属于本片或已不存在')
  return {**json.loads(r['doc']),'path':r['path']}
 def adopt(self,pid,revision,aid):
  with self.tx() as c:
   p=self._project(c,pid);self._revision(p,revision)
   row=c.execute('SELECT doc FROM assets WHERE id=? AND project_id=?',(aid,pid)).fetchone()
   if not row:raise ValueError('只能采用本片的素材')
   a=json.loads(row['doc'])
   if a['kind']=='scene':
    if a.get('setting_version')!=p['setting_version']:raise Conflict('这张图对应旧设定，不能冒充当前场景主图')
    p['scene_masters'][a['scene_id']]=aid;p['board_accepted']=False;p['final_asset']=None
   elif a['kind']=='take':
    if not p['board_accepted'] or a.get('board_version')!=p['board_version'] or a.get('master_id')!=p['scene_masters'].get(a.get('scene_id')):raise Conflict('此版本对应旧分镜或旧主图，请核对后重新拍摄')
    p['adopted_takes'][a['shot_id']]=aid;p['final_asset']=None
   elif a['kind']=='final':
    if not p['board_accepted'] or not p['setting_accepted'] or a.get('board_version')!=p['board_version'] or a.get('setting_version')!=p['setting_version']:raise Conflict('该成片对应旧设定或分镜，不能覆盖当前版本')
    p['final_asset']=aid;p['status']='complete'
   else:raise ValueError('素材不能采用')
   self._save(c,p)
  return self.project(pid)
 def use_reference(self,pid,revision,scene_id,reference_id,path):
  p=self.project(pid)
  if not p['setting_accepted']:raise ValueError('请先确认剧情设定')
  if scene_id not in {s['id'] for s in p['setting']['scenes']}:raise ValueError('场景不存在')
  from .catalog import SCENES
  ref=next((s for s in SCENES if s['id']==reference_id),None);scene=next(s for s in p['setting']['scenes'] if s['id']==scene_id)
  if not ref or sorted(scene['cast_ids'])!=sorted(ref['cast_ids']):raise ValueError('现有场景的出镜人物与本场景不匹配，请生成本片主图')
  if not ref.get('direct_use'):raise ValueError('该参考图不是竖版主图，请根据它生成本片场景')
  if any(prop not in ref.get('props',[]) for prop in scene['props']):raise ValueError('现有图未确认包含剧本所需道具，请生成本片场景主图')
  target=self.root/'reference-imports'/(uid('img')+Path(path).suffix);target.parent.mkdir(exist_ok=True);target.write_bytes(Path(path).read_bytes())
  asset=self.add_asset(pid,'scene',target,{'name':ref['name'],'scene_id':scene_id,'setting_version':p['setting_version'],'reference_id':reference_id})
  return self.adopt(pid,revision,asset['id'])
 def cancel(self,jid):
  j=self.job(jid)
  if j['status'] not in ['queued','running','waiting_gpu','submitted']:return
  self.progress(jid,'取消采用；已提交的共享GPU不被中断',status='cancelled' if j['status']=='queued' else None,cancel_requested=True)
 def resume(self,jid):
  job=self.job(jid)
  if job['status']!='needs_attention':raise ValueError('只有待核对的任务可以恢复原回执')
  with self.connection() as c:
   active=c.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running','waiting_gpu','submitted') AND id<>?",(job['project_id'],jid)).fetchone()
  if active:raise Conflict('本片另有进行中的任务，不能并行恢复')
  self.progress(jid,'核对原任务回执，不重复提交',status='queued',error=None,cancel_requested=False)
 def recover(self):
  with self.connection() as c:ids=[r['id'] for r in c.execute("SELECT id FROM jobs WHERE status IN ('running','waiting_gpu','submitted')")]
  with self.connection() as c:
   paused=[r['id'] for r in c.execute("SELECT id,doc FROM jobs WHERE status='needs_attention'") if json.loads(r['doc']).get('progress','').startswith('服务暂停')]
  for jid in ids+paused:self.progress(jid,'服务恢复：继续核对同一任务的保存回执',status='queued')
