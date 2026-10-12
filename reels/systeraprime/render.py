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
W,H,FPS=900,1600,24
DUR=5
SERIF="/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GOLD=(243,198,112); WHITE=(255,251,239); MUTED=(230,223,208)
SCENES=[
 ("a-young-woman-gazes-a-the-bookshelf-in-the-library-50728","¿TU TESIS SIGUE PENDIENTE?","INVESTIGA CON CRITERIO","Acompañamiento académico profesional",""),
 ("a-woman-reading-a-book-at-a-coffee-shop-225","TAREAS ACADÉMICAS","ORIENTACIÓN PERSONALIZADA","Organización y revisión","S/ 15"),
 ("a-woman-gently-turning-the-pages-of-a-book-50731","INFORMES Y MONOGRAFÍAS","NORMAS APA","Estructura • fuentes • referencias","S/ 30"),
 ("a-woman-using-a-tablet-1784","ESTADÍSTICA","ANÁLISIS DE DATOS","Resultados • gráficos • interpretación","S/ 30"),
 ("business-woman-on-call-while-working-42628","PROYECTOS Y SISTEMAS","DESARROLLO TÉCNICO","Análisis • diseño • documentación","S/ 50"),
 ("a-young-woman-scans-the-library-shelf-and-then-picks-50718","INVESTIGACIONES","TESINAS Y ARTÍCULOS","Metodología • revisión • referencias","S/ 80"),
 ("a-young-student-woman-picks-a-book-from-the-library-50714","ASESORÍA INTEGRAL DE TESIS","AVANCE POR ETAPAS","Guía metodológica • observaciones","S/ 150"),
 ("close-up-view-of-a-cheerful-woman-on-a-phone-49933","¿NECESITA OTRO SERVICIO?","COTIZACIÓN GRATUITA","Cuéntenos su proyecto académico",""),
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
  attempts.append("https://huggingface.co/datasets/FastVideo/Mixkit-Src/resolve/main/Woman/mixkit-"+slug+"_clip_1.mp4?download=true")
  attempts.append("https://huggingface.co/datasets/FastVideo/Mixkit-Src/resolve/main/Business/mixkit-"+slug+"_clip_1.mp4?download=true")
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
  # Cinematic light and gold. The full frame remains a continuous live-action shot.
  for y in range(H):
    bottom=max(0.0,min(1.0,(y-980)/560))
    top=max(0.0,1.0-y/300)
    a=int(4+int(bottom*bottom*216)+int(top*top*84))
    d.line([(0,y),(W,y)],fill=(12,16,19,min(230,a)))
  # Small luxury emblem and consistent branding, not a collage/card.
  d.line((76,68,824,68),fill=(219,182,112,218),width=2)
  center(d,"SysTeraPrime",86,font(SERIF,64),(248,210,141))
  center(d,"ASESORÍA ACADÉMICA  |  INVESTIGACIÓN",167,font(BOLD,22),WHITE)
  d.line((285,220,615,220),fill=(221,187,122,185),width=3)
  if index==0:
    center(d,"EL SIGUIENTE CAPÍTULO",1115,font(SERIF,50),WHITE)
    center(d,"EMPIEZA HOY",1190,font(SERIF,70),GOLD)
    center(d,"TU INVESTIGACIÓN, TU AUTORÍA",1310,font(BOLD,31),WHITE)
  elif index==7:
    center(d,"¿NO VE SU SERVICIO?",1038,font(SERIF,49),WHITE)
    center(d,"CONSULTE GRATIS",1125,font(SERIF,58),GOLD)
    center(d,"WhatsApp",1209,font(BOLD,31),WHITE)
    center(d,"+51 948 370 116",1260,font(SERIF,53),GOLD)
    center(d,"PRECIOS REFERENCIALES DESDE",1370,font(BOLD,24),WHITE)
    center(d,"Varían según hojas, procesos, complejidad,",1407,font(SANS,22),WHITE)
    center(d,"citas, correcciones y requerimientos.",1443,font(SANS,22),WHITE)
  else:
    # Big clear one-price-at-a-time titles, not a multi-service chart.
    titlefont=font(SERIF,54 if len(title)<22 else 44)
    center(d,title,1083,titlefont,WHITE)
    d.line((218,1174,682,1174),fill=(220,182,105,198),width=2)
    center(d,kicker,1195,font(BOLD,33),GOLD)
    center(d,detail,1260,font(SANS,25),WHITE)
    center(d,"DESDE",1328,font(BOLD,24),WHITE)
    center(d,price,1370,font(SERIF,78),GOLD)
  center(d,"systeraprime.com",1530,font(BOLD,26),WHITE)
  out=WORK/f"overlay_{index:02d}.png"; im.save(out);return out
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
def create_voice():
  url="https://dnznrvs05pmza.cloudfront.net/text_to_speech/772ebe79-b636-4bdb-904b-4d21e4a83b9c/SysTeraPrime_Locuci_n_Premium_Cine_40s.mp3?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMTAwMmNjNzcxZDM4Nzg1NCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5MTkzNzI3MX0.UaeMmfP5pwhN7AgorWs7B8sMhPr82HHJ5WZdvgSB8vw"
  raw=WORK/"locutora_es_mexico.mp3"
  response=requests.get(url,timeout=50,headers={"User-Agent":"Mozilla/5.0"})
  print("VOICE DOWNLOAD",response.status_code,len(response.content),flush=True)
  response.raise_for_status()
  raw.write_bytes(response.content)
  if b"ID3" not in response.content[:10] and b"\xff\xfb" not in response.content[:10] and b"\xff\xf3" not in response.content[:10]:print("Audio may have nonstandard header; ffprobe validates",flush=True)
  d=probe(raw); target=38.5; speed=max(1,d/target)
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
     "-stream_loop","-1","-ss","0.0","-i",src,"-loop","1","-i",png,
     "-filter_complex",f"[0:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,trim=duration=5,setpts=PTS-STARTPTS,eq=contrast=1.08:brightness=0.018:saturation=1.12[bg];[bg][1:v]overlay=0:0:shortest=1,format=yuv420p,fade=t=in:st=0:d=0.25,fade=t=out:st=4.7:d=0.3[v]",
     "-map","[v]","-an","-t","5","-r",str(FPS),"-c:v","libx264","-pix_fmt","yuv420p","-preset","veryfast","-b:v","1450k","-maxrate","1750k","-bufsize","2400k",part])
  lst=WORK/"parts.txt"
  lst.write_text("".join("file '"+str((WORK/f"part_{i:02d}.mp4").resolve())+"'\n" for i in range(8)))
  music=make_music()
  try:voice=create_voice()
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
