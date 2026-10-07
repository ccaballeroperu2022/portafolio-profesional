import os, math, random, subprocess, json, zipfile, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT=Path("render_v02")
OUT=ROOT/"mp4"
IMG=ROOT/"images"
AUD=ROOT/"audio"
for p in [OUT,IMG,AUD]: p.mkdir(parents=True,exist_ok=True)

W,H=720,1280
FPS=24
FONT_B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def F(n,b=False): return ImageFont.truetype(FONT_B if b else FONT_R,n)

REELS=[
("Ventas","TUS VENTAS DEBEN DECIDIR","Ventas, utilidad, margen y metas","Dashboard ejecutivo de ventas","Tus ventas no deberían terminar en una tabla. Diseño dashboards en Excel y Power BI que muestran utilidad, margen, metas y crecimiento para detectar qué impulsa el negocio y dónde actuar primero. Convierte datos dispersos en decisiones claras. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((250,247,239),(31,105,79),(224,167,74),(35,42,39)),"bars",0),
("VBA","RECUPERA HORAS CADA SEMANA","Macros, validaciones y procesos automáticos","Automatización con Excel y VBA","Si cada semana repites copiar, pegar, validar y consolidar, estás perdiendo tiempo. Automatizo procesos en Excel con VBA para reducir errores y ejecutar tareas con un clic. Menos trabajo manual, más productividad y control. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((245,252,247),(30,126,78),(109,190,132),(37,48,41)),"flow",1),
("Gerencia","GERENCIA SIN REPORTES TARDÍOS","KPIs, tendencias y alertas ejecutivas","Power BI para gerencia","La gerencia no necesita más archivos; necesita respuestas. Creo tableros Power BI con indicadores, tendencias, alertas y comparativos para visualizar el negocio en segundos y decidir antes de que el problema crezca. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((255,251,242),(118,84,31),(243,188,61),(58,51,38)),"line",2),
("Finanzas","TU CAJA NO ADMITE SORPRESAS","Ingresos, egresos, presupuesto y rentabilidad","Control financiero","Controla el dinero antes de que el dinero controle tu operación. Desarrollo soluciones en Excel y Power BI para flujo de caja, ingresos, egresos, presupuesto y rentabilidad. Visualiza desviaciones y conoce dónde se gana o pierde. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((252,247,242),(126,67,54),(216,139,91),(58,43,39)),"waterfall",3),
("Logistica","STOCK INTELIGENTE, NO IMPROVISADO","Rotación, quiebres, compras y alertas","Logística e inventarios","Un stock mal controlado genera pérdidas invisibles. Diseño tableros para inventario, rotación, compras, quiebres y alertas de stock crítico. Identifica excesos, faltantes y productos inmovilizados antes de afectar ventas y caja. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((245,251,250),(25,112,108),(66,181,161),(40,57,57)),"donut",4),
("RRHH","EL TALENTO TAMBIÉN SE MIDE","Asistencia, productividad, costos y desempeño","Analítica de Recursos Humanos","Los datos de recursos humanos pueden mostrar mucho más que asistencia. Creo tableros para productividad, costos, ausentismo y desempeño con indicadores que revelan tendencias y ayudan a gestionar personas con evidencia. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((255,247,246),(145,73,70),(231,150,143),(65,47,47)),"radar",5),
("Mineria","CADA GUARDIA DEJA DATOS","Toneladas, metros, HH, HM y avance","Control de operaciones mineras","En minería, cada guardia debe dejar trazabilidad. Desarrollo controles para toneladas, metros perforados, avance, horas hombre, horas máquina y productividad. Compara turnos y detecta desviaciones antes de perder rendimiento. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((250,248,240),(104,81,42),(199,153,65),(48,45,39)),"gauge",6),
("Clinicas","UNA CLÍNICA TAMBIÉN NECESITA KPIs","Citas, ocupación, ingresos y productividad","Gestión para clínicas","Controla citas, atención, productividad médica e ingresos sin buscar información en múltiples archivos. Creo dashboards para clínicas que integran operación y gestión en una sola vista clara. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((247,253,250),(49,130,110),(123,200,172),(45,60,56)),"area",7),
("Educacion","DEL AULA AL INDICADOR","Matrículas, notas, asistencia y pagos","Gestión académica","Transforma la información académica en decisiones. Desarrollo controles para matrículas, notas, asistencia, pagos y rendimiento por curso o grupo. Menos archivos dispersos y más visibilidad para administrar mejor. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((255,251,241),(118,94,44),(225,184,86),(58,50,38)),"heatmap",8),
("CRM","NO PIERDAS EL PRÓXIMO CLIENTE","Leads, embudo, conversión y forecast","CRM y analítica comercial","No pierdas oportunidades por falta de seguimiento. Diseño controles comerciales para leads, embudo, conversiones, vendedores y forecast. Identifica dónde se frenan las ventas y qué oportunidades deben atenderse primero. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((250,248,252),(96,65,103),(190,145,194),(53,43,56)),"funnel",9),
("PowerQuery","DE CIEN ARCHIVOS A UNA SOLA FUENTE","Consolida, limpia y actualiza","Automatización con Power Query","¿Recibes decenas de archivos cada semana? Con Power Query puedo consolidarlos, limpiar datos y actualizar reportes sin repetir el proceso manual. Convierte carpetas dispersas en una sola fuente confiable y lista para analizar. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((247,251,244),(69,115,66),(157,192,116),(47,58,42)),"pipeline",10),
("DAX","UN KPI MAL CALCULADO ENGAÑA","DAX, acumulados, variaciones y metas","Modelado y DAX avanzado","Un dashboard bonito no sirve si sus métricas están mal definidas. Desarrollo medidas DAX para acumulados, variaciones, metas y comparativos dinámicos. Indicadores correctos, contexto correcto y decisiones con fundamento. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((253,249,241),(118,82,29),(224,171,60),(59,51,35)),"kpi",11),
("Excel","EXCEL PUEDE SER UN SISTEMA","Fórmulas, tablas, segmentadores y control","Excel avanzado profesional","Excel puede ser mucho más que una hoja de cálculo. Diseño soluciones con fórmulas avanzadas, tablas dinámicas, segmentadores, validaciones y controles para convertir datos en una herramienta profesional de gestión. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((245,252,247),(30,114,72),(99,181,125),(39,55,44)),"table",12),
("Cobranzas","COBRA CON PRIORIDAD, NO A CIEGAS","Vencidos, aging, morosidad y recuperación","Dashboard de cobranzas","Cobrar mejor empieza por saber a quién priorizar. Creo dashboards de cartera, vencidos, morosidad, recuperación y aging para enfocar la gestión donde realmente impacta. Menos seguimiento a ciegas, más recuperación. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((255,248,241),(141,77,45),(228,151,97),(61,46,38)),"aging",13),
("Compras","EL PRECIO MÁS BAJO NO SIEMPRE GANA","Costo, plazo, cumplimiento y proveedor","Compras y proveedores","El precio más bajo no siempre es la mejor compra. Desarrollo controles para costos, tiempos de entrega, cumplimiento y evaluación de proveedores. Compara desempeño y negocia con información real. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((248,251,252),(54,96,107),(118,171,183),(42,55,59)),"scatter",14),
("Operaciones","ENCUENTRA EL CUELLO DE BOTELLA","Eficiencia, tiempos muertos y alertas","Control de operaciones","Cuando la operación se frena, el dato debe mostrar dónde. Diseño tableros para productividad, eficiencia, tiempos muertos y alertas por proceso. Visualiza cuellos de botella y prioriza acciones antes de afectar el resultado. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((252,250,243),(97,97,50),(184,182,92),(57,57,41)),"process",15),
("Proyectos","EL AVANCE DEBE SER MEDIBLE","Cronograma, presupuesto, hitos y riesgos","Control de proyectos","Un proyecto no se controla con percepciones. Creo dashboards para avance, presupuesto, cronograma, hitos y riesgos con semáforos que muestran dónde actuar primero. Estado real del proyecto en una sola vista. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((249,248,253),(82,72,113),(154,145,201),(48,45,64)),"gantt",16),
("Servicio","CADA TICKET ES UNA SEÑAL","SLA, respuesta, satisfacción y carga","Analítica de servicio al cliente","Cada ticket contiene una señal sobre tu servicio. Diseño tableros para tiempos de respuesta, SLA, satisfacción, carga por agente y causas recurrentes. Detecta dónde se deteriora la experiencia y actúa con datos. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((246,252,252),(32,111,124),(96,183,192),(43,58,60)),"sla",17),
("Integracion","CONECTA TODO EL PROCESO","Excel, Power BI, bases de datos y flujos","Automatización empresarial","Conecta datos, procesos y decisiones. Integro Excel, Power BI, bases de datos y automatizaciones para reducir tareas manuales y mantener la información actualizada. Menos pasos aislados, más trazabilidad y control de punta a punta. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((250,252,247),(65,110,72),(154,192,127),(45,58,45)),"network",18),
("Experto","EXPERTO EN EXCEL Y POWER BI","Proyectos, dashboards y automatización","Desarrollo profesional de trabajos y proyectos","Si necesitas desarrollar un proyecto serio en Excel o Power BI, puedo ayudarte. Creo dashboards, automatizaciones, modelos, indicadores y soluciones personalizadas para distintas áreas y negocios. Convierte tus datos en control y decisiones. Escríbeme gratis al WhatsApp cincuenta y uno, nueve cuatro ocho, tres siete cero, uno uno seis.",((255,252,246),(57,88,61),(226,180,75),(43,48,42)),"master",19),
]

def rounded(d,b,r,fill,outline=None,w=1): d.rounded_rectangle(b,radius=r,fill=fill,outline=outline,width=w)
def wrap(d,text,ft,maxw):
    lines=[]; cur=""
    for word in text.split():
        trial=(cur+" "+word).strip()
        if d.textlength(trial,font=ft)<=maxw: cur=trial
        else:
            if cur: lines.append(cur)
            cur=word
    if cur: lines.append(cur)
    return lines

def draw_excel_header(d,accent,dark,mode):
    d.rectangle((0,0,W,78),fill=(250,250,248))
    if mode%2==0:
        rounded(d,(25,15,68,59),8,accent); d.text((38,21),"X",font=F(25,1),fill="white")
        menu="Archivo   Inicio   Insertar   Fórmulas   Datos   Revisar   Vista"
    else:
        rounded(d,(25,15,68,59),8,(245,190,50))
        for i,h in enumerate([12,20,28,36]): d.rounded_rectangle((35+i*7,52-h,40+i*7,52),2,fill=dark)
        menu="Archivo   Inicio   Insertar   Modelado   Ver   Ayuda"
    d.text((86,27),menu,font=F(15),fill=dark)

def soft_bg(pal,seed):
    bg,a,b,dark=pal
    im=Image.new("RGB",(W,H),bg); dr=ImageDraw.Draw(im); rnd=random.Random(seed)
    for _ in range(10):
        cx=rnd.randint(-80,W+80); cy=rnd.randint(80,H+80); r=rnd.randint(70,230); src=a if rnd.random()>.5 else b
        c=tuple(int(0.18*x+0.82*255) for x in src)
        dr.ellipse((cx-r,cy-r,cx+r,cy+r),fill=c)
    return im.filter(ImageFilter.GaussianBlur(18))

def chart(d,kind,box,pal,seed):
    x0,y0,x1,y1=box; bg,a,b,dark=pal; rounded(d,box,24,(255,255,255),outline=(225,225,220),w=2)
    ax=(x0+25,y0+35,x1-25,y1-28); rnd=random.Random(seed)
    if kind in ["bars","kpi","table","master"]:
        vals=[rnd.randint(28,96) for _ in range(7)]; bw=(ax[2]-ax[0]-30)//7
        for i,v in enumerate(vals):
            hh=int((ax[3]-ax[1]-20)*v/100); x=ax[0]+i*bw+8
            rounded(d,(x,ax[3]-hh,x+bw-12,ax[3]),6,a if i%2==0 else b)
    elif kind in ["line","area","sla"]:
        pts=[]
        for i in range(9):
            x=ax[0]+i*(ax[2]-ax[0])//8; y=ax[3]-rnd.randint(35,max(36,ax[3]-ax[1]-30)); pts.append((x,y))
        if kind=="area": d.polygon([(pts[0][0],ax[3])]+pts+[(pts[-1][0],ax[3])],fill=tuple(int((c+255)/2) for c in b))
        d.line(pts,fill=a,width=6,joint="curve")
        for x,y in pts: d.ellipse((x-6,y-6,x+6,y+6),fill=b,outline="white",width=2)
    elif kind=="donut":
        cx=(ax[0]+ax[2])//2; cy=(ax[1]+ax[3])//2; r=min(ax[2]-ax[0],ax[3]-ax[1])//3
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=b); d.pieslice((cx-r,cy-r,cx+r,cy+r),15,285,fill=a); d.ellipse((cx-r//2,cy-r//2,cx+r//2,cy+r//2),fill="white"); d.text((cx-35,cy-20),"76%",font=F(27,1),fill=dark)
    elif kind=="funnel":
        widths=[330,270,210,150]; yy=ax[1]+20; cx=(ax[0]+ax[2])//2
        for i,ww in enumerate(widths):
            d.polygon([(cx-ww//2,yy),(cx+ww//2,yy),(cx+ww//2-18,yy+60),(cx-ww//2+18,yy+60)],fill=a if i%2==0 else b); yy+=72
    elif kind=="heatmap":
        cw=(ax[2]-ax[0])//6; ch=(ax[3]-ax[1])//5
        for r in range(5):
            for c in range(6):
                t=rnd.random(); col=tuple(int(a[i]*t+b[i]*(1-t)) for i in range(3)); rounded(d,(ax[0]+c*cw+3,ax[1]+r*ch+3,ax[0]+(c+1)*cw-3,ax[1]+(r+1)*ch-3),5,col)
    elif kind=="waterfall":
        vals=[31,-14,22,-10,27,-8]; cur=ax[3]-70; bw=(ax[2]-ax[0])//6
        for i,v in enumerate(vals):
            hh=abs(v)*4; ya=cur-hh if v>0 else cur; yb=cur if v>0 else cur+hh; rounded(d,(ax[0]+i*bw+5,ya,ax[0]+(i+1)*bw-8,yb),5,a if v>0 else b); cur=ya if v>0 else yb
    elif kind=="gauge":
        cx=(ax[0]+ax[2])//2; cy=ax[3]-15; r=145; d.arc((cx-r,cy-r,cx+r,cy+r),180,360,fill=(215,215,210),width=28); d.arc((cx-r,cy-r,cx+r,cy+r),180,320,fill=a,width=28); ang=math.radians(320); d.line((cx,cy,cx+r*.75*math.cos(ang),cy+r*.75*math.sin(ang)),fill=dark,width=7)
    elif kind=="radar":
        cx=(ax[0]+ax[2])//2; cy=(ax[1]+ax[3])//2; r=145; n=6
        pts=[]
        for i in range(n):
            ang=-math.pi/2+2*math.pi*i/n; rr=r*rnd.uniform(.5,.95); pts.append((cx+rr*math.cos(ang),cy+rr*math.sin(ang)))
        d.polygon(pts,fill=tuple(int((c+255)/2) for c in b),outline=a)
    elif kind=="aging":
        labs=[("0-30",90),("31-60",68),("61-90",43),("+90",24)]
        for i,(lab,v) in enumerate(labs):
            yy=ax[1]+i*72; d.text((ax[0],yy+8),lab,font=F(18,1),fill=dark); rounded(d,(ax[0]+95,yy,ax[0]+95+v*3,yy+42),10,a if i<2 else b)
    elif kind=="scatter":
        for _ in range(30):
            x=rnd.randint(ax[0]+10,ax[2]-10); y=rnd.randint(ax[1]+10,ax[3]-10); rr=rnd.randint(5,10); d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=a if rnd.random()>.45 else b)
    elif kind=="gantt":
        for r0 in range(6):
            yy=ax[1]+r0*48; st=rnd.randint(0,120); dur=rnd.randint(80,210); rounded(d,(ax[0]+st,yy,min(ax[0]+st+dur,ax[2]),yy+28),8,a if r0%2==0 else b)
    else:
        nodes=[(ax[0]+55,ax[1]+65),(ax[0]+210,ax[1]+145),(ax[0]+365,ax[1]+60),(ax[0]+270,ax[1]+270),(ax[0]+470,ax[1]+250)]
        for p,q in zip(nodes,nodes[1:]): d.line((p,q),fill=b,width=5)
        for i,(x,y) in enumerate(nodes): d.ellipse((x-26,y-26,x+26,y+26),fill=a if i%2==0 else b,outline="white",width=3)

def scene(data,idx,s):
    key,title,subtitle,service,narr,pal,kind,layout=data; bg,a,b,dark=pal
    im=soft_bg(pal,idx*91+s*37+layout); d=ImageDraw.Draw(im); draw_excel_header(d,a,dark,s+layout)
    if s==0:
        d.text((42,126),title,font=F(45,1),fill=dark)
        yy=190
        for ln in wrap(d,subtitle,F(22),620): d.text((44,yy),ln,font=F(22),fill=a); yy+=31
        # Layout-specific hero
        if layout%4==0:
            chart(d,kind,(42,310,678,850),pal,idx+s)
            rounded(d,(42,890,678,1040),28,(255,255,255),outline=(226,226,220),w=2)
            d.text((67,920),service,font=F(25,1),fill=dark); d.text((67,970),"SOLUCIÓN PROFESIONAL • EXCEL + POWER BI",font=F(16,1),fill=a)
        elif layout%4==1:
            rounded(d,(42,310,300,840),28,(255,255,255),outline=(226,226,220),w=2); chart(d,kind,(325,310,678,840),pal,idx+s)
            d.text((68,350),"ANTES",font=F(20,1),fill=b); d.text((68,410),"Horas\nmanuales",font=F(34,1),fill=dark,spacing=10); d.text((68,590),"DESPUÉS",font=F(20,1),fill=a); d.text((68,650),"Control\nautomático",font=F(31,1),fill=dark,spacing=10)
        elif layout%4==2:
            chart(d,kind,(42,310,678,700),pal,idx+s)
            for j,(lab,val) in enumerate([("VISIBILIDAD","100%"),("DECISIÓN","RÁPIDA"),("RIESGO","↓")]):
                x=42+j*215; rounded(d,(x,740,x+200,875),22,(255,255,255),outline=(226,226,220),w=2); d.text((x+18,766),lab,font=F(15,1),fill=a); d.text((x+18,808),val,font=F(28,1),fill=dark)
        else:
            # diagonal layout
            rounded(d,(42,310,678,810),30,(255,255,255),outline=(226,226,220),w=2); chart(d,kind,(70,350,650,770),pal,idx+s)
            d.text((42,855),service.upper(),font=F(27,1),fill=dark)
    elif s==1:
        d.text((42,126),"DE DATOS A CONTROL",font=F(37,1),fill=dark); d.text((42,178),service,font=F(21,1),fill=a)
        chart(d,kind,(42,260,678,760),pal,idx+33)
        labels=[("FUENTE","Excel / BD"),("MODELO","Limpio"),("KPIs","Accionables")]
        for j,(lab,val) in enumerate(labels):
            x=42+j*215; rounded(d,(x,800,x+200,930),22,(255,255,255),outline=(226,226,220),w=2); d.text((x+18,826),lab,font=F(15,1),fill=(100,100,96)); d.text((x+18,865),val,font=F(22,1),fill=dark)
        d.text((42,980),"Información clara. Menos improvisación.",font=F(24,1),fill=a)
    elif s==2:
        d.text((42,126),"LO QUE CAMBIA",font=F(38,1),fill=dark)
        benefits=["Menos tareas repetitivas","Indicadores visibles","Alertas oportunas","Decisiones con evidencia"]
        yy=220
        for j,t in enumerate(benefits):
            rounded(d,(42,yy,678,yy+112),24,(255,255,255),outline=(226,226,220),w=2)
            d.ellipse((66,yy+35,104,yy+73),fill=a if j%2==0 else b); d.text((126,yy+34),t,font=F(25,1),fill=dark); yy+=132
        rounded(d,(42,780,678,965),28,a); d.text((70,820),"EXCEL + POWER BI",font=F(31,1),fill="white"); d.text((70,870),"Diseñado para tu proceso, no para una plantilla.",font=F(20,1),fill="white")
    else:
        d.text((42,140),"¿TIENES UN PROYECTO?",font=F(39,1),fill=dark)
        rounded(d,(42,245,678,560),32,(255,255,255),outline=(226,226,220),w=2)
        d.text((72,286),"EXPERTO EN EXCEL Y POWER BI",font=F(29,1),fill=dark)
        d.text((72,350),service,font=F(22,1),fill=a)
        d.text((72,415),"Desarrollo de trabajos y proyectos",font=F(19),fill=(90,90,86))
        rounded(d,(42,630,678,810),32,a); d.text((75,670),"ESCRÍBEME GRATIS AL WHATSAPP",font=F(23,1),fill="white"); d.text((75,725),"(51) 948-370-116",font=F(40,1),fill="white")
        rounded(d,(42,855,678,980),28,(255,255,255),outline=(226,226,220),w=2); d.text((119,890),"systeracore.com",font=F(34,1),fill=dark)
        d.text((42,1035),"Convierte tus datos en decisiones.",font=F(22,1),fill=a)
    d.text((42,H-52),"systeracore.com",font=F(18,1),fill=dark); d.text((W-270,H-52),"WhatsApp 948 370 116",font=F(17),fill=dark)
    return im

def duration(path):
    v=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)]).decode().strip()
    return float(v)

model="kokoro-v1.0.int8.onnx"; voices="voices-v1.0.bin"
tts=Kokoro(model,voices)
basevoices=["ef_dora","em_alex","ef_dora","em_santa"]
speeds=[1.00,1.03,0.97,1.05,1.01,0.95,1.06,0.99]

manifest=[]
for i,data in enumerate(REELS):
    key,title,subtitle,service,narr,pal,kind,layout=data
    rimg=IMG/f"{i+1:02d}_{key}"; rimg.mkdir(exist_ok=True)
    paths=[]
    for s in range(4):
        p=rimg/f"scene_{s+1}.png"; scene(data,i,s).save(p,quality=95); paths.append(p)
    voice=basevoices[i%len(basevoices)]; speed=speeds[i%len(speeds)]
    samples,sr=tts.create(narr,voice=voice,speed=speed,lang="es")
    raw=AUD/f"reel_{i+1:02d}_raw.wav"; sf.write(raw,samples,sr,subtype="PCM_16")
    clean=AUD/f"reel_{i+1:02d}.wav"
    eq = "highpass=f=75,lowpass=f=11500,acompressor=threshold=-20dB:ratio=2:attack=8:release=100,alimiter=limit=0.95"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(raw),"-af",eq,str(clean)],check=True)
    adur=duration(clean)
    base=[4.2,4.2,4.2]
    last=max(4.2,adur-sum(base)+0.6)
    total=sum(base)+last
    # still-video pieces, add subtle zoompan
    segs=[]
    for s,p in enumerate(paths):
        seg=ROOT/f"seg_{i+1:02d}_{s+1}.mp4"; dur=base[s] if s<3 else last
        z="zoompan=z='min(zoom+0.0007,1.045)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=720x1280:fps=24"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-loop","1","-t",f"{dur:.3f}","-i",str(p),"-vf",z,"-r","24","-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p",str(seg)],check=True)
        segs.append(seg)
    concat=ROOT/f"concat_{i+1:02d}.txt"
    concat.write_text("\n".join([f"file '{x.resolve()}'" for x in segs]),encoding="utf-8")
    silent=ROOT/f"silent_{i+1:02d}.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)],check=True)
    out=OUT/f"REEL_{i+1:02d}_{key}_V02.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(silent),"-i",str(clean),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",str(out)],check=True)
    manifest.append({"reel":i+1,"file":out.name,"voice":voice,"speed":speed,"audio_s":round(adur,2),"video_s":round(duration(out),2),"service":service})

(ROOT/"MANIFEST_V02.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
zip_path=ROOT/"REELS_OCT_2026_Y_V02_20_MP4.zip"
with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for f in sorted(OUT.glob("*.mp4")): z.write(f,arcname=f.name)
    z.write(ROOT/"MANIFEST_V02.json",arcname="MANIFEST_V02.json")
print(zip_path)
print(json.dumps(manifest,ensure_ascii=False,indent=2))
