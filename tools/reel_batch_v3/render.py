from __future__ import annotations
import asyncio, json, math, random, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import edge_tts

W,H,FPS=1080,1920,30
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"; OUT.mkdir(parents=True,exist_ok=True)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

SECTION_LABELS=[
["LECTURA COMERCIAL","MARGEN VISIBLE","OPORTUNIDAD","DECISIÓN EJECUTIVA"],
["TAREA REPETITIVA","FLUJO AUTOMÁTICO","CONTROL DE ERROR","HORAS RECUPERADAS"],
["SEÑAL GERENCIAL","ALERTA TEMPRANA","TENDENCIA CLAVE","DECISIÓN A TIEMPO"],
["SALUD FINANCIERA","CAJA EN MOVIMIENTO","DESVIACIÓN","RENTABILIDAD REAL"],
["INVENTARIO VIVO","ROTACIÓN","STOCK CRÍTICO","COMPRA OPORTUNA"],
["PULSO DEL EQUIPO","ASISTENCIA","DESEMPEÑO","PRODUCTIVIDAD"],
["GUARDIA MINERA","AVANCE","HH / HM","RENDIMIENTO"],
["OPERACIÓN CLÍNICA","AGENDA","OCUPACIÓN","PRODUCTIVIDAD MÉDICA"],
["PULSO ACADÉMICO","ASISTENCIA","RENDIMIENTO","GESTIÓN EDUCATIVA"],
["EMBUDO REAL","CONVERSIÓN","PRIORIDAD","FORECAST"],
["ARCHIVOS DISPERSOS","CONSOLIDACIÓN","LIMPIEZA","ACTUALIZACIÓN"],
["MODELO CORRECTO","CONTEXTO DAX","VARIACIÓN","MÉTRICA CON SENTIDO"],
["HOJA INTELIGENTE","ANÁLISIS","INTERACCIÓN","CONTROL EN EXCEL"],
["CARTERA VENCIDA","AGING","PRIORIDAD","RECUPERACIÓN"],
["PROVEEDOR","COSTO TOTAL","CUMPLIMIENTO","NEGOCIACIÓN"],
["CUELLO DE BOTELLA","TIEMPO MUERTO","EFICIENCIA","ACCIÓN OPERATIVA"],
["PLAN VS REAL","HITO","RIESGO","AVANCE CONTROLADO"],
["TICKET","SLA","CAUSA","EXPERIENCIA"],
["DATOS CONECTADOS","FLUJO","TRAZABILIDAD","AUTOMATIZACIÓN"],
["PROYECTO PROFESIONAL","MODELO","DASHBOARD","RESULTADO"]
]
CHART_LABELS=[
"VENTAS VS UTILIDAD","FLUJO VBA","TENDENCIA GERENCIAL","PUENTE FINANCIERO","ROTACIÓN DE STOCK",
"RADAR DE DESEMPEÑO","MEDIDOR DE AVANCE","OCUPACIÓN CLÍNICA","MATRIZ ACADÉMICA","EMBUDO COMERCIAL",
"PIPELINE DE DATOS","TABLERO DAX","HOJA INTERACTIVA","ANTIGÜEDAD DE CARTERA","MAPA DE PROVEEDORES",
"FLUJO OPERATIVO","CRONOGRAMA GANTT","CUMPLIMIENTO SLA","RED DE AUTOMATIZACIÓN","VISIÓN 360°"
]
LAYOUTS=[
(0,),(1,),(2,),(3,),(4,),(5,),(6,),(7,),(8,),(9,),
(10,),(11,),(12,),(13,),(14,),(15,),(16,),(17,),(18,),(19,)
]

