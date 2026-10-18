# Contenido diario de Libreta — guía para cada corrida

Este repo genera y publica **un posteo por día** sobre Libreta (libretaapp.com) en
**Instagram @maxis.news, la página de Facebook y TikTok @maxi.bustamanteok**, vía Metricool.
Las imágenes y videos se suben acá porque Instagram necesita una URL pública:
`https://raw.githubusercontent.com/autosrafaela/libreta-redes/main/posts/<id>/<archivo>`.

## Qué es Libreta (lo que se puede afirmar)
- Historial de mantenimiento del auto o moto **por patente**. Lo cargan **los profesionales** (mecánica, gomería,
  lubricentro, frenos, electricidad, chapa y pintura, tapicería, lavadero, GNC, motos…). El dueño no puede inventar trabajos.
- Los trabajos **no se borran ni se editan**; los **km solo van para adelante**. Los talleres se verifican (CUIT o DNI + fotos del local) y llevan tilde azul.
- Avisos al celular (y por email) antes de que venzan **VTV, seguro, patente, licencia, matafuegos**. Checklist de equipamiento (balizas, botiquín, chaleco…).
- Mantenimiento: cuándo toca aceite, filtros, alineación, cubiertas, según km y tiempo.
- Turnos entre usuario y taller, con botón para Google Calendar.
- Al vender: **informe para el comprador** con un link y **transferencia** del historial al nuevo dueño.
- Profesionales: buscan la patente, cargan el trabajo en segundos con sugerencia de repuestos, le mandan el link al cliente por WhatsApp; la app les dice a qué cliente llamar cuando le toca el próximo service.
- Precio hoy: **gratis** para usuarios y profesionales, sin tarjeta. (Plan completo opcional: no lo promocionar salvo que Maxi lo pida.)
- Nunca inventar números de usuarios, testimonios, premios, alianzas ni descuentos. Los talleres y patentes de ejemplo son ficticios (AB 123 CD, "Taller Don Pepe").
- Libreta y Mikiosco son proyectos distintos: nunca mezclarlos.

## Público y tono
- Cuenta de noticias de Rafaela (~4.000 seguidores): gente local con auto o moto, y talleres de la zona.
- Español rioplatense con voseo, directo, cero tecnicismos. Frases cortas. Nada de "revolucionario" ni "potenciá".
- Alternar ángulos: dueño (vencimientos, multas, vender mejor, mantenimiento) ~70% y profesionales/talleres ~30%.

## Antes de publicar: revisar
Mirar SIEMPRE las láminas (o 4–5 fotogramas del reel con ffmpeg) con la herramienta de lectura de imágenes: texto que no se corta ni se superpone, nada fuera de la pantalla, sin errores de ortografía. Si algo falla, corregir el spec y volver a generar.

## Preparar la sesión
`sh tools/setup.sh` (instala dependencias). Generar con `node tools/render.mjs posts/<id>/spec.json`. La primera vez descarga la voz (~115 MB) sola.

## Rotación de formatos
Seguir el ciclo por número de posteo (ver `content/log.json`): **reel, carrusel, reel, imagen, carrusel, reel, carrusel**.
- **Reel** (1080×1920, 18–35 s, 5–8 escenas): SIEMPRE con voz en off. Cada escena lleva `say` (lo que dice la voz, 1 o 2 frases cortas);
  el texto en pantalla resume con palabras clave en `*ámbar*`. Primera escena = gancho en menos de 2 s. Última = CTA a libretaapp.com.
- **Carrusel** (1080×1350, 5–7 láminas): lámina 1 gancho fuerte, después desarrollo, la última siempre `cta`.
- **Imagen** (1 lámina 1080×1350): un dato o consejo concreto + libretaapp.com en el pie (ya va en todas las láminas).

## Cómo se arma un spec (`posts/<YYYY-MM-DD>/spec.json`)
```json
{ "id": "2026-10-20", "theme": "<clave del tema>", "format": "reel|carousel|image",
  "slides": [ ... ]   // carrusel o imagen
  "scenes": [ { ...lámina, "dur": 3, "say": "texto de la voz" } ]  // reel
}
```
Tipos de lámina/escena (en textos: `*palabra*` = ámbar, `**palabra**` = negrita, `\n` = salto):
- `hook` {kicker?, title, sub?, plate?}
- `list` {kicker?, title, mark: "num"|"check"|"x", items: [{t, d?}]} — máximo 4 ítems
- `quote` {text, by?}
- `plate` {plate, title, sub?, kicker?}
- `phone` {title?, sub?, screen: {kind, plate?, vehicle?, km?, items?}} — kinds: `vencimientos`, `historial`, `patente`, `trabajo`,
  `mantenimiento`, `informe`, `turno`, `aviso` (notificaciones en pantalla bloqueada). Sin `items` usa datos de ejemplo coherentes.
