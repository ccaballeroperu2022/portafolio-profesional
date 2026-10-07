from __future__ import annotations
import asyncio, json, math, os, random, subprocess, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import edge_tts

W,H,FPS=1080,1920,30
SCENES=6
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"
OUT.mkdir(parents=True,exist_ok=True)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def ft(n,b=False): return ImageFont.truetype(BOLD if b else FONT,n)
def rgb(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def tint(c,a=.8): return tuple(int(v+(255-v)*a) for v in c)
def rr(d,b,r,fill,outline=None,w=1): d.rounded_rectangle(b,radius=r,fill=fill,outline=outline,width=w)
def wrap(d,s,f,m):
    lines=[]; cur=""
    for word in s.split():
        t=(cur+" "+word).strip()
        if d.textlength(t,font=f)<=m: cur=t
        else:
            if cur: lines.append(cur)
            cur=word
    if cur: lines.append(cur)
    return lines
def paragraph(d,s,x,y,f,color,maxw,leading=None,maxlines=5):
    leading=leading or int(f.size*1.23)
    for line in wrap(d,s,f,maxw)[:maxlines]:
        d.text((x,y),line,font=f,fill=color); y+=leading
    return y
def icon_excel(d,x,y,s,p):
    rr(d,(x,y,x+s,y+s),int(s*.18),p); d.text((x+s*.31,y+s*.16),"X",font=ft(int(s*.52),True),fill="white")
def icon_pbi(d,x,y,s,ink):
    rr(d,(x,y,x+s,y+s),int(s*.18),"#F2C811")
    for i,h in enumerate([.22,.38,.55,.72]):
        xx=x+s*(.25+i*.13); d.rounded_rectangle((xx,y+s*(.79-h),xx+s*.08,y+s*.79),radius=4,fill=ink)
def icon_wa(d,x,y,s):
    d.ellipse((x,y,x+s,y+s),fill="#20B95A"); d.arc((x+s*.22,y+s*.20,x+s*.78,y+s*.75),195,505,fill="white",width=max(4,int(s*.075)))
    d.polygon([(x+s*.28,y+s*.68),(x+s*.19,y+s*.83),(x+s*.40,y+s*.74)],fill="white")
def chrome(d,app,p,ink):
    d.rectangle((0,0,W,112),fill="#FCFCFA")
    if app=="Excel": icon_excel(d,34,24,62,p); name="Excel"; menu="Archivo   Inicio   Insertar   Fórmulas   Datos   Revisar   Vista"
    else: icon_pbi(d,34,24,62,ink); name="Power BI"; menu="Archivo   Inicio   Insertar   Modelado   Ver   Ayuda"
    d.text((118,27),name,font=ft(28,True),fill=ink); d.text((118,70),menu,font=ft(18),fill="#696762")
    d.line((0,111,W,111),fill="#E4E1DA",width=2)

def bg_image(bg,p,s,seed):
    im=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(im); rng=random.Random(seed)
    for k in range(11):
        cx=rng.randint(-180,W+180); cy=rng.randint(140,H+160); r=rng.randint(100,360)
        base=p if k%2==0 else s; d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=tint(base,.82+rng.random()*.12))
    return im.filter(ImageFilter.GaussianBlur(20))

def metrics(d,p,s,ink,y,labels):
    x=58
    for i,(a,b) in enumerate(labels):
        rr(d,(x,y,x+302,y+164),28,"white",outline="#E5E2DB",w=2)
        d.text((x+25,y+22),a,font=ft(19,True),fill="#79756F"); d.text((x+25,y+62),b,font=ft(42,True),fill=p if i%2==0 else ink)
        d.rounded_rectangle((x+244,y+36,x+280,y+72),radius=11,fill=s if i%2 else tint(p,.62)); x+=332