def ft(n,b=False): return ImageFont.truetype(BOLD if b else FONT,n)
def rgb(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def tint(c,a=.82): return tuple(int(v+(255-v)*a) for v in c)
def rr(d,b,r,fill,outline=None,w=1): d.rounded_rectangle(b,radius=r,fill=fill,outline=outline,width=w)
def wrap(d,s,f,m):
    out=[]; cur=""
    for word in s.split():
        q=(cur+" "+word).strip()
        if d.textlength(q,font=f)<=m: cur=q
        else:
            if cur: out.append(cur)
            cur=word
    if cur: out.append(cur)
    return out
def para(d,s,x,y,f,color,maxw,leading=None,maxlines=6):
    leading=leading or int(f.size*1.22)
    for line in wrap(d,s,f,maxw)[:maxlines]:
        d.text((x,y),line,font=f,fill=color); y+=leading
    return y

def excel_icon(d,x,y,s,p):
    rr(d,(x,y,x+s,y+s),int(s*.17),p); d.text((x+s*.29,y+s*.13),"X",font=ft(int(s*.55),True),fill="white")
def pbi_icon(d,x,y,s,ink):
    rr(d,(x,y,x+s,y+s),int(s*.17),"#F2C811")
    for i,h in enumerate([.24,.40,.58,.72]):
        xx=x+s*(.25+i*.13); d.rounded_rectangle((xx,y+s*(.8-h),xx+s*.075,y+s*.8),radius=4,fill=ink)
def wa_icon(d,x,y,s):
    d.ellipse((x,y,x+s,y+s),fill="#20B95A"); d.arc((x+s*.23,y+s*.20,x+s*.78,y+s*.74),198,502,fill="white",width=max(4,int(s*.075)))
    d.polygon([(x+s*.30,y+s*.68),(x+s*.20,y+s*.84),(x+s*.42,y+s*.75)],fill="white")
def appbar(d,app,p,ink):
    d.rectangle((0,0,W,108),fill="#FCFCFA"); d.line((0,107,W,107),fill="#E2E0DA",width=2)
    if app=="Excel":
        excel_icon(d,32,22,62,p); name="Excel"; menu="Archivo   Inicio   Insertar   Fórmulas   Datos   Revisar   Vista"
    else:
        pbi_icon(d,32,22,62,ink); name="Power BI"; menu="Archivo   Inicio   Insertar   Modelado   Ver   Ayuda"
    d.text((116,24),name,font=ft(27,True),fill=ink); d.text((116,67),menu,font=ft(17),fill="#68655F")

def backdrop(bg,p,s,seed,decor):
    im=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(im); rng=random.Random(seed)
    # 20 distinct background motifs.
    if decor%5==0:
        for k in range(9):
            r=120+k*35; d.arc((W-420-r,180-r,W-420+r,180+r),20,310,fill=tint(p,.65+k*.02),width=5)
    elif decor%5==1:
        for k in range(-3,8):
            d.line((0,240+k*170,W,40+k*170),fill=tint(s,.80),width=5)
    elif decor%5==2:
        for k in range(16):
            x=rng.randint(-50,W); y=rng.randint(150,H); r=rng.randint(40,160); d.ellipse((x-r,y-r,x+r,y+r),fill=tint(p,.88 if k%2 else .78))
    elif decor%5==3:
        for k in range(8):
            x=70+k*145; d.rounded_rectangle((x,220,x+58,H-220),radius=29,fill=tint(s,.88-k*.01))
    else:
        step=88
        for x in range(0,W,step):
            for y in range(160,H,step):
                if (x//step+y//step+decor)%3==0: d.ellipse((x,y,x+9,y+9),fill=tint(p,.55))
    return im.filter(ImageFilter.GaussianBlur(12))

def world(d,b,p):
    x0,y0,x1,y1=b; cx=(x0+x1)/2; cy=(y0+y1)/2; rx=(x1-x0)/2; ry=(y1-y0)/2
    d.ellipse(b,outline=tint(p,.40),width=3)
    for f in (-.55,0,.55): d.arc((cx-rx*(1-abs(f)*.38),y0,cx+rx*(1-abs(f)*.38),y1),90,270,fill=tint(p,.50),width=2)
    for f in (-.45,0,.45):
        yy=cy+ry*f; d.arc((x0,yy-ry*.30,x1,yy+ry*.30),0,360,fill=tint(p,.50),width=2)

def chart(d,kind,b,p,s,ink,seed,label):
    x0,y0,x1,y1=b; rng=random.Random(seed); rr(d,b,30,"white",outline="#E2DED6",w=2)
    d.text((x0+30,y0+22),label,font=ft(18,True),fill="#77736C")
    ax=(x0+38,y0+68,x1-38,y1-34); aw=ax[2]-ax[0]; ah=ax[3]-ax[1]
    if kind=="bars":
        vals=[44,66,57,82,69,93,76]
        for i,v in enumerate(vals):
            bw=aw/7; h=ah*v/108; xx=ax[0]+i*bw+9; d.rounded_rectangle((xx,ax[3]-h,xx+bw-18,ax[3]),radius=9,fill=p if i%2==0 else s)
    elif kind in ("line","area","sla","master"):
        vals=[40,58,51,72,65,87,79,96]; pts=[(ax[0]+i*aw/7,ax[3]-v*ah/110) for i,v in enumerate(vals)]
        if kind=="area": d.polygon([(pts[0][0],ax[3])]+pts+[(pts[-1][0],ax[3])],fill=tint(s,.56))
        d.line(pts,fill=p,width=8,joint="curve")
        for q in pts: d.ellipse((q[0]-7,q[1]-7,q[0]+7,q[1]+7),fill=s,outline="white",width=2)
        if kind=="sla": d.line((ax[0],ax[1]+ah*.28,ax[2],ax[1]+ah*.28),fill="#D94E4E",width=4)
        if kind=="master":
            for i,v in enumerate([55,76,67,91,84]):
                bw=aw*.065; xx=ax[0]+i*aw*.10; hh=ah*.38*v/100; d.rounded_rectangle((xx,ax[3]-hh,xx+bw,ax[3]),radius=7,fill=s)
    elif kind=="waterfall":
        cur=ax[3]-40
        for i,v in enumerate([33,-14,24,-9,36,-12]):
            bw=aw/6; h=abs(v)*min(7,ah/55); a=cur-h if v>0 else cur; z=cur if v>0 else cur+h
            d.rounded_rectangle((ax[0]+i*bw+8,a,ax[0]+(i+1)*bw-12,z),radius=8,fill=p if v>0 else s); cur=a if v>0 else z
    elif kind=="donut":
        cx=(ax[0]+ax[2])/2; cy=(ax[1]+ax[3])/2; r=min(aw,ah)*.34
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=s); d.pieslice((cx-r,cy-r,cx+r,cy+r),16,292,fill=p); d.ellipse((cx-r*.52,cy-r*.52,cx+r*.52,cy+r*.52),fill="white"); d.text((cx-64,cy-26),"76%",font=ft(46,True),fill=ink)
    elif kind=="radar":
        cx=(ax[0]+ax[2])/2; cy=(ax[1]+ax[3])/2; r=min(aw,ah)*.39; n=6
        for f in (.33,.66,1):
            pts=[(cx+r*f*math.cos(-math.pi/2+2*math.pi*i/n),cy+r*f*math.sin(-math.pi/2+2*math.pi*i/n)) for i in range(n)]; d.line(pts+[pts[0]],fill="#D3D0C9",width=2)
        vals=[.80,.56,.91,.68,.84,.64]; pts=[(cx+r*vals[i]*math.cos(-math.pi/2+2*math.pi*i/n),cy+r*vals[i]*math.sin(-math.pi/2+2*math.pi*i/n)) for i in range(n)]; d.polygon(pts,fill=tint(s,.50),outline=p)
    elif kind=="gauge":
        cx=(ax[0]+ax[2])/2; cy=ax[3]-16; r=min(aw*.35,ah*.72); d.arc((cx-r,cy-r,cx+r,cy+r),180,360,fill="#D5D3CD",width=40); d.arc((cx-r,cy-r,cx+r,cy+r),180,326,fill=p,width=40); a=math.radians(326); d.line((cx,cy,cx+r*.72*math.cos(a),cy+r*.72*math.sin(a)),fill=ink,width=10)
    elif kind=="heatmap":
        rows,cols=5,7; cw=aw/cols; ch=ah/rows
        for r in range(rows):
            for c in range(cols):
                q=(r*cols+c)/(rows*cols); col=tuple(int(p[i]*(1-q)+s[i]*q) for i in range(3)); d.rounded_rectangle((ax[0]+c*cw+4,ax[1]+r*ch+4,ax[0]+(c+1)*cw-4,ax[1]+(r+1)*ch-4),radius=8,fill=col)
    elif kind=="funnel":
        cy=ax[1]+10
        for i,wf in enumerate([.94,.74,.55,.38]):
            ww=aw*wf; hh=ah*.19; cx=(ax[0]+ax[2])/2; d.polygon([(cx-ww/2,cy),(cx+ww/2,cy),(cx+ww/2-28,cy+hh),(cx-ww/2+28,cy+hh)],fill=p if i%2==0 else s); cy+=hh+11
    elif kind in ("flow","pipeline","process","network"):
        pts=[(ax[0]+aw*.08,ax[1]+ah*.28),(ax[0]+aw*.29,ax[1]+ah*.52),(ax[0]+aw*.52,ax[1]+ah*.18),(ax[0]+aw*.73,ax[1]+ah*.69),(ax[0]+aw*.92,ax[1]+ah*.39)]
        for a,b2 in zip(pts,pts[1:]): d.line((a,b2),fill=s,width=9)
        if kind=="network": d.line((pts[0],pts[3]),fill=tint(p,.35),width=5); d.line((pts[1],pts[4]),fill=tint(s,.25),width=5)
        for i,(xx,yy) in enumerate(pts):
            r=27+(i%2)*7; d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=p if i%2==0 else s,outline="white",width=4)
    elif kind=="kpi":
        vals=[("MARGEN","31%"),("YTD","+18%"),("META","94%"),("Δ MES","+7.4%")]
        for i,(lab,val) in enumerate(vals):
            cw=aw/2-15; ch=ah/2-15; xx=ax[0]+(i%2)*(cw+20); yy=ax[1]+(i//2)*(ch+20); rr(d,(xx,yy,xx+cw,yy+ch),22,tint(p,.90) if i%2==0 else tint(s,.90)); d.text((xx+21,yy+18),lab,font=ft(17,True),fill="#77736C"); d.text((xx+21,yy+57),val,font=ft(42,True),fill=ink)
    elif kind=="sheet":
        cols,rows=7,9; cw=aw/cols; ch=ah/rows
        for c in range(cols):
            d.rectangle((ax[0]+c*cw,ax[1],ax[0]+(c+1)*cw,ax[1]+ch),fill=tint(p,.72) if c<2 else "#F1F1EE"); d.text((ax[0]+c*cw+9,ax[1]+8),chr(65+c),font=ft(14,True),fill=ink)
        for r in range(1,rows):
            for c in range(cols):
                d.rectangle((ax[0]+c*cw,ax[1]+r*ch,ax[0]+(c+1)*cw,ax[1]+(r+1)*ch),fill="white" if (r+c)%2==0 else "#FAFAF7",outline="#E4E2DC")
                if c in (2,4,6): d.rectangle((ax[0]+c*cw+9,ax[1]+r*ch+ch*.38,ax[0]+c*cw+9+rng.randint(26,max(28,int(cw-20))),ax[1]+r*ch+ch*.60),fill=s)
    elif kind=="aging":
        for i,(lab,v) in enumerate([("0–30",92),("31–60",68),("61–90",47),("+90",29)]):
            yy=ax[1]+i*ah/4; d.text((ax[0],yy+20),lab,font=ft(18,True),fill=ink); d.rounded_rectangle((ax[0]+135,yy+17,ax[0]+135+aw*.72*v/100,yy+58),radius=12,fill=p if i<2 else s)
    elif kind=="scatter":
        for i in range(28):
            xx=rng.randint(int(ax[0]+18),int(ax[2]-18)); yy=rng.randint(int(ax[1]+18),int(ax[3]-18)); r=rng.randint(7,20); d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=p if i%3 else s)
    elif kind=="gantt":
        for i in range(6):
            yy=ax[1]+i*ah/6+15; start=rng.uniform(0,.36)*aw; dur=rng.uniform(.25,.52)*aw; d.rounded_rectangle((ax[0]+start,yy,min(ax[0]+start+dur,ax[2]),yy+38),radius=11,fill=p if i%2==0 else s)

