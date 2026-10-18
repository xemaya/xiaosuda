"""Moving H3 canopy plus small controlled wind on the lowest needle clusters.

The larger native crop reinterpreted the pine/camera and is rejected. Use the
stable original-size native wind layer, and animate the lowest bough from its
accepted initial geometry with a small anchored non-looping displacement field.
No character pixels or dialogue are regenerated or retimed.
"""
from pathlib import Path
import cv2,numpy as np,subprocess,json
R=Path(__file__).resolve().parent;FF='/opt/homebrew/bin/ffmpeg'
def main():
 out=R/'canopy-layered-wind.mp4'
 if out.exists():return
 src=cv2.VideoCapture(str(R/'source-01.mp4'));ok,ref=src.read();src.release();assert ok
 native=cv2.VideoCapture(str(R/'canopy-native.mp4'))
 h,w=990,1080;yy,xx=np.mgrid[:h,:w].astype(np.float32)
 clusters=np.zeros((h,w),np.float32)
 for x,y,rx,ry in [(220,765,95,35),(380,790,100,40),(445,865,100,40),(570,835,60,55),(650,770,70,35)]:
  clusters=np.maximum(clusters,np.exp(-2*(((xx-x)/rx)**2+((yy-y)/ry)**2)))
 weight=clusters*np.clip((1000-xx)/780,0,1)*np.clip((yy-680)/60,0,1)
 blend=np.clip((720-yy)/40,0,1)[...,None]
 p=subprocess.Popen([FF,'-v','error','-n','-f','rawvideo','-pix_fmt','bgr24','-s','1080x990','-r','24','-i','-','-an','-c:v','libx264','-threads','3','-crf','12','-preset','fast','-pix_fmt','yuv420p','-video_track_timescale','12288',str(out)],stdin=subprocess.PIPE)
 try:
  for i in range(197):
   t=i/24;ok,im=native.read();assert ok
   dx=weight*(1.4*np.sin(.63*t)+.45*np.sin(1.17*t))
   dy=weight*(2.4*np.sin(.78*t)+.65*np.sin(1.73*t))
   b=cv2.remap(ref[:h],(xx+dx).astype(np.float32),(yy+dy).astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)
   top=cv2.resize(im,(1080,720),interpolation=cv2.INTER_LANCZOS4)
   b[:720]=np.clip(top.astype(np.float32)*blend[:720]+b[:720]*(1-blend[:720]),0,255).astype(np.uint8)
   p.stdin.write(b.tobytes())
 finally:
  p.stdin.close();native.release()
 assert p.wait()==0
 (R/'layered-wind.json').write_text(json.dumps({'native_canopy':'canopy-native.mp4','lowest_needles_source':'source-01.mp4 actual first retained frame','frames':197,'fps':24,'native_region_y':[0,720],'lowest_needles_displacement_px_max':[1.85,3.05],'rigid_trunk_and_mountains':'reference geometry','spatial_layer_feather_y':[680,720],'temporal_crossfade':False,'repeated_or_padded_frames':0,'retimed_actor_frames':0,'large_crop_rejected':'canopy-tall-native.mp4 reinterpreted tree/camera; never selected'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
