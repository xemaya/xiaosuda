"""Read-only production bible. Character IDs, visual style and voices are server-owned."""
from pathlib import Path
import hashlib,json,os
MAX_EPISODE_SECONDS=300
MAX_SHOTS=150
PRACTICE_GAP_FRAMES=21
PULL_DOWN_FRAMES=8
SERIES={'title':'Hi, Soda!','bible_version':'2026-10-16-v1','format':'少儿英语情景剧','max_seconds':MAX_EPISODE_SECONDS,'structure':'由生活事件、角色互动和行动推动，可分部分；不强制讲解或练习环节。','family':'Soda、Jacky、Angela、Dad、Mom 是跨物种家庭；Mimi 与栗子是朋友。','mimi_intro':'Mimi 在公园初遇后逐渐成为朋友，初登场前不默认相识。','practice':'Practice time! 仅在剧本确有练习环节时选用。','cinematography':'安排全景交代环境与背景活动，特写强调表情；场景随剧情和台词变化，北方使用冰雪场景。换景别和地点分别准备主图。','idle':'Jacky喜欢单簧管、足球、搭乐高；Angela喜欢看书、编织。不说话时可做自己的事，被介绍时自然回应。','reference':'How are you? 为技术原点，不约束新剧集内容和编号。'}
PROJECT=Path(os.environ.get('SODA_PROJECT',str(Path(__file__).resolve().parents[1])))
STYLE_ID='soda-plush-v14'
STYLE='Original cute chibi 3D plush toy mascots, dense fine soft fibers, rounded big-head short-limb proportions, tactile fleece and knitted cloth, warm ivory and cornflower-blue/golden-yellow palette, soft warm window light, gentle depth of field, physical grounded poses. Preserve the supplied character-sheet identity and outfit exactly; never render a sheet, chart, labels, text, watermark, extra actors or extra limbs inside a scene. One clean full-frame cinematic portrait composition, 768x1376, fixed camera for dialogue.'
CHARACTERS=[
 dict(id='xiaosuda',name='小苏打',english_name='Soda',role='主角 · 乐观贪吃的弟弟',species='阿拉斯加犬',height_cm=35,scale=1.0,sheet='sheets/xiaosuda.png',color='#6884a5',voice_id='Cute_Elf',pitch=0,aliases=['Soda','小苏打','小狗','苏打','Baking Soda'],anchor='Black-and-white Alaskan malamute plush puppy, dark gray-black back/head/ears, white face mask/muzzle/chest/belly/paws, pink inner ears and rosy cheeks, black nose, warm brown round eyes, large fluffy curled white-tipped tail, small brown backpack. Warm playful personality.'),
 dict(id='mengji-gege',name='奇奇',english_name='Jacky',role='哥哥 · 喜欢单簧管、足球和搭乐高积木',hobbies=['单簧管','足球','搭乐高积木'],idle_actions=['安静搭积木','轻轻整理足球','仅在剧情安排时吹单簧管'],species='小鸡',height_cm=42,scale=1.2,sheet='sheets/mengji-gege.png',color='#dba34d',voice_id='chunzhen_xuedi',pitch=1,aliases=['Jacky','奇奇','萌鸡','萌鸡哥哥','小鸡','鸡哥哥','Chick','Mengji'],anchor='Round warm-yellow plush chick, pale cream belly, orange-yellow beak and feet, orange-red comb, rosy cheeks, dark-brown bright eyes, blue hoodie with a WHITE C on the chest, soft small wings and fluffy tail. Slightly taller than Soda, about 1.2 times his height.'),
 dict(id='mianyang-jiejie',name='露露',english_name='Angela',role='姐姐 · 喜欢看书和编织',hobbies=['看书','编织'],idle_actions=['坐着读书并偶尔翻页','整理毛线或安静编织'],species='绵羊',height_cm=48,scale=1.37,sheet='sheets/mianyang-jiejie.png',color='#c9909a',voice_id='Chinese (Mandarin)_Soft_Girl',pitch=2,aliases=['Angela','露露','绵羊姐姐','羊姐姐','小羊','绵羊'],anchor='Cream-white curly-wool plush sheep, long drooping pale-pink inner ears, light-brown horns/hooves, rosy cheeks, gentle brown eyes, pink sweater dress, pink bow and small backpack. About 1.37 times Soda height.'),
 dict(id='long-mama',name='妈妈',english_name='Mom',role='温柔守护 · 优雅又强大',species='东方龙',height_cm=65,scale=1.86,sheet='sheets/long-mama.png',color='#ba9d62',voice_id='Chinese (Mandarin)_Sweet_Lady',pitch=0,aliases=['Mom','妈妈','龙妈妈'],anchor='Friendly original Eastern dragon plush mother, gold-and-white scales, warm golden horns/mane, soft whiskers, pale-pink cheeks and inner ears, coral-pink nose, pink flower hair accessory, fluffy tail, deep-brown eyes with eyelashes. About 1.86 times Soda height, same chibi scale; never a giant.'),
 dict(id='niu-baba',name='爸爸',english_name='Dad',role='稳重可靠 · 温暖幽默',species='黄牛',height_cm=70,scale=2.0,sheet='sheets/niu-baba.png',color='#a27a5f',voice_id='English_Trustworthy_Man',pitch=-2,aliases=['Dad','爸爸','牛爸爸'],anchor='Warm brown-yellow plush ox father, creamy pale muzzle/fur accents, curved dark-brown horns, fluffy forelock, warm friendly eyes, pink-brown inner ears/nose, gray hoodie and shorts, swishing ox tail. About twice Soda height, same chibi family scale; never a giant.'),
 dict(id='xiaomi-mimi',name='小咪',english_name='Mimi',role='公园偶遇的新朋友 · 好奇独立，熟悉后温柔亲近',species='三花短毛家猫',pronouns='she/her',height_cm=33,scale=.94,sheet='sheets/xiaomi-mimi.png',color='#c88b5f',voice_id=None,pitch=None,voice_direction='清亮、活泼、语速稍快的童声，待试听定稿',aliases=['Mimi','小咪','咪咪','Kitty','小猫咪','猫咪'],anchor='Original female calico short-haired plush kitten, about one year old, she/her, creamy-white base with warm orange and dark gray-brown patches, large amber-brown eyes NEVER green, pink nose/inner ears/paw pads, fluffy tail, brown collar with a golden bell. No extra outfit unless explicitly required by the story. Natural standing height 33cm to top of head excluding ears, about .94 times Soda height. Curious, lively, independent and a little proud; gentle after getting acquainted. Meets Soda at the park for the first time, gradually becomes friends. Voice is not yet approved.'),
 dict(id='hualishu-tongxue',name='栗子',english_name='',role='花栗鼠同学 · 好奇的冒险搭子',species='花栗鼠',height_cm=30,scale=.86,sheet='sheets/hualishu-tongxue.png',color='#b77c50',voice_id=None,pitch=None,aliases=['栗子','花栗鼠','花栗鼠同学'],anchor='Original warm-brown chipmunk plush friend, creamy white cheeks and belly, dark-brown back stripes, orange-brown ears/cheeks, pink nose/inner ears, glossy dark eyes, gray-brown paws and large fluffy striped tail. About .86 times Soda height. Character sheet exists; voice is not yet approved.'),
]
SCENES=[
 dict(id='living-room',name='暖光客厅',description='窗边地毯、木色家具，技术样片固定机位',path='recipes/plush-dialogue-v14/assets/scene-master.png',cast_ids=['xiaosuda','mengji-gege'],direct_use=True,props=['地毯','沙发','窗户','书架']),
 dict(id='sofa-practice',name='沙发练习区',description='同一暖色客厅的沙发区，适合问答与击掌',path='recipes/ep01-v12/assets/practice-firstframe.png',cast_ids=['xiaosuda','mengji-gege'],direct_use=True,props=['地毯','沙发','窗户']),
 dict(id='snack-table',name='点心桌',description='餐厅点心桌，适合分享食物与日常对话',path='firstframes/xiaosuda+mengji-snack-table.png',cast_ids=['xiaosuda','mengji-gege'],direct_use=False,props=['点心','桌子']),
 dict(id='birthday',name='生日角落',description='傍晚生日蛋糕氛围',path='firstframes/xiaosuda+mengji-birthday.png',cast_ids=['xiaosuda','mengji-gege'],direct_use=False,props=['生日蛋糕']),
]
PACKAGING=[dict(id='op',name='Hi, Soda!',seconds=2,path='assets/op/hi-soda-motion/hi-soda-op-2s.mp4'),dict(id='practice',name='Practice time! · A',seconds=32/24,path='assets/intertitles/motion/a-paw-pop-preview.mp4')]

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def character(cid):
 item=next((c for c in CHARACTERS if c['id']==cid),None)
 if not item:raise ValueError('只能选择人物库中已有的角色')
 return item

