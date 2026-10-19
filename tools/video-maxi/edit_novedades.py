import json, subprocess, sys, math, re, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = sys.argv[1]            # carpeta de trabajo
SRC = f"{D}/final.mp4"
W, H, FPS = 1080, 1920, 30
AMBER = (245, 166, 35); WHITE = (255, 255, 255); BLACK = (0, 0, 0)
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FX = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
FR = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
gaps = json.load(open(f"{D}/chunks.json"))["gaps"]
KEY = {"asombro","registrando","negocios","conocida","ciudad","gracias!","gracias","dolor","funcionalidades","opiniones","profesional","turnos","acepte","horario","libretaapp.com","libretaappcom","nuevo"}
SEGS = [
 ("hook", 9.30, 18.60, "Para mi asombro, también se fueron registrando varios negocios de gente muy conocida dentro de la ciudad."),
 ("s1", 3.85, 7.60, "Quiero agradecer a todos aquellos que se fueron registrando en libretaapp.com."),
 ("s1b", 7.60, 9.30, "¡Mil gracias!"),
 ("s2", 18.90, 23.50, "Aparentemente apunté, o acerté, en un dolor bastante importante."),
 ("s3", 25.00, 30.70, "Durante el fin de semana estuve trabajando en libretaapp.com y le agregué algunas funcionalidades"),
 ("s4", 30.77, 47.00, "para que puedan dejar opiniones sobre el profesional y además para que directamente desde la aplicación puedan tomar turnos y que el profesional también los acepte o le proponga un nuevo horario."),
 ("end", 47.40, 51.00, ""),
]
# ---- partir cada segmento sacando silencios largos ----
pieces = []  # (seg, src_s, src_e)
for name, s, e, _ in SEGS:
    cur = s
    for gs, ge in gaps:
        if ge - gs >= 0.2 and gs > cur + 0.05 and ge < e - 0.05:
            pieces.append((name, cur, gs + 0.06)); cur = ge - 0.06
    pieces.append((name, cur, e))
out_t = 0; P = []
for name, s, e in pieces:
    P.append((name, s, e, out_t)); out_t += e - s
TAIL = 0.6
TOTAL = out_t + TAIL
def src2out(name, t):
    for n, s, e, o in P:
        if n == name and s - 1e-6 <= t <= e + 1e-6: return o + (t - s)
    # si cae en un silencio quitado, ir al siguiente pedazo
    for n, s, e, o in P:
        if n == name and s > t: return o
    return None
# ---- tiempos por palabra (proporcional a letras, solo en partes con voz) ----
words = []  # (out_s, out_e, word, seg)
for name, s, e, text in SEGS:
    if not text: continue
    ws = text.split()
    # tiempo con voz del segmento
    segp = [(ps, pe, o) for n, ps, pe, o in P if n == name]
    speech = []
    for ps, pe, o in segp:
        cur = ps
        for gs, ge in gaps:
            if gs >= cur and ge <= pe and ge - gs >= 0.1:
                if gs > cur: speech.append((cur, gs, o + (cur - ps)))
                cur = ge
        if pe > cur: speech.append((cur, pe, o + (cur - ps)))
    tot = sum(b - a for a, b, _ in speech)
    weights = [len(w) + 2 for w in ws]; sw = sum(weights)
    # mapear tiempo acumulado de voz -> tiempo de salida
    def at(x):
        acc = 0
        for a, b, o in speech:
            if x <= acc + (b - a): return o + (x - acc)
            acc += b - a
        a, b, o = speech[-1]; return o + (b - a)
    acc = 0
    for w, wt in zip(ws, weights):
        d = wt / sw * tot
        words.append((at(acc), at(acc + d), w, name)); acc += d
# agrupar de a 1-3 palabras (corte en puntuación)
groups = []; g = []
for wd in words:
    g.append(wd)
    if len(g) == 3 or re.search(r"[.,!?]$", wd[2]) or len(" ".join(x[2] for x in g)) > 13:
        groups.append(g); g = []
if g: groups.append(g)
caps = []
for i, g in enumerate(groups):
    s = g[0][0]; e = groups[i + 1][0][0] if i + 1 < len(groups) and groups[i + 1][0][3] == g[0][3] else g[-1][1] + 0.15
    caps.append((s, e, g))
def wt(word):  # tiempo de salida de la 1ra aparición
    for s, e, w, n in words:
        if re.sub(r"[^\wáéíóúñ%]", "", w.lower()) == word: return s
    return None
T_FUN, T_OP, T_TUR, T_ACE, T_HOR = wt("funcionalidades"), wt("opiniones"), wt("turnos"), wt("acepte"), wt("horario")
seg_out = {}
for n, s, e, o in P:
    a, b = seg_out.get(n, (o, o)); seg_out[n] = (min(a, o), max(b, o + e - s))
