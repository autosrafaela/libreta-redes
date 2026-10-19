import sys, subprocess, numpy as np, cv2, math
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision

SRC, OUT, MODEL = sys.argv[1], sys.argv[2], sys.argv[3]
LIMIT = int(sys.argv[4]) if len(sys.argv) > 4 else 0
IW, IH = 478, 850
W, H, FPS = 1080, 1920, 30

seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
    base_options=mpt.BaseOptions(model_asset_path=MODEL),
    running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True))

# ---------- fondo gamer (capas en escala de grises, se colorean por frame) ----------
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def glow_line(x0, y0, x1, y1, width, blur):
    m = np.zeros((H, W), np.float32)
    cv2.line(m, (x0, y0), (x1, y1), 1.0, width, cv2.LINE_AA)
    core = m.copy()
    g = cv2.GaussianBlur(m, (0, 0), blur)
    return np.clip(core * 1.0 + g * 2.2, 0, 1.6)
# capa A (magenta/violeta): tubos verticales izquierda + hexágonos
A = np.zeros((H, W), np.float32)
A += glow_line(90, 150, 90, 1500, 10, 28)
A += glow_line(200, 300, 200, 1200, 6, 22) * 0.6
# hexágonos a la derecha arriba
def hexagon(cx, cy, r):
    pts = np.array([[cx + r*math.cos(math.pi/3*k + math.pi/6), cy + r*math.sin(math.pi/3*k + math.pi/6)] for k in range(6)], np.int32)
    m = np.zeros((H, W), np.float32); cv2.polylines(m, [pts], True, 1.0, 7, cv2.LINE_AA)
    return np.clip(m + cv2.GaussianBlur(m, (0, 0), 18) * 2.0, 0, 1.5)
HEX = [(800, 380), (930, 455), (800, 530), (930, 605), (1060, 380)]
B = np.zeros((H, W), np.float32)
B += glow_line(990, 120, 990, 1550, 10, 28)
B += glow_line(880, 900, 880, 1500, 6, 22) * 0.6
# tira LED horizontal (escritorio) abajo
C = glow_line(0, 1580, W, 1580, 8, 30)
# monitor/pantalla difusa detrás (rectángulo con brillo)
mon = np.zeros((H, W), np.float32); cv2.rectangle(mon, (260, 700), (820, 1050), 1.0, -1)
mon = cv2.GaussianBlur(mon, (0, 0), 60) * 0.55
# bokeh
bok = np.zeros((H, W), np.float32)
for _ in range(38):
    cv2.circle(bok, (int(rng.uniform(0, W)), int(rng.uniform(0, H))), int(rng.uniform(10, 34)), float(rng.uniform(0.15, 0.45)), -1, cv2.LINE_AA)
