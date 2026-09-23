"""Renderer gratuito local: formatos 1080x1920, gráficos originales, audio sintetizado.
No presenta la música como voz humana ni garantiza la elegibilidad de monetización.
"""
from __future__ import annotations
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import math
import numpy as np
import subprocess
import tempfile
import wave

FONT='/usr/share/fonts/truetype/lato/Lato-Heavy.ttf'
REG='/usr/share/fonts/truetype/lato/Lato-Regular.ttf'
BACKUP='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
W,H=1080,1920

def font(px,heavy=False):
    p=FONT if heavy else REG
    if not Path(p).exists():p=BACKUP
    return ImageFont.truetype(p,px)

def wrap(draw,text,ft,maxwidth):
    words=text.split()
    lines=[]; current=''
    for word in words:
        test=(current+' '+word).strip()
        if draw.textbbox((0,0),test,font=ft)[2] <= maxwidth: current=test
        else:
            if current:lines.append(current)
            current=word
    if current:lines.append(current)
    return lines

def draw_frame(short,index,total,head,body,output):
    # Fondo claro, contrastes verde cálido y naranja, mapa global sutil.
    img=Image.new('RGB',(W,H),(248,247,242));draw=ImageDraw.Draw(img)
    # Franjas y círculos translúcidos estilizados; evitar fotos de stock.
    draw.rounded_rectangle((48,56,W-48,150),radius=25,fill=(24,97,76))
    draw.text((76,76),'SYSTERACORE   /   SYSTERA LATAM',fill='white',font=font(42,True))
    draw.ellipse((650,280,1240,870),outline=(221,229,220),width=6)
    for lat in range(-2,3):
        y=575+lat*65
        draw.arc((650,y-120,1240,y+120),0,360,fill=(225,228,220),width=3)
    for lon in range(-2,3):
        x=940+lon*75
        draw.arc((x-130,280,x+130,870),90,270,fill=(225,228,220),width=3)
    draw.rounded_rectangle((64,295,1016,1185),radius=60,fill=(255,255,255),outline=(223,228,220),width=4)
    accent=(231,111,61) if short['topic'].lower().startswith('power') else (32,124,83)
    draw.rounded_rectangle((110,375,246,388),radius=6,fill=accent)
    h=font(89 if len(head)<25 else 69,True)
    lines=wrap(draw,head.upper(),h,850)
    cy=440
    for line in lines:
        draw.text((114,cy),line,font=h,fill=(27,45,37));cy+=120 if len(head)<25 else 99
    cy=max(cy+80,800)
    f=font(66)
    for line in wrap(draw,body,f,830):
        draw.text((114,cy),line,font=f,fill=(66,77,68));cy+=92
    draw.text((95,1330),'RESULTADOS REALES, NO PROMESAS',font=font(47,True),fill=(40,115,82))
    for i in range(1,6):
        x=105+(i-1)*182
        fill=accent if i<=index+1 else (219,223,214)
        draw.rounded_rectangle((x,1450,x+154,1468),radius=9,fill=fill)
    draw.rounded_rectangle((72,1580,1007,1830),radius=45,fill=(27,93,72))
    draw.text((118,1610),'PROYECTOS A MEDIDA',font=font(62,True),fill='white')
    draw.text((118,1697),'WhatsApp: +51 948 370 116',font=font(49),fill=(255,234,204))
    draw.text((92,1875),'Ing. Carlos Andrés Caballero Castillo',font=font(33),fill=(72,78,68))
    img.save(output,optimize=True)

def make_audio(seconds,path):
    # Audio instrumental electrónico original. No usa muestras de terceros.
    sr=22050;t=np.arange(int(seconds*sr),dtype=np.float64)/sr
    harmonies=[196.0,246.94,293.66,392.0]
    sample=np.zeros_like(t)
    for i,h in enumerate(harmonies):
        # Entrada/salida lenta, volumen bajo para no saturar.
        sample+=(0.055/(i+1))*np.sin(2*np.pi*h*t)*(0.5+0.5*np.sin(2*np.pi*.115*t+i))
    beat=np.exp(-((t*2.0)%1)*18)*np.sin(2*np.pi*(65-20*((t*2)%1))*t)*.09
    fade=np.minimum(np.minimum(t/1.2,(seconds-t)/1.2),1).clip(0,1)
    sound=np.int16(np.clip((sample+beat)*fade,-1,1)*32767)
    with wave.open(str(path),'w') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(sr)
        wav.writeframes(sound.tobytes())

def render_short(short:dict,destination:Path,seconds_per_frame=5):
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    frames=[('¿SABÍA QUE...?',short['hook'])]+[(h,b) for h,b in short['scenes']]
    with tempfile.TemporaryDirectory(prefix='systera_vid_') as temp:
        temp=Path(temp)
        concat=[]
        for i,(head,body) in enumerate(frames):
            p=temp/f'scene_{i:02}.png'
            draw_frame(short,i,len(frames),head,body,p)
            concat.extend([f"file '{p}'",f'duration {seconds_per_frame}'])
        concat.append(f"file '{temp/f'scene_{len(frames)-1:02}.png'}'")
        (temp/'frames.txt').write_text('\n'.join(concat)+'\n',encoding='utf-8')
        total=len(frames)*seconds_per_frame
        make_audio(total,temp/'audio.wav')
        subprocess.run(['ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y',
            '-safe','0','-f','concat','-i',str(temp/'frames.txt'),'-i',str(temp/'audio.wav'),
            '-vf','fps=24,format=yuv420p','-c:v','libx264','-preset','ultrafast',
            '-crf','26','-c:a','aac','-b:a','128k','-t',str(total),'-movflags','+faststart',
            '-shortest',str(destination)],check=True,timeout=220)
    return destination