print("total", round(TOTAL, 2), {k: (round(a, 2), round(b, 2)) for k, (a, b) in seg_out.items()})
# ---- cortar el video ----
fc = []; ins = []
for i, (n, s, e, o) in enumerate(P):
    fc.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={max(0,e-s-0.015)}:d=0.015[a{i}]")
cat = "".join(f"[v{i}][a{i}]" for i in range(len(P))) + f"concat=n={len(P)}:v=1:a=1[cv][ca]"
fc.append(cat); fc.append(f"[cv]fps={FPS},tpad=stop_mode=clone:stop_duration={TAIL}[vv];[ca]apad=pad_dur={TAIL}[aa]")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", SRC, "-filter_complex", ";".join(fc), "-map", "[vv]", "-map", "[aa]",
                "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "pcm_s16le", f"{D}/cut.mov"], check=True)
# ---- gráficos ----
def font(p, s): return ImageFont.truetype(p, s)
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def text_rich(draw, xy, tokens, f, stroke=8, anchor_center=True):
    # tokens: [(texto, color)]
    widths = [draw.textlength(t, font=f) for t, _ in tokens]; sp = draw.textlength(" ", font=f)
    total = sum(widths) + sp * (len(tokens) - 1)
    x = xy[0] - total / 2 if anchor_center else xy[0]
    for (t, c), w in zip(tokens, widths):
        draw.text((x, xy[1]), t, font=f, fill=c, stroke_width=stroke, stroke_fill=BLACK); x += w + sp
    return total
def caption_img(g, scale):
    im = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    toks = []
    for _, _, w, _ in g:
        k = re.sub(r"[^\wáéíóúñ%¡!]", "", w.lower())
        toks.append((w.upper().rstrip(",."), AMBER if k in KEY or k.strip("¡!") in KEY else WHITE))
    size = 86
    while size > 50:
        f = font(FB, size); tw = sum(d.textlength(t, font=f) for t, _ in toks) + d.textlength(" ", font=f) * (len(toks) - 1)
        if tw <= 940: break
        size -= 4
    f = font(FB, int(size * scale))
    text_rich(d, (W / 2, 130 - f.size * 0.6), toks, f, stroke=int(9 * scale))
    return im
logo = Image.open("/home/claude/libreta-redes/assets/logo.png").convert("RGBA")
def rounded(w, h, r, fill):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill); return im
def notif(msg):
    c = rounded(900, 150, 34, (28, 28, 36, 235)); d = ImageDraw.Draw(c)
    lg = logo.resize((78, 78)); c.alpha_composite(lg, (28, 36))
    d.text((128, 30), "LIBRETA  ·  ahora", font=font(FR, 28), fill=(170, 170, 185))
    d.text((128, 70), msg, font=font(FX, 40), fill=WHITE)
    return c
dirc = Image.open("/home/claude/libreta-redes/assets/app/directorio.png").convert("RGBA").crop((16, 484, 374, 584))
dirc = dirc.resize((900, int(900 * dirc.height / dirc.width)), Image.LANCZOS)
OPIN = rounded(dirc.width, dirc.height, 30, (255, 255, 255, 255)); OPIN.putalpha(OPIN.split()[3]); _t = Image.new("RGBA", dirc.size); _t.paste(dirc, (0, 0), OPIN); OPIN = _t
NOTIFS = [(T_ACE, notif("El taller aceptó tu turno: jueves 10:00")), (T_HOR, notif("Te propusieron otro horario: viernes 9:30"))]
def chip(text, color, icon):
    f = font(FB, 54); w = int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(text, font=f)) + 150
    c = rounded(w, 110, 55, (18, 18, 24, 235)); d = ImageDraw.Draw(c)
    d.ellipse((24, 22, 90, 88), fill=color)
    if icon == "x": d.line((42, 40, 72, 70), fill=WHITE, width=9); d.line((72, 40, 42, 70), fill=WHITE, width=9)
    else: d.line((40, 56, 52, 70), fill=WHITE, width=9); d.line((52, 70, 76, 42), fill=WHITE, width=9)
    d.text((112, 55), text, font=f, fill=WHITE, anchor="lm"); return c
