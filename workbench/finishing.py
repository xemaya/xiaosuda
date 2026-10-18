"""Local deterministic finishing: original voices, CFR24, fixed OP/A assets."""
from pathlib import Path
import json,math,shutil,subprocess,wave,re
from functools import lru_cache
from PIL import ImageFont
import numpy as np
from .catalog import PROJECT,digest,MAX_EPISODE_SECONDS,PRACTICE_GAP_FRAMES,PULL_DOWN_FRAMES
from .domain import NeedsAttention
from .providers import run,probe
from .store import atomic_json

def time_ass(t):
 n=round(t*100);h,r=divmod(n,360000);m,r=divmod(r,6000);s,c=divmod(r,100);return f'{h}:{m:02}:{s:02}.{c:02}'
def time_srt(t):
 n=round(t*1000);h,r=divmod(n,3600000);m,r=divmod(r,60000);s,c=divmod(r,1000);return f'{h:02}:{m:02}:{s:02},{c:03}'
def ass_text(t):return str(t).replace('\\','\\\\').replace('{','\\{').replace('}','\\}').replace('\n','\\N')

@lru_cache(maxsize=8)
def caption_font(size):
 return ImageFont.truetype(str(PROJECT/'recipes/plush-dialogue-v14/assets/Alibaba-PuHuiTi-Regular.ttf'),size)

def wrap_caption(value,size,width=620):
 font=caption_font(size);result=[]
 for paragraph in str(value).splitlines() or ['']:
  tokens=re.findall(r'\S+\s*',paragraph) if re.search(r'[A-Za-z]',paragraph) and ' ' in paragraph else list(paragraph)
  line=''
  for token in tokens:
   if font.getlength(token.strip())>width:
    for char in token:
     if line and font.getlength((line+char).rstrip())>width:result.append(line.rstrip());line=''
     line+=char
   elif line and font.getlength((line+token).rstrip())>width:
    split=None
    for match in reversed(list(re.finditer(r'(?<=[,.;:!?])\s+',line))):
     head=line[:match.start()].strip();tail=(line[match.end():].strip()+' '+token.strip()).strip()
     if font.getlength(head)>=width*.4 and font.getlength(tail)<=width:split=(head,tail);break
    if split:result.append(split[0]);line=split[1]+' '
    else:result.append(line.rstrip());line=token.lstrip()
   else:line+=token
  if line.strip():result.append(line.strip())
 return result

def caption_header():
 return '[Script Info]\nScriptType: v4.00+\nPlayResX: 768\nPlayResY: 1376\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Alibaba PuHuiTi,38,&H00FFFFFF,&H00FFFFFF,&H50000000,&H90000000,0,0,0,0,100,100,0,0,1,1.6,0.5,2,64,64,121,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'

def caption_content(line):
 english='\\N'.join(ass_text(x) for x in wrap_caption(line['text'],38))
 chinese='\\N'.join(ass_text(x) for x in wrap_caption(line.get('translation',''),34))
 return english+('\\N{\\fs34}'+chinese if chinese else '')

def pull_down_audio(previous,upcoming,previous_take,next_take):
 """Overlap only silent handles; keep every spoken sample and its timing intact."""
 duration=PULL_DOWN_FRAMES/24
 prev_end=max((t['end'] for t in previous_take['audio']['turns']),default=0)
 next_start=min((t['start'] for t in next_take['audio']['turns']),default=next_take['keep_frames']/24)
 if prev_end>previous_take['keep_frames']/24-duration+1e-6 or next_start<duration-1e-6:
  raise NeedsAttention('下拉转场的头尾静音不足，不能覆盖原对白；请为对应镜头留出转场缓冲')
 n=round(duration*32000)*4
 left=np.frombuffer(previous[-n:],dtype='<i2').astype(np.int32)
 right=np.frombuffer(upcoming[:n],dtype='<i2').astype(np.int32)
 if len(left)!=len(right) or len(left)!=n//2:raise NeedsAttention('转场音轨长度不足，原素材保留')
 mixed=left+right
 if np.abs(mixed).max()>32767:raise NeedsAttention('转场音轨混音削波，原音轨保留')
 return previous[:-n]+mixed.astype('<i2').tobytes()+upcoming[n:]