def chart(d,kind,b,p,s,ink,seed):
    x0,y0,x1,y1=b; rng=random.Random(seed); rr(d,b,32,"white",outline="#E4E1DA",w=2)
    d.text((x0+34,y0+28),"VISUAL ANALÍTICO",font=ft(18,True),fill="#79756F")
    ax=(x0+48,y0+78,x1-44,y1-46); aw=ax[2]-ax[0]; ah=ax[3]-ax[1]
    if kind=="bars":
        for i,v in enumerate([42,68,58,83,65,94,77]):
            bw=aw/7; hh=ah*v/110; xx=ax[0]+i*bw+10; d.rounded_rectangle((xx,ax[3]-hh,xx+bw-20,ax[3]),radius=10,fill=p if i%2==0 else s)
    elif kind in ("line","area","sla"):
        vals=[42,55,48,70,64,83,76,95]; pts=[(ax[0]+i*aw/7,ax[3]-v*ah/110) for i,v in enumerate(vals)]
        if kind=="area": d.polygon([(pts[0][0],ax[3])]+pts+[(pts[-1][0],ax[3])],fill=tint(s,.55))
        d.line(pts,fill=p,width=8,joint="curve")
        for xx,yy in pts: d.ellipse((xx-8,yy-8,xx+8,yy+8),fill=s,outline="white",width=3)
        if kind=="sla": d.line((ax[0],ax[1]+ah*.30,ax[2],ax[1]+ah*.30),fill="#D94E4E",width=4)
    elif kind=="waterfall":
        cur=ax[3]-70
        for i,v in enumerate([34,-14,25,-9,37,-13]):
            bw=aw/6; hh=abs(v)*6; a=cur-hh if v>0 else cur; z=cur if v>0 else cur+hh
            d.rounded_rectangle((ax[0]+i*bw+8,a,ax[0]+(i+1)*bw-12,z),radius=8,fill=p if v>0 else s); cur=a if v>0 else z
    elif kind=="donut":
        cx=(ax[0]+ax[2])//2; cy=(ax[1]+ax[3])//2; r=min(aw,ah)//3
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=s); d.pieslice((cx-r,cy-r,cx+r,cy+r),18,292,fill=p)
        d.ellipse((cx-r*.52,cy-r*.52,cx+r*.52,cy+r*.52),fill="white"); d.text((cx-70,cy-28),"76%",font=ft(48,True),fill=ink)
    elif kind=="radar":
        cx=(ax[0]+ax[2])//2; cy=(ax[1]+ax[3])//2; r=min(aw,ah)*.37; n=6
        for f in (.33,.66,1):
            pts=[(cx+r*f*math.cos(-math.pi/2+2*math.pi*i/n),cy+r*f*math.sin(-math.pi/2+2*math.pi*i/n)) for i in range(n)]; d.line(pts+[pts[0]],fill="#D7D5CE",width=2)
        vals=[.78,.55,.92,.68,.84,.63]; pts=[(cx+r*vals[i]*math.cos(-math.pi/2+2*math.pi*i/n),cy+r*vals[i]*math.sin(-math.pi/2+2*math.pi*i/n)) for i in range(n)]
        d.polygon(pts,fill=tint(s,.50),outline=p)
    elif kind=="gauge":
        cx=(ax[0]+ax[2])//2; cy=ax[3]-20; r=min(aw*.36,ah*.72)
        d.arc((cx-r,cy-r,cx+r,cy+r),180,360,fill="#D6D5CF",width=42); d.arc((cx-r,cy-r,cx+r,cy+r),180,326,fill=p,width=42)
        a=math.radians(326); d.line((cx,cy,cx+r*.72*math.cos(a),cy+r*.72*math.sin(a)),fill=ink,width=10); d.ellipse((cx-16,cy-16,cx+16,cy+16),fill=ink)
    elif kind=="heatmap":
        rows,cols=5,7; cw=aw/cols; ch=ah/rows
        for r in range(rows):
            for c in range(cols):
                q=(r*cols+c)/(rows*cols); col=tuple(int(p[i]*(1-q)+s[i]*q) for i in range(3))
                d.rounded_rectangle((ax[0]+c*cw+5,ax[1]+r*ch+5,ax[0]+(c+1)*cw-5,ax[1]+(r+1)*ch-5),radius=9,fill=col)
    elif kind=="funnel":
        cy=ax[1]+20
        for i,wf in enumerate([.92,.72,.54,.38]):
            ww=aw*wf; hh=ah*.18; cx=(ax[0]+ax[2])/2
            d.polygon([(cx-ww/2,cy),(cx+ww/2,cy),(cx+ww/2-28,cy+hh),(cx-ww/2+28,cy+hh)],fill=p if i%2==0 else s); cy+=hh+18
    elif kind in ("flow","pipeline","process","network"):
        pts=[(ax[0]+aw*.10,ax[1]+ah*.25),(ax[0]+aw*.33,ax[1]+ah*.48),(ax[0]+aw*.56,ax[1]+ah*.20),(ax[0]+aw*.72,ax[1]+ah*.68),(ax[0]+aw*.91,ax[1]+ah*.42)]
        for a,b in zip(pts,pts[1:]): d.line((a,b),fill=s,width=10)
        if kind=="network": d.line((pts[0],pts[3]),fill=tint(p,.4),width=5); d.line((pts[1],pts[4]),fill=tint(s,.2),width=5)
        for i,(xx,yy) in enumerate(pts): r=28+(i%2)*8; d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=p if i%2==0 else s,outline="white",width=4)
    elif kind=="kpi":
        vals=[("MARGEN","31%"),("YTD","+18%"),("META","94%"),("Δ MES","+7.4%")]
        for i,(lab,val) in enumerate(vals):
            cw=aw/2-18; ch=ah/2-18; xx=ax[0]+(i%2)*(cw+24); yy=ax[1]+(i//2)*(ch+24)
            rr(d,(xx,yy,xx+cw,yy+ch),22,tint(p,.90) if i%2==0 else tint(s,.90)); d.text((xx+24,yy+20),lab,font=ft(18,True),fill="#77736C"); d.text((xx+24,yy+62),val,font=ft(46,True),fill=ink)
    elif kind=="sheet":
        cols,rows=7,9; cw=aw/cols; ch=ah/rows
        for c in range(cols):
            d.rectangle((ax[0]+c*cw,ax[1],ax[0]+(c+1)*cw,ax[1]+ch),fill=tint(p,.72) if c<2 else "#F4F4F1"); d.text((ax[0]+c*cw+10,ax[1]+10),chr(65+c),font=ft(15,True),fill=ink)
        for r in range(1,rows):
            for c in range(cols):
                d.rectangle((ax[0]+c*cw,ax[1]+r*ch,ax[0]+(c+1)*cw,ax[1]+(r+1)*ch),fill="white" if (r+c)%2==0 else "#FAFAF7",outline="#E5E4DE")
                if c in (2,4,6): d.rectangle((ax[0]+c*cw+10,ax[1]+r*ch+ch*.35,ax[0]+c*cw+10+rng.randint(30,int(cw-20)),ax[1]+r*ch+ch*.60),fill=s)
    elif kind=="aging":
        for i,(lab,v) in enumerate([("0–30",92),("31–60",68),("61–90",47),("+90",29)]):
            yy=ax[1]+i*ah/4; d.text((ax[0],yy+22),lab,font=ft(20,True),fill=ink); d.rounded_rectangle((ax[0]+150,yy+18,ax[0]+150+aw*.72*v/100,yy+62),radius=13,fill=p if i<2 else s)
    elif kind=="scatter":
        for i in range(30):
            xx=rng.randint(int(ax[0]+20),int(ax[2]-20)); yy=rng.randint(int(ax[1]+20),int(ax[3]-20)); r=rng.randint(8,22); d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=p if i%3 else s)
    elif kind=="gantt":
        for i in range(6):
            yy=ax[1]+i*ah/6+18; start=rng.uniform(0,.38)*aw; dur=rng.uniform(.25,.52)*aw
            d.rounded_rectangle((ax[0]+start,yy,min(ax[0]+start+dur,ax[2]),yy+42),radius=12,fill=p if i%2==0 else s)
    else:
        pts=[(ax[0]+i*aw/6,ax[3]-[42,62,58,80,70,92,86][i]*ah/110) for i in range(7)]; d.line(pts,fill=p,width=8)
        for i,v in enumerate([55,78,66,90,84]): bw=aw*.075; xx=ax[0]+i*aw*.11; hh=ah*.42*v/100; d.rounded_rectangle((xx,ax[3]-hh,xx+bw,ax[3]),radius=8,fill=s)

