"""Install isolated Soda backend; independent TLS site is enabled only when ready."""
from pathlib import Path
import fcntl,hashlib,json,os,socket,subprocess,sys,tarfile,time,urllib.request
archive=Path(sys.argv[1]);digest=sys.argv[2];release=sys.argv[3]
assert hashlib.sha256(archive.read_bytes()).hexdigest()==digest
root=Path('/home/huanghaibin/soda');data=Path('/data/app/huanghaibin/soda');service=Path('/etc/systemd/system/soda-workbench.service')
root.mkdir(parents=True,exist_ok=True);data.mkdir(parents=True,exist_ok=True)
with (root/'deploy.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 if len(sys.argv)>4:assert (root/'current').resolve().name==sys.argv[4],'Live release changed in parallel; preserve it and rebase before publishing'
 target=root/'releases'/release;assert not target.exists(),'Existing release retained'
 target.mkdir(parents=True)
 with tarfile.open(archive,'r:gz') as tar:
  for m in tar.getmembers():
   path=Path(m.name);assert m.isfile() and not path.is_absolute() and '..' not in path.parts and path.parts[0]=='xiaosuda'
   p=target/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tar.extractfile(m).read())
 project=target/'xiaosuda';manifest=json.loads((project/'workbench/deploy/release.json').read_text())
 for name,h in manifest['files'].items():assert hashlib.sha256((project/name).read_bytes()).hexdigest()==h,'Bundle mismatch '+name
 env=os.environ.copy();env.update(SODA_DATA=str(data/'preflight'/release),SODA_AUTH='gate',SODA_WORKER='off',SODA_PROJECT=str(project))
 subprocess.run(['/home/huanghaibin/envs/webui/bin/python','-c','import numpy,PIL,httpx,fastapi,uvicorn; from workbench.app import create_app; from workbench.catalog import catalog; from workbench.providers import require_tools; require_tools(); a=create_app(run_worker=False); c=catalog(); assert all(x["available"] for x in c["characters"]); assert len(c["characters"])==7 and c["series"]["max_seconds"]==300'],cwd=project,env=env,check=True,timeout=30)
 try:
  with socket.create_connection(('127.0.0.1',3214),timeout=2):
   h=json.load(urllib.request.urlopen('http://127.0.0.1:3214/api/health'));assert h.get('service')=='soda','Port 3214 belongs to another service'
 except (ConnectionRefusedError,TimeoutError):pass
 database=data/'state.sqlite'
 if database.exists():
  import sqlite3
  with sqlite3.connect('file:'+str(database)+'?mode=ro',uri=True) as c:assert c.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running','waiting_gpu','submitted')").fetchone()[0]==0,'Soda has active jobs; keep original service running'
 current=root/'current';previous=os.readlink(current) if current.is_symlink() else None;assert not current.exists() or current.is_symlink()
 backup=root/'backups'/release;backup.mkdir(parents=True);oldservice=service.read_bytes() if service.exists() else None
 if oldservice:(backup/'service-before.txt').write_bytes(oldservice)
 (backup/'previous.json').write_text(json.dumps({'previous':previous}))
 try:
  service.write_text(f'''[Unit]
Description=Hi Soda script-first production workbench
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/home/huanghaibin/soda/current/xiaosuda
Environment=SODA_DATA=/data/app/huanghaibin/soda
Environment=SODA_PROJECT=/home/huanghaibin/soda/current/xiaosuda
Environment=SODA_AUTH=gate
Environment=SODA_WORKER=on
Environment=SODA_PUBLIC_ORIGIN=https://soda.buplayground.cn
Environment=SODA_RELEASE={release}
Environment=SODA_MINIMAX_KEY_FILE=/data/app/huanghaibin/llm/minimax_api_key
ExecStart=/home/huanghaibin/envs/webui/bin/python -m uvicorn workbench.app:app --host 127.0.0.1 --port 3214
Restart=on-failure
RestartSec=4
TimeoutStopSec=15
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
[Install]
WantedBy=multi-user.target
''')
  nextlink=root/'current-next';nextlink.unlink(missing_ok=True);nextlink.symlink_to(target);os.replace(nextlink,current)
  subprocess.run(['systemctl','daemon-reload'],check=True,timeout=15);subprocess.run(['systemctl','enable','--now','soda-workbench.service'],check=True,timeout=30)
  if previous:subprocess.run(['systemctl','restart','soda-workbench.service'],check=True,timeout=30)
  health=None
  for _ in range(15):
   try:
    health=json.load(urllib.request.urlopen('http://127.0.0.1:3214/api/health',timeout=3))
    if health.get('worker') and health.get('release')==release:break
   except Exception:pass
   time.sleep(1)
  assert health and health.get('worker') and health.get('release')==release,'Soda health check failed'
 except BaseException:
  if previous:
   temp=root/'current-next';temp.unlink(missing_ok=True);temp.symlink_to(previous);os.replace(temp,current)
  else:current.unlink(missing_ok=True)
  if oldservice:service.write_bytes(oldservice)
  else:subprocess.run(['systemctl','stop','soda-workbench.service'],check=False);service.unlink(missing_ok=True)
  subprocess.run(['systemctl','daemon-reload'],check=False)
  if previous:subprocess.run(['systemctl','restart','soda-workbench.service'],check=False)
  raise
 cert=Path('/data/app/huanghaibin/web/letsencrypt/live/soda.buplayground.cn/fullchain.pem')
 if cert.is_file():subprocess.run(['/home/huanghaibin/envs/webui/bin/python',str(project/'workbench/deploy/enable_site.py')],check=True,timeout=30)
 print(json.dumps({'installed':True,'release':release,'url':'https://soda.buplayground.cn/','health':health,'independent_data':str(data),'tls_ready':cert.is_file(),'other_services_restarted':False,'shortvideo_site_modified':False}))
