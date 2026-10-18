"""Read-only local handoff verification. No network, GPU, TTS or project mutation."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads((ROOT/p).read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 current=read('releases/huangshan/current.json');folder=ROOT/'releases/huangshan';manifest=json.loads((folder/current['manifest']).read_text());release=folder/current['video'];assert digest(release)==current['sha256']==manifest['sha256'];v4=current.get('revision')=='v4';frames=3389 if v4 else 3325;assert current['frames']==manifest['frames']==frames and current['fps']==24
 for name,expected in manifest['evidence_sha256'].items():assert digest((folder/current['manifest']).parent/name)==expected,name
 idx=read('episodes/travel/huangshan/production-index.json');assert idx['final_sha256']==current['sha256'] and ROOT/idx['final_video']==release
 for name,expected in idx['sources_sha256'].items():assert digest(ROOT/name)==expected,name
 shots=idx['shots'];assert len(shots)==20;cursor=48
 for sh in shots:assert sh['start_frame']==cursor;assert sh['end_frame_exclusive']-cursor==sh.get('final_frames',sh['native_frames']);cursor=sh['end_frame_exclusive']
 assert cursor==idx['frames']==frames
 assert len(idx['dialogue'])==23 and len({x['id'] for x in idx['dialogue']})==23
 subtitle=folder/current['subtitles'];blocks=[x.splitlines() for x in subtitle.read_text().strip().split('\n\n') if x.strip()];assert len(blocks)==23
 for cue,line in zip(blocks,idx['dialogue']):assert ''.join(cue[2:])==line['text'],line['id']
 assert sorted(x for sh in shots for x in sh['dialogue_ids'])==sorted(x['id'] for x in idx['dialogue'])
 lookup={x['id']:x for x in shots};assert lookup['S05']['final_onscreen_character_ids']==[] and lookup['S05']['offscreen_speaker_ids']==['mianyang-jiejie'];assert not lookup['S06']['native_continuation']
 assert lookup['S11']['final_visual_kind']=='silent_cloud_cutaway' and lookup['S11']['final_onscreen_character_ids']==[] and lookup['S11']['dialogue_ids']==[];assert [lookup['S11']['start_frame'],lookup['S11']['end_frame_exclusive']]==[1472,1624]
 assert all(x['speaker_id']=='xiaosuda' for x in idx['dialogue'] if x['id'] in ['d16','d17'])
 if v4:
  accepted=read('jobs/1018-huangshan-pine-village-v4/user-confirmation.json');assert accepted['status']=='user_accepted' and accepted['sha256']==current['sha256']
  assert lookup['S03']['final_visual_kind']=='dialogue_with_repaired_pine' and lookup['S03']['final_postproduction']['new_fullframe_native_take'] is False
  assert lookup['S22']['final_visual_kind']=='silent_village_walk' and lookup['S22']['native_selected_frames']==[24,240] and lookup['S22']['final_frames']==216
  base=read('episodes/travel/huangshan/production-index-v3.json');assert idx['dialogue']==base['dialogue']
  for a in idx['masters']:
   for path in a['local_matching_paths']:assert digest(ROOT/path)==a['sha256'],path
 masters={x['scene_id']:x for x in idx['masters']};assert masters['sea-of-clouds']['id']=='a_07f29c00826a4dd4';assert all(x['id']!='a_cbdd23c0f5dc4fdb' for x in idx['masters'])
 server=read('episodes/travel/huangshan/server-source-index.json');integrity=read('episodes/travel/huangshan/server-integrity.json');assert not server['errors'] and len(server['masters'])==11 and len(server['takes'])==20;assert integrity['all_match'] and len(integrity['assets'])==31
 hashes={x['id']:x['actual_sha256'] for x in integrity['assets']}
 for a in list(server['masters'].values())+list(server['takes'].values()):assert hashes[a['id']]==a['sha256']
 for ref in read('episodes/travel/huangshan/references-index.json'):
  p=ROOT/ref['project_local_path'];assert p.exists() and digest(p)==ref['sha256'],ref['id']
 print(f'Verified final SHA and frozen release evidence;20 shots /23 original lines /{frames} frames;S05/S06/S11 and current revision overrides;11 exact masters;6 local reference photos.')
 print('31 remote media hashes match the saved read-only export. This run did not reconnect or rehash remote files, verify online licensing, or replace visual review.')
if __name__=='__main__':main()
