from pathlib import Path
import json,subprocess,os
root=Path('/home/huanghaibin/soda');web=Path('/data/app/huanghaibin/web');config=web/'conf/nginx.conf';site=web/'conf/sites/soda.conf'
assert (web/'letsencrypt/live/soda.buplayground.cn/fullchain.pem').is_file(),'Independent TLS certificate not ready'
source=Path(__file__).resolve().with_name('soda.conf');before=config.read_bytes();old=site.read_bytes() if site.exists() else None
backup=root/'site-backups';backup.mkdir(exist_ok=True)
import time
stamp=str(time.time_ns());(backup/(stamp+'-nginx.conf')).write_bytes(before)
if old:(backup/(stamp+'-soda.conf')).write_bytes(old)
include='  include '+str(site)+';\n';nginx=['/home/huanghaibin/envs/web/bin/nginx','-p',str(web),'-e',str(web/'logs/error.log'),'-c',str(config)];changed=False
try:
 assert config.read_bytes()==before,'Concurrent nginx changes preserved'
 site.write_bytes(source.read_bytes());text=before.decode()
 if str(site) not in text:
  pos=text.rfind('}');assert pos>0;config.write_text(text[:pos]+include+text[pos:]);changed=True
 subprocess.run(nginx+['-t','-q'],check=True,timeout=15);subprocess.run(nginx+['-s','reload'],check=True,timeout=15)
except BaseException:
 if old is None:site.unlink(missing_ok=True)
 else:site.write_bytes(old)
 if changed:config.write_text(config.read_text().replace(include,'',1))
 subprocess.run(nginx+['-t','-q'],check=False);subprocess.run(nginx+['-s','reload'],check=False);raise
print(json.dumps({'url':'https://soda.buplayground.cn/','independent_site':True,'login_gate':True,'other_site_files_changed':False}))