def sentences(s):
    parts=[x.strip() for x in s.replace("? ","?. ").replace("! ","!. ").split(". ") if x.strip()]
    while len(parts)<4: parts.append(parts[-1] if parts else s)
    return parts[:4]

def make_scene(t,scene_i,reel_i,path):
    bg,phex,shex,ihex=t["colors"]; p,s,ink=rgb(phex),rgb(shex),rgb(ihex)
    im=bg_image(rgb(bg),p,s,reel_i*131+scene_i*17); d=ImageDraw.Draw(im)
    chrome(d,"Excel" if (reel_i+scene_i)%2==0 else "Power BI",p,ink)
    rr(d,(58,142,345,196),27,"white",outline="#E2DED6",w=2); d.text((82,157),"systeracore.com",font=ft(21,True),fill=ink)
    ss=sentences(t["narration"]); variant=reel_i%5
    if scene_i==0:
        x=[62,140,62,200,88][variant]; y=250
        y=paragraph(d,t["title"],x,y,ft(64,True),ink,920-x,76,4); d.text((x,y+18),t["tag"],font=ft(29,True),fill=p)
        chart(d,t["chart"],(58,540,1022,1398),p,s,ink,reel_i*11); rr(d,(58,1450,1022,1655),34,"white",outline="#E5E1D9",w=2)
        paragraph(d,t["service"],92,1490,ft(32,True),ink,850,42,2); d.text((92,1585),"Solución profesional • personalizada • medible",font=ft(23),fill=p)
    elif scene_i==1:
        d.text((62,255),"DIAGNÓSTICO",font=ft(24,True),fill=p); paragraph(d,ss[0],62,320,ft(48,True),ink,930,61,5)
        metrics(d,p,s,ink,680,[("TIEMPO","↓"),("CONTROL","↑"),("RIESGO","↓")]); chart(d,t["chart"],(62,930,1018,1648),p,s,ink,reel_i*17+1)
    elif scene_i==2:
        d.text((62,255),"SOLUCIÓN",font=ft(24,True),fill=p); paragraph(d,ss[1],62,320,ft(43,True),ink,930,55,5)
        chart(d,t["chart"],(62,680,1018,1510),p,s,ink,reel_i*23+2); rr(d,(62,1550,1018,1690),30,p); d.text((94,1593),"Excel + Power BI + lógica de negocio",font=ft(30,True),fill="white")
    elif scene_i==3:
        d.text((62,255),"VENTAJA",font=ft(24,True),fill=p); paragraph(d,ss[2],62,320,ft(43,True),ink,930,55,5)
        cards=[("01",t["tag"].split(" • ")[0]),("02",t["service"]),("03","Trazabilidad y control"),("04","Decisiones con evidencia")]
        y=760
        for j,(num,txt) in enumerate(cards):
            xx=62 if j%2==0 else 150; ww=956 if j%2==0 else 868; rr(d,(xx,y,xx+ww,y+142),30,"white",outline="#E5E2DB",w=2)
            d.ellipse((xx+28,y+37,xx+88,y+97),fill=p if j%2==0 else s); d.text((xx+45,y+54),num,font=ft(15,True),fill="white")
            paragraph(d,txt,xx+118,y+42,ft(27,True),ink,ww-160,35,2); y+=165
    elif scene_i==4:
        d.text((62,255),"IMPACTO",font=ft(24,True),fill=p); paragraph(d,ss[3],62,320,ft(43,True),ink,930,55,5)
        metrics(d,p,s,ink,680,[("VELOCIDAD","+"),("VISIÓN","+"),("RETRABAJO","↓")]); chart(d,t["chart"],(62,930,1018,1648),p,s,ink,reel_i*29+4)
    else:
        d.text((62,260),"HABLEMOS DE TU PROYECTO",font=ft(47,True),fill=ink); rr(d,(62,390,1018,930),42,"white",outline="#E4E0D7",w=2)
        icon_excel(d,108,455,116,p); icon_pbi(d,260,455,116,ink); d.text((108,610),"EXPERTO EN EXCEL + POWER BI",font=ft(40,True),fill=ink)
        paragraph(d,t["service"],108,692,ft(31,True),p,790,43,3); d.text((108,833),"Proyectos • dashboards • automatización",font=ft(25),fill="#6E6B65")
        rr(d,(62,1015,1018,1268),44,p); icon_wa(d,104,1065,92); d.text((224,1060),"ESCRÍBEME GRATIS AL WHATSAPP",font=ft(28,True),fill="white"); d.text((224,1122),"(51) 948-370-116",font=ft(48,True),fill="white")
        rr(d,(62,1335,1018,1510),38,"white",outline="#E4E0D7",w=2); d.text((194,1381),"systeracore.com",font=ft(48,True),fill=ink); d.text((62,1585),"Convierte datos en control y decisiones.",font=ft(31,True),fill=s)
    d.line((56,1815,1024,1815),fill="#D8D4CB",width=2); d.text((58,1843),"systeracore.com",font=ft(22,True),fill=ink); icon_wa(d,742,1832,46); d.text((804,1844),"948 370 116",font=ft(22,True),fill=ink)
    im.save(path,quality=94)