CHIP0 = chip("2 funciones nuevas", (40, 170, 90), "v")
CHIP1 = chip("NUEVO: opiniones", (245, 166, 35), "v"); CHIP2 = chip("NUEVO: turnos", (245, 166, 35), "v")
def hook_img():
    im = Image.new("RGBA", (W, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f1 = font(FB, 88); f2 = font(FB, 104)
    d.text((W / 2, 120), "NO LO PODÍA CREER:", font=f1, fill=WHITE, anchor="mm", stroke_width=10, stroke_fill=BLACK)
    d.text((W / 2, 245), "NEGOCIOS DE", font=f2, fill=AMBER, anchor="mm", stroke_width=10, stroke_fill=BLACK)
    d.text((W / 2, 360), "RAFAELA EN LIBRETA", font=font(FB, 92), fill=AMBER, anchor="mm", stroke_width=10, stroke_fill=BLACK)
    return im
HOOK = hook_img()
def end_card():
    im = Image.new("RGBA", (W, H), (8, 8, 14, 150)); d = ImageDraw.Draw(im)
    lg = logo.resize((200, 200)); im.alpha_composite(lg, (W // 2 - 100, 560))
    d.text((W / 2, 880), "PROBALA", font=font(FB, 110), fill=WHITE, anchor="mm")
    d.text((W / 2, 1000), "GRATIS", font=font(FB, 130), fill=AMBER, anchor="mm")
    d.text((W / 2, 1160), "libretaapp.com", font=font(FB, 84), fill=WHITE, anchor="mm")
    pill = rounded(560, 90, 45, (40, 170, 90, 255)); ImageDraw.Draw(pill).text((280, 45), "Link en mi perfil", font=font(FX, 40), fill=WHITE, anchor="mm")
    im.alpha_composite(pill, (W // 2 - 280, 1250)); return im
END = end_card()
def paste(base, im, x, y, alpha=1.0, scale=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
        x += (im.width / scale - im.width) / 2 if False else 0
    if alpha < 1: a = im.split()[3].point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(x), int(y)))
# zoom por pedazo (corte con salto)
zooms = []
segnames = [n for n, *_ in SEGS]
for i, (n, s, e, o) in enumerate(P):
    base = {"hook": 1.14, "s1": 1.0, "s1b": 1.2, "s2": 1.08, "s3": 1.0, "s4": 1.04, "end": 1.0}[n]
    zooms.append((o, o + e - s, base + (0.05 if i % 2 else 0)))
def zoom_at(t):
    for a, b, z in zooms:
        if a <= t < b: return z + 0.03 * (t - a) / max(0.5, b - a)
    return 1.0
dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", f"{D}/cut.mov", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", f"{D}/cut.mov", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", f"{D}/editado.mp4"], stdin=subprocess.PIPE)
fi = 0; end_s = seg_out["end"][0]
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    t = fi / FPS
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    z = zoom_at(t)
    if z > 1.001:
        cx, cy = W / 2, 760
        M = np.float32([[z, 0, cx - z * cx], [0, z, cy - z * cy]])
        fr = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if t >= end_s:
        k = ease((t - end_s) / 0.35)
        fr = cv2.GaussianBlur(fr, (0, 0), 1 + 18 * k)
    img = Image.fromarray(np.ascontiguousarray(fr)).convert("RGBA")
    # barra de progreso
    ImageDraw.Draw(img).rectangle((0, 0, int(W * t / TOTAL), 12), fill=AMBER + (255,))
    if t < end_s:
        # gancho
        hs, he = seg_out["hook"]; he = min(he, 3.2)
        if t < he + 0.6:
            k = ease(t / 0.25); a = 1 if t < he + 0.3 else max(0, 1 - (t - he - 0.3) / 0.3)
            sc = 0.85 + 0.15 * k
            hi = HOOK.resize((int(W * sc), int(420 * sc)))
            paste(img, hi, (W - hi.width) / 2, 70 + (420 - hi.height) / 2, alpha=a * k)
        s4a, s4b = seg_out["s4"]
        for tn, im, y in [(T_OP, CHIP1, 230), (T_TUR, CHIP2, 360)]:
            if tn is not None and tn - 0.1 <= t < s4b + 0.2:
                k = ease((t - tn + 0.1) / 0.3)
                paste(img, im, (W - im.width) / 2, y + (1 - k) * 40, alpha=k)
        if T_OP is not None and T_OP <= t < (T_TUR or s4b):
            k = ease((t - T_OP) / 0.35); paste(img, OPIN, 90 + (1 - k) * 700, 1400, alpha=min(1, 1.5 * k))
        for j, (tn, im) in enumerate(NOTIFS):
            if tn is not None and tn - 0.1 <= t < s4b + 0.2:
                k = ease((t - tn + 0.1) / 0.35)
                paste(img, im, 90 + (1 - k) * 700, 1400 + j * 170, alpha=min(1, k * 1.5))
        if T_FUN is not None and T_FUN - 0.1 <= t < s4a:
            k = ease((t - T_FUN + 0.1) / 0.3); paste(img, CHIP0, (W - CHIP0.width) / 2, 300 + (1 - k) * 40, alpha=k)
        # subtítulos
        for s, e, g in caps:
            if s <= t < e:
                k = ease((t - s) / 0.12); ci = caption_img(g, 0.9 + 0.1 * k)
                paste(img, ci, 0, 1120)
                break
    else:
        k = ease((t - end_s) / 0.4)
        paste(img, END, 0, (1 - k) * 60, alpha=k)
    enc.stdin.write(np.asarray(img.convert("RGB")).tobytes()); fi += 1
enc.stdin.close(); enc.wait()
print("frames", fi, "dur", fi / FPS)
json.dump({"caps": [(round(s, 2), round(e, 2), " ".join(w[2] for w in g)) for s, e, g in caps]}, open(f"{D}/caps.json", "w"), ensure_ascii=False, indent=0)
