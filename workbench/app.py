import asyncio,json,os,time
from contextlib import asynccontextmanager
from pathlib import Path
import httpx
from fastapi import FastAPI,Request,UploadFile,File
from fastapi.responses import FileResponse,JSONResponse,Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,ConfigDict,Field
from .store import Store
from .worker import Worker
from .domain import Conflict,fingerprint
from .catalog import catalog,media_path,PROJECT,digest,CHARACTERS

ROOT=Path(__file__).resolve().parent
class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class Script(Strict):
 title:str=Field(min_length=1,max_length=120)
 script:str=Field(min_length=1,max_length=100000)
 cast_ids:list[str]=Field(default_factory=lambda:[c['id'] for c in CHARACTERS])
class Import(Strict):
 scripts:list[Script]=Field(min_length=1,max_length=50)
 request_key:str=Field(min_length=8,max_length=120)
class Change(Strict):
 revision:int
 title:str|None=None
 script:str|None=None
 cast_ids:list[str]|None=None
 setting:dict|None=None
 board:dict|None=None
 packaging:dict|None=None
class Command(Strict):revision:int
class Task(Command):
 kind:str
 request_key:str=Field(min_length=8,max_length=120)
 scene_id:str|None=None
 shot_id:str|None=None
 reuse_audio_job_id:str|None=None
class Accept(Command):stage:str
class Adopt(Command):asset_id:str
class Reference(Command):scene_id:str;reference_id:str


