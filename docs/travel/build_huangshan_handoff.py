"""Build Huangshan documentation indexes from saved evidence; no network or model calls."""
from pathlib import Path
import json,hashlib,copy
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'episodes/travel/huangshan'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp(frame):
 ms=round(frame/24*1000);return f'{ms//60000:02}:{ms//1000%60:02}.{ms%1000:03}'
def build_v4(current):
 """Explicit V4 delta over saved V3 provenance, never infer a new film mapping."""
 baseline=read('episodes/travel/huangshan/production-index-v3.json')
 job='jobs/1018-huangshan-pine-village-v4'
 patch=read(job+'/delivery.json');accepted=read(job+'/user-confirmation.json')
 assert accepted['status']=='user_accepted' and current['sha256']==accepted['sha256']==patch['sha256']
 assert baseline['final_sha256']==patch['source_sha256'] and baseline['frames']==3325
 assert current['frames']==3389 and patch['ending_native_selected_frames']==[24,240]
 idx=copy.deepcopy(baseline);idx.update(revision='v4',frames=3389,final_video='releases/huangshan/'+current['video'],final_sha256=current['sha256'],baseline_index='episodes/travel/huangshan/production-index-v3.json',acceptance=job+'/user-confirmation.json')
 lookup={x['id']:x for x in idx['shots']};pine=lookup['S03']
 pine['final_visual_kind']='dialogue_with_repaired_pine';pine['final_frames']=197
 pine['final_postproduction']={'source':job+'/delivery.json','method':'own H3 canopy + controlled lowest-needle wind + spatial composite excluding actors','native_canopy_source':read(job+'/canopy-result.json'),'layered_wind':read(job+'/layered-wind.json'),'actor_performance':'original S03 retained; no new mouth/body animation','new_fullframe_native_take':False}
 tail=lookup['S22'];old=copy.deepcopy(tail);native=read(job+'/ending-result.json');master=read(job+'/evidence/village-master-v2-result.json')
 tail.update(previous_shot=old,source_scene_id='village-walk-ending',final_visual_kind='silent_village_walk',end_frame_exclusive=3389,end_seconds=3389/24,timecode=[stamp(3173),stamp(3389)],native_frames=240,final_frames=216,native_selected_frames=[24,240],source_native_asset_id=native['id'],source_native_sha256=native['sha256'],remote_native_path=native['path'],master_id=master['id'],job_id=native['job_id'],seed=native['seed'],prompt_id=native['prompt_id'],voice_wave_path=None,voice_wave_sha256=None,final_postproduction={'source':job+'/delivery.json','trim_native_head_frames':24,'reason':'discard first1s with silent mouth articulation; retain grounded turn and walk','audio':'copy original full prefix through frame3173; stretch only existing silent music/ambience tail to9s','new_tts_requests':0})
 idx['historical_master_replaced']=next(x for x in idx['masters'] if x['id']==old['master_id'])
 idx['masters']=[x for x in idx['masters'] if x['id']!=old['master_id']]
 idx['masters'].append({'scene_id':'village-walk-ending','id':master['id'],'sha256':master['sha256'],'remote_path':master['path'],'local_matching_paths':[job+'/village-master-v2.png'],'job_id':master['job_id'],'seed':master['seed'],'prompt_id':master['prompt_id'],'generator_or_derivation':master['generator'],'references':master['references'],'note':'new V4 Qwen reference image; historical pending overridden by full-film acceptance'})
 idx['sources_sha256'].update({p:sha(ROOT/p) for p in ['episodes/travel/huangshan/production-index-v3.json',job+'/delivery.json',job+'/user-confirmation.json',job+'/ending-result.json',job+'/canopy-result.json',job+'/evidence/village-master-v2-result.json',job+'/layered-wind.json',job+'/evidence/native-job-evidence.tar.gz']})
 idx['warnings']=[x.replace('Final V3 release is local','Final V4 release is local') for x in idx['warnings']]
 idx['warnings'].append('server-source-index.json/server-integrity.json cover the V3 baseline only; V4 sources are explicitly added in S03/S22 and sources_sha256. No new live workbench readback performed.')
 (OUT/'production-index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
 md=(OUT/'final-script-v3.md').read_text()
 md=md.replace('2026-10-18，依据已交付成片及真实原声窗口生成；','2026-10-18，V4获用户认可；23句原声与时刻沿用V3，')
 md=md.replace('pine-medium · 角色对白','pine-medium · 原角色对白；动态树冠局部修复',1)
 md=md.replace('| S22 | 02:12.208–02:18.542 | hot-spring-ending · 温泉远景收尾；无对白 | `a_c90408fa1df84acf` |',f'| S22 | 02:12.208–02:21.208 | village-walk-ending · 并肩进村，缓慢拉远；无对白 | `{native["id"]}`；选第24–239帧 |')
 md+='\nV4迎客松分层修复、9秒温馨收尾及用户验收见[认可配方](../../../recipes/huangshan-pine-village-v1/README.md)。原生来源与最终后期分别记录，S22不再使用旧温泉原片；其他23句对白时刻不动。\n'
 (OUT/'final-script.md').write_text(md)
 print('Built accepted V4 index:20 shots,23 unchanged voice lines,3389frames; explicit S03/S22 provenance.')
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 current=read('releases/huangshan/current.json')
 if current.get('revision')=='v4':
  build_v4(current);return
 current=read('releases/huangshan/current.json');release=ROOT/'releases/huangshan'/current['manifest'];manifest=json.loads(release.read_text());snapshot=read('jobs/1017-huangshan-quadruped-v2/snapshot.json');audit=read('jobs/1017-huangshan-quadruped-v2/selection-audit.json');server=read('episodes/travel/huangshan/server-source-index.json');integrity=read('episodes/travel/huangshan/server-integrity.json');patch=read('jobs/1018-huangshan-silent-cloud-v3/delivery.json')
 assert manifest['sha256']==patch['sha256'],'A new release requires a new provenance mapping; do not mix this V3 edit with another final film.'
 assert not server['errors'] and integrity['all_match'];assert len(audit['rows'])==20
 names={'xiaosuda':'Soda / 小苏打','mianyang-jiejie':'Angela / 露露姐姐'};selected={x['shot']:x for x in audit['rows']};cursor=48;shots=[];dialogue=[]
 for sh in snapshot['board']['shots']:
  row=selected[sh['id']];a=server['takes'][row['asset']];assert a['sha256']==row['video_sha256'];assert a['master_id']==snapshot['scene_masters'][sh['scene_id']]
  end=cursor+row['frames'];sid=sh['id'];kind='dialogue' if sh['dialogue_ids'] else 'silent_reaction';visible=sh.get('onscreen_character_ids',sh['character_ids']);off=sh.get('offscreen_speaker_ids',[]);treatment=None
  if sid=='S05':kind='offscreen_voiceover_insert'
  if sid in ['S18','S21']:kind='prop_detail'
  if sid=='S22':kind='silent_scenic_with_back_views'
  if sid=='S11':
   assert [cursor,end]==patch['reframed_frames'];kind='silent_cloud_cutaway';visible=[];treatment={'source':'jobs/1018-huangshan-silent-cloud-v3/delivery.json','crop_source_pixels':patch['crop_source_pixels'],'coordinate_space':[1080,1932],'crop_format':'x,y,width,height','nature_motion':'existing native cloud motion; no new model call','raw_uncropped_take_rejected_for':'silent mouth motion at62-66s','final_entry_is_cut':True}
  entry={'id':sid,'source_scene_id':sh['scene_id'],'final_visual_kind':kind,'start_frame':cursor,'end_frame_exclusive':end,'start_seconds':cursor/24,'end_seconds':end/24,'timecode':[stamp(cursor),stamp(end)],'native_frames':row['frames'],'native_continuation':sh['continuation'],'native_context_dependency':row['dependency'],'final_onscreen_character_ids':visible,'offscreen_speaker_ids':off,'dialogue_ids':sh['dialogue_ids'],'source_native_asset_id':row['asset'],'source_native_sha256':row['video_sha256'],'remote_native_path':a['path'],'master_id':row['master_id'],'job_id':a.get('job_id'),'seed':row['seed'],'prompt_id':row['prompt_id'],'voice_wave_path':a['audio']['wave'],'voice_wave_sha256':row['voice_wave_sha256'],'final_postproduction':treatment}
  shots.append(entry)
  for turn in a['audio']['turns']:
   dialogue.append({'id':turn['id'],'shot_id':sid,'speaker_id':turn['speaker_id'],'speaker_name':names[turn['speaker_id']],'text':turn['text'],'start_seconds':round(cursor/24+turn['start'],6),'end_seconds':round(cursor/24+turn['end'],6),'offscreen':turn['speaker_id'] in off})
  cursor=end
 assert cursor==3325 and len(dialogue)==23 and len({x['id'] for x in dialogue})==23
 # Match actual master bytes to available local files, never choose by similar filename.
 candidates=[]
 for folder in ['jobs/1017-huangshan-fur-batch-v1/masters','jobs/1017-huangshan-quadruped-v1/masters','jobs/1017-huangshan-full-film-v1/guides']:
  candidates+=list((ROOT/folder).glob('*.png'))
 candidates+=[ROOT/'jobs/1017-huangshan-quadruped-v1/pine-medium-local-v2.png']
 byhash={}
 for p in candidates:
  if p.is_file():byhash.setdefault(sha(p),[]).append(str(p.relative_to(ROOT)))
 masters=[]
 for aid,a in sorted(server['masters'].items()):
  jid=a.get('job_id');job=server['jobs'].get(jid,{});receipt=job.get('evidence',{}).get('scene-receipt.json',{}).get('data',{})
  masters.append({'scene_id':a['scene_id'],'id':aid,'sha256':a['sha256'],'remote_path':a['path'],'local_matching_paths':byhash.get(a['sha256'],[]),'job_id':jid,'seed':a.get('seed'),'source_seed':a.get('source_seed'),'prompt_id':receipt.get('prompt_id'),'generator_or_derivation':a.get('generator',a.get('derivation')),'source_master':a.get('source_master'),'note':'Empty local_matching_paths means fetch this exact remote asset; do not substitute an older similarly named image.'})
 refs=[]
 for f in ['jobs/1016-huangshan-pilot-v1/references/manifest.json','jobs/1016-huangshan-sequence-v2/references/manifest.json']:
  for source in read(f):
   a=dict(source);path=Path(a['local_path']);path=path if str(path).startswith('jobs/') else Path(f).parent.parent/path;a['project_local_path']=str(path);a['source_manifest']=f;a['local_exists']=(ROOT/path).is_file();a['local_sha256_matches_record']=a['local_exists'] and sha(ROOT/path)==a['sha256'];a['rights_metadata_status']='Imported from 2026-10-16 reference records; not revalidated online by this documentation pass';refs.append(a)
 (OUT/'references-index.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n')
 sources=['jobs/1017-huangshan-quadruped-v2/snapshot.json','jobs/1017-huangshan-quadruped-v2/selection-audit.json','jobs/1018-huangshan-silent-cloud-v3/delivery.json','episodes/travel/huangshan/server-source-index.json','episodes/travel/huangshan/server-integrity.json','episodes/travel/huangshan/references-index.json']
 index={'kind':'huangshan_final_handoff_index','date':'2026-10-18','series':'Hi, Soda!','branch':'环游世界 / independent travel films','final_current':'releases/huangshan/current.json','final_video':str((release.parent/manifest['video']).relative_to(ROOT)),'final_sha256':manifest['sha256'],'frames':3325,'fps':24,'op_frames':48,'dialogue_language':'Chinese; this pilot does not freeze future episode language','shots':shots,'dialogue':dialogue,'masters':masters,'sources_sha256':{p:sha(ROOT/p) for p in sources},'live_project_snapshot':server['live_project_readback'],'warnings':['Do not use old story drafts or raw S11 as the final edit.','Sea-of-clouds current master is a_07f29c00826a4dd4; a_cbdd23c0f5dc4fdb has an extra crown ear.','Historical jobs contain fixed IDs; this index is not a GPU launch plan.','Final V3 release is local; live workbench readback has no adopted_takes or final_asset.','Remote media evidence was exported and31 asset files rehashed read-only; most raw clips, WAVs and tail PNGs remain remote.']}
 (OUT/'production-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
 md=['# 黄山最终剪辑与对白','', '2026-10-18，依据已交付成片及真实原声窗口生成；以正式 release 为准。旧 V1 的约三分钟段落时长及挥爪动作不再适用。','','正式片头：00:00.000–00:02.000，Hi, Soda!，无副标题。','', '| 镜头 | 成片时间 | 最终画面 / 说话方式 | 原生来源 |','|---|---|---|---|']
 labels={'dialogue':'角色对白','silent_reaction':'静默动作','offscreen_voiceover_insert':'迎客松枝条近景；Angela画外音','silent_cloud_cutaway':'纯云海近景；无角色、无对白','prop_detail':'手账/小爪特写；无对白','silent_scenic_with_back_views':'温泉远景收尾；无对白'}
 for x in shots:md.append(f'| {x["id"]} | {x["timecode"][0]}–{x["timecode"][1]} | {x["source_scene_id"]} · {labels[x["final_visual_kind"]]} | `{x["source_native_asset_id"]}` |')
 md+=['','镜头编号沿用生产历史，因此没有 S02/S04，不是漏片。共20个正文窗口，23句对白；最终 S11 是原视频后期取景，不能直接用未裁切的 S11 原片重拼。','','## 实际逐句原声','']
 for x in dialogue:
  md.append(f'- **{x["id"]} · {x["speaker_name"]}'+('（画外音）' if x['offscreen'] else '')+f' · {x["start_seconds"]:.3f}–{x["end_seconds"]:.3f}s**：{x["text"]}')
 md+=['','所有原声均为已有文件复用。具体WAV路径、SHA、实际任务/种子/prompt_id及主图见[production-index.json](production-index.json)；完整只读远端证据见[server-source-index.json](server-source-index.json)。','', 'S13的d16、d17均由Soda说；S11没有对白。照片、图画书和旅行手账各自按最终机位图与成片核对，不能把它们合并为一个道具。','']
 (OUT/'final-script.md').write_text('\n'.join(md))
 print(f'Built final index: {len(shots)} shots, {len(dialogue)} original lines, {len(masters)} used masters; {cursor}frames.')
if __name__=='__main__':main()