def media_path(key):
 paths={c['id']:c['sheet'] for c in CHARACTERS}|{s['id']:s['path'] for s in SCENES}|{x['id']:x['path'] for x in PACKAGING}
 paths['series-bible']='docs/series-bible.md'
 paths['ep01']='releases/ep01/2026-10-15/Hi-Soda_EP01_How-Are-You.mp4'
 if key=='font':paths[key]='recipes/plush-dialogue-v14/assets/Alibaba-PuHuiTi-Regular.ttf'
 if key not in paths:raise ValueError('素材不存在')
 path=(PROJECT/paths[key]).resolve()
 if not path.is_relative_to(PROJECT.resolve()) or not path.is_file():raise ValueError('素材文件尚未同步')
 return path

def catalog():
 chars=[]
 for c in CHARACTERS:
  path=PROJECT/c['sheet'];chars.append({**c,'available':path.is_file(),'voice_ready':bool(c['voice_id']),'image_url':'api/catalog/media/'+c['id'],'sha256':digest(path) if path.is_file() else None})
 return {'series':SERIES,'style':{'id':STYLE_ID,'name':'暖光毛绒 3D','description':'固定角色设计、细密毛绒与针织材质、暖色自然光','prompt':STYLE,'locked':True,'fps':24,'width':768,'height':1376,'recipe_id':'plush-dialogue-v14'},'characters':chars,'scenes':[{**s,'image_url':'api/catalog/media/'+s['id'],'available':(PROJECT/s['path']).is_file()} for s in SCENES],'packaging':[{**x,'url':'api/catalog/media/'+x['id']} for x in PACKAGING],'reference_episode':{'title':'技术样片 · How are you?','url':'api/catalog/media/ep01','duration':38.299}}

def bible():return {'series':SERIES,'style_id':STYLE_ID,'style':STYLE,'characters':[{**{k:c[k] for k in ['id','name','english_name','role','aliases','anchor','scale','voice_id','pitch']},'hobbies':c.get('hobbies',[]),'idle_actions':c.get('idle_actions',[])} for c in CHARACTERS],'rules':['Use only supplied character IDs. Never invent a new actor, outfit or visual style.','Use canonical English names Soda, Jacky, Angela, Dad, Mom, Mimi. Old speaker aliases map to the same character IDs; normalize character names in spoken lines without rewriting other dialogue.','Respect the source script: no invented or dropped dialogue. Unmapped speaker names are unresolved, not permission for a new character.','Generate one canonical clean HD scene image per camera setup; never animate a character sheet.','One native continuous take up to 10 seconds; picture-only 22-frame context for continuation, from actually retained frames.','Speaker ownership and closed-mouth listener behavior must be reviewed; preserve requested gestures and ending actions.']}