def header_chip(d,text,ink):
    rr(d,(54,138,330,190),26,"white",outline="#E2DED6",w=2); d.text((76,153),text,font=ft(20,True),fill=ink)
def footer(d,ink):
    d.line((54,1818,1026,1818),fill="#D8D4CB",width=2); d.text((56,1844),"systeracore.com",font=ft(22,True),fill=ink); wa_icon(d,742,1833,46); d.text((802,1844),"948 370 116",font=ft(22,True),fill=ink)

def cover(t,i,d,p,s,ink):
    m=i
    label=CHART_LABELS[i]
    # Twenty deliberately different compositions.
    if m==0:
        para(d,t["title"],60,252,ft(66,True),ink,920,78,3); d.text((62,420),t["tag"],font=ft(27,True),fill=p); chart(d,t["chart"],(58,560,1022,1390),p,s,ink,i,label); service=(58,1450,1022,1650)
    elif m==1:
        chart(d,t["chart"],(510,250,1022,1230),p,s,ink,i,label); para(d,t["title"],58,285,ft(62,True),ink,410,72,4); para(d,t["tag"],58,610,ft(28,True),p,390,38,4); world(d,(74,970,430,1328),p); service=(58,1420,1010,1625)
    elif m==2:
        chart(d,t["chart"],(58,240,1022,1020),p,s,ink,i,label); para(d,t["title"],90,1110,ft(68,True),ink,900,80,3); d.text((92,1338),t["tag"],font=ft(27,True),fill=p); service=(90,1430,990,1640)
    elif m==3:
        d.polygon([(0,170),(1080,170),(1080,780),(0,1030)],fill=tint(p,.87)); para(d,t["title"],72,265,ft(70,True),ink,820,82,3); d.text((74,530),t["tag"],font=ft(26,True),fill=p); chart(d,t["chart"],(100,760,980,1470),p,s,ink,i,label); service=(100,1520,980,1685)
    elif m==4:
        para(d,t["title"],64,252,ft(62,True),ink,650,74,3); rr(d,(735,240,1015,515),42,p); d.text((782,295),"STOCK",font=ft(26,True),fill="white"); d.text((775,355),"LIVE",font=ft(58,True),fill="white"); chart(d,t["chart"],(100,630,980,1450),p,s,ink,i,label); service=(64,1510,1016,1680)
    elif m==5:
        d.rectangle((0,210,300,1720),fill=tint(p,.78)); d.text((74,300),"PEOPLE",font=ft(25,True),fill=p); para(d,t["title"],350,260,ft(64,True),ink,650,76,4); d.text((350,610),t["tag"],font=ft(26,True),fill=p); chart(d,t["chart"],(350,720,1015,1440),p,s,ink,i,label); service=(350,1490,1015,1680)
    elif m==6:
        para(d,t["title"],62,245,ft(61,True),ink,760,72,3); d.text((64,470),t["tag"],font=ft(25,True),fill=p); chart(d,t["chart"],(58,620,690,1440),p,s,ink,i,label); rr(d,(730,620,1020,910),34,"white",outline="#E2DED6",w=2); d.text((770,665),"GUARDIA",font=ft(21,True),fill="#77736C"); d.text((770,715),"A",font=ft(82,True),fill=p); world(d,(740,1010,1010,1280),p); service=(730,1340,1020,1680)
    elif m==7:
        chart(d,t["chart"],(58,240,1022,860),p,s,ink,i,label); rr(d,(58,930,1022,1215),34,tint(p,.88)); para(d,t["title"],92,975,ft(58,True),ink,850,69,3); d.text((92,1150),t["tag"],font=ft(25,True),fill=p); service=(58,1320,1022,1600)
    elif m==8:
        rr(d,(58,238,1022,520),38,"white",outline="#E2DED6",w=2); para(d,t["title"],92,286,ft(60,True),ink,820,72,3); d.text((92,445),t["tag"],font=ft(25,True),fill=p); chart(d,t["chart"],(58,580,1022,1370),p,s,ink,i,label); service=(178,1440,902,1670)
    elif m==9:
        chart(d,t["chart"],(58,270,640,1510),p,s,ink,i,label); para(d,t["title"],700,300,ft(56,True),ink,330,67,5); para(d,t["tag"],700,720,ft(26,True),p,320,35,4); service=(680,1120,1020,1630)
    elif m==10:
        para(d,t["title"],80,260,ft(72,True),ink,900,83,3); d.text((82,518),t["tag"],font=ft(28,True),fill=p); rr(d,(58,630,1022,800),36,p); d.text((94,680),"CARPETAS → MODELO → REPORTE",font=ft(35,True),fill="white"); chart(d,t["chart"],(58,865,1022,1480),p,s,ink,i,label); service=(58,1530,1022,1695)
    elif m==11:
        rr(d,(58,235,1022,600),44,tint(p,.88)); para(d,t["title"],96,300,ft(66,True),ink,830,77,3); d.text((96,515),t["tag"],font=ft(27,True),fill=p); chart(d,t["chart"],(110,690,970,1450),p,s,ink,i,label); service=(180,1510,900,1685)
    elif m==12:
        # Excel-grid hero
        chart(d,"sheet",(58,235,1022,1065),p,s,ink,i,label); rr(d,(130,990,950,1330),38,"white",outline="#DCD8CF",w=3); para(d,t["title"],170,1040,ft(59,True),ink,730,70,4); d.text((170,1248),t["tag"],font=ft(25,True),fill=p); service=(130,1400,950,1665)
    elif m==13:
        d.text((64,245),"CARTERA",font=ft(28,True),fill=p); para(d,t["title"],64,300,ft(74,True),ink,940,86,3); chart(d,t["chart"],(58,640,1022,1350),p,s,ink,i,label); d.text((64,1422),t["tag"],font=ft(28,True),fill=p); service=(58,1500,1022,1680)
    elif m==14:
        para(d,t["title"],60,250,ft(70,True),ink,700,82,3); world(d,(720,225,1030,535),p); chart(d,t["chart"],(58,640,1022,1430),p,s,ink,i,label); rr(d,(58,1490,1022,1680),38,tint(s,.86)); service=(80,1505,1000,1668)
    elif m==15:
        rr(d,(58,245,420,640),42,p); d.text((112,305),"OEE",font=ft(30,True),fill="white"); d.text((108,380),"87%",font=ft(92,True),fill="white"); para(d,t["title"],480,265,ft(59,True),ink,520,70,4); d.text((480,580),t["tag"],font=ft(25,True),fill=p); chart(d,t["chart"],(58,720,1022,1450),p,s,ink,i,label); service=(58,1510,1022,1680)
    elif m==16:
        para(d,t["title"],64,245,ft(68,True),ink,900,80,3); d.text((66,465),t["tag"],font=ft(27,True),fill=p); d.line((130,650,130,1410),fill=p,width=8)
        for k,y in enumerate((680,870,1060,1250)): d.ellipse((105,y-25,155,y+25),fill=s if k%2 else p); d.text((190,y-26),["INICIO","HITO","RIESGO","CIERRE"][k],font=ft(27,True),fill=ink)
        chart(d,t["chart"],(470,650,1018,1430),p,s,ink,i,label); service=(58,1500,1022,1680)
    elif m==17:
        rr(d,(58,235,1022,505),38,tint(p,.90)); para(d,t["title"],90,285,ft(61,True),ink,840,72,3); d.text((90,445),t["tag"],font=ft(25,True),fill=p)
        chart(d,t["chart"],(58,575,1022,1270),p,s,ink,i,label)
        for k,(a,b2) in enumerate([("SLA","96%"),("RESP.","2.4h"),("CSAT","4.7")]): x=58+k*330; rr(d,(x,1325,x+300,1465),26,"white",outline="#E2DED6",w=2); d.text((x+24,1352),a,font=ft(18,True),fill="#77736C"); d.text((x+24,1390),b2,font=ft(34,True),fill=p)
        service=(58,1515,1022,1680)
    elif m==18:
        chart(d,t["chart"],(270,350,1020,1415),p,s,ink,i,label); d.rectangle((58,250,220,1540),fill=tint(p,.79)); d.text((91,315),"AI",font=ft(35,True),fill=p); para(d,t["title"],300,215,ft(58,True),ink,700,69,4); para(d,t["tag"],84,620,ft(24,True),ink,110,34,6); service=(270,1485,1020,1680)
    else:
        world(d,(710,220,1020,530),p); para(d,t["title"],58,250,ft(62,True),ink,620,74,4); d.text((60,590),t["tag"],font=ft(25,True),fill=p); chart(d,t["chart"],(58,700,1022,1430),p,s,ink,i,label); service=(120,1490,960,1680)
    rr(d,service,28,"white",outline="#E1DDD4",w=2); para(d,t["service"],service[0]+25,service[1]+28,ft(28,True),ink,service[2]-service[0]-50,38,3)

