"""SysTeraCore — ejecutor GitHub gratuito, sin secretos en el repositorio."""
import base64, datetime as dt, json, os, pathlib, subprocess, sys
from zoneinfo import ZoneInfo

ROOT=pathlib.Path(__file__).parent
NOW=dt.datetime.now(ZoneInfo("America/Lima"))
SLOT=NOW.hour//8
CYCLE=f"{NOW:%Y%m%d}-{SLOT}"
OUT=ROOT/"output"/CYCLE
OUT.mkdir(parents=True,exist_ok=True)
posts=json.loads((ROOT/"posts.json").read_text(encoding="utf-8"))
shorts=json.loads((ROOT/"shorts.json").read_text(encoding="utf-8"))
chosen=[posts[(SLOT*4+i)%len(posts)] for i in range(4)]
chosen_short=[shorts[(SLOT*2+i)%len(shorts)] for i in range(2)]
WHATSAPP="https://wa.me/51948370116"
def post_text(item):
    return f"{item['title']}\n\n{item['body']}\n\nEscribir: {WHATSAPP}\nhttps://www.systeracore.com/\n{item['tags']}"
prepared=[dict(item,copy=post_text(item)) for item in chosen]
(OUT/"facebook_preparadas.json").write_text(json.dumps(prepared,indent=2,ensure_ascii=False),encoding="utf-8")
(OUT/"youtube_guiones.json").write_text(json.dumps(chosen_short,indent=2,ensure_ascii=False),encoding="utf-8")
(OUT/"cola_grupos_MANUAL.csv").write_text("nombre,url,permiso_verificado,estado\n",encoding="utf-8")
results=[]
errors=[]
def render_short(item):
    """Crea MP4 gráfico original 1080x1920, subtítulos y sonido instrumental simple."""
    try:
        from PIL import Image,ImageDraw,ImageFont
    except ImportError:
        errors.append("Pillow no está disponible; no se ha renderizado el MP4.")
        return None
    import tempfile
    video=OUT/(item["id"]+".mp4")
    with tempfile.TemporaryDirectory() as td:
        td=pathlib.Path(td)
        lines=[]
        scenes=[item["hook"]]+item["scenes"]
        font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        for i,headline in enumerate(scenes):
            image=Image.new("RGB",(1080,1920),(247,247,241))
            d=ImageDraw.Draw(image)
            d.rounded_rectangle((45,55,1035,180),radius=28,fill=(22,91,72))
            d.text((80,91),"SYSTERACORE / SYSTERA LATAM",font=ImageFont.truetype(font,48),fill="white")
            d.rounded_rectangle((65,350,1015,1240),radius=55,fill="white",outline=(226,228,219),width=4)
            words=headline.upper().split()
            ln=[];buf=""
            ft=ImageFont.truetype(font,69)
            for w in words:
                nxt=(buf+" "+w).strip()
                if d.textbbox((0,0),nxt,font=ft)[2]<825:buf=nxt
                else:
                    ln.append(buf);buf=w
            if buf:ln.append(buf)
            y=530
            for line in ln:
                d.text((115,y),line,font=ft,fill=(28,46,39));y+=110
            d.rounded_rectangle((65,1510,1015,1795),radius=34,fill=(22,91,72))
            d.text((115,1550),"ESCRÍBANOS AL WHATSAPP",font=ImageFont.truetype(font,50),fill="white")
            d.text((115,1655),"+51 948 370 116",font=ImageFont.truetype(font,58),fill=(246,230,200))
            img=td/f"{i:02}.png"
            image.save(img)
            lines += [f"file '{img}'","duration 5"]
        lines.append(f"file '{img}'")
        (td/"scenes.txt").write_text("\n".join(lines),encoding="utf-8")
        try:
            subprocess.run(["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-y",
              "-safe","0","-f","concat","-i",str(td/"scenes.txt"),"-f","lavfi","-i",
              "sine=frequency=250:sample_rate=22050","-vf","fps=24,format=yuv420p",
              "-c:v","libx264","-preset","ultrafast","-crf","27","-c:a","aac",
              "-filter:a","volume=0.03","-t",str(5*len(scenes)),"-shortest",
              "-movflags","+faststart",str(video)],check=True,timeout=200)
            return video
        except Exception:
            errors.append("No se pudo renderizar: "+item["id"])
            return None
rendered={}
for item in chosen_short:
    rendered[item["id"]]=render_short(item)
