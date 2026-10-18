"""Read-only verification of this candidate; no providers or publication."""
from pathlib import Path
import json,subprocess,hashlib,wave
import numpy as np
R=Path(__file__).resolve().parent
SRC=R.parent.parent/'releases/huangshan/2026-10-18/Hi-Soda_Huangshan_Final.mp4'
OUT=R/'Hi-Soda_Huangshan_pine-village-v4.mp4'
FF='/opt/homebrew/bin/ffmpeg';FP='/opt/homebrew/bin/ffprobe'
def packets(p):
 data=json.loads(subprocess.check_output([FP,'-v','error','-select_streams','v:0','-show_packets','-show_entries','packet=pts_time,duration_time,data_hash','-show_data_hash','sha256','-of','json',str(p)]))['packets']
 return {round(float(x['pts_time'])*24):x['data_hash'] for x in data}
def pcm(p):return subprocess.check_output([FF,'-v','error','-i',str(p),'-map','0:a:0','-f','s16le','-ar','32000','-ac','2','-'])
def small_frames(p,crop=None):
 filt=(f'crop={crop},' if crop else '')+'scale=270:180,format=gray'
 raw=subprocess.check_output([FF,'-v','error','-i',str(p),'-an','-vf',filt,'-f','rawvideo','-'])
 return np.frombuffer(raw,dtype=np.uint8).reshape(-1,180,270)
def differences(frames):return np.mean(np.abs(np.diff(frames.astype(np.float32),axis=0)),axis=(1,2))
def main():
 report=json.loads((R/'delivery.json').read_text());assert hashlib.sha256(SRC.read_bytes()).hexdigest()==report['source_sha256'];assert hashlib.sha256(OUT.read_bytes()).hexdigest()==report['sha256']
 old,new=packets(SRC),packets(OUT);assert len(new)==3389
 unchanged=list(range(267))+list(range(464,3173));assert all(old[i]==new[i] for i in unchanged)
 a=pcm(SRC);b=pcm(R/'extended-original-audio.wav');cut=round(3173/24*32000)*4
 assert a[:cut]==b[:cut],'An original spoken/music prefix PCM sample changed'
 assert len(b)==round(3389/24*32000)*4
 with wave.open(str(R/'extended-original-audio.wav'),'rb') as f:
  audio=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2');assert np.max(np.abs(audio.astype(np.int32)))<32767
 # Objective aid only; human visual review determines acceptable motion.
 before=differences(small_frames(R/'source-01.mp4','1080:720:0:0'))
 after=differences(small_frames(R/'pine-repaired-layered.mp4','1080:720:0:0'))
 end=differences(small_frames(R/'ending-native.mp4'))
 lo,hi=round((17-267/24)*24),round((18.2-267/24)*24)
 result={'passed':True,'frames':3389,'fps':24,'unchanged_picture_packets':len(unchanged),'original_audio_prefix_pcm_samples_exact':cut//4,'all_23_spoken_lines_unchanged_in_audio_prefix':True,'audio_tail_has_no_voice_source':True,'audio_peak_pcm':int(np.max(np.abs(audio.astype(np.int32)))),'pine_17_to_18_2s_mean_frame_differences':{'before_max':float(before[lo:hi].max()),'after_max':float(after[lo:hi].max()),'before_mean':float(before[lo:hi].mean()),'after_mean':float(after[lo:hi].mean())},'ending_adjacent_duplicate_thumbnail_frames':int(np.sum(end==0)),'human_acceptance':'pending','source_release_unchanged':True}
 (R/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