def inner(t,i,scene,d,p,s,ink):
    labels=SECTION_LABELS[i]; label=labels[scene-1]; textparts=[q.strip() for q in t["narration"].replace("? ","? |").replace("! ","! |").replace(". ",". |").split("|") if q.strip()]
    while len(textparts)<4: textparts.append(t["service"])
    msg=textparts[min(scene-1,len(textparts)-1)]
    mode=(i*3+scene*5)%10
    d.text((62,245),label,font=ft(25,True),fill=p)
    if mode==0:
        para(d,msg,62,315,ft(48,True),ink,930,61,5); chart(d,t["chart"],(58,700,1022,1490),p,s,ink,i*31+scene,CHART_LABELS[i])
    elif mode==1:
        chart(d,t["chart"],(58,260,620,1500),p,s,ink,i*31+scene,CHART_LABELS[i]); para(d,msg,680,320,ft(42,True),ink,330,53,8)
    elif mode==2:
        para(d,msg,62,315,ft(45,True),ink,900,57,5); rr(d,(58,710,1022,920),36,p); d.text((92,765),t["tag"],font=ft(31,True),fill="white"); chart(d,t["chart"],(58,990,1022,1590),p,s,ink,i*31+scene,CHART_LABELS[i])
    elif mode==3:
        rr(d,(58,300,1022,680),42,"white",outline="#E2DED6",w=2); para(d,msg,96,350,ft(43,True),ink,850,55,6); chart(d,t["chart"],(120,760,960,1530),p,s,ink,i*31+scene,CHART_LABELS[i])
    elif mode==4:
        para(d,msg,62,315,ft(43,True),ink,650,55,6); world(d,(725,285,1015,575),p); chart(d,t["chart"],(58,700,1022,1500),p,s,ink,i*31+scene,CHART_LABELS[i])
    elif mode==5:
        chart(d,t["chart"],(58,260,1022,980),p,s,ink,i*31+scene,CHART_LABELS[i]); rr(d,(58,1050,1022,1530),40,tint(p,.89)); para(d,msg,96,1110,ft(44,True),ink,830,56,6)
    elif mode==6:
        for k,(a,b2) in enumerate([(labels[0],"01"),(labels[1],"02"),(labels[2],"03")]):
            y=340+k*245; x=58+k*45; rr(d,(x,y,990,y+190),34,"white",outline="#E1DDD4",w=2); d.text((x+30,y+30),b2,font=ft(24,True),fill=p); para(d,a,x+110,y+42,ft(31,True),ink,700,40,3)
        para(d,msg,90,1130,ft(41,True),ink,870,52,6)
    elif mode==7:
        rr(d,(58,300,460,1480),42,p); d.text((105,360),label[:10],font=ft(27,True),fill="white"); para(d,msg,520,350,ft(43,True),ink,480,55,8); chart(d,t["chart"],(505,890,1018,1530),p,s,ink,i*31+scene,CHART_LABELS[i])
    elif mode==8:
        para(d,msg,110,320,ft(47,True),ink,850,60,6); rr(d,(120,770,960,960),36,tint(s,.83)); d.text((165,825),t["service"],font=ft(31,True),fill=ink); chart(d,t["chart"],(58,1040,1022,1590),p,s,ink,i*31+scene,CHART_LABELS[i])
    else:
        chart(d,t["chart"],(160,300,920,1200),p,s,ink,i*31+scene,CHART_LABELS[i]); para(d,msg,90,1300,ft(40,True),ink,900,50,5)