bok = cv2.GaussianBlur(bok, (0, 0), 6)
# base: degradé oscuro azul/violeta + viñeta
base = np.zeros((H, W, 3), np.float32)
t = yy / H
base[..., 0] = 0.10 + 0.08 * (1 - t)  # B (BGR)
base[..., 1] = 0.03
base[..., 2] = 0.06 + 0.05 * t
vig = 1 - 0.55 * (((xx - W/2) / (W*0.75))**2 + ((yy - H*0.45) / (H*0.7))**2)
base *= np.clip(vig, 0.3, 1)[..., None]
# grilla tenue en perspectiva en el piso
grid = np.zeros((H, W), np.float32)
for i in range(-10, 11):
    cv2.line(grid, (W//2 + i*40, 1450), (W//2 + i*260, H), 0.35, 2, cv2.LINE_AA)
for j, y in enumerate([1480, 1530, 1600, 1690, 1800, 1920]):
    cv2.line(grid, (0, y), (W, y), 0.3, 2, cv2.LINE_AA)
grid = cv2.GaussianBlur(grid, (0, 0), 1.5)

def hsv(h, s=1, v=1):
    c = cv2.cvtColor(np.uint8([[[int(h % 180), int(s*255), int(v*255)]]]), cv2.COLOR_HSV2BGR)[0, 0]
    return c.astype(np.float32) / 255

def background(i):
    tt = i / FPS
    hA = 150 + 18 * math.sin(tt * 0.35)          # magenta ↔ violeta
    hB = 92 + 14 * math.sin(tt * 0.3 + 1.0)      # cian ↔ azul
    hC = (tt * 22) % 180                          # tira RGB que recorre colores
    pulse = 0.85 + 0.15 * math.sin(tt * 2.2)
    cA, cB, cC = hsv(hA), hsv(hB), hsv(hC)
    hexs = np.zeros((H, W), np.float32)
    for k, (cx, cy) in enumerate(HEX):
        on = 0.5 + 0.5 * math.sin(tt * 1.4 + k * 1.3)
        hexs += hexagon(cx, cy, 70) * (0.25 + 0.75 * on) if i == -1 else 0  # placeholder (pre-render abajo)
    img = base.copy()
    img += A[..., None] * cA * 0.9 * pulse
    img += B[..., None] * cB * 0.9 * (1.9 - pulse)
    img += C[..., None] * cC * 0.9
    img += HEXL @ np.array([0.5 + 0.5 * math.sin(tt * 1.4 + k * 1.3) for k in range(len(HEX))], np.float32).reshape(-1, 1) if False else 0
    for k in range(len(HEX)):
        on = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(tt * 1.4 + k * 1.3))
        img += HEXL[k][..., None] * cB * on * 0.8
    img += mon[..., None] * (cA * 0.5 + cB * 0.5)
    img += bok[..., None] * (cA * 0.6 + cC * 0.4)
    img += grid[..., None] * cC * 0.6
    return img, cA, cB, cC
HEXL = [hexagon(cx, cy, 70) for cx, cy in HEX]
BG_BLUR = 3

def gf(I, p, r, eps):
    k = (2*r+1, 2*r+1)
    mI = cv2.boxFilter(I, -1, k); mp_ = cv2.boxFilter(p, -1, k)
    cIp = cv2.boxFilter(I*p, -1, k) - mI*mp_; vI = cv2.boxFilter(I*I, -1, k) - mI*mI
    a = cIp / (vI + eps); b = mp_ - a*mI
    return cv2.boxFilter(a, -1, k) * I + cv2.boxFilter(b, -1, k)
# ---------- video ----------
dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", SRC, "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", SRC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
prev = None; i = 0
while True:
    buf = dec.stdout.read(IW * IH * 3)
    if len(buf) < IW * IH * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(IH, IW, 3)
    rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
    res = seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)), int(i * 1000 / FPS))
    m = res.confidence_masks[0].numpy_view().astype(np.float32)
    if m.ndim == 3: m = m[..., 0]
    m = cv2.resize(m, (IW, IH))
    prev = m if prev is None else 0.55 * m + 0.45 * prev
    m = prev
    # escalar a 1080x1920
    big = cv2.resize(fr, (W, H), interpolation=cv2.INTER_CUBIC)
    bl = cv2.GaussianBlur(big, (0, 0), 1.2)
    big = cv2.addWeighted(big, 1.5, bl, -0.5, 0)  # nitidez
    mb = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    mb = gf(cv2.cvtColor(big, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255, mb, 10, 1e-3)
    mb = np.clip((mb - 0.25) / 0.5, 0, 1)
    mb = cv2.GaussianBlur(mb, (0, 0), 1.0)
    # sacar el halo blanco de la pared en el borde (pelo)
    inner = cv2.erode(mb, np.ones((31, 31), np.uint8))
    band = np.clip(mb - inner, 0, 1)
    band = cv2.GaussianBlur(band, (0, 0), 4) > 0.02
    f = big.astype(np.float32) / 255
    mn = f.min(axis=2); mx = f.max(axis=2)
    white = np.clip((mn - 0.62) / 0.15, 0, 1) * np.clip(1 - (mx - mn) / 0.18, 0, 1)
    mb = mb * (1 - 0.95 * white * band)
    mb = cv2.GaussianBlur(mb, (0, 0), 0.8)
    bg, cA, cB, cC = background(i)
    # persona: un poco más de contraste y tono frío
    p = big.astype(np.float32) / 255
    p = np.clip((p - 0.5) * 1.12 + 0.5, 0, 1)
    p = p * np.array([1.04, 0.98, 0.97], np.float32)
    # luz ambiente del fondo sobre la persona (leve)
    p = p * 0.92 + p * (cA * 0.5 + cB * 0.5) * 0.12
    # luz de borde (rim): magenta izquierda, cian derecha
    edge = np.clip(mb - cv2.erode(mb, np.ones((15, 15), np.uint8)), 0, 1)
    edge = cv2.GaussianBlur(edge, (0, 0), 7)
    side = (xx / W)[..., None]
    rim = edge[..., None] * ((1 - side) * cA + side * cB) * 1.1
    p = np.clip(p + rim, 0, 1)
    # halo detrás de la persona
    halo = cv2.GaussianBlur(mb, (0, 0), 40)[..., None] * (cA * 0.5 + cB * 0.5) * 0.25
    bg = bg + halo
    out = p * mb[..., None] + np.clip(bg, 0, 1) * (1 - mb[..., None])
    enc.stdin.write((np.clip(out, 0, 1) * 255).astype(np.uint8).tobytes())
    i += 1
    if LIMIT and i >= LIMIT: break
    if i % 150 == 0: print(i, flush=True)
enc.stdin.close(); enc.wait(); dec.kill()
print("frames", i)
