# Videos de Maxi a cámara: fondo neón + edición con retención

1. Fondo: `python3 fx.py in.mp4 final.mp4 selfie_segmentation.tflite` (saca la pared, pone el fondo neón con luces que cambian y luz de borde de colores; 478×850 de entrada → 1080×1920; tarda ~1 min por cada 2 s de video).
   El modelo viene del wheel de mediapipe 0.10.14 (pypi), porque storage.googleapis.com y huggingface están bloqueados.
2. Transcripción: whisper-small de sherpa-onnx (github releases k2-fsa/sherpa-onnx, asr-models). `python3 chunks.py audio.wav <dir whisper> chunks.json` da los silencios y frases con tiempo.
3. Edición: en `edit.py`, armar `SEGS` (gancho primero, sacar muletillas y repeticiones) y los textos; genera cortes con zoom, subtítulos con claves en ámbar, notificaciones/etiquetas, barra de progreso y cierre con libretaapp.com.
Revisar siempre fotogramas y volver a transcribir el resultado para chequear que no queden palabras cortadas.
