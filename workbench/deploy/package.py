from pathlib import Path
import hashlib,json,tarfile,datetime
P=Path(__file__).resolve().parents[2];out=P/'workbench/evidence';out.mkdir(exist_ok=True)
files=[x for x in (P/'workbench').rglob('*') if x.is_file() and not any(part in ['.runtime','__pycache__','evidence','.pytest_cache'] for part in x.parts) and x.name!='release.json']
paths=['docs/series-bible.md','characters.md','WORKFLOW.md','recipes/plush-dialogue-v14/recipe.json','recipes/plush-dialogue-v14/continuity.py','recipes/plush-dialogue-v14/README.md','recipes/plush-dialogue-v14/assets/Alibaba-PuHuiTi-Regular.ttf','recipes/plush-dialogue-v14/assets/v14-local.ass','recipes/plush-dialogue-v14/assets/scene-master.png','recipes/ep01-v12/assets/practice-firstframe.png','firstframes/xiaosuda+mengji-snack-table.png','firstframes/xiaosuda+mengji-birthday.png','assets/intertitles/motion/a-paw-pop-preview.mp4','assets/intertitles/motion/a-paw-pop-alpha.mov','assets/intertitles/motion/a-paw-pop.wav','assets/op/hi-soda-motion/hi-soda-op-2s.mp4','assets/op/hi-soda-motion/hi-soda-op.wav','releases/ep01/2026-10-15/Hi-Soda_EP01_How-Are-You.mp4']
files+=list((P/'sheets').glob('*.png'))+[P/x for x in paths]
manifest={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(set(files))};digest=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()[:12]
release=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+digest
meta=P/'workbench/deploy/release.json';meta.write_text(json.dumps({'release':release,'files':manifest},indent=2)+'\n');files.append(meta)
archive=out/(release+'.tar.gz')
with tarfile.open(archive,'w:gz') as tar:
 for f in sorted(set(files)):tar.add(f,arcname='xiaosuda/'+str(f.relative_to(P)),recursive=False)
r={'release':release,'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'size_bytes':archive.stat().st_size,'files':len(files)};(out/'package.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