def create_app(data=None,auth=None,run_worker=None,writer=None,production=None):
 store=Store(data or os.environ.get('SODA_DATA',str(ROOT/'.runtime')));auth=auth or os.environ.get('SODA_AUTH','gate');worker=Worker(store,writer,production)
 enabled=run_worker if run_worker is not None else os.environ.get('SODA_WORKER','on')=='on'
 public_origin=os.environ.get('SODA_PUBLIC_ORIGIN','https://soda.buplayground.cn')
 @asynccontextmanager
 async def lifespan(app):
  async with httpx.AsyncClient(timeout=5,trust_env=False) as client:
   app.state.gate=client
   if enabled:worker.start()
   try:yield
   finally:worker.stop()
 app=FastAPI(title='Hi, Soda! 制片工作台',lifespan=lifespan,docs_url=None,redoc_url=None)
 app.state.store=store;app.state.worker=worker
 @app.exception_handler(ValueError)
 async def invalid(request,exc):return JSONResponse({'detail':str(exc)},status_code=400)
 @app.exception_handler(Conflict)
 async def conflict(request,exc):return JSONResponse({'detail':str(exc)},status_code=409)
 @app.exception_handler(KeyError)
 async def missing(request,exc):return JSONResponse({'detail':str(exc).strip("'")},status_code=404)
 @app.exception_handler(Exception)
 async def error(request,exc):
  import logging;logging.exception('Soda request failed')
  return JSONResponse({'detail':'操作未完成，输入与历史结果仍保留，请刷新后核对'},status_code=500)
 @app.middleware('http')
 async def protect(request,call_next):
  host=request.url.hostname;loopback=host in ['127.0.0.1','localhost','::1'] and request.client and request.client.host in ['127.0.0.1','::1','testclient']
  health=request.url.path=='/api/health' and loopback
  if auth=='off' and not loopback:return JSONResponse({'detail':'本地开发模式不对外开放'},status_code=403)
  if auth=='gate' and not health:
   try:
    r=await app.state.gate.get('http://127.0.0.1:3100/gate/check',headers={'Cookie':request.headers.get('cookie','')})
    if r.status_code!=204:return JSONResponse({'detail':'请先登录工作台','login':'/gate/login?next=/'},status_code=401)
   except httpx.HTTPError:return JSONResponse({'detail':'登录服务暂不可用'},status_code=503)
  elif auth not in ['off','gate']:return JSONResponse({'detail':'访问配置无效'},status_code=503)
  if request.method not in ['GET','HEAD','OPTIONS']:
   origin=request.headers.get('origin')
   if origin and origin not in [public_origin,str(request.base_url).rstrip('/')]:return JSONResponse({'detail':'请从本工作台提交'},status_code=403)
   try:
    if int(request.headers.get('content-length','0'))>8*1024*1024:return JSONResponse({'detail':'本批剧本超过8MB'},status_code=413)
   except ValueError:return JSONResponse({'detail':'请求长度无效'},status_code=400)
  r=await call_next(request)
  r.headers['X-Content-Type-Options']='nosniff';r.headers['Referrer-Policy']='same-origin'
  r.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; font-src 'self'; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
  if 'Cache-Control' not in r.headers:r.headers['Cache-Control']='private, no-cache' if request.url.path.startswith('/api/') else 'no-cache'
  return r
 @app.get('/api/health')
 def health():return {'ok':True,'service':'soda','worker':bool(worker.threads and all(t.is_alive() for t in worker.threads)),'release':os.environ.get('SODA_RELEASE','development')}
 @app.get('/api/catalog')
 def get_catalog():return catalog()
 cap_cache={'time':0,'value':{}}
 @app.get('/api/capabilities')
 async def capabilities():
  if time.time()-cap_cache['time']<25:return cap_cache['value']
  def check():
   writer_ready=False
   try:
    import urllib.request
    with urllib.request.urlopen(worker.writer.url.replace('/v1/chat/completions','/health'),timeout=3) as r:writer_ready=r.status==200
   except Exception:pass
   value={'writer':writer_ready,'voice':bool(worker.production.key()),'renderer':worker.production.input.parent.exists(),'worker':bool(worker.threads and all(t.is_alive() for t in worker.threads)),'style':'soda-plush-v14'}
   cap_cache.update(time=time.time(),value=value);return value
  return await asyncio.to_thread(check)
 @app.get('/api/projects')
 def projects():return store.list()
 @app.post('/api/projects/batch')
 def batch(body:Import):return store.import_scripts([s.model_dump() for s in body.scripts],body.request_key)
 @app.get('/api/projects/{pid}')
 def project(pid:str,request:Request):
  p=store.project(pid);tag='"'+fingerprint(p)+'"'
  if request.headers.get('if-none-match')==tag:return Response(status_code=304,headers={'ETag':tag})
  return JSONResponse(p,headers={'ETag':tag})
 @app.patch('/api/projects/{pid}')
 def update(pid:str,body:Change):return store.update(pid,body.revision,body.model_dump(exclude_none=True,exclude={'revision'}))
 @app.post('/api/projects/{pid}/accept')
 def accept(pid:str,body:Accept):return store.accept(pid,body.revision,body.stage)
 @app.post('/api/projects/{pid}/tasks')
 def task(pid:str,body:Task):
  extra={k:v for k,v in {'scene_id':body.scene_id,'shot_id':body.shot_id,'reuse_audio_job_id':body.reuse_audio_job_id}.items() if v}
  return store.enqueue(pid,body.revision,body.kind,body.request_key,extra)
 @app.post('/api/projects/{pid}/adopt')
 def adopt(pid:str,body:Adopt):return store.adopt(pid,body.revision,body.asset_id)
 @app.post('/api/projects/{pid}/reference')
 def reference(pid:str,body:Reference):return store.use_reference(pid,body.revision,body.scene_id,body.reference_id,media_path(body.reference_id))
 @app.post('/api/jobs/{jid}/cancel')
 def cancel(jid:str):store.cancel(jid);return {'ok':True}
 @app.post('/api/jobs/{jid}/resume')
 def resume(jid:str):store.resume(jid);return {'ok':True}
 @app.get('/api/jobs/{jid}')
 def job(jid:str):
  j=store.job(jid);j.pop('payload',None);return j
 @app.get('/api/projects/{pid}/export')
 def export(pid:str):return Response(json.dumps(store.project(pid),ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="soda-{pid}.json"'})
 @app.get('/api/projects/{pid}/versions/{vid}')
 def version(pid:str,vid:str):
  store.project(pid)
  with store.connection() as c:r=c.execute('SELECT doc,stage FROM versions WHERE id=? AND project_id=?',(vid,pid)).fetchone()
  if not r:raise KeyError('历史版本不存在')
  return {'id':vid,'stage':r['stage'],'content':json.loads(r['doc'])}
 @app.get('/api/media/{aid}')
 def media(aid:str,download:bool=False):
  asset=store.asset(aid);path=Path(asset['path']).resolve()
  if not path.is_relative_to(store.root) or not path.is_file():raise ValueError('素材文件尚不可用')
  if digest(path)!=asset['sha256']:raise ValueError('素材校验失败，原版本未覆盖')
  return FileResponse(path,filename=('hi-soda-'+aid+path.suffix) if download else None,headers={'Cache-Control':'private, max-age=3600','ETag':'"'+asset['sha256']+'"'})
 @app.get('/api/catalog/media/{key}')
 def catalog_media(key:str):
  path=media_path(key);return FileResponse(path,headers={'Cache-Control':'private, max-age=3600'})
 @app.get('/')
 def index():return FileResponse(ROOT/'web/index.html')
 app.mount('/static',StaticFiles(directory=ROOT/'web'),name='static')
 return app
app=create_app()
