"""Register review candidates only. Never adopts a master/take/final."""
import copy,json,shutil
from pathlib import Path
from workbench.store import Store,atomic_json
from workbench.providers import Production
from workbench.catalog import digest
s=Store('/data/app/huanghaibin/soda');pid='p_5e6ea50dd70a4026';root=s.root/'batches/s1e01-generation-review';p=s.project(pid)
source=json.loads((root/'source-project.json').read_text())
assert p['revision']==source['revision']==84 and p['board_version']==source['board_version'],'Project changed, retain candidates without touching current state'
prod=Production(s);result={}
master=s.add_asset(pid,'scene',root/'S07-clean-start.png',{'name':'姐姐段 · 清除源图蓝袖口，保留侧身起点','scene_id':'angela-reading','setting_version':p['setting_version'],'source_asset_id':p['scene_masters']['angela-reading'],'review':'candidate','operator_batch':'s1e01-generation-review','reason':'原始首帧的蓝布已被实际API图和文件哈希证实，纠正后用于全段新生成；未修改视频像素'})
result['clean_start_master']=master['id']
for sid,variant,aid in [('S07','clean-start-guide','a_234de381fb284651'),('S08','guide-only','a_793b8839a2a64b93')]:
 folder=root/(sid+'-'+variant);receipt=json.loads((folder/'receipt.json').read_text());assert receipt['phase']=='completed' and digest(receipt['output'])==receipt['sha256']
 original=s.asset(aid,pid);g=json.loads((folder/'graph.json').read_text());h=json.loads((folder/'history.json').read_text());tailnode=next(k for k,n in g.items() if n['class_type']=='SaveImage');tails=[]
 for i,file in enumerate(prod.output_files(h,tailnode)):
  target=folder/f'tail-{i:02}.png'
  if not target.exists():shutil.copy2(file,target)
  tails.append(str(target))
 assert len(tails)==22
 meta={k:copy.deepcopy(v) for k,v in original.items() if k not in ['id','project_id','path','url','kind','sha256','created','job_id']}
 experiment=json.loads((folder/'experiment.json').read_text())
 meta.update(name=sid+' · '+('干净首帧＋转身关键帧重拍' if sid=='S07' else '放书＋全身关键帧重拍'),master_id=master['id'] if sid=='S07' else original['master_id'],source_asset_id=aid,source_job_id=experiment['source_job'],operator_batch='s1e01-generation-review',prompt_id=receipt['prompt_id'],graph_path=str(folder/'graph.json'),guide_images=experiment['guides'],tail_frames=tails,review='candidate',human_acceptance='pending',pixel_postprocessing=False,source_audio_unchanged=True)
 asset=s.add_asset(pid,'take',receipt['output'],meta);result[sid]={'asset_id':asset['id'],'url':'https://soda.buplayground.cn/'+asset['url'],'sha256':asset['sha256']}
after=s.project(pid)
for key in ['revision','scene_masters','adopted_takes','final_asset','board_version','setting_version']:assert after[key]==source[key],key
result.update(project_id=pid,revision_unchanged=after['revision'],current_selections_unchanged=True,human_acceptance='pending')
atomic_json(root/'candidate-assets.json',result);print(json.dumps(result,ensure_ascii=False))