def picture_chain(entries):
 """Return input args and deterministic cut/wipe graph with exact CFR24 length."""
 args=[];filters=[];index=0;last=None;frames=0
 for entry in entries:
  label='v'+str(index)
  if 'gap' in entry:
   args+=['-f','lavfi','-i','color=c=black:s=768x1376:r=24'];n=entry['gap']
  else:args+=['-i',entry['path']];n=entry['frames']
  resize='scale=768:1376:flags=lanczos,' if entry.get('packaging') else ''
  filters.append(f'[{index}:v]trim=end_frame={n},setpts=PTS-STARTPTS,settb=AVTB,{resize}setsar=1,format=yuv444p,fps=24[{label}]')
  if last is not None:
   merged='join'+str(index)
   if entry.get('transition')=='pull_down':
    overlap=PULL_DOWN_FRAMES
    filters.append(f'[{last}][{label}]xfade=transition=wipedown:duration={overlap/24}:offset={(frames-overlap)/24},fps=24[{merged}]')
    frames+=n-overlap
   else:
    filters.append(f'[{last}][{label}]concat=n=2:v=1:a=0,fps=24[{merged}]');frames+=n
   last=merged
  else:last=label;frames=n
  index+=1
 filters.append(f'[{last}]trim=end_frame={frames},setpts=PTS-STARTPTS,fps=24[body0]')
 return args,filters,index

