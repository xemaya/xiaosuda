"""Read-only frozen recipe verification. No rendering, provider, write or network."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def main():
 frozen=json.loads((HERE/'frozen-files.json').read_text())
 for name,expected in frozen['files'].items():
  p=ROOT/name;assert p.is_file(),name;assert sha(p)==expected,name
 r=json.loads((HERE/'recipe.json').read_text());a=json.loads((HERE/'user-confirmation.json').read_text())
 assert a['status']==r['status']=='user_accepted'
 assert r['accepted_video']['sha256']==a['sha256']==sha(ROOT/r['accepted_video']['path'])
 assert r['delivery']['frames']==3389 and r['ending']['native_selected_frames']==[24,240]
 print(f"Verified {len(frozen['files'])} frozen files, accepted Huangshan V4, exact sources and local edit provenance. No GPU/TTS/network or writes.")
if __name__=='__main__':main()
