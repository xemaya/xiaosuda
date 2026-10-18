"""Production contracts and validation. Provider output never expands the roster."""
import copy,json,hashlib,re,math
from .catalog import CHARACTERS,STYLE_ID,character,MAX_EPISODE_SECONDS,MAX_SHOTS,PRACTICE_GAP_FRAMES,PULL_DOWN_FRAMES
class Conflict(ValueError):pass
class NeedsAttention(RuntimeError):pass

def fingerprint(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def text(value,name,limit=12000):
 if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError(name+'不能为空或超过长度限制')
 return value.strip()
def cast_ids(values,allowed=None):
 if not isinstance(values,list) or len(values)>len(CHARACTERS):raise ValueError('角色列表无效')
 known={c['id'] for c in CHARACTERS};allowed=known if allowed is None else set(allowed)
 if not all(isinstance(v,str) for v in values) or len(values)!=len(set(values)) or any(c not in known or c not in allowed for c in values):raise ValueError('角色必须来自本工程人物库且不能重复')
 return values

def validate_setting(raw,selected):
 d=copy.deepcopy(raw);allowed=cast_ids(selected)
 if d.get('style_id',STYLE_ID)!=STYLE_ID:raise ValueError('画风固定，不能更换')
 d['style_id']=STYLE_ID
 for k in ['title','logline','premise']:d[k]=text(d.get(k),k,3000)
 cast=d.get('cast',[])
 if not cast:raise ValueError('至少需要一名库内角色')
 ids=cast_ids([c.get('character_id') for c in cast],allowed)
 for c in cast:c['story_role']=text(c.get('story_role'),'人物剧情定位',1200)
 scenes=d.get('scenes',[])
 if not isinstance(scenes,list) or not 1<=len(scenes)<=12:raise ValueError('场景数量应为1–12')
 sceneids=[]
 for i,s in enumerate(scenes):
  s['id']=s.get('id') or f'scene-{i+1}'
  if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',s['id']) or s['id'] in sceneids:raise ValueError('场景编号无效')
  s['framing']=s.get('framing','medium')
  if s['framing'] not in ['wide','medium','close_up']:raise ValueError('景别只能是全景、中景或特写')
  sceneids.append(s['id']);s['name']=text(s.get('name'),'场景名',100);s['setting']=text(s.get('setting'),'场景设定',4000)
  s['cast_ids']=cast_ids(s.get('cast_ids',[]),ids)
  if not s['cast_ids']:raise ValueError('每个场景都需要明确出镜角色')
  activities=s.get('idle_actions',{})
  if not isinstance(activities,dict) or any(cid not in s['cast_ids'] for cid in activities):raise ValueError('背景活动只能安排给当前场景里的角色')
  s['idle_actions']={cid:text(action,'背景活动',1000) for cid,action in activities.items()}
  s['lighting']=str(s.get('lighting','暖色窗光'))[:500]
  s['props']=[str(p)[:200] for p in s.get('props',[])][:12]
  s['reference_scene_id']=s.get('reference_scene_id') or None
  if s['reference_scene_id'] and s['reference_scene_id'] not in ['living-room','sofa-practice','snack-table','birthday']:raise ValueError('参考场景不存在')
 dialogue=d.get('dialogue',[])
 if not isinstance(dialogue,list) or len(dialogue)>80:raise ValueError('对白数量无效')
 lineids=[]
 for i,line in enumerate(dialogue):
  line['id']=line.get('id') or f'd{i+1}'
  if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',line['id']) or line['id'] in lineids:raise ValueError('对白编号重复或无效')
  lineids.append(line['id'])
  if line.get('speaker_id') not in ids:raise ValueError('对白说话人不在本片演员表')
  line['text']=text(line.get('text'),'对白',1600);line['translation']=str(line.get('translation',''))[:1600]
  line['emotion']=str(line.get('emotion','自然'))[:100]
  line['speed']=float(line.get('speed',1))
  if not .85<=line['speed']<=1.1:raise ValueError('配音速度只能在已验证范围内')
 d['beats']=[{'summary':text(b.get('summary'),'剧情节拍',1500),'scene_id':b.get('scene_id')} for b in d.get('beats',[])]
 if not d['beats'] or any(b['scene_id'] not in sceneids for b in d['beats']):raise ValueError('剧情节拍需要绑定已有场景')
 d['notes']=[str(x)[:1500] for x in d.get('notes',[])][:20]
 d['unresolved_characters']=[str(x)[:100] for x in d.get('unresolved_characters',[])][:12]
 return d

def validate_board(raw,setting,packaging=None):
 d=copy.deepcopy(raw);shots=d.get('shots',[])
 if not isinstance(shots,list) or not 1<=len(shots)<=MAX_SHOTS:raise ValueError(f'每部作品需要1–{MAX_SHOTS}个镜头')
 scenes={s['id']:s for s in setting['scenes']};lines={x['id']:x for x in setting['dialogue']};used=[];ids=[];previous=None
 for i,s in enumerate(shots):
  s['id']=s.get('id') or f'S{i+1:02}'
  if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',s['id']) or s['id'] in ids:raise ValueError('镜头编号重复或无效')
  ids.append(s['id'])
  if s.get('scene_id') not in scenes:raise ValueError('镜头必须使用已确认场景')
  scene=scenes[s['scene_id']];s['framing']=s.get('framing',scene.get('framing','medium'))
  if s['framing']!=scene.get('framing','medium'):raise ValueError('景别变化需要对应的新机位主图，不能沿用旧机位')
  s['character_ids']=cast_ids(s.get('character_ids',scene['cast_ids']),scene['cast_ids'])
  if not s['character_ids']:raise ValueError('镜头出镜人物不能为空')
  s['dialogue_gap_seconds']=float(s.get('dialogue_gap_seconds',.35))
  if not math.isfinite(s['dialogue_gap_seconds']) or not .12<=s['dialogue_gap_seconds']<=.8:raise ValueError('对白句间停顿应为0.12–0.8秒')
  s['seconds']=float(s.get('seconds',5))
  if not math.isfinite(s['seconds']) or not 2<=s['seconds']<=10:raise ValueError('单次连续拍摄必须为2–10秒')
  for k in ['beat','action','camera']:s[k]=text(s.get(k),k,4000)
  s['dialogue_ids']=s.get('dialogue_ids',[])
  if not isinstance(s['dialogue_ids'],list) or any(x not in lines for x in s['dialogue_ids']):raise ValueError('镜头引用了不存在的对白')
  if any(lines[x]['speaker_id'] not in s['character_ids'] for x in s['dialogue_ids']):raise ValueError('说话者必须在镜头的出镜人物中')
  used+=s['dialogue_ids'];s['continuation']=bool(s.get('continuation',False))
  if s['continuation'] and (not previous or previous['scene_id']!=s['scene_id'] or previous['character_ids']!=s['character_ids']):raise ValueError('连续镜头必须继承同一场景、同组角色')
  s['transition']=s.get('transition','cut')
  if s['transition'] not in ['cut','practice_time','pull_down']:raise ValueError('只使用直接剪接、下拉换景或已选A幕间')
  if i==0 and s['transition']!='cut':raise ValueError('首镜前无需转场')
  if s['continuation'] and s['transition']!='cut':raise ValueError('连续表演内不能插入幕间')
  s['prompt_en']=str(s.get('prompt_en',''))[:14000]
  previous=s
 if sorted(used)!=sorted(lines):raise ValueError('分镜必须将每句对白恰好安排一次，不能漏句或重复')
 after=(packaging or {}).get('op_after_shot')
 if after and after not in ids:raise ValueError('片头位置必须对应已有镜头编号')
 if episode_frames(shots,packaging)>MAX_EPISODE_SECONDS*24:raise ValueError('单集含片头和幕间总时长不能超过5分钟')
 d['summary']=str(d.get('summary',''))[:2000];d['notes']=[str(x)[:1500] for x in d.get('notes',[])][:20]
 return d

def episode_frames(shots,packaging=None):
 return sum(math.ceil(s['seconds']*24) for s in shots)+(48 if (packaging or {}).get('op',True) else 0)+sum(PRACTICE_GAP_FRAMES for s in shots if s.get('transition')=='practice_time')-sum(PULL_DOWN_FRAMES for s in shots if s.get('transition')=='pull_down')

def normalize_packaging(value):
 if not isinstance(value,dict) or set(value)-{'op','op_after_shot'}:raise ValueError('片头配置无效')
 result={'op':bool(value.get('op',True))}
 after=value.get('op_after_shot')
 if after:
  if not result['op'] or not isinstance(after,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',after):raise ValueError('片头位置无效')
  result['op_after_shot']=after
 return result
