"""Offline integrity check. Does not upload, render, use a GPU or alter files."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(2**20),b''):h.update(block)
 return h.hexdigest()
def main():
 frozen=json.loads((HERE/'frozen-files.json').read_text());errors=[]
 for name,value in frozen['files'].items():
  path=HERE/name
  if not path.is_file():errors.append('missing '+name)
  elif sha(path)!=value:errors.append('changed '+name)
 recipe=json.loads((HERE/'recipe.json').read_text());video=HERE/recipe['accepted_video']['path']
 if not video.is_file():errors.append('missing accepted video '+str(video))
 elif sha(video)!=recipe['accepted_video']['sha256']:errors.append('accepted video changed')
 total=48 if recipe['packaging'].get('op',True) else 0
 for sid in recipe['shot_order']:
  shot=recipe['shots'][sid];total+=shot['keep_frames']-(8 if shot['transition']=='pull_down' else 0)
  if shot['audio']['keep_frames']!=shot['keep_frames']:errors.append(sid+' audio length mismatch')
  if shot['continuation']:errors.append('Unexpected continuation: inspect actual retained-tail dependency')
 if total!=recipe['delivery']['frames']:errors.append('picture timeline frame total mismatch')
 graphfiles=set()
 for a in json.loads((HERE/'accepted/asset-provenance.json').read_text()).values():
  gen=a.get('generation')
  if not gen or gen['graph'] in graphfiles:continue
  graphfiles.add(gen['graph']);g=json.loads((HERE/gen['graph']).read_text());mapping=json.loads((HERE/gen['input_map']).read_text())
  names={Path(v).name for v in mapping.values()}
  for n in g.values():
   typ=n['class_type'];key='image' if typ=='LoadImage' else 'file' if typ=='LoadVideo' else None
   if key and n['inputs'][key] not in names:errors.append('unmapped generation input '+n['inputs'][key])
 if errors:raise SystemExit('\n'.join(errors))
 print(f'Verified {len(frozen["files"])} frozen files, {len(graphfiles)} source graphs, seven-shot timeline, and accepted S1E01 SHA256.')
if __name__=='__main__':main()
