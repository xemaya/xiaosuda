"""Read-only integrity check for S1E02 accepted references; no GPU/network/TTS."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def main():
 m=json.loads((HERE/'frozen-files.json').read_text());errors=[]
 for name,expected in m['files'].items():
  p=HERE/name
  if not p.is_file():errors.append('missing '+name)
  elif sha(p)!=expected:errors.append('changed '+name)
 r=json.loads((HERE/'recipe.json').read_text())
 assert sum(r['take_frames'])+48==r['delivery']['frames']==768
 assert r['status']=='user_accepted' and r['delivery']['fps']==24
 if errors:raise SystemExit('\n'.join(errors))
 print(f'Verified {len(m["files"])} frozen files/references, approved movie and 768-frame S1E02 timeline.')
if __name__=='__main__':main()
