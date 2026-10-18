from pathlib import Path
import copy,json,hashlib,shutil
from workbench.store import Store,atomic_json
from workbench.domain import validate_setting,validate_board,episode_frames
s=Store('/data/app/huanghaibin/soda');pid='p_5e6ea50dd70a4026';folder=s.root/'batches'/'s1e01-review-v2';folder.mkdir(parents=True,exist_ok=True)
receipt=folder/'revision.json'
if receipt.exists():
 print(json.dumps(json.loads(receipt.read_text()),ensure_ascii=False));raise SystemExit(0)
p=s.project(pid);assert p['revision']==22 and p['board_version']=='v_a5053563ef83402d','Project edited in parallel; preserve it'
source=copy.deepcopy(p);atomic_json(folder/'source-project-v1.json',source)
new_image=Path('/tmp/soda-jacky-corner-v3-9460403c5a35.png');assert hashlib.sha256(new_image.read_bytes()).hexdigest()=='9460403c5a3537c0a62be4d1b60720f5b8093902c0973db2eed80b49283d2bd4'
setting=copy.deepcopy(p['setting']);board=copy.deepcopy(p['board'])
board['shots']=[x for x in board['shots'] if x['id'] not in ['S01','S04']]
for shot in board['shots']:
 if shot['id']=='S03':
  shot.update(seconds=6.5,dialogue_ids=['d2','d3'],continuation=False,dialogue_gap_seconds=.18,beat='介绍寒冷北方后立即奔跑，一次连续表演',action='Soda从原雪地主图开始，0.4–2.954秒介绍寒冷来处；说完 immediately 在约2.95秒开始向画面右侧跑几步，3.134–5.479秒说 and I can run super fast!，边跑边说，5.5–6.5秒平稳减速并转头看观众。不站着等两秒，不瞬移，不换机位。')
  shot['prompt_en']='A single continuous 6.5-second full-body snowy shot of the exact same black-and-white Alaskan plush puppy Soda with his small brown backpack. Fixed snowy environment and camera, original plush toy style. Only Soda appears. At 0.40–2.954s he speaks <d>[EN] I come from a very cold place,</d>. As soon as that phrase ends at 2.95s, push off immediately and run cheerfully a few steps toward screen right while remaining fully in frame. After a SHORT 0.18s speech gap, at 3.134–5.479s he speaks <d>[EN] and I can run super fast!</d> while running. Decelerate naturally during 5.5–6.5s. No two-second idle pause, no pose reset, no cut, no new clothing, no added characters or music. Original voice timing is authoritative.'
 if shot['id']=='S06':
  shot.update(beat='奇奇哥哥在同一景深里明显高于Soda',action='严格继承新主图同一地面及景深：左侧Jacky站着搭积木，右侧Soda自然站立。哥哥42cm，小苏打35cm，哥哥头顶保持约高20%，不可把哥哥缩小或让小狗在前景变大。Soda说话；Jacky喙全程闭合，搭好一块积木，被叫到时自然抬头回应，再继续。')
  shot['prompt_en']='Use the adopted corrected image as exact identity, scale, pose, depth and camera authority. Exactly one chick Jacky on screen left, one puppy Soda on screen right, both standing on the SAME floor plane at the SAME camera distance. Jacky is the older brother: 42cm versus Soda 35cm, visibly about 20 percent taller, including his head/comb. Preserve that size ratio on EVERY frame. Jacky wears his blue hoodie with white C, no backpack, and places a block at the low table; his beak remains CLOSED throughout. Soda has his small brown backpack and speaks the exact original line <d>[EN] This is my big brother, Jacky. He\'s a cheerful little chick.</d>. At his name Jacky may briefly look up and make a small wing greeting, then return to the blocks. Keep the room, low table, plush fibers and warm light fixed. No giant foreground puppy, no shrinking chick, no duplicated actors, no humans, no new costumes, no music.'
