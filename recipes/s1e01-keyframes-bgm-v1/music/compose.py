"""Original sparse major-key cue, rendered locally; no media/model uploads."""
from pathlib import Path
import json,random
root=Path(__file__).resolve().parent;rng=random.Random(101701)
bpm=90;beat=60/bpm;events=[]
def note(track,pitch,start,duration,velocity):
 events.extend([dict(time=round(start,6),track=track,note=pitch,velocity=velocity,on=True),dict(time=round(start+duration,6),track=track,note=pitch,velocity=0,on=False)])
# Cmaj7, Am7, Fmaj7, G6; a soft ii-V variation in the third phrase.
chords=[([48,55,59,64],36),([45,52,55,60],33),([41,48,52,57],29),([43,50,55,59],31)]
melodies=[[(.5,76,.6),(2,79,.55),(3,76,.6)],[(1,72,.65),(2.5,74,.6)],[(.5,76,.65),(2,72,.7)],[(1,74,.6),(2.5,71,.65)],[(.5,72,.6),(2,76,.6),(3,79,.65)],[(1,81,.7),(2.5,79,.6)],[(.5,76,.65),(2,74,.7)],[(1,71,.7),(2.5,74,.7)]]
for bar in range(16):
 t=bar*4*beat;chord,bass=chords[bar%4]
 for step in [0,1,2,3]:
  pitch=chord[[0,2,1,3][step]]+12
  note(0,pitch,t+step*beat+rng.uniform(-.009,.009),beat*.82,39+rng.randint(-4,4))
  if step in [1,3]:note(0,chord[1]+12,t+(step+.48)*beat,beat*.32,25+rng.randint(-2,2))
 for b,pitch in [(0,bass),(2,bass+7)]:note(2,pitch,t+b*beat,beat*1.55,36)
 for b,pitch,length in melodies[bar%8]:note(1,pitch,t+b*beat,beat*length,41+rng.randint(-4,4))
# End on a sustained tonic rather than chopping an accompaniment loop.
t=16*4*beat
for i,pitch in enumerate([60,64,67,71]):note(0,pitch,t+i*.065,2.3,35)
note(1,72,t+.25,1.8,37);note(2,36,t,2.6,34)
events.sort(key=lambda e:(e['time'],e['on']))
doc=dict(title='Soda Sunny Steps',bpm=bpm,key='C major',duration=46.333333,instruments=[dict(program=24,name='nylon guitar'),dict(program=12,name='marimba'),dict(program=32,name='acoustic bass')],events=events,source='Original note arrangement, local system instrument rendering',seed=101701)
(root/'score.json').write_text(json.dumps(doc,indent=2))
print(f'{len(events)//2} notes written')