published_file=ROOT/"state.json"
state=json.loads(published_file.read_text(encoding="utf-8")) if published_file.exists() else {}
if os.getenv("RUN_PUBLISH","false").lower()=="true":
    import requests
    page=os.getenv("FB_PAGE_ID","")
    token=os.getenv("FB_PAGE_ACCESS_TOKEN","")
    item=chosen[0]
    key=f"fb:{page}:{item['id']}"
    if page and token and not state.get(key):
        try:
            created=requests.post(f"https://graph.facebook.com/v26.0/{page}/feed",
                data={"message":post_text(item),"access_token":token},timeout=30)
            created.raise_for_status()
            pid=created.json()["id"]
            checked=requests.get(f"https://graph.facebook.com/v26.0/{pid}",
                params={"fields":"id,permalink_url","access_token":token},timeout=30)
            checked.raise_for_status()
            obj=checked.json()
            if obj.get("id")==pid:
                result={"platform":"Facebook Página","content_id":item["id"],"id":pid,
                        "url":obj.get("permalink_url"),"state":"PUBLICADO_VERIFICADO"}
                results.append(result);state[key]=result
        except Exception as exc:
            errors.append(f"Facebook: no confirmado ({type(exc).__name__}); verificar token y permisos.")
    else:errors.append("Facebook pendiente de token/ID de Página o duplicado evitado.")
    target=os.getenv("YOUTUBE_TARGET_CHANNEL_ID","")
    token64=os.getenv("YOUTUBE_OAUTH_TOKEN_JSON_BASE64","")
    item=chosen_short[0]
    key=f"yt:{target}:{item['id']}"
    video=rendered.get(item["id"])
    if target and token64 and video and not state.get(key):
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            oauth=json.loads(base64.b64decode(token64).decode("utf-8"))
            creds=Credentials.from_authorized_user_info(oauth,scopes=[
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.readonly"])
            if creds.expired and creds.refresh_token:creds.refresh(Request())
            if not creds.valid:raise RuntimeError("OAuth inválido")
            yt=build("youtube","v3",credentials=creds,cache_discovery=False)
            mine=yt.channels().list(part="id",mine=True).execute().get("items",[])
            if len(mine)!=1 or mine[0].get("id")!=target:raise PermissionError("Canal OAuth incorrecto")
            upload=yt.videos().insert(part="snippet,status",body={
                "snippet":{"title":item["title"],"description":item["description"],"categoryId":"28"},
                "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False}},
                media_body=MediaFileUpload(str(video),mimetype="video/mp4",resumable=True))
            response=None
            while response is None:
                _,response=upload.next_chunk()
            vid=response.get("id")
            check=yt.videos().list(part="status",id=vid).execute().get("items",[])
            privacy=check[0].get("status",{}).get("privacyStatus") if check else "unknown"
            obj={"platform":"YouTube","content_id":item["id"],"id":vid,
                 "url":f"https://www.youtube.com/shorts/{vid}",
                 "state":"PUBLICADO_VERIFICADO" if privacy=="public" else "SUBIDO_NO_PUBLICO"}
            results.append(obj)
            if privacy=="public":state[key]=obj
        except Exception as exc:
            errors.append(f"YouTube: no confirmado ({type(exc).__name__}); revisar OAuth, canal y auditoría.")
    else:errors.append("YouTube pendiente de OAuth/ID de canal, MP4 o duplicado evitado.")
else:errors.append("Solo preparación: RUN_PUBLISH=false; ninguna publicación remota.")
published_file.write_text(json.dumps(state,indent=2,ensure_ascii=False),encoding="utf-8")
report={"fecha_pet":NOW.isoformat(),"ciclo":CYCLE,
        "facebook_preparadas":len(prepared),"shorts_mp4_generados":sum(bool(v) for v in rendered.values()),
        "facebook_publicaciones_verificadas":sum(x["platform"]=="Facebook Página" and x["state"]=="PUBLICADO_VERIFICADO" for x in results),
        "grupos_facebook_publicados_verificados":0,
        "youtube_publicados_verificados":sum(x["platform"]=="YouTube" and x["state"]=="PUBLICADO_VERIFICADO" for x in results),
        "monetizacion":"NO VERIFICADA - requiere Analytics/Studio autorizados",
        "resultados":results,"observaciones":errors}
(OUT/"REPORTE.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