- `cta` {title?, sub?, pill?}
Títulos: máximo ~7 palabras. Si un título queda en más de 4 renglones, acortarlo.

## Texto del posteo (caption)
- Primera línea = gancho (se ve antes del "ver más"). 3–8 líneas cortas, algún emoji puntual (🚗 🔧 📅 ✅).
- SIEMPRE cerrar con el llamado: `👉 Entrá gratis a libretaapp.com` (+ "link en la bio" en Instagram).
- 5–8 hashtags al final, mezclando: #Rafaela #Santafe #Autos #Motos #VTV #Mecanica #Taller #Libreta + los del tema.
- TikTok: el mismo texto acortado (máx. ~150 caracteres + 3 hashtags) en `tiktokData.title` solo para carruseles de fotos.

## Publicar en Metricool
- blogId `7490896`, zona `America/Cordoba`. Proveedores: instagram, facebook, tiktok.
- Horario: `getBestTimeToPostByNetwork` (instagram) para hoy; elegir la mejor hora que esté al menos 40 min en el futuro (si Metricool todavía no tiene datos —todos los valores en 0— usar 20:12 de lunes a viernes y 18:52 sábados y domingos; si ya pasó, la próxima hora con al menos 40 min de margen, nunca después de las 22:30).
- Reel: instagramData.type `REEL` (showReelOnFeed true), facebookData.type `REEL`, video `reel.mp4`, `videoThumbnailUrl` = `cover.jpg`.
  Marcar `isAiGenerated: true` (Instagram) e `isAigc: true` (TikTok) porque la voz es sintética.
- Carrusel/imagen: instagramData.type `POST`, facebookData.type `POST`, media = las láminas en orden; tiktokData con `title` y `autoAddMusic: true`.
- autoPublish true, draft false. Antes de programar, revisar con `getScheduledPosts` que no haya ya un posteo de Libreta ese día (no duplicar).
- Si Metricool rechaza una red (por ejemplo TikTok), volver a programar sin esa red y anotarlo en el log.

## Registro
Agregar una entrada a `content/log.json` y hacer commit + push de todo (spec, imágenes/video, log) a `main` ANTES de programar en Metricool (las URLs tienen que existir). Metricool copia los archivos a su servidor al programar.
Agregar una entrada a `content/log.json` por posteo: `{id, theme, format, hook, scheduled_at, networks, planner_url, notes}`.
No repetir un `theme` usado en los últimos 21 días. Lista de temas en `content/temas.md` (se puede ampliar).

## Resumen semanal (lunes)
Con `getAnalyticsDataByMetrics` (Instagram: alcance, reproducciones, interacciones, guardados, seguidores) de los últimos 7 días:
escribir `content/semanas/<fecha>.md` con qué posteos funcionaron mejor y por qué, y 2–3 ajustes concretos para la semana
(temas, ganchos, horarios). Aplicar esos ajustes en las corridas siguientes.

## Guion para grabar (Maxi a cámara, uno por día)
Maxi sube todos los días un video propio hablando a cámara (tiene buena llegada, ya lo hace). Cada corrida le deja un guion:
- 25–40 segundos hablado (≈70–100 palabras), en primera persona, voseo, como lo diría él: es mandatario del automotor en Rafaela y creador de Libreta.
- **Gancho** en la primera frase (pregunta o situación real: "Ayer vino uno a transferir un auto y…").
- **Desarrollo**: un solo problema y cómo lo resuelve Libreta. Sin inventar casos con nombres, cifras ni testimonios; las anécdotas se plantean como situaciones típicas ("pasa mucho que…").
- **Cierre**: "Entrá gratis a libretaapp.com, el link está en mi perfil".
- Sumar: 2–3 palabras clave para poner en pantalla, lugar sugerido para grabar (taller, auto, oficina), texto para el posteo con hashtags, y hora sugerida (al menos 4 h antes o después del posteo automático).
- Registrar en `content/guiones.json`: `{fecha, tema, gancho, guion, caption}`. Su experiencia como mandatario es el mejor ángulo: transferencias, compra de usados, papeles, VTV.
