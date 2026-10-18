"""Local surgical reframe: original moving cloud pixels, no new image/video generation."""
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parent
SRC=R.parent/'1017-huangshan-quadruped-v2/Hi-Soda_Huangshan_quadruped-v2.mp4'
SOURCE_SHA='69728837c4cec7597abec68bfccbb185b32d6168217903d045ae808201eb816b'
START,END=1472,1624
CROP=(260,200,560,1002)
def run(args):subprocess.run([str(x) for x in args],check=True)
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(p)]))
def video(p):return next(x for x in probe(p)['streams'] if x['codec_type']=='video')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ahash(p):return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-']).decode().strip()
def main():
 assert sha(SRC)==SOURCE_SHA
 keys=json.loads((R/'keyframes.json').read_text());begin,finish=keys['start'],keys['end'];assert begin<=START<END<=finish
 segments=[R/f'segment-{i:02}.mp4' for i in range(3)]
 if not all(p.exists() for p in segments):
  assert not any(p.exists() for p in segments),'Inspect partial split rather than overwrite'
  run(['ffmpeg','-v','error','-n','-i',SRC,'-map','0:v:0','-an','-c:v','copy','-f','segment','-segment_times',f'{begin/24:.12f},{finish/24:.12f}','-segment_time_delta','0.00001','-reset_timestamps','1','-segment_format','mp4',R/'segment-%02d.mp4'])
 expected=[begin,finish-begin,3325-finish]
 assert [int(video(p)['nb_frames']) for p in segments]==expected
 lo,hi=START-begin,END-begin;mid=R/'middle-reframed.mp4'
 if not mid.exists():
  x,y,w,h=CROP
  sar=video(segments[1])['sample_aspect_ratio'].replace(':','/')
  # Here the next source keyframe is exactly the end of S11: no trailing fringe.
  assert hi==expected[1]
  filt=f'[0:v]split=2[a][b];[a]trim=end_frame={lo},setpts=PTS-STARTPTS[h];[b]trim=start_frame={lo}:end_frame={hi},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale=1080:1932:flags=lanczos,setsar={sar}:max=10000[cloud];[h][cloud]concat=n=2:v=1:a=0,setpts=N/(24*TB),format=yuv420p[v]'
  run(['ffmpeg','-v','error','-n','-threads','2','-i',segments[1],'-filter_complex_threads','1','-filter_complex',filt,'-map','[v]','-an','-c:v','libx264','-threads','3','-preset','fast','-crf','14','-profile:v','high','-level:v','4.2','-r','24','-fps_mode','cfr','-video_track_timescale','12288','-movflags','+faststart',mid])
 assert int(video(mid)['nb_frames'])==expected[1]
 concat=R/'pictures.ffconcat';parts=[segments[0],mid,segments[2]];concat.write_text('ffconcat version 1.0\n'+''.join(f"file '{p}'\nduration {n/24:.12f}\n" for p,n in zip(parts,expected)))
 out=R/'Hi-Soda_Huangshan_silent-cloud-v3.mp4'
 if not out.exists():run(['ffmpeg','-v','error','-n','-f','concat','-safe','0','-i',concat,'-i',SRC,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-video_track_timescale','12288','-movflags','+faststart',out])
 v=video(out);assert v['sample_aspect_ratio']==video(SRC)['sample_aspect_ratio'];a=next(x for x in probe(out)['streams'] if x['codec_type']=='audio')
 assert int(v['nb_frames'])==3325 and v['avg_frame_rate']=='24/1' and (v['width'],v['height'])==(1080,1932)
 assert abs(float(v['start_time']))<.001 and abs(float(a['start_time']))<.001
 assert ahash(out)==ahash(SRC)
 report={'source':str(SRC),'source_sha256':SOURCE_SHA,'path':str(out),'sha256':sha(out),'frames':3325,'fps':24,'reframed_frames':[START,END],'reframed_seconds':[START/24,END/24],'crop_source_pixels':list(CROP),'reencoded_gop_frames':[begin,finish],'outside_gop_video_stream_copy':True,'all_other_picture_content_preserved':True,'audio_encoded_stream_exact':True,'new_image_or_video_model_calls':0,'copied_still_or_frozen_tail_frames':0,'human_acceptance':'pending'}
 (R/'delivery.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
