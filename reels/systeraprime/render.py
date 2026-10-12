#!/usr/bin/env python3
"""Reel cinematografico SysTeraPrime: video stock filmado, no diapositivas."""
import asyncio, math, os, re, subprocess, sys, wave
from pathlib import Path
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT=Path(__file__).resolve().parent
WORK=ROOT/"work"
WORK.mkdir(parents=True,exist_ok=True)
OUT=ROOT/"SysTeraPrime_PELICULA_40s_REEL.mp4"
W,H,FPS=720,1280,24
DUR=5
SERIF="/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GOLD=(243,198,112); WHITE=(255,251,239); MUTED=(230,223,208)
SCENES=[
 ("a-woman-working-in-a-boardroom-1785","¿SU TESIS NO AVANZA?","ASESORÍA ACADÉMICA","Profesional • personalizada",""),
 ("elegant-woman-working-hard-in-an-office-44787","APOYO EN TAREAS","ACOMPAÑAMIENTO","Orientación por actividad","S/ 15"),
 ("a-man-wearing-a-suit-works-at-the-office-1816","INFORMES Y APA","REDACCIÓN ACADÉMICA","Normas APA • referencias","S/ 30"),
 ("portrait-of-an-elegant-woman-working-in-her-office-44790","ESTADÍSTICA","ANÁLISIS DE DATOS","Resultados e interpretación","S/ 30"),
 ("professional-woman-working-in-an-office-42664","PROYECTOS","INGENIERÍA Y SISTEMAS","Análisis • documentación","S/ 50"),
 ("a-woman-working-with-her-laptop-1788","INVESTIGACIONES","TESINAS Y ARTÍCULOS","Metodología • revisión","S/ 80"),
 ("elegant-woman-taking-a-call-in-the-office-44785","ASESORÍA DE TESIS","PROYECTO DE INVESTIGACIÓN","Guía por etapas • observaciones","S/ 150"),
 ("a-woman-working-in-her-office-199","¿SU SERVICIO NO APARECE?","COTICE GRATIS","Evaluamos su proyecto a medida",""),
]
def font(path,size):return ImageFont.truetype(path,size)
def center(draw,text,y,f,fill):
  b=draw.textbbox((0,0),text,font=f); draw.text(((W-(b[2]-b[0]))/2,y),text,font=f,fill=fill,stroke_width=1,stroke_fill=(28,24,26))
def get_video(slug,i):
  dest=WORK/f"clip_{i:02d}.mp4"
  if dest.exists() and dest.stat().st_size>80000:return dest
  session=requests.Session()
  session.headers.update({"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36","Referer":"https://mixkit.co/"})
  attempts=[f"https://assets.mixkit.co/videos/preview/mixkit-{slug}-{sz}.mp4" for sz in ("large","medium","small")]
  for url in attempts:
    try:
      with session.get(url,timeout=45,stream=True) as r:
        if r.status_code!=200:
          print('CDN HTTP',r.status_code,url,flush=True)
          continue
        with dest.open("wb") as f:
          for block in r.iter_content(1024*256):
            if block:f.write(block)
      with dest.open("rb") as f:header=f.read(48)
      if b'ftyp' not in header: print('INVALID HEADER',slug,repr(header[:30]),flush=True)
      if b"ftyp" in header and dest.stat().st_size>80000:
        print("DOWNLOADED",slug,dest.stat().st_size,flush=True);return dest
    except Exception as e:print("download retry",slug,str(e)[:100],flush=True)
    dest.unlink(missing_ok=True)
  return None
def overlay(scene,index):
  title,kicker,detail,price=scene[1:]
  im=Image.new("RGBA",(W,H),(0,0,0,0))
  d=ImageDraw.Draw(im)
  # Subtle dark gradient for text legibility; remains one full-frame film scene.
  for y in range(H):
    a=int(5+max(0,1-y/650)*28+max(0,(y-565)/(H-565))*204)
    d.rectangle((0,y,W,y+1),fill=(6,16,26,min(218,a)))
  d.rounded_rectangle((34,38,W-34,130),radius=16,fill=(8,26,38,175),outline=GOLD,width=2)
  center(d,"SysTeraPrime",54,font(SERIF,46),GOLD)
  d.line([(70,150),(650,150)],fill=GOLD,width=3)
  center(d,"APOYO ACADÉMICO • METODOLOGÍA • INVESTIGACIÓN",169,font(BOLD,19),WHITE)
  # Lower-third with champagne gold editorial treatment
  d.rounded_rectangle((35,745,W-35,1218),radius=29,fill=(8,18,31,227),outline=GOLD,width=3)
  center(d,title,782,font(BOLD,34),WHITE)
  center(d,kicker,847,font(SERIF,28),GOLD)
  center(d,detail,902,font(SANS,22),MUTED)
  if price:
    center(d,"DESDE",954,font(BOLD,23),WHITE)
    center(d,price,988,font(SERIF,77),GOLD)
  else:
    center(d,"¡ESCRÍBANOS HOY!",975,font(SERIF,36),GOLD)
  d.line((75,1113,646,1113),fill=GOLD,width=2)
  center(d,"WhatsApp  +51 948 370 116",1130,font(BOLD,28),WHITE)
  center(d,"systeraprime.com",1170,font(SANS,22),GOLD)
  if index==7:
    d.rounded_rectangle((36,530,W-36,724),radius=16,fill=(10,22,34,223),outline=GOLD,width=2)
    for j,line in enumerate(("PRECIOS REFERENCIALES","Sujeto a hojas, complejidad, citas,","correcciones y requerimientos")):
      center(d,line,552+j*47,font(BOLD if j==0 else SANS,24),GOLD if j==0 else WHITE)
  out=WORK/f"overlay_{index:02d}.png";im.save(out);return out