VOICE_LOCALES=["es-ES","es-PE","es-MX","es-CO","es-AR","es-CL","es-US","es-VE","es-EC","es-UY","es-BO","es-CR","es-DO","es-PR","es-CU","es-GT","es-HN","es-NI","es-PA","es-PY","es-SV"]
async def spanish_voices():
    vs=[v for v in await edge_tts.list_voices() if v.get("Locale","").startswith("es-")]
    def rank(v):
        try:return VOICE_LOCALES.index(v.get("Locale",""))
        except:return 99
    vs=sorted(vs,key=lambda v:(rank(v),v.get("Gender",""),v.get("ShortName","")))
    out=[]; used=set()
    for gender in ["Female","Male"]*10:
        c=[v for v in vs if v.get("Gender")==gender and v["ShortName"] not in used]
        if not c:c=[v for v in vs if v["ShortName"] not in used]
        v=c[0] if c else vs[len(out)%len(vs)]; out.append(v); used.add(v["ShortName"])
    return out
async def tts(text,voice,path,i):
    rates=["+3%","+6%","+2%","+5%","+4%"]; pitches=["+0Hz","-1Hz","+1Hz","-2Hz","+2Hz"]
    await edge_tts.Communicate(text,voice,rate=rates[i%5],pitch=pitches[i%5]).save(str(path))