def cta(t,i,d,p,s,ink):
    d.text((60,260),["HABLEMOS","ACTIVA EL CAMBIO","LLEVA EL CONTROL","CONVIERTE TUS DATOS","DA EL SIGUIENTE PASO"][i%5],font=ft(48,True),fill=ink)
    rr(d,(58,390,1022,930),46,"white",outline="#E2DED6",w=2)
    if i%2==0: excel_icon(d,110,455,116,p); pbi_icon(d,265,455,116,ink)
    else: pbi_icon(d,110,455,116,ink); excel_icon(d,265,455,116,p)
    para(d,t["service"],110,630,ft(39,True),ink,820,50,4); d.text((110,830),"Solución profesional a medida",font=ft(25),fill=p)
    rr(d,(58,1010,1022,1275),44,p); wa_icon(d,105,1066,92); d.text((226,1060),"ESCRÍBEME GRATIS AL WHATSAPP",font=ft(28,True),fill="white"); d.text((226,1125),"(51) 948-370-116",font=ft(50,True),fill="white")
    rr(d,(58,1350,1022,1530),38,"white",outline="#E2DED6",w=2); d.text((190,1398),"systeracore.com",font=ft(50,True),fill=ink); d.text((60,1610),["Decide con datos.","Automatiza con criterio.","Control visible.","Gestión sin puntos ciegos.","Resultados medibles."][i%5],font=ft(31,True),fill=s)