def cmd(args):
  print("RUN", " ".join(map(str,args))[:240],flush=True)
  subprocess.run([str(x) for x in args],check=True)
def probe(path):
  s=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1",str(path)]).decode().strip()
  return float(s)
def make_music():
  sr=24000;sec=40
  n=np.arange(sr*sec,dtype=np.float64);data=np.zeros(n.shape,dtype=np.float64)
  roots=[196.00,174.61,220.00,164.81]
  for k in range(0,40,2):
    root=roots[(k//2)%4]
    for semitone,volume in [(0,.018),(4,.014),(7,.012),(12,.006)]:
      freq=root*(2**(semitone/12))
      length=int(sr*1.8);tt=np.arange(length)/sr
      env=np.exp(-tt*2.4)*(1-np.exp(-tt*24))
      tone=env*(np.sin(2*np.pi*freq*tt)+.25*np.sin(2*np.pi*2*freq*tt))
      data[k*sr:k*sr+length]+=tone*volume
  data=np.clip(data,-.6,.6)
  out=WORK/"music.wav"
  with wave.open(str(out),"wb") as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
    f.writeframes((data*32767).astype("<i2").tobytes())
  return out
async def create_voice():
  script=("¿Su tesis está estancada? En SysTeraPrime le ayudamos a avanzar "
  "con orientación académica personalizada. Apoyo en tareas desde quince soles, "
  "informes y normas APA desde treinta, estadística desde treinta, "
  "proyectos de ingeniería desde cincuenta, investigaciones desde ochenta "
  "y asesoría de tesis desde ciento cincuenta soles. "
  "El presupuesto depende de hojas, complejidad, correcciones y requerimientos. "
  "¿No encuentra su servicio? Consulte gratis por WhatsApp "
  "al más cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.")
  raw=WORK/"locutora_es_mexico.mp3"
  await edge_tts.Communicate(script,voice="es-MX-DaliaNeural",rate="+10%",pitch="+0Hz").save(str(raw))
  d=probe(raw);target=38.5;speed=max(1,d/target)
  out=WORK/"voz_final.m4a"
  cmd(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",raw,"-af",f"atempo={speed:.5f},aresample=48000","-c:a","aac","-b:a","112k",out])
  print("VOICE",d,"adjusted",probe(out),flush=True)
  return out
def build():
  videos=[get_video(s[0],i) for i,s in enumerate(SCENES)]
  valid=[p for p in videos if p]
  if len(set(map(str,valid)))<5:raise RuntimeError("Menos de 5 tomas reales descargadas; no sustituir por fotografías.")
  for i in range(len(videos)):
    if videos[i] is None:videos[i]=valid[i%len(valid)]
  for i,(scene,src) in enumerate(zip(SCENES,videos)):
    png=overlay(scene,i)
    part=WORK/f"part_{i:02d}.mp4"
    # The actor footage changes on every frame: these are real filmed video segments.
    cmd(["ffmpeg","-y","-hide_banner","-loglevel","error",
     "-ss","0.3","-i",src,"-loop","1","-i",png,
     "-filter_complex",f"[0:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,trim=duration=5,setpts=PTS-STARTPTS,eq=contrast=1.035:saturation=1.03[bg];[bg][1:v]overlay=0:0:shortest=1,format=yuv420p,fade=t=in:st=0:d=0.25,fade=t=out:st=4.7:d=0.3[v]",
     "-map","[v]","-an","-t","5","-r",str(FPS),"-c:v","libx264","-pix_fmt","yuv420p","-preset","veryfast","-b:v","1250k","-maxrate","1500k","-bufsize","2400k",part])
  lst=WORK/"parts.txt"
  lst.write_text("".join("file '"+str((WORK/f"part_{i:02d}.mp4").resolve())+"'\n" for i in range(8)))
  music=make_music()
  try:voice=asyncio.run(create_voice())
  except Exception as e:
    raise RuntimeError("Falló la locución femenina natural; se detiene la exportación para evitar entregar otro MP4 sin voz.") from e
  cmd(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",lst,"-i",voice,"-i",music,
     "-filter_complex","[1:a]volume=1.0,apad=pad_dur=40[voice];[2:a]volume=0.20[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=0,atrim=0:40,afade=t=out:st=39:d=1[a]",
     "-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","112k","-t","40","-movflags","+faststart",OUT])
  dur=probe(OUT);size=OUT.stat().st_size
  print("RESULT",OUT,"SECONDS",dur,"BYTES",size,flush=True)
  if not (39.8<=dur<=40.2):raise RuntimeError("Duración incorrecta "+str(dur))
  if size>10_000_000:raise RuntimeError("Archivo supera 10MB "+str(size))
if __name__=="__main__":
  build()
