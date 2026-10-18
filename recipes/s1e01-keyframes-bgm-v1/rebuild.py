"""Rebuild the accepted cut from frozen takes/voices/captions/music, entirely offline."""
from pathlib import Path
import argparse,json,shutil,subprocess
HERE=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--dry-run',action='store_true');p.add_argument('--ffmpeg',default=shutil.which('ffmpeg'));p.add_argument('--ffprobe',default=shutil.which('ffprobe'));a=p.parse_args()
 if not a.ffmpeg or not a.ffprobe:raise SystemExit('Provide ffmpeg and ffprobe paths.')
 recipe=json.loads((HERE/'recipe.json').read_text());out=a.out.resolve();work=out.parent/(out.stem+'-work')
 assert recipe['packaging'].get('op',True) and not recipe['packaging'].get('op_after_shot'),'Frozen episode uses front OP'
 if not a.dry_run:
  import verify;verify.main()
  if out.exists() or work.exists():raise SystemExit('Choose a fresh output path; accepted artifacts are never overwritten.')
  work.mkdir(parents=True)
 commands=[]
 inputs=[];filters=[];last=None;frames=0
 for i,sid in enumerate(recipe['shot_order']):
  shot=recipe['shots'][sid];label='v'+str(i);n=shot['keep_frames'];inputs+=['-i',str(HERE/shot['file'])]
  filters.append(f'[{i}:v]trim=end_frame={n},setpts=PTS-STARTPTS,settb=AVTB,setsar=1,format=yuv444p,fps=24[{label}]')
  if last:
   merged='join'+str(i)
   if shot['transition']=='pull_down':filters.append(f'[{last}][{label}]xfade=transition=wipedown:duration={8/24}:offset={(frames-8)/24},fps=24[{merged}]');frames+=n-8
   else:filters.append(f'[{last}][{label}]concat=n=2:v=1:a=0,fps=24[{merged}]');frames+=n
   last=merged
  else:last=label;frames=n
 filters.append(f'[{last}]trim=end_frame={frames},setpts=PTS-STARTPTS,fps=24[body0]')
 filters.append('[body0]format=yuv420p,ass=accepted/captions.ass:fontsdir=assets,scale=1080:1932:flags=lanczos[v]')
 body=work/'body-picture.mp4';op=work/'op-picture.mp4';mixed=work/'music-mix.wav';concat=work/'pictures.ffconcat'
 commands.append([a.ffmpeg,'-hide_banner','-loglevel','error','-n']+inputs+['-filter_complex_threads','1','-filter_complex',';'.join(filters),'-map','[v]','-an','-c:v','libx264','-threads','3','-preset','fast','-crf','17','-pix_fmt','yuv420p','-r','24','-fps_mode','cfr','-video_track_timescale','12288','-movflags','+faststart',str(body)])
 commands.append([a.ffmpeg,'-v','error','-n','-i',str(HERE/'assets/op.mp4'),'-map','0:v:0','-c:v','copy','-an',str(op)])
 duck=recipe['music']['duck'];af=f'[1:a][0:a]sidechaincompress=threshold={duck["threshold"]}:ratio={duck["ratio"]}:attack={duck["attack_ms"]}:release={duck["release_ms"]}:knee={duck["knee"]}:makeup=1:detection=rms[bed];[0:a][bed]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[out]'
 commands.append([a.ffmpeg,'-v','error','-n','-i',str(HERE/'accepted/final-audio.wav'),'-i',str(HERE/recipe['music']['file']),'-filter_complex',af,'-map','[out]','-ar','32000','-ac','2','-c:a','pcm_s16le',str(mixed)])
 commands.append([a.ffmpeg,'-v','error','-n','-f','concat','-safe','0','-i',str(concat),'-i',str(mixed),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-video_track_timescale','12288','-movflags','+faststart',str(out)])
 if a.dry_run:print(json.dumps({'commands':commands,'expected_frames':1112,'network':False,'gpu':False},ensure_ascii=False,indent=2));return
 concat.write_text("ffconcat version 1.0\nfile '"+str(op)+"'\nduration 2\nfile '"+str(body)+"'\n")
 for i,cmd in enumerate(commands,1):print(f'Offline stage {i}/4',flush=True);subprocess.run(cmd,cwd=HERE,check=True,timeout=1200)
 meta=json.loads(subprocess.check_output([a.ffprobe,'-v','error','-show_streams','-of','json',str(out)]));v=next(x for x in meta['streams'] if x['codec_type']=='video')
 assert v['nb_frames']=='1112' and v['r_frame_rate']==v['avg_frame_rate']=='24/1'
 print('Rebuilt 1112 frames, CFR24. The separately archived accepted master remains the exact SHA256 reference.')
if __name__=='__main__':main()