def media_duration(path):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True); return float(r.stdout.strip())
def render(frames,audio,out,i):
    ad=media_duration(audio); total=max(15.0,min(22.0,ad+1.0)); seg=total/SCENES
    cmd=["ffmpeg","-y","-loglevel","error"]
    for f in frames: cmd += ["-loop","1","-framerate",str(FPS),"-t",f"{seg:.3f}","-i",str(f)]
    cmd += ["-i",str(audio)]
    filters=[]
    for k in range(SCENES):
        if k%2==0: filters.append(f"[{k}:v]scale=1120:1992,crop=1080:1920:20:36,fade=t=in:st=0:d=0.18,fade=t=out:st={max(0,seg-.18):.3f}:d=0.18,setpts=PTS-STARTPTS[v{k}]")
        else: filters.append(f"[{k}:v]scale=1080:1920,fade=t=in:st=0:d=0.18,fade=t=out:st={max(0,seg-.18):.3f}:d=0.18,setpts=PTS-STARTPTS[v{k}]")
    filters.append("".join(f"[v{k}]" for k in range(SCENES))+f"concat=n={SCENES}:v=1:a=0[vout]")
    filters.append(f"[{SCENES}:a]afade=t=in:st=0:d=0.15,afade=t=out:st={max(0,ad-.35):.3f}:d=0.35,apad=pad_dur=2[aout]")
    cmd += ["-filter_complex",";".join(filters),"-map","[vout]","-map","[aout]","-t",f"{total:.3f}","-r",str(FPS),"-c:v","libx264","-preset","veryfast","-crf","25","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(out)]
    subprocess.run(cmd,check=True)
    return total
async def main():
    data=json.loads((ROOT/"reels.json").read_text(encoding="utf-8")); voices=await spanish_voices(); manifest=[]
    for i,t in enumerate(data):
        work=OUT/f"work_{i+1:02d}"; work.mkdir(exist_ok=True); frames=[]
        for s in range(SCENES):
            f=work/f"scene_{s+1:02d}.jpg"; make_scene(t,s,i,f); frames.append(f)
        voice=voices[i]["ShortName"]; audio=work/"voice.mp3"; await tts(t["narration"],voice,audio,i)
        out=OUT/f"REEL_{i+1:02d}_{t['slug'].upper()}.mp4"; dur=render(frames,audio,out,i)
        manifest.append({"file":out.name,"title":t["title"],"service":t["service"],"chart":t["chart"],"colors":t["colors"],"voice":voice,"gender":voices[i].get("Gender"),"locale":voices[i].get("Locale"),"duration":round(dur,2)})
        print("OK",i+1,out.name,voice,round(dur,1))
    assert len(manifest)==20 and len({x["title"] for x in manifest})==20 and len({x["service"] for x in manifest})==20 and len({x["chart"] for x in manifest})==20
    assert len({tuple(x["colors"]) for x in manifest})==20 and all(x["duration"]>=11 for x in manifest)
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": asyncio.run(main())
