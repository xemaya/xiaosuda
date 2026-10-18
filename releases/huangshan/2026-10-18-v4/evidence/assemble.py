"""Surgical S03 canopy layer + new silent S22. All other pictures copied."""
from pathlib import Path
import subprocess,json,hashlib,sys,wave
R=Path(__file__).resolve().parent
SRC=R.parent.parent/'releases/huangshan/2026-10-18/Hi-Soda_Huangshan_Final.mp4'
EXPECTED='f93c763d99de10762a646e9da632af04cc51141342b3e44b229db40eeef2cd15'
FF='/opt/homebrew/bin/ffmpeg';FP='/opt/homebrew/bin/ffprobe'
PINE_START,PINE_END,ENDING_START=267,464,3173
NEW_ENDING=216
ENDING_IN=24
def run(args):subprocess.run([str(x) for x in args],check=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def probe(p):return json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-of','json',str(p)]))
def vid(p):return next(s for s in probe(p)['streams'] if s['codec_type']=='video')
ENC=['-c:v','libx264','-threads','3','-preset','fast','-crf','14','-profile:v','high','-level:v','4.2','-pix_fmt','yuv420p','-r','24','-fps_mode','cfr','-video_track_timescale','12288','-movflags','+faststart']
def split():
 assert sha(SRC)==EXPECTED
 parts=[R/f'source-{i:02}.mp4' for i in range(4)]
 if not all(p.exists() for p in parts):
  assert not any(p.exists() for p in parts),'Inspect incomplete split; never overwrite it blindly'
  run([FF,'-v','error','-n','-i',SRC,'-map','0:v:0','-an','-c:v','copy','-f','segment','-segment_times',','.join(f'{x/24:.12f}' for x in [PINE_START,PINE_END,ENDING_START]),'-segment_time_delta','0.00001','-reset_timestamps','1','-segment_format','mp4',R/'source-%02d.mp4'])
 assert [int(vid(p)['nb_frames']) for p in parts]==[267,197,2709,152]
 return parts

def pine(parts):
 out=R/'pine-repaired-layered.mp4'
 if out.exists():return out
 assert int(vid(R/'canopy-layered-wind.mp4')['nb_frames'])>=197
 # Replace the moving tree background down to y990; a conservative elliptical
 # exclusion protects Angela's head and every pixel below990 stays original.
 # Feather is spatial, not a temporal dissolve. The tree is moving footage.
 mask="255*clip((990-Y)/30,0,1)*clip((sqrt(pow((X-800)/280,2)+pow((Y-1060)/270,2))-1)*20,0,1)"
 filt=f"[0:v]setpts=PTS-STARTPTS,format=yuv420p[old];[1:v]trim=end_frame=197,setpts=PTS-STARTPTS,scale=1080:990:flags=lanczos,pad=1080:1932:0:0,setsar=644/645:max=10000,format=yuv420p[tree];nullsrc=s=1080x1932:r=24,format=gray,geq=lum='{mask}',trim=end_frame=197[mask];[old][tree][mask]maskedmerge,setsar=644/645:max=10000,format=yuv420p[v]"
 (R/'canopy-composite-filter.txt').write_text(filt)
 run([FF,'-v','error','-n','-threads','2','-i',parts[1],'-i',R/'canopy-layered-wind.mp4','-filter_complex_threads','1','-filter_complex',filt,'-map','[v]','-an','-frames:v','197',*ENC,out])
 assert int(vid(out)['nb_frames'])==197
 return out

def ending():
 out=R/'village-ending.mp4'
 if not out.exists():
  assert int(vid(R/'ending-native.mp4')['nb_frames'])>=NEW_ENDING
  run([FF,'-v','error','-n','-threads','2','-i',R/'ending-native.mp4','-vf',f'trim=start_frame={ENDING_IN}:end_frame={ENDING_IN+NEW_ENDING},setpts=PTS-STARTPTS,scale=1080:1932:flags=lanczos,setsar=644/645:max=10000','-an',*ENC,out])
 assert int(vid(out)['nb_frames'])==NEW_ENDING
 return out

def audio():
 out=R/'extended-original-audio.wav'
 if out.exists():return out
 # Original speech is over before S22. Preserve the entire decoded original
 # audio prefix; stretch only the silent ending's existing music/ambience.
 # No new TTS, no repeated words, no time-stretch applied to any spoken line.
 cut=round(ENDING_START/24*32000);total=round((ENDING_START+NEW_ENDING)/24*32000)
 prefix=subprocess.check_output([FF,'-v','error','-i',str(SRC),'-map','0:a:0','-ar','32000','-ac','2','-f','s16le','-'])[:cut*4]
 filt=f'atrim=start_sample={cut}:end_sample={round(3325/24*32000)},asetpts=PTS-STARTPTS,atempo={152/216:.12f},apad=whole_len=288000,atrim=end_sample=288000,afade=t=out:st=7.8:d=1.2'
 tail=subprocess.check_output([FF,'-v','error','-i',str(SRC),'-map','0:a:0','-af',filt,'-ar','32000','-ac','2','-f','s16le','-'])
 data=prefix+tail;assert len(data)==total*4
 with wave.open(str(out),'wb') as f:
  f.setnchannels(2);f.setsampwidth(2);f.setframerate(32000);f.writeframes(data)
 (R/'audio-pcm-copy.json').write_text(json.dumps({'source_prefix_samples':cut,'prefix_sha256':hashlib.sha256(prefix).hexdigest(),'method':'byte copy decoded original PCM prefix; time-stretch tail alone','tail_samples':288000,'total_samples':total},indent=2))
 return out

def main():
 parts=split();p=pine(parts)
 if '--pine-only' in sys.argv:return
 e=ending();a=audio();concat=R/'pictures.ffconcat'
 concat.write_text('ffconcat version 1.0\n'+''.join(f"file '{x}'\nduration {n/24:.12f}\n" for x,n in zip([parts[0],p,parts[2],e],[267,197,2709,216])))
 out=R/'Hi-Soda_Huangshan_pine-village-v4.mp4'
 if not out.exists():run([FF,'-v','error','-n','-f','concat','-safe','0','-i',concat,'-i',a,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-video_track_timescale','12288','-movflags','+faststart',out])
 v=vid(out);assert int(v['nb_frames'])==3389 and v['avg_frame_rate']=='24/1' and v['sample_aspect_ratio']=='644:645'
 assert (v['width'],v['height'])==(1080,1932)
 report={'source':str(SRC),'source_sha256':EXPECTED,'path':str(out),'sha256':sha(out),'frames':3389,'fps':24,'seconds':3389/24,'pine_frames':[267,464],'pine_background_layer':{'maximum_y':990,'head_exclusion_ellipse':[800,1060,280,270],'spatial_feather_only':True},'pine_actor_performance_preserved':True,'unchanged_stream_copy_frames':[[0,267],[464,3173]],'ending_frames':[3173,3389],'ending_native_selected_frames':[24,240],'new_ending_seconds':9,'original_ending_seconds':152/24,'original_speech_and_subtitle_times_preserved':True,'original_audio_prefix_samples':round(ENDING_START/24*32000),'music_ambience_only_tail_atempo':152/216,'new_tts_requests':0,'new_candidate_only':True,'human_acceptance':'pending','current_release_unchanged':True}
 (R/'delivery.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
