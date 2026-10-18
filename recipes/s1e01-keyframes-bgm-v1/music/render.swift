import Foundation
import AVFoundation
import AudioToolbox

struct Instrument: Decodable { let program: Int; let name: String }
struct Event: Decodable { let time: Double; let track: Int; let note: Int; let velocity: Int; let on: Bool }
struct Score: Decodable { let duration: Double; let instruments: [Instrument]; let events: [Event] }
let scoreURL=URL(fileURLWithPath:CommandLine.arguments[1])
let score=try JSONDecoder().decode(Score.self,from:Data(contentsOf:scoreURL))
let engine=AVAudioEngine()
let format=AVAudioFormat(standardFormatWithSampleRate:48000,channels:2)!
let bank=URL(fileURLWithPath:"/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls")
var instruments:[AVAudioUnitSampler]=[]
for spec in score.instruments {
 let sampler=AVAudioUnitSampler();engine.attach(sampler)
 try sampler.loadSoundBankInstrument(at:bank,program:UInt8(spec.program),bankMSB:UInt8(kAUSampler_DefaultMelodicBankMSB),bankLSB:0)
 engine.connect(sampler,to:engine.mainMixerNode,format:format);instruments.append(sampler)
}
try engine.enableManualRenderingMode(.offline,format:format,maximumFrameCount:1024)
engine.prepare();try engine.start()
let out=URL(fileURLWithPath:CommandLine.arguments[2])
var file:AVAudioFile?=try AVAudioFile(forWriting:out,settings:format.settings)
let buffer=AVAudioPCMBuffer(pcmFormat:format,frameCapacity:1024)!
let total=AVAudioFramePosition((score.duration*48000).rounded())
var cursor:AVAudioFramePosition=0;var i=0;var retries=0
while cursor<total {
 while i<score.events.count && AVAudioFramePosition((score.events[i].time*48000).rounded())<=cursor {
  let e=score.events[i]
  if e.on {instruments[e.track].startNote(UInt8(e.note),withVelocity:UInt8(e.velocity),onChannel:0)}
  else {instruments[e.track].stopNote(UInt8(e.note),onChannel:0)}
  i+=1
 }
 let next=i<score.events.count ? AVAudioFramePosition((score.events[i].time*48000).rounded()):total
 let n=AVAudioFrameCount(min(1024,total-cursor,max(1,next-cursor)))
 let status=try engine.renderOffline(n,to:buffer)
 if status == .success {try file!.write(from:buffer);cursor+=AVAudioFramePosition(n);retries=0}
 else {retries+=1;if retries>100 {fatalError("Offline render did not progress: \(status)")}}
}
engine.stop()
file=nil
print("Rendered \(cursor) frames at 48 kHz")
