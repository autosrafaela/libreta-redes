# Voz en off con acento argentino (Piper es_AR "daniela", vía sherpa-onnx).
# Uso: python3 tools/voice.py posts/<id>/spec.json
# Escribe posts/<id>/.voice/sNN.wav y posts/<id>/.voice/durations.json ({"0": 2.31, ...})
import json, os, re, sys, subprocess, tarfile, urllib.request

MODEL_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-es_AR-daniela-high.tar.bz2"
CACHE = os.environ.get("TTS_DIR", os.path.expanduser("~/.cache/libreta-tts"))
M = os.path.join(CACHE, "vits-piper-es_AR-daniela-high") + "/"

# Cómo se escriben las palabras para que suenen como en Argentina
SAY = [
    (r"libretaapp\.com", "Libreta app punto com"), (r"\bWhatsApp\b", "uatsap"), (r"\bservice\b", "sérvis"),
    (r"\bVTV\b", "ve te ve"), (r"\bRTO\b", "erre te o"), (r"\bkm\b", "kilómetros"), (r"\bGNC\b", "ge ene ce"),
    (r"\bCUIT\b", "cuit"), (r"\bok\b", "oquei"), (r"\bapp\b", "app"),
]

def fix(t):
    for a, b in SAY:
        t = re.sub(a, b, t, flags=re.I)
    return t

def ensure_model():
    if os.path.exists(M + "es_AR-daniela-high.onnx"):
        return
    os.makedirs(CACHE, exist_ok=True)
    tb = os.path.join(CACHE, "m.tar.bz2")
    urllib.request.urlretrieve(MODEL_URL, tb)
    with tarfile.open(tb) as t:
        t.extractall(CACHE)
    os.remove(tb)

def main():
    spec_path = sys.argv[1]
    out = os.path.join(os.path.dirname(spec_path), ".voice")
    os.makedirs(out, exist_ok=True)
    spec = json.load(open(spec_path))
    ensure_model()
    import sherpa_onnx, soundfile as sf
    cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=M + "es_AR-daniela-high.onnx", tokens=M + "tokens.txt", data_dir=M + "espeak-ng-data"),
        num_threads=4))
    tts = sherpa_onnx.OfflineTts(cfg)
    speed = float(spec.get("voiceSpeed", 1.05))
    durs = {}
    for i, s in enumerate(spec["scenes"]):
        txt = (s.get("say") or "").strip()
        if not txt:
            continue
        a = tts.generate(fix(txt), sid=0, speed=speed)
        f = os.path.join(out, f"s{i:02d}.wav")
        sf.write(f, a.samples, a.sample_rate)
        durs[str(i)] = round(len(a.samples) / a.sample_rate, 3)
    json.dump(durs, open(os.path.join(out, "durations.json"), "w"))
    print("voz:", durs)

main()
