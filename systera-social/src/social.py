"""SysTera Social v1: publicación autorizada, idempotencia y evidencia verificable.
No publica en perfiles personales ni grupos de Facebook: Graph Groups API retirada.
"""
from __future__ import annotations
import argparse
import base64
import csv
import datetime as dt
import json
import os
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PET = ZoneInfo('America/Lima')
WHATSAPP = 'https://wa.me/51948370116'
WEBSITE = 'https://www.systeracore.com/'


def now_pet() -> dt.datetime:
    return dt.datetime.now(PET)


def iso_cycle(when: dt.datetime) -> str:
    w = when.astimezone(PET)
    slot = w.hour // 8  # 00:00, 08:00 y 16:00; corrida idempotente por intervalo.
    return f'{w.date().isoformat()}-{slot}'


def cycle_number(when: dt.datetime) -> int:
    first = dt.date(2026, 9, 23)
    w = when.astimezone(PET)
    return max(0, (w.date() - first).days * 3 + w.hour // 8)


def load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    with path.open(encoding='utf-8') as handle:
        return json.load(handle)


def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    temp.replace(path)


def page_text(post: dict) -> str:
    return '\n\n'.join((post['title'], post['body'],
        f'Cotizaciones: {WHATSAPP}\n{WEBSITE}', post['hashtags']))


def safe_error(exc: Exception) -> str:
    # Nunca registrar token, cabeceras Authorization ni respuesta textual sin depurar.
    return f'{type(exc).__name__}: operación no confirmada; revise credenciales, permisos y registros privados del proveedor.'


def facebook_post_verified(post: dict, page_id: str, token: str, version: str = 'v26.0', session=None) -> dict:
    """Publica exclusivamente en la Página configurada. No inventa permalink."""
    import requests
    session = session or requests.Session()
    url = f'https://graph.facebook.com/{version}/{page_id}/feed'
    response = session.post(url, data={'message': page_text(post), 'access_token': token}, timeout=35)
    response.raise_for_status()
    result = response.json()
    post_id = result.get('id')
    if not post_id:
        raise ValueError('Meta no devolvió ID de publicación.')
    try:
        check = session.get(f'https://graph.facebook.com/{version}/{post_id}',
            params={'fields': 'id,permalink_url', 'access_token': token}, timeout=30)
        check.raise_for_status()
        verified = check.json()
        if str(verified.get('id')) != str(post_id):
            return {'state':'ENVIADO_NO_VERIFICADO', 'id':post_id, 'url':None}
        return {'state':'PUBLICADO_VERIFICADO', 'id':post_id, 'url':verified.get('permalink_url')}
    except Exception:
        # Meta ya creó el post; no volver a enviarlo por un fallo posterior del GET.
        return {'state':'ENVIADO_NO_VERIFICADO', 'id':post_id, 'url':None}


def ensure_google_files():
    """Acepta secretos GitHub codificados; NO genera ni inventa autorización OAuth."""
    secret_path = Path(os.getenv('YOUTUBE_CLIENT_SECRET_FILE', str(ROOT/'secrets/client_secret.json')))
    token_path = Path(os.getenv('YOUTUBE_TOKEN_FILE', str(ROOT/'secrets/youtube_token.json')))
    for env_var, target in [('YOUTUBE_CLIENT_SECRET_JSON_BASE64', secret_path),
                            ('YOUTUBE_OAUTH_TOKEN_JSON_BASE64', token_path)]:
        value = os.getenv(env_var, '').strip()
        if value:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base64.b64decode(value, validate=True))
            try: target.chmod(0o600)
            except OSError: pass
    return secret_path, token_path


def get_youtube_credentials(interactive: bool = False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    secret_path, token_path = ensure_google_files()
    scopes = ['https://www.googleapis.com/auth/youtube.upload',
              'https://www.googleapis.com/auth/youtube.readonly']
    if os.getenv('YOUTUBE_ANALYTICS_ENABLED','false').lower() == 'true':
        scopes += ['https://www.googleapis.com/auth/yt-analytics-monetary.readonly']
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes=scopes)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding='utf-8')
    if not creds or not creds.valid:
        if not interactive or not secret_path.exists():
            raise RuntimeError('OAuth de YouTube no conectado. Ejecute authorize-youtube en su equipo.')
        flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), scopes=scopes)
        creds = flow.run_local_server(port=0, prompt='consent', access_type='offline')
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding='utf-8')
    return creds


