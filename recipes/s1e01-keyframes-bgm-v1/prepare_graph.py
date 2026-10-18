"""Stage archived inputs and emit a selected graph. Never submits a GPU job."""
from pathlib import Path
import argparse,hashlib,json,shutil
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('asset_id');p.add_argument('--comfy-input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
sources=json.loads((HERE/'accepted/asset-provenance.json').read_text());record=sources[a.asset_id];gen=record.get('generation')
if record.get('metadata',{}).get('edit'):raise SystemExit('This take is an edit of multiple native sources. Read metadata.edit.source_ranges and prepare each source_asset_id separately; its inherited graph cannot reproduce the full edited take.')
if not gen:raise SystemExit('This is an edited/reused take; inspect its source_asset_ids and edit ranges first.')
mapping=json.loads((HERE/gen['input_map']).read_text());a.comfy_input.mkdir(parents=True,exist_ok=True)
for name in mapping.values():
 source=HERE/name;dest=a.comfy_input/Path(name).name
 if dest.exists():
  if hashlib.sha256(dest.read_bytes()).digest()!=hashlib.sha256(source.read_bytes()).digest():raise SystemExit('Existing different input: '+str(dest))
 else:shutil.copy2(source,dest)
g=json.loads((HERE/gen['graph']).read_text())
for n in g.values():
 if n['class_type'] in ['SaveImage','SaveVideo']:n['inputs']['filename_prefix']='soda/s1e01-replay/'+a.asset_id+'/'+Path(n['inputs']['filename_prefix']).name
with a.out.open('x') as f:json.dump(g,f,ensure_ascii=False,indent=2)
print('Inputs staged; graph emitted. Check the shared queue and persist a NEW prompt_id before any intentional submission.')
