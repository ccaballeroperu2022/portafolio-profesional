import argparse, array, io, json, math, os, pathlib, random, subprocess, urllib.request
from PIL import Image, ImageDraw, ImageFont
from mido import MidiFile,MidiTrack,Message,MetaMessage,bpm2tempo

def main(reel):
 cfg=json.load(open('reels_manifest.json','r',encoding='utf8'))
 idx=reel-1
 out=pathlib.Path('output');out.mkdir(exist_ok=True)
 work=pathlib.Path('work');work.mkdir(exist_ok=True)
 entry=cfg['theme'][idx]
 col,brown,dark=entry['pal']
 def run(*args):
  subprocess.run([str(x) for x in args],check=True)
 def probe(p):
  x=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nk=1:nw=1',str(p)],capture_output=True,text=True,check=True)
  return float(x.stdout.strip())
 def download(url,p):
  headers={'User-Agent':'Mozilla/5.0'}
  with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=90) as resp,open(p,'wb') as target:
   while True:
    b=resp.read(327680)
    if not b:break
    target.write(b)
  assert p.stat().st_size>2048,('Empty download',url)
 print('START REEL',reel,entry['title'],flush=True)
 # Deterministic allocation, no stock video repeated across the 10 films
 api='https://huggingface.co/api/datasets/FastVideo/Mixkit-Src/tree/main/Business?recursive=false&expand=false'
 import requests
 rr=requests.get(api,timeout=60);rr.raise_for_status()
 files=[x['path'].split('/')[-1] for x in rr.json() if x.get('path','').lower().endswith('.mp4')]
 humans=['woman','women','man-','-man-','people','colleague','team','coworker','business','entrepreneur','employee','professional','person','executive','worker','office']
 activities=['working','typing','writing','report','office','laptop','tablet','meeting','computer','documents','notes','contract','present','reading','suit','planning','phone','desk','call','business','presentation','team','discussion']
 banned=['car-','truck','construction','drone','aerial','factory','party','danc','exercise','running','hike','street','solar-panel','wind-farm','shipping','containers','warehouse','machine','industrial','camera','virus','mask','ski']
 pool=sorted(p for p in files if any(k in p.lower() for k in humans) and any(k in p.lower() for k in activities) and not any(k in p.lower() for k in banned))
 # A curated priority list ensures realistic activities: typing, reading, consulting, reviewing.
 assert len(pool)>=50,('Insufficient nonrepeating live-action sources',len(pool))
 priority=['writing','laptop','computer','meeting','tablet','report','office','working','business','present','typing','person','call']
 rng=random.Random(120102026)
 # First allocate all fifty globally so independent runners agree on identity.
 assigned=[];pool_available=list(pool)
 for r in range(1,11):
  for scene in range(5):
   key=priority[(r*3+scene*2)%len(priority)]
   ranking=sorted(pool_available,key=lambda p:(
      0 if key in p.lower() else 1,
      0 if ('woman' in p.lower() or 'man-' in p.lower() or 'people' in p.lower()) else 1,
      (sum(ord(z)*(r+scene+1) for z in p)%10007)))
   f=ranking[0];assigned.append(f);pool_available.remove(f)
 chosen=assigned[idx*5:(idx+1)*5]
 assert len(set(chosen))==5
 print('FOOTAGE',chosen,flush=True)
 for j,f in enumerate(chosen):
  url='https://huggingface.co/datasets/FastVideo/Mixkit-Src/resolve/main/Business/'+f+'?download=true'
  try:
   download(url,work/f'c{j}.mp4')
   print('REAL_ACTOR',j,f,'SOURCE_DURATION',probe(work/f'c{j}.mp4'),flush=True)
  except Exception as ex:raise RuntimeError('Required genuine video missing '+f+': '+str(ex))
 audio=work/'voice.mp3'
 download(cfg['urls'][idx],audio)
 voice_duration=probe(audio); print('VOICE',cfg['voices'][idx],voice_duration,flush=True)
 # Serif families rotate across posters, with ten bright premium visual identities
 fonts=['/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSerif.ttf']
 weights=['/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf']
 series=idx%4
 body='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
 bodyb='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
 def ff(sz,b=False,ser=True):
  path=(weights[series] if b else fonts[series]) if ser else (bodyb if b else body)
  if not os.path.exists(path):path=weights[0] if b else fonts[0]
  return ImageFont.truetype(path,sz)
 def center(d,s,y,sz=34,color=None,b=False,ser=True,limit=970):
  font=ff(sz,b,ser);box=d.textbbox((0,0),s,font=font)
  while box[2]-box[0]>limit and sz>22:
   sz-=2;font=ff(sz,b,ser);box=d.textbbox((0,0),s,font=font)
  d.text(((1080-(box[2]-box[0]))/2,y),s,font=font,fill=color or dark)
 def picture(scene):
  im=Image.new('RGBA',(1080,1920),(0,0,0,0)); d=ImageDraw.Draw(im)
  d.rectangle((0,1300,1080,1920),fill=col)
  d.rectangle((0,1295,1080,1304),fill=brown)
  # Each reel has distinct premium title arrangement and ornament spacing.
  a=idx%3
  d.rounded_rectangle((60+20*a,38,1020-20*a,132),radius=[18,38,8][a],fill=col,outline=brown,width=3)
  center(d,'S Y S T E R A P R I M E',64,31,brown,True,False,800)
  center(d,entry['head'][scene],1350,58,dark,True,True)
  left=105+(idx%5)*12;right=975-(idx%5)*12
  d.line((left,1443,right,1443),fill=brown,width=3)
  services=[
    ('Tareas académicas','S/ 15'),('Informes APA','S/ 30'),('Estadística y datos','S/ 30'),
    ('Proyectos y sistemas','S/ 50'),('Investigaciones y tesinas','S/ 80'),
    ('Asesoría integral de tesis','S/ 150'),('Otras áreas académicas','S/ 30')]
  # Fixed services, story-specific ordering; legal/commercial conditions always shown
  rot=(idx*3)%7
  order=services[rot:]+services[:rot]
  if scene<3:
   sub=order[scene*2:scene*2+2]
   if len(sub)<2:sub+=order[:2-len(sub)]
   for k,(label,price) in enumerate(sub):
    yy=1517+k*134
    d.text((85,yy),label,font=ff(31,False,False),fill=dark)
    font=ff(49,True,True);box=d.textbbox((0,0),price,font=font)
    d.text((988-(box[2]-box[0]),yy-9),price,font=font,fill=brown)
    d.line((90,yy+85,990,yy+85),fill=brown,width=1)
  elif scene==3:
   # Display full non-duplicated rate table compactly for every reel
   center(d,'PRECIO REFERENCIAL',1490,40,brown,True)
   for j,(label,amount) in enumerate(services):
    yy=1550+j*32
    d.text((88,yy),label,font=ff(22,False,False),fill=dark)
    d.text((880,yy),amount,font=ff(22,True,False),fill=brown)
   center(d,'Sujeto a alcance, hojas, citas y correcciones',1802,24,dark,False,False)
  else:
   center(d,'CONSULTA INICIAL GRATUITA',1503,42,brown,True)
   center(d,'MAGÍSTER CARLOS CABALLERO',1573,36,dark,True,False)
   center(d,'+51 948 370 116',1655,65,brown,True)
   center(d,'systeraprime.com',1740,36,dark,True,False)
   center(d,'Proyectos integrales: evaluación personalizada',1810,21,dark,False,False)
  d.line((65,1863,1015,1863),fill=brown,width=2)
  center(d,f'REEL {reel:02d}  •  SysTeraPrime  •  WhatsApp +51 948 370 116',1880,20,dark,False,False)
  p=work/f'overlay{scene}.png';im.save(p);return p
 parts=[]
 for j in range(5):
  card=picture(j)
  piece=work/f'part{j}.mp4';vid=work/f'c{j}.mp4'
  # Source is real-motion footage: entire actor footage is shown, not illustrated
  filt=('[0:v]fps=24,scale=1080:1290:force_original_aspect_ratio=increase,crop=1080:1290,'
        'setsar=1,eq=contrast=1.03:saturation=0.98[real];'
        '[real][1:v]overlay=0:0:shortest=1,format=yuv420p[v]')
  run('ffmpeg','-y','-v','error','-stream_loop','-1','-i',vid,
      '-loop','1','-framerate','24','-i',card,
      '-filter_complex',filt,'-map','[v]','-t','8.32','-r','24',
      '-an','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p',piece)
  parts.append(piece)
 # Four different types of transitions across ten films, no static frames
 trans=['fade','smoothleft','smoothright','circleopen','dissolve','wipeup','wipedown','fadeblack','slideup','slideright']
 inputs=[]
 for p in parts:inputs.extend(['-i',str(p)])
 filters=[];prev='0:v'
 for j in range(1,5):
  nextname=f'v{j}';offset=round(j*7.92,3)
  transition=trans[(idx+j-1)%10]
  filters.append(f'[{prev}][{j}:v]xfade=transition={transition}:duration=0.4:offset={offset}[{nextname}]')
  prev=nextname
 filters.append(f'[{prev}]trim=duration=40,setpts=PTS-STARTPTS,format=yuv420p[video]')
 visuals=work/'visuals.mp4'
 run('ffmpeg','-y','-v','error',*inputs,'-filter_complex',';'.join(filters),
     '-map','[video]','-t','40','-r','24','-c:v','libx264',
     '-preset','veryfast','-crf','23','-pix_fmt','yuv420p',visuals)
 # Each movie receives its own original score with different instruments, key and rhythm
 mid=MidiFile(ticks_per_beat=480)
 bpm=[96,92,102,88,100,90,98,94,104,86][idx]
 temp=MidiTrack();temp.append(MetaMessage('set_tempo',tempo=bpm2tempo(bpm),time=0));mid.tracks.append(temp)
 origins=[50,53,55,52,57,48,54,51,56,49]
 base=origins[idx]
 patterns=[(0,7,12),(0,5,9),(0,4,7),(0,7,10)]
 instruments=[0,11,48,24,46,6,5,40,1,0]
 tracks=[(0,instruments[idx]),(1,[48,49,50,42,46,48,49,45,50,48][idx])]
 for ch,program in tracks:
  t=MidiTrack();mid.tracks.append(t)
  t.append(Message('program_change',channel=ch,program=program,time=0))
  events=[]
  for bar in range(19):
   start=bar*4
   chord=patterns[(bar+(idx%4))%4]
   notes=[base+n+(bar%3-1)*2 for n in chord]
   if ch==0:
    for beat in range(8):
     pitch=notes[(beat+idx)%3]+(12 if beat in (3,7) else 0)
     events.append((int((start+beat*.5)*480),1,pitch,40+((beat+idx)%4)*4))
     events.append((int((start+beat*.5+.43)*480),0,pitch,0))
   else:
    for pitch in notes:
     events.append((start*480,1,pitch,23))
     events.append(((start+3.88)*480,0,pitch,0))
  events.sort(key=lambda z:(z[0],z[1]));last=0
  for tick,on,pitch,velocity in events:
   t.append(Message('note_on' if on else 'note_off',channel=ch,note=pitch,velocity=velocity,time=tick-last));last=tick
  t.append(MetaMessage('end_of_track'))
 midi=work/'music.mid';mid.save(midi)
 sf='/usr/share/sounds/sf2/FluidR3_GM.sf2'
 if not pathlib.Path(sf).exists():sf='/usr/share/sounds/sf2/TimGM6mb.sf2'
 music=work/'music.wav'
 run('fluidsynth','-ni','-g','0.65',sf,midi,'-F',music,'-r','44100')
 # Pitch-preserving speed correction, only what is required to fit 39 seconds.
 stretch=max(0.90,min(1.55,voice_duration/38.7))
 mix=work/'mix.m4a'
 af=(f'[0:a]atempo={stretch:.5f},apad,atrim=duration=40,volume=1.30[voice];'
     '[1:a]apad,atrim=duration=40,afade=t=out:st=38:d=2,volume=0.22[music];'
     '[voice][music]amix=inputs=2:duration=first:dropout_transition=0[a]')
 run('ffmpeg','-y','-v','error','-i',audio,'-i',music,'-filter_complex',af,'-map','[a]',
     '-t','40','-c:a','aac','-b:a','160k',mix)
 target=out/f'REEL_{reel:02d}_SYSTERAPRIME_TESIS_CINE_40s.mp4'
 run('ffmpeg','-y','-v','error','-i',visuals,'-i',mix,'-map','0:v:0','-map','1:a:0',
     '-c:v','copy','-c:a','copy','-t','40','-movflags','+faststart',target)
 duration=probe(target)
 stream=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_type,width,height','-of','json',target],capture_output=True,text=True,check=True)
 dat=json.loads(stream.stdout)
 assert abs(duration-40)<.18,('Bad duration',duration)
 assert any(s.get('codec_type')=='video' and s.get('width')==1080 and s.get('height')==1920 for s in dat['streams'])
 assert any(s.get('codec_type')=='audio' for s in dat['streams'])
 print('VERIFIED',target, 'DURATION',duration,'SIZE',target.stat().st_size,'VOICE',cfg['voices'][idx],flush=True)
 meta={'reel':reel,'story':entry['title'],'voice':cfg['voices'][idx],'footage':chosen,'duration':duration,'size':target.stat().st_size}
 (out/f'REEL_{reel:02d}_INFO.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
 # Six stills for QA only; user receives real-motion MP4
 ims=[]
 for k,second in enumerate([2,9,16,23,31,38]):
  p=work/f'check{k}.jpg'
  run('ffmpeg','-y','-v','error','-ss',second,'-i',target,'-frames:v','1',p)
  ims.append(Image.open(p).convert('RGB').resize((270,480)))
 c=Image.new('RGB',(810,960),'white')
 for k,im in enumerate(ims):c.paste(im,((k%3)*270,(k//3)*480))
 c.save(out/f'REEL_{reel:02d}_QA.jpg',quality=86)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--reel',type=int,required=True)
 main(parser.parse_args().reel)