def youtube_upload_verified(video: Path, short: dict, target_channel_id: str) -> dict:
    """Upload con OAuth. Nunca presupone que la API dejó el vídeo público."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    yt = build('youtube', 'v3', credentials=get_youtube_credentials(False), cache_discovery=False)
    mine = yt.channels().list(part='id,snippet', mine=True).execute().get('items',[])
    if len(mine) != 1 or mine[0].get('id') != target_channel_id:
        raise PermissionError('OAuth no coincide con el canal de destino definido.')
    if not video.is_file() or video.stat().st_size == 0:
        raise FileNotFoundError('El MP4 todavía no existe.')
    upload = yt.videos().insert(part='snippet,status', body={
        'snippet': {'title':short['title'], 'description':short['description'],
                    'categoryId':'28'},
        'status': {'privacyStatus':'public', 'selfDeclaredMadeForKids':False}},
        media_body=MediaFileUpload(str(video), mimetype='video/mp4', resumable=True))
    response = None
    while response is None:
        _, response = upload.next_chunk()
    vid = response.get('id')
    if not vid:
        raise RuntimeError('YouTube no entregó ID del video.')
    # El ID confirma que ya se subió; cualquier fallo al verificar NO autoriza una segunda subida.
    try:
        check = yt.videos().list(part='status,snippet', id=vid).execute().get('items',[])
        privacy = check[0].get('status',{}).get('privacyStatus') if check else 'unknown'
        processing = check[0].get('status',{}).get('uploadStatus') if check else 'unknown'
        status = ('PUBLICADO_VERIFICADO' if privacy == 'public' and
                  processing not in ('rejected','failed') else
                  'SUBIDO_NO_PUBLICO' if privacy != 'public' else 'PUBLICO_EN_PROCESO')
    except Exception:
        privacy = 'unknown'
        status = 'SUBIDO_NO_VERIFICADO'
    return {'state':status,'id':vid,'url':f'https://www.youtube.com/shorts/{vid}',
            'privacy':privacy}


def next_unsent(items: list[dict], prefix: str, target: str, registry: dict, start: int = 0):
    """Elige otra pieza original si la rotación ya publicó la primera.
    Detiene la salida al agotar el catálogo, en vez de reciclar anuncios.
    """
    for offset in range(len(items)):
        item = items[(start + offset) % len(items)]
        if f'{prefix}:{target}:{item["id"]}' not in registry:
            return item
    return None


def read_group_queue() -> list[dict]:
    file = ROOT / 'config/grupos.csv'
    if not file.exists(): return []
    with file.open(encoding='utf-8-sig', newline='') as handle:
        return [row for row in csv.DictReader(handle) if row.get('url_grupo')]


def render_group_csv(path: Path, posts: list[dict], when: dt.datetime) -> int:
    """Cola para publicación nativa MANUAL; jamás afirma que publicó en grupos."""
    groups = [g for g in read_group_queue() if g.get('permite_publicidad','').strip().lower() == 'si'
              and g.get('prueba_permiso','').strip()]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.writer(handle)
        writer.writerow(['grupo','url','pieza','texto_preparado','estado','fecha_pet','prueba_permiso'])
        for group in groups:
            for p in posts[:1]:  # No hacer envíos repetitivos masivos.
                writer.writerow([group['nombre_grupo'],group['url_grupo'],p['id'],
                    page_text(p),'PENDIENTE_PUBLICACION_MANUAL',when.isoformat(),group['prueba_permiso']])
    return len(groups)


def report_markdown(when, prepared, shorts, outcomes, groups, errors, revenue):
    written = sum(1 for o in outcomes if o.get('state')=='PUBLICADO_VERIFICADO' and o.get('platform')=='Facebook Página')
    videos = sum(1 for o in outcomes if o.get('state')=='PUBLICADO_VERIFICADO' and o.get('platform')=='YouTube')
    groups_published = sum(1 for o in outcomes if o.get('platform')=='Facebook Grupo' and o.get('state')=='PUBLICADO_VERIFICADO')
    lines = [f'# SysTera — reporte de ejecución {when.strftime("%Y-%m-%d %H:%M %Z")}', '',
        f'- Publicidades de Facebook preparadas: {len(prepared)}',
        f'- Guiones/videos YouTube programados: {len(shorts)}',
        f'- Publicaciones verificadas en Facebook Página: {written}',
        f'- Publicaciones verificadas en Facebook Grupos: {groups_published}',
        f'- Grupos autorizados en cola manual: {groups}',
        f'- YouTube Shorts publicados y verificados: {videos}',
        f'- Monetización verificada: {revenue}',
        '- Cifra histórica de ingresos: SIN ACCESO/NO VERIFICADA; no equivale a S/ 0.',
        '', '## Resultados comprobables']
    lines.extend(f"- {o.get('platform')} | {o.get('id')} | {o.get('state')} | {o.get('url') or 'URL no disponible'}" for o in outcomes)
    if not outcomes: lines.append('- No se realizó ninguna publicación externa.')
    lines += ['', '## Observaciones']
    lines.extend(f'- {e}' for e in errors)
    return '\n'.join(lines)+'\n'


def run_cycle(now: dt.datetime | None = None, publish: bool = False, render: bool = False):
    when = now or now_pet()
    slot = cycle_number(when)
    cycle = iso_cycle(when)
    posts = load_json(ROOT/'config/posts.json',[])
    shorts = load_json(ROOT/'config/shorts.json',[])
    if not posts or not shorts: raise ValueError('Configure publicaciones y shorts antes de ejecutar.')
    chosen_posts = [posts[(slot*4+i) % len(posts)] for i in range(4)]
    chosen_shorts = [shorts[(slot*2+i) % len(shorts)] for i in range(2)]
    out = ROOT/'output'/cycle
    out.mkdir(parents=True,exist_ok=True)
    save_json(out/'publicaciones_preparadas.json',[dict(p, text=page_text(p)) for p in chosen_posts])
    save_json(out/'guiones_shorts.json',chosen_shorts)
    groups = render_group_csv(out/'cola_grupos_MANUAL.csv',chosen_posts,when)
    state_path = ROOT/'data/state.json'
    state = load_json(state_path,{'published':{}, 'runs':{}})
    state.setdefault('published',{})
    state.setdefault('runs',{})
    outcomes=[]
    errors=[]
    if render:
        from render import render_short
        for short in chosen_shorts:
            dest = out/f"{short['id']}.mp4"
            render_short(short,dest)
    allowed = publish and os.getenv('RUN_PUBLISH','false').lower()=='true'
    if publish and not allowed: errors.append('PUBLICACIÓN BLOQUEADA: falta RUN_PUBLISH=true.')
    if allowed:
        page_id=os.getenv('FB_PAGE_ID','').strip()
        token=os.getenv('FB_PAGE_ACCESS_TOKEN','').strip()
        post=next_unsent(posts,'fb',page_id,state['published'],slot*4) if page_id else None
        key=f"fb:{page_id}:{post['id']}" if post else ''
        if page_id and token and post:
            try:
                result=facebook_post_verified(post,page_id,token,os.getenv('META_API_VERSION','v26.0'))
                result.update(platform='Facebook Página', content_id=post['id'])
                outcomes.append(result)
                # Conservar también la respuesta con ID no verificado: bloquea duplicados.
                if result.get('id'):
                    state['published'][key]=result
                    save_json(state_path,state)
            except Exception as exc:errors.append('Facebook Página '+safe_error(exc))
        elif not page_id or not token: errors.append('Facebook Página pendiente: FB_PAGE_ID/FB_PAGE_ACCESS_TOKEN y permisos oficiales.')
        else:errors.append('Facebook: catálogo original agotado para esta Página; cree piezas nuevas antes del siguiente envío.')
        target=os.getenv('YOUTUBE_TARGET_CHANNEL_ID','').strip()
        short=next_unsent(shorts,'yt',target,state['published'],slot*2) if target else None
        key=f'yt:{target}:{short["id"]}' if short else ''
        video=out/f'{short["id"]}.mp4' if short else None
        if target and short:
            try:
                if not video.exists():
                    from render import render_short
                    render_short(short,video)
                result=youtube_upload_verified(video,short,target)
                result.update(platform='YouTube',content_id=short['id'])
                outcomes.append(result)
                # Un video privado sigue estando subido y no debe volver a cargarse.
                if result.get('id'):
                    state['published'][key]=result
                    save_json(state_path,state)
            except Exception as exc:errors.append('YouTube '+safe_error(exc))
        elif not target: errors.append('YouTube pendiente: OAuth y YOUTUBE_TARGET_CHANNEL_ID.')
        else: errors.append('YouTube: catálogo original agotado; no volver a subir videos ya enviados.')
    else:
        errors.append('Modo preparación: conexiones externas no invocadas; ninguna publicación afirmada.')
    if not groups: errors.append('No hay grupos autorizados documentados; cola manual vacía.')
    revenue='NO VERIFICADO (no hay lectura autorizada de ingresos)'
    # Ingresos sólo se consignan cuando el API devuelve la métrica; jamás se calculan por vistas.
    if allowed and os.getenv('YOUTUBE_ANALYTICS_ENABLED','false').lower()=='true':
        try:
            from googleapiclient.discovery import build
            creds=get_youtube_credentials(False)
            ana=build('youtubeAnalytics','v2',credentials=creds,cache_discovery=False)
            date=when.date()-dt.timedelta(days=2)  # últimos datos consolidados, no hoy
            raw=ana.reports().query(ids='channel==MINE',startDate=date.isoformat(),endDate=date.isoformat(),
                       metrics='estimatedRevenue',currency='USD').execute()
            rows=raw.get('rows') or []
            if rows: revenue=f'USD {float(rows[0][0]):.2f} estimado, fecha {date.isoformat()} (YouTube Analytics)'
        except Exception as exc: errors.append('Monetización YouTube '+safe_error(exc))
    state['runs'][cycle]={'at':when.isoformat(),'prepared_posts':len(chosen_posts),
        'prepared_short_scripts':len(chosen_shorts),'groups_prepared':groups,'outcomes':outcomes,
        'revenue':revenue}
    save_json(state_path,state)
    report=report_markdown(when,chosen_posts,chosen_shorts,outcomes,groups,errors,revenue)
    (out/'REPORTE.md').write_text(report,encoding='utf-8')
    verified_pages = sum(v.get('state') == 'PUBLICADO_VERIFICADO'
        for k,v in state['published'].items() if k.startswith('fb:'))
    verified_shorts = sum(v.get('state') == 'PUBLICADO_VERIFICADO'
        for k,v in state['published'].items() if k.startswith('yt:'))
    (out/'REPORTE_ACUMULADO.json').write_text(json.dumps({
        'fecha_pet':when.isoformat(), 'fb_verificadas_historico_sistema': verified_pages,
        'youtube_verificados_historico_sistema': verified_shorts,
        'facebook_grupos_verificados_historico_sistema':0,
        'monetizacion_historica':'NO VERIFICADA', 'publicaciones_con_evidencia':list(state['published'].values())
    },indent=2,ensure_ascii=False),encoding='utf-8')
    print(report)
    return {'prepared_posts':len(chosen_posts),'shorts':len(chosen_shorts),'groups':groups,
            'published_fb':sum(o['platform']=='Facebook Página' and o['state']=='PUBLICADO_VERIFICADO' for o in outcomes),
            'published_yt':sum(o['platform']=='YouTube' and o['state']=='PUBLICADO_VERIFICADO' for o in outcomes),
            'report_path':str(out/'REPORTE.md')}


def main():
    parser=argparse.ArgumentParser(description='SysTera: automatización verificable Facebook Page y YouTube')
    commands=parser.add_subparsers(dest='cmd',required=True)
    run=commands.add_parser('run')
    run.add_argument('--publish',action='store_true',help='Publica sólo si además RUN_PUBLISH=true y OAuth válido.')
    run.add_argument('--render',action='store_true',help='Generar videos MP4 de los shorts del ciclo.')
    commands.add_parser('authorize-youtube',help='Iniciar consentimiento OAuth en el navegador local del titular.')
    args=parser.parse_args()
    if args.cmd=='authorize-youtube':
        get_youtube_credentials(interactive=True)
        print('OAuth completado para la sesión autorizada; confirme ID del canal antes de publicar.')
    else:
        run_cycle(publish=args.publish,render=args.render)

if __name__=='__main__':main()