def assemble(store,job,stop):
 p=job['payload']['project'];op_after=p['packaging'].get('op_after_shot') if p['packaging'].get('op',True) else None;front_op=bool(p['packaging'].get('op',True) and not op_after);folder=store.root/'jobs'/job['id'];shots=p['board']['shots'];takes=[];entries=[];offset=0;overlays=[];body_audio=b'';cues=[];previous=None
 for shot in shots:
  a=store.asset(p['adopted_takes'][shot['id']],p['id'])
  if a.get('board_version')!=p['board_version'] or a.get('master_id')!=p['scene_masters'][shot['scene_id']]:raise ValueError('采用的片段对应旧分镜或旧主图，请先核对该镜')
  if digest(a['path'])!=a['sha256']:raise NeedsAttention('原拍摄片段已变化，不能继续拼接')
  if shot['continuation'] and a.get('context_dependency')!=previous['id']:raise ValueError('上一镜采用版本已改变，请先续拍当前镜以对齐真实末尾')
  if shot['transition']=='practice_time':
   if not takes:raise ValueError('首镜前不能放练习幕间')
   overlays.append(offset-5);entries.append({'gap':PRACTICE_GAP_FRAMES});offset+=PRACTICE_GAP_FRAMES;body_audio+=b'\0'*(round(PRACTICE_GAP_FRAMES/24*32000)*4)
  if shot['transition']=='pull_down':
   if not takes:raise ValueError('首镜前不能下拉换景')
   offset-=PULL_DOWN_FRAMES
  entries.append({'path':a['path'],'frames':a['keep_frames'],'transition':shot['transition']});takes.append(a)
  audio=a['audio']
  with wave.open(audio['wave'],'rb') as f:data=f.readframes(f.getnframes());assert f.getframerate()==32000 and f.getnchannels()==2
  body_audio=pull_down_audio(body_audio,data,previous,a) if shot['transition']=='pull_down' else body_audio+data
  for line in audio['turns']:cues.append({**line,'start':offset/24+line['start'],'end':offset/24+line['end']})
  offset+=a['keep_frames'];previous=a
  if shot['id']==op_after:
   entries.append({'path':str(PROJECT/'assets/op/hi-soda-motion/hi-soda-op-2s.mp4'),'frames':48,'transition':'cut','packaging':True})
   with wave.open(str(PROJECT/'assets/op/hi-soda-motion/hi-soda-op.wav'),'rb') as f:
    assert f.getframerate()==32000 and f.getnchannels()==2
    body_audio+=f.readframes(f.getnframes())
   offset+=48
 if offset+(48 if front_op else 0)>MAX_EPISODE_SECONDS*24:raise ValueError('实际配音及画面加包装超过5分钟，请调整分镜后合成')
 wavebody=folder/'body-audio.wav'
 with wave.open(str(wavebody),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(32000);f.writeframes(body_audio)
 sound=np.frombuffer(body_audio,dtype='<i2').reshape(-1,2).astype(np.int32)
 for startframe in overlays:
  with wave.open(str(PROJECT/'assets/intertitles/motion/a-paw-pop.wav'),'rb') as f:fx=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').reshape(-1,2)
  start=round(startframe/24*32000);sound[start:start+len(fx)]+=fx
 if np.abs(sound).max()>32767:raise NeedsAttention('动效混音出现削波，请调整后再合成；原音轨保留')
 with wave.open(str(wavebody),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(32000);f.writeframes(sound.astype('<i2').tobytes())
 op=front_op;prefix=2 if front_op else 0
 headers=caption_header()
 events=[];srt=[]
 for i,line in enumerate(cues,1):
  events.append('Dialogue: 0,'+time_ass(line['start'])+','+time_ass(line['end'])+',Default,,0,0,0,,'+caption_content(line))
  srt.extend([str(i),time_srt(prefix+line['start'])+' --> '+time_srt(prefix+line['end']),line['text']+('\n'+line['translation'] if line.get('translation') else ''),''])
 ass=folder/'captions.ass';ass.write_text(headers+'\n'.join(events)+'\n');(folder/'captions.srt').write_text('\n'.join(srt))
 inputs,filters,index=picture_chain(entries)
 args=['ffmpeg','-hide_banner','-loglevel','error','-n']+inputs;last='body0'
 for j,start in enumerate(overlays):
  args+=['-i',str(PROJECT/'assets/intertitles/motion/a-paw-pop-alpha.mov')];filters.append(f'[{index}:v]setpts=PTS-STARTPTS+{start/24}/TB[fx{j}]');nextlabel='body'+str(j+1);filters.append(f'[{last}][fx{j}]overlay=eof_action=pass:repeatlast=0:format=auto[{nextlabel}]');last=nextlabel;index+=1
 filters.append(f'[{last}]format=yuv420p,ass={ass}:fontsdir={PROJECT/"recipes/plush-dialogue-v14/assets"},scale=1080:1932:flags=lanczos[v]')
 body=folder/'body-picture.mp4'
 if not body.exists():run(args+['-filter_complex_threads','1','-filter_complex',';'.join(filters),'-map','[v]','-an','-c:v','libx264','-threads','3','-preset','fast','-crf','17','-pix_fmt','yuv420p','-r','24','-fps_mode','cfr','-video_track_timescale','12288','-movflags','+faststart',body])
 final=folder/'hi-soda-final.mp4';audio=folder/'final-audio.wav';data=sound.astype('<i2').tobytes()
 if op:
  opvideo=PROJECT/'assets/op/hi-soda-motion/hi-soda-op-2s.mp4';vonly=folder/'op-picture.mp4'
  if not vonly.exists():run(['ffmpeg','-v','error','-n','-i',opvideo,'-map','0:v:0','-c:v','copy','-an',vonly])
  with wave.open(str(PROJECT/'assets/op/hi-soda-motion/hi-soda-op.wav'),'rb') as f:data=f.readframes(f.getnframes())+data
  concat=folder/'pictures.ffconcat';concat.write_text("ffconcat version 1.0\nfile '"+str(vonly)+"'\nduration 2\nfile '"+str(body)+"'\n");videoargs=['-f','concat','-safe','0','-i',concat]
 else:videoargs=['-i',body]
 with wave.open(str(audio),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(32000);f.writeframes(data)
 if not final.exists():run(['ffmpeg','-v','error','-n']+videoargs+['-i',audio,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-video_track_timescale','12288','-movflags','+faststart',final])
 meta=probe(final);v=next(x for x in meta['streams'] if x['codec_type']=='video');expected=offset+(48 if op else 0)
 if int(v['nb_frames'])!=expected or v['avg_frame_rate']!='24/1' or abs(float(v.get('start_time',0)))>.001:raise NeedsAttention('最终帧数、帧率或起点未通过检查，不能交付')
 provenance={'takes':[{'id':a['id'],'sha256':a['sha256'],'shot_id':a['shot_id'],'keep_frames':a['keep_frames']} for a in takes],'frames':expected,'fps':24,'op':bool(p['packaging'].get('op',True)),'op_after_shot':op_after,'intertitle':'A paw pop' if overlays else None,'board_version':p['board_version'],'subtitles':str(folder/'captions.srt'),'transitions':[{'shot_id':s['id'],'kind':s['transition']} for s in shots if s['transition']!='cut'],'native_voices_preserved':True,'human_acceptance':'pending'};atomic_json(folder/'final-manifest.json',provenance)
 return store.add_asset(p['id'],'final',final,{'name':p['title'],'job_id':job['id'],'board_version':p['board_version'],'setting_version':p['setting_version'],'frames':expected,'seconds':float(meta['format']['duration']),'manifest':provenance,'review':'candidate'})
