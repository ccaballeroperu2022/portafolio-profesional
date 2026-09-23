# SysTera Social — Automatizador en GitHub

Sistema de publicaciones en lote cada 8 horas para SysTeraCore. Genera 4 anuncios distintos, 2 videos Shorts MP4 y un reporte por ciclo. Sólo publica en **Páginas** de Facebook y canales de YouTube mediante API oficial si la configuración `RUN_PUBLISH=true` y credenciales autorizadas existen. De lo contrario prepara entregables sin afirmar publicaciones.

**Estado actual:** credenciales Facebook/YouTube no conectadas aquí. La publicación de Facebook en grupos no se ejecuta con bots: Meta retiró la API de Grupos en 2024. La cola grupal permanece manual y sólo para grupos que permiten promociones.

En GitHub: **Settings → Secrets and variables → Actions**, introducir `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN`, `YOUTUBE_TARGET_CHANNEL_ID`, `YOUTUBE_OAUTH_TOKEN_JSON_BASE64`; crear variable `RUN_PUBLISH=true` únicamente tras la prueba autorizada. La conexión de Google requiere OAuth con alcance YouTube Upload y Readonly desde la cuenta titular; no proporcione tokens en el chat. El flujo corre 00:00, 08:00 y 16:00 de Perú, sujeto a retrasos de Actions; tiene botón manual **Run workflow**.

Autora de los contenidos: Ingeniero de Sistemas Carlos Andrés Caballero Castillo. Sitio https://www.systeracore.com/ WhatsApp https://wa.me/51948370116

**Importante:** un proyecto YouTube API no auditado puede subir videos únicamente como privados; no se cuentan como publicación pública. Ingresos `NO VERIFICADOS` mientras no exista acceso explícito a Analytics/Studio. No declarar monetización por número de vistas.

Paquete complementario completo con manual Windows y cuatro MP4 iniciales: carpeta privada del titular en Google Drive, «Desarrollo Automatizacion V1 - 2026-09-23 16-20 PET».
