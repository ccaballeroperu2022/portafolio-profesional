# SysTera Social — Automatización comercial v1.0

**Autoría:** Ingeniero de Sistemas Carlos Andrés Caballero Castillo. Material original de SysTeraCore.

Aplicación reproducible para **preparar lotes cada ocho horas**, generar Shorts originales con subtítulos y sonido instrumental original, publicar en una **Página de Facebook** autorizada mediante Meta Graph API y subir videos al **canal de YouTube** autorizado con OAuth. Todas las publicaciones se validan por ID y estado obtenido del proveedor. Registra un estado reutilizable en `data/state.json` para no repetir una pieza ya verificada.

**No automatiza grupos de Facebook ni perfiles personales.** Meta retiró Groups API y `publish_to_groups` en abril de 2024. Se incluye una cola CSV para grupos donde **se haya verificado** que permiten publicidad; la publicación real la realiza el titular mediante la interfaz nativa autorizada. Ninguna herramienta debe evadir bloqueos, CAPTCHAs ni restricciones de plataforma.

## Ejecutar el paquete de demostración — S/ 0

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests
python src/social.py run --render
```

El modo predeterminado es **preparación, no publicación**. Produce cuatro copys distintos, dos Shorts MP4 1080x1920 sin voz (subtitulados con música instrumental original), guiones, cola manual de grupos y reporte en `output/FECHA-FRANJA/`. No incluye fotos, clips ni música ajenos sin licencia. Su estilo es gráfico; no simula interfaces reales de clientes.

## Habilitar Facebook Página (Meta Graph API v26.0)

1. Cree/seleccione una aplicación en Meta for Developers y configure su autorización oficial.
2. Su identidad debe ser administradora de la Página, con las tareas y permisos exigidos para publicar, por ejemplo `pages_manage_posts` y `pages_read_engagement` y, cuando corresponda, `pages_show_list`, sujetos a revisión y modo de aplicación.
3. Obtenga el **ID numérico de la PÁGINA** y el **Page Access Token**. No utilice el ID del perfil personal en `FB_PAGE_ID`.
4. Guarde los valores como variables locales de entorno o secretos de GitHub. Nunca en este repositorio, una conversación o Drive compartido.
5. En `config/posts.json` redacte contenido original nuevo después de agotar los originales, compruebe que no sea spam y ejecute de forma explícita `RUN_PUBLISH=true python src/social.py run --publish --render`.

Verificación: el programa devuelve `PUBLICADO_VERIFICADO` sólo cuando la API confirma la existencia del ID recién creado. El permalink, si la API lo proporciona, se registra.

## Habilitar canal de YouTube (OAuth de Google)

1. Desde Google Cloud habilite **YouTube Data API v3**; configure pantalla de consentimiento y cliente OAuth **Aplicación de escritorio**; descargue su JSON privado a `secrets/client_secret.json`.
2. Inicie sesión con la cuenta que sea titular del canal y ejecute en el PC `python src/social.py authorize-youtube`. La autorización genera `secrets/youtube_token.json` para ese canal. No suba ambos archivos al repositorio.
3. Obtenga y confirme el ID del canal de destino desde YouTube Studio. Configure `YOUTUBE_TARGET_CHANNEL_ID`; el programa contrasta este ID con el canal que devuelve `channels.list(mine=True)` antes de subir nada.
4. Dé a conocer los videos, condiciones comerciales y derechos. Un proyecto YouTube API creado desde el 28/07/2020 sin auditoría puede forzar **modo privado**, aunque se solicite público. El programa no presenta una carga privada como publicación pública.
5. Para monetización, la aprobación del Programa para Partners, requisitos en vigor, contenido original y AdSense para YouTube son independientes del acto de subir videos. No hay ingresos garantizados.

**Segundo canal:** se prepara una propuesta editorial en `config/segundo_canal.txt`; el canal se crea en YouTube/Google bajo autorización del titular y requiere su consentimiento OAuth independiente. El API de publicación no crea canales ni activa monetización automáticamente.

## Automatizar cada 8 horas con GitHub Actions

Una vez instalado en `systera-social/` en la rama principal de un repositorio personal con Actions habilitado, la plantilla `.github/workflows/systera-social-8h.yml` programa corridas a las 00:17, 08:17 y 16:17 de Perú, con posible retraso de GitHub. La corrida se puede iniciar con **Run workflow**. Se conservan los ZIP de cada lote en los **artifacts** de la ejecución durante 30 días.

**Secrets necesarios cuando esté preparado para publicar:** `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN`, `YOUTUBE_TARGET_CHANNEL_ID`, `YOUTUBE_CLIENT_SECRET_JSON_BASE64`, `YOUTUBE_OAUTH_TOKEN_JSON_BASE64`. Los valores base64 se obtienen de sus archivos OAuth privados. La variable del repositorio `RUN_PUBLISH` debe ser exactamente `true`; por defecto todo queda en modo preparación. La acción no podrá publicar mientras falten permisos o secretos autorizados; no los suplanta ni los inventa.

Almacene el repositorio **preferentemente privado**. El GitHub vinculado actualmente contiene únicamente el repositorio público `portafolio-profesional`; por eso una eventual rama en él debe contener **sólo código y material publicable**. Los secretos nunca entran en el commit.

El archivo `data/state.json` sólo se incorpora por GitHub Actions después de cada corrida; las carpetas `output/` con videos y reportes se descargan como artifacts. Si el repositorio no dispone de Actions o políticas adecuadas, use el Programador de tareas de Windows; `docs/INSTALACION_PASO_A_PASO.txt` tiene las instrucciones.

## Límites transparentes y prevención de duplicados

- `--publish` más `RUN_PUBLISH=true` habilitan los envíos, pero exigen credenciales válidas y configuración previa. Sin credenciales genera entregables y muestra **PENDIENTE**.
- Sólo publica una pieza por plataforma y corrida de ocho horas; prepara cuatro anuncios y dos guiones para selección. Nunca publica las cuatro variantes idénticas en múltiples grupos.
- Al agotar las piezas originales del catálogo (12 copys y cuatro shorts en la primera versión), necesita nuevos guiones originales. Una ejecución periódica **no** equivale a contenido ilimitado ni garantiza monetización.
- La métrica de ingresos no se estima a partir de visualizaciones. Puede activar `YOUTUBE_ANALYTICS_ENABLED=true` sólo después del consentimiento específico `yt-analytics-monetary.readonly`; se intenta leer la estimación consolidada para un día anterior. Meta exige sus propias métricas reales desde sus productos de monetización.
- Publicaciones que devuelvan error, sólo confirmación de carga o estado privado no se contabilizan como publicadas verificadas.

## Material y soporte

`config/posts.json` (12 copies), `config/shorts.json` (4 guiones), `config/grupos.csv` (vacío: no inventamos grupos), `src/social.py` (automatizador), `src/render.py` (generador gráfico gratuito), `tests/test_social.py` (pruebas), `.github/workflows` (ciclos), `docs/INSTALACION_PASO_A_PASO.txt` (guía), `output/` (videos e informes), `data/state.json` (deduplicación).

**Fuentes oficiales:**
- Meta Graph API: https://developers.facebook.com/docs/graph-api/
- Cambio Groups API: https://developers.facebook.com/docs/graph-api/changelog/version19.0
- YouTube Data API upload: https://developers.google.com/youtube/v3/docs/videos/insert
- YPP y requisitos: https://support.google.com/youtube/answer/72851?hl=es

## Registro y protección contra duplicados (v1.1)

Si Meta crea una publicación pero falla su consulta posterior, se guarda el ID como `ENVIADO_NO_VERIFICADO`: **no se reenvía** automáticamente. Si YouTube devuelve ID pero deja el vídeo privado, se registra `SUBIDO_NO_PUBLICO`: tampoco se vuelve a cargar. `REPORTE_ACUMULADO.json` contiene únicamente publicaciones confirmadas por el sistema y sus enlaces de evidencia. Al agotar el catálogo original, se detiene la publicación y pide material nuevo. No confundir número de anuncios preparados con publicaciones reales.
