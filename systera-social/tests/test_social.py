import json
from pathlib import Path
import sys
import datetime as dt
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import social

def test_cycle_same_slot():
    d=dt.datetime(2026,9,23,16,12,tzinfo=ZoneInfo('America/Lima'))
    assert social.iso_cycle(d)=='2026-09-23-2'
    assert social.iso_cycle(d+dt.timedelta(hours=7))=='2026-09-23-2'

def test_posts_have_unique_ids_and_wa():
    posts=json.loads((ROOT/'config/posts.json').read_text(encoding='utf-8'))
    assert len(posts)>=12 and len({p['id'] for p in posts})==len(posts)
    assert all('wa.me/51948370116' in social.page_text(p) for p in posts)

def test_no_credentials_no_external_posts(tmp_path,monkeypatch):
    monkeypatch.setattr(social,'ROOT',tmp_path)
    (tmp_path/'config').mkdir()
    (tmp_path/'config/posts.json').write_text((ROOT/'config/posts.json').read_text(encoding='utf-8'),encoding='utf-8')
    (tmp_path/'config/shorts.json').write_text((ROOT/'config/shorts.json').read_text(encoding='utf-8'),encoding='utf-8')
    (tmp_path/'config/grupos.csv').write_text('nombre_grupo,url_grupo,permite_publicidad,prueba_permiso,ultima_publicacion,observaciones\n',encoding='utf-8')
    monkeypatch.delenv('RUN_PUBLISH',raising=False)
    monkeypatch.setattr(social,'facebook_post_verified',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('no debe llamar la API')))
    value=social.run_cycle(now=dt.datetime(2026,9,23,16,0,tzinfo=ZoneInfo('America/Lima')),publish=True,render=False)
    assert value['prepared_posts']==4 and value['shorts']==2
    assert value['published_fb']==value['published_yt']==0
    assert (tmp_path/'output/2026-09-23-2/REPORTE.md').exists()

def test_fb_only_verified_with_get():
    class Response:
        def __init__(self,data):self.data=data
        def raise_for_status(self):return None
        def json(self):return self.data
    class FakeSession:
        def post(self,url,data,timeout):
            assert '/feed' in url and data['access_token']=='dummy'
            return Response({'id':'100_200'})
        def get(self,url,params,timeout):
            assert params['fields']=='id,permalink_url'
            return Response({'id':'100_200','permalink_url':'https://www.facebook.com/test/posts/200'})
    post=json.loads((ROOT/'config/posts.json').read_text(encoding='utf-8'))[0]
    v=social.facebook_post_verified(post,'100','dummy',session=FakeSession())
    assert v['state']=='PUBLICADO_VERIFICADO' and v['id']=='100_200'

def test_groups_never_published(tmp_path,monkeypatch):
    monkeypatch.setattr(social,'ROOT',tmp_path)
    (tmp_path/'config').mkdir()
    (tmp_path/'config/grupos.csv').write_text('nombre_grupo,url_grupo,permite_publicidad,prueba_permiso,ultima_publicacion,observaciones\nDemo,https://facebook.com/groups/123,si,URL-regla,,\n',encoding='utf-8')
    posts=json.loads((ROOT/'config/posts.json').read_text(encoding='utf-8'))
    n=social.render_group_csv(tmp_path/'cola.csv',posts,dt.datetime(2026,9,23,tzinfo=ZoneInfo('America/Lima')))
    assert n==1 and 'PENDIENTE_PUBLICACION_MANUAL' in (tmp_path/'cola.csv').read_text(encoding='utf-8-sig')


def test_no_duplicate_upload_or_post_after_id():
    registry={'fb:PAGE:FB-001':{'state':'ENVIADO_NO_VERIFICADO','id':'PAGE_1'},
              'yt:CHANNEL:YT-001':{'state':'SUBIDO_NO_PUBLICO','id':'VID01'}}
    posts=json.loads((ROOT/'config/posts.json').read_text(encoding='utf8'))
    shorts=json.loads((ROOT/'config/shorts.json').read_text(encoding='utf8'))
    assert social.next_unsent(posts,'fb','PAGE',registry,0)['id']=='FB-002'
    assert social.next_unsent(shorts,'yt','CHANNEL',registry,0)['id']=='YT-002'
    complete={f'fb:PAGE:{post["id"]}':{'id':'x'} for post in posts}
    assert social.next_unsent(posts,'fb','PAGE',complete) is None

def test_fb_created_not_retried_when_verification_fails():
    class Response:
        def raise_for_status(self): pass
        def json(self):return {'id':'10_20'}
    class Session:
        def post(self,*a,**k):return Response()
        def get(self,*a,**k):raise ConnectionError('GET failed after POST')
    post=json.loads((ROOT/'config/posts.json').read_text(encoding='utf8'))[0]
    out=social.facebook_post_verified(post,'10','dummy',session=Session())
    assert out['state']=='ENVIADO_NO_VERIFICADO' and out['id']=='10_20'
