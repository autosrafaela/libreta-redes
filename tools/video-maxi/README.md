# Videos de Maxi a cámara: fondo neón + edición con retención

1. Fondo: `python3 fx.py in.mp4 final.mp4 selfie_segmentation.tflite` (saca la pared, pone el fondo neón con luces que cambian y luz de borde de colores; 478×850 de entrada → 1080×1920; tarda ~1 min por cada 2 s de video).
   El modelo viene del wheel de mediapipe 0.10.14 (pypi), porque storage.googleapis.com y huggingface están bloqueados.
2. Transcripción: whisper-small de sherpa-onnx (github releases k2-fsa/sherpa-onnx, asr-models). `python3 chunks.py audio.wav <dir whisper> chunks.json` da los silencios y frases con tiempo.
3. Edición: en `edit.py`, armar `SEGS` (gancho primero, sacar muletillas y repeticiones) y los textos; genera cortes con zoom, subtítulos con claves en ámbar, notificaciones/etiquetas, barra de progreso y cierre con libretaapp.com.
Revisar siempre fotogramas y volver a transcribir el resultado para chequear que no queden palabras cortadas.

## Versión con Remotion (varios clips cortos → un video)
Ejemplo: `remotion/` (video del 20/10, "autos que rejuvenecen").
1. Normalizar cada clip a 478×850 30 fps (`ffmpeg -nostdin`, ojo: sin `-nostdin` ffmpeg se come el stdin del while) y pasar `fx.py` a cada uno, **de a 2 en paralelo como máximo** (con 6 se quedó sin memoria y cortó videos sin avisar: chequear duraciones).
2. `sil.py` (silencios por clip) + `plan.py` (textos corregidos, recortes y tiempos por palabra → `plan.json`), cortar y unir con ffmpeg a `public/cut.mp4` (+3 s de cola para la placa final).
3. `remotion/src/Composition.tsx`: cambios de ángulo por corte (zoom/encuadre), golpes de zoom con temblor, efecto "filtro", cuentakilómetros que baja/sube, sellos, chips, confeti, subtítulos palabra por palabra, barra de progreso, sonidos sintetizados (remotion.media está bloqueado) y placa final.
   Render: `npx remotion render MaxiKm out/x.mp4 --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell --concurrency=2`; después recomprimir (crf 25, maxrate 6M).