def make_scene(t,scene,i,path):
    bg,phex,shex,ihex=t["colors"]; p,s,ink=rgb(phex),rgb(shex),rgb(ihex)
    im=backdrop(rgb(bg),p,s,i*101+scene*19,i); d=ImageDraw.Draw(im); appbar(d,"Excel" if (i+scene)%2==0 else "Power BI",p,ink); header_chip(d,"systeracore.com",ink)
    if scene==0: cover(t,i,d,p,s,ink)
    elif scene==5: cta(t,i,d,p,s,ink)
    else: inner(t,i,scene,d,p,s,ink)
    footer(d,ink); im.save(path,quality=94)

LOCALE_PRIORITY=["es-ES","es-PE","es-MX","es-CO","es-AR","es-CL","es-US","es-VE","es-EC","es-UY","es-BO","es-CR","es-DO","es-PR","es-CU","es-GT","es-HN","es-NI","es-PA","es-PY","es-SV"]
async def voices20():
    vs=[v for v in await edge_tts.list_voices() if v.get("Locale","").startswith("es-")]
    def rk(v):
        try:return LOCALE_PRIORITY.index(v.get("Locale",""))
        except:return 99
    vs=sorted(vs,key=lambda v:(rk(v),v["ShortName"]))
    out=[]; used=set()
    for i in range(20):
        want="Female" if i%2==0 else "Male"
        c=[v for v in vs if v.get("Gender")==want and v["ShortName"] not in used]
        if not c: c=[v for v in vs if v["ShortName"] not in used]
        v=c[0] if c else vs[i%len(vs)]; out.append(v); used.add(v["ShortName"])
    return out