board['summary']='S1E01审片修订V2：片头后直接进入Soda特写，7段视频；北方介绍和奔跑合为一次连续表演，句间0.18秒；仅重拍雪地与哥哥镜头，其余表演和原配音复用。'
board['notes']=['去掉原S01家庭开场，保留2秒Hi, Soda!片头。','S03合并原d2/d3，句间0.18秒，说完寒冷来处立即跑；不剪掉尾巴后沿用旧上下文。','S06哥哥42cm、Soda35cm，同一景深和地面，不用透视把小狗显大。','字幕使用新安全宽度自动断行，中文和英文均保留完整。','全部旧配音原样复用；V1保留，V2仍待用户审片。']
setting['premise']='片头后直接进入Soda特写自我介绍。向下揭幕到北方雪地，介绍寒冷来处后马上开始跑，两句之间只停0.18秒，一次原生连续表演完成。回家后介绍哥哥姐姐；哥哥镜头采用同一地面与景深，42cm的Jacky明显比35cm的Soda高。姐姐和结尾使用既有表演，保留温暖家庭收尾。'
setting['logline']='Soda特写开场，在北方边介绍边奔跑，介绍比自己高的哥哥和温柔姐姐，最后一家靠近。'
for scene in setting['scenes']:
 if scene['id']=='jacky-corner':
  scene['setting']='同一暖光积木角中景，Jacky在左侧站着搭积木，Soda在右侧同一地面和景深自然站立。两人脚落同一地面基线，哥哥42cm、小苏打35cm，Jacky头顶约高20%，不可把小狗放在近处显大、把哥哥缩小。保留蓝外套白色C和Soda棕背包，哥哥没有背包。'
  scene['idle_actions']={'mengji-gege':'站在矮桌边搭积木，喙闭合，听到名字时短暂抬头自然回应。'}
setting['beats']=[{'summary':x['id']+' · '+x['beat'],'scene_id':x['scene_id']} for x in board['shots']]
setting['notes']=board['notes']
script='# S1E01 自我介绍 · 审片修订 V2\n\n'+ '\n'.join(setting['notes'])+'\n\n## 逐句对白（原配音不变）\n\n'+'\n\n'.join('Soda: '+l['text']+'\n'+l['translation'] for l in setting['dialogue'])
setting=validate_setting(setting,p['cast_ids']);board=validate_board(board,setting,p['packaging'])
p=s.update(pid,p['revision'],{'script':script,'setting':setting});p=s.accept(pid,p['revision'],'setting');atomic_json(folder/'revision-setting.json',p['setting'])
imports=s.root/'imports'/('s1e01-review-v2-'+p['setting_version']);imports.mkdir(parents=True,exist_ok=True)
masters={}
for scene in p['setting']['scenes']:
 old=s.asset(source['scene_masters'][scene['id']],pid);src=new_image if scene['id']=='jacky-corner' else Path(old['path']);dest=imports/(scene['id']+'.png')
 shutil.copy2(src,dest)
 a=s.add_asset(pid,'scene',dest,{'name':scene['name']+' · 审片修订V2','scene_id':scene['id'],'setting_version':p['setting_version'],'source_asset_id':old['id'],'source_setting_version':source['setting_version'],'revision_reason':'用户纠正哥哥透视和身高' if scene['id']=='jacky-corner' else '原图原样复用，未重生成','review':'working_master_for_requested_revision'})
 p=s.adopt(pid,p['revision'],a['id']);masters[scene['id']]=a['id']
p=s.update(pid,p['revision'],{'board':board});p=s.accept(pid,p['revision'],'board')
reused={}
for shot in board['shots']:
 if shot['id'] in ['S03','S06']:continue
 old=s.asset(source['adopted_takes'][shot['id']],pid);assert not old.get('context_dependency')
 dest=imports/(shot['id']+'-unchanged.mp4');shutil.copy2(old['path'],dest)
 metadata={k:copy.deepcopy(v) for k,v in old.items() if k not in ['id','project_id','created','url','sha256','path','kind']}
 metadata.update(name=shot['id']+' · 保留原表演',board_version=p['board_version'],master_id=masters[shot['scene_id']],source_asset_id=old['id'],source_board_version=old['board_version'],source_master_id=old['master_id'],reuse_reason='未修改视频或原配音，仅适配新剪辑版本')
 a=s.add_asset(pid,'take',dest,metadata);assert a['sha256']==old['sha256'];p=s.adopt(pid,p['revision'],a['id']);reused[shot['id']]=a['id']
result={'project_id':pid,'setting_version':p['setting_version'],'board_version':p['board_version'],'source_board_version':source['board_version'],'old_shoot_job_id':'j_5bb2c6045ec44148','remaining_shots':['S03','S06'],'jobs':{},'reused_takes':reused,'estimated_seconds':episode_frames(board['shots'],p['packaging'])/24,'ready':True}
atomic_json(receipt,result);atomic_json(folder/'reviewed-board-v2.json',board);print(json.dumps(result,ensure_ascii=False))