def spoken(txt):
    return (txt.replace("Power BI","Power B I").replace("VBA","V B A").replace("Power Query","Power Query")
            .replace("systeracore.com","Sístera Core punto com").replace("WhatsApp","WhatsApp"))
async def make_voice(txt,voice,path,i):
    rates=["+7%","+5%","+8%","+6%","+4%"]; pitches=["+0Hz","-1Hz","+1Hz","-2Hz","+2Hz"]
    await edge_tts.Communicate(spoken(txt),voice,rate=rates[i%5],pitch=pitches[i%5]).save(str(path))
def duration(p):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(p)],capture_output=True,text=True,check=True); return float(r.stdout.strip())

def render(frames,audio,out,i):
    ad=duration(audio); total=max(16.0,min(30.0,ad+1.0)); seg=total/6
    cmd=["ffmpeg","-y","-loglevel","error"]
    for f in frames: cmd += ["-loop","1","-framerate","30","-t",f"{seg:.3f}","-i",str(f)]
    cmd += ["-i",str(audio)]
    fs=[]
    for k in range(6):
        if (i+k)%3==0: base=f"[{k}:v]scale=1120:1992,crop=1080:1920:20:36,setsar=1"
        elif (i+k)%3==1: base=f"[{k}:v]scale=1100:1956,crop=1080:1920:10:18,setsar=1"
        else: base=f"[{k}:v]scale=1080:1920,setsar=1"
        fs.append(base+f",fade=t=in:st=0:d=0.18,fade=t=out:st={max(0,seg-.18):.3f}:d=0.18,setpts=PTS-STARTPTS[v{k}]")
    fs.append("".join(f"[v{k}]" for k in range(6))+"concat=n=6:v=1:a=0[vout]")
    fs.append(f"[6:a]afade=t=in:st=0:d=0.15,afade=t=out:st={max(0,ad-.35):.3f}:d=0.35,apad=pad_dur=2[aout]")
    cmd += ["-filter_complex",";".join(fs),"-map","[vout]","-map","[aout]","-t",f"{total:.3f}","-r","30","-c:v","libx264","-preset","veryfast","-crf","24","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(out)]
    subprocess.run(cmd,check=True); return total

async def main():
    data=json.loads((ROOT.parent/"reel_batch_v2"/"reels.json").read_text(encoding="utf-8")); voices=await voices20(); manifest=[]
    for i,t in enumerate(data):
        work=OUT/f"work_{i+1:02d}"; work.mkdir(exist_ok=True); frames=[]
        for s in range(6):
            f=work/f"scene_{s+1:02d}.jpg"; make_scene(t,s,i,f); frames.append(f)
        audio=work/"voice.mp3"; v=voices[i]; await make_voice(t["narration"],v["ShortName"],audio,i)
        out=OUT/f"REEL_{i+1:02d}_{t['slug'].upper()}_V03.mp4"; dur=render(frames,audio,out,i)
        manifest.append({"file":out.name,"title":t["title"],"service":t["service"],"chart":t["chart"],"colors":t["colors"],"voice":v["ShortName"],"gender":v.get("Gender"),"locale":v.get("Locale"),"duration":round(dur,2),"section_labels":SECTION_LABELS[i]})
        print("OK",i+1,out.name,v["ShortName"],v.get("Gender"),v.get("Locale"),round(dur,2),flush=True)
    assert len(manifest)==20
    assert len({x["title"] for x in manifest})==20
    assert len({x["service"] for x in manifest})==20
    assert len({x["chart"] for x in manifest})==20
    assert len({tuple(x["colors"]) for x in manifest})==20
    assert len({x["voice"] for x in manifest})==20
    assert all(x["duration"]>=11 for x in manifest)
    (OUT/"manifest_v03.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": asyncio.run(main())
