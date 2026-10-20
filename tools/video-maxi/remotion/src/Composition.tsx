import React from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  Composition,
  Easing,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  random,
} from "remotion";
import { Audio, Video } from "@remotion/media";
import plan from "./plan.json";

const FPS = 30;
const AMBER = "#F5A623";
const GREEN = "#2BB673";
const RED = "#FF4D4F";
const END_DUR = 2.6; // s de placa final
const TOTAL = plan.total + END_DUR;

type Props = Record<string, unknown>;
const calculateMetadata: CalculateMetadataFunction<Props> = () => ({
  durationInFrames: Math.round(TOTAL * FPS),
});

export const MyComposition = () => (
  <Composition
    id="MaxiKm"
    component={MaxiKm}
    durationInFrames={Math.round(TOTAL * FPS)}
    fps={FPS}
    width={1080}
    height={1920}
    calculateMetadata={calculateMetadata}
  />
);

// ---------- tiempos ----------
type Piece = { clip: number; s: number; e: number; o: number };
const P = plan.pieces as Piece[];
const clipStart = (c: number) => P.find((p) => p.clip === c)!.o;
const clipEnd = (c: number) => {
  const ps = P.filter((p) => p.clip === c);
  const l = ps[ps.length - 1];
  return l.o + (l.e - l.s);
};
const W = plan.words as { w: string; s: number; e: number; clip: number }[];
const norm = (w: string) => w.toLowerCase().replace(/[^\wáéíóúñ.]/g, "").replace(/\.$/, "");
const wordAt = (needle: string, clip?: number) =>
  W.find((x) => norm(x.w) === needle && (clip === undefined || x.clip === clip))!.s;
const F = (t: number) => Math.round(t * FPS);
const clampOpts = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// ---------- fuentes ----------
const FontFaces = () => (
  <style>{`
@font-face{font-family:Archivo;font-weight:900;src:url(${staticFile("archivo-latin-900-normal.woff2")})}
@font-face{font-family:Archivo;font-weight:800;src:url(${staticFile("archivo-latin-800-normal.woff2")})}
@font-face{font-family:Barlow;font-weight:700;src:url(${staticFile("barlow-latin-700-normal.woff2")})}
@font-face{font-family:Mono;font-weight:800;src:url(${staticFile("jetbrains-mono-latin-800-normal.woff2")})}
`}</style>
);

// ---------- cámara: zoom y cambios de ángulo por corte ----------
const ANGLES = [
  { z: 1.3, x: 0, y: 60, r: 0 }, // gancho: primer plano
  { z: 1.0, x: 0, y: 0, r: 0 }, // plano general
  { z: 1.14, x: -70, y: 30, r: -1.2 }, // medio, hacia la izquierda
  { z: 1.24, x: 60, y: 70, r: 1.0 }, // cerrado, hacia la derecha
  { z: 1.07, x: 30, y: -20, r: 0 },
];
const SEQ = [0, 3, 2, 1, 4, 3, 1, 2, 0, 4, 3, 1, 2, 0, 1];

const camera = (t: number) => {
  const i = P.findIndex((p) => t >= p.o && t < p.o + (p.e - p.s));
  const idx = i < 0 ? P.length - 1 : i;
  const p = P[idx];
  const a = ANGLES[SEQ[idx % SEQ.length]];
  const prog = (t - p.o) / (p.e - p.s);
  return { ...a, z: a.z + 0.05 * Math.min(1, Math.max(0, prog)), idx };
};

// golpes de zoom (punch) en momentos clave
const punches = () => [
  { t: wordAt("vecina", 2), amp: 0.16, shake: 1 },
  { t: wordAt("libreta", 5), amp: 0.2, shake: 1 },
  { t: wordAt("gratis", 10), amp: 0.18, shake: 0.6 },
];

const Camera: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const c = camera(t);
  let extra = 0;
  let sx = 0;
  let sy = 0;
  for (const p of punches()) {
    const d = t - p.t;
    if (d >= 0 && d < 0.6) {
      extra += p.amp * Math.exp(-d * 7) * Math.min(1, d * 25);
      const k = Math.exp(-d * 9) * 28 * p.shake;
      sx += (random(`x${frame}`) - 0.5) * k;
      sy += (random(`y${frame}`) - 0.5) * k;
    }
  }
  return (
    <AbsoluteFill
      style={{
        transformOrigin: "540px 820px",
        scale: String(c.z + extra),
        translate: `${c.x + sx}px ${c.y + sy}px`,
        rotate: `${c.r}deg`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

// ---------- efecto "filtro" (chiste de la vecina) ----------
const filterWindow = () => [clipStart(3), clipEnd(3)];

const Base = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const [fs, fe] = filterWindow();
  const on = interpolate(t, [fs, fs + 0.25, fe - 0.15, fe], [0, 1, 1, 0], clampOpts);
  const endK = interpolate(t, [plan.total - 0.05, plan.total + 0.4], [0, 1], clampOpts);
  return (
    <AbsoluteFill
      style={{
        filter: `saturate(${1 + 0.6 * on}) brightness(${1 + 0.14 * on}) contrast(${1 - 0.12 * on}) blur(${1.6 * on + 18 * endK}px) hue-rotate(${-12 * on}deg)`,
      }}
    >
      <Camera>
        <Video src={staticFile("cut.mp4")} style={{ width: "100%", height: "100%" }} />
      </Camera>
    </AbsoluteFill>
  );
};

const FilterFx = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const [fs, fe] = filterWindow();
  if (t < fs || t > fe) return null;
  const on = interpolate(t, [fs, fs + 0.25, fe - 0.15, fe], [0, 1, 1, 0], clampOpts);
  const sparkles = Array.from({ length: 22 }, (_, i) => {
    const x = random(`sx${i}`) * 1080;
    const y = 250 + random(`sy${i}`) * 1100;
    const ph = random(`sp${i}`) * 6;
    const tw = Math.max(0, Math.sin(t * 7 + ph));
    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: x,
          top: y,
          width: 30,
          height: 30,
          opacity: tw * on,
          scale: String(0.5 + tw),
          background: "radial-gradient(circle, #fff 0 18%, rgba(255,200,240,.7) 30%, transparent 65%)",
          borderRadius: "50%",
        }}
      />
    );
  });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, rgba(255,150,210,.0) 30%, rgba(255,120,200,.35) 100%)", opacity: on }} />
      {sparkles}
      <div
        style={{
          position: "absolute",
          top: 150,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          opacity: on,
        }}
      >
        <div style={{ font: "800 54px Archivo", color: "#fff", background: "rgba(255,90,180,.85)", padding: "16px 34px", borderRadius: 60, letterSpacing: 2 }}>
          ✨ FILTRO: ON
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------- piezas gráficas ----------
const pop = (frame: number, start: number, fps: number) =>
  spring({ frame: frame - start, fps, config: { damping: 12, stiffness: 180 } });

const Headline = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const end = F(clipEnd(1)) + 4;
  const k = pop(frame, 0, fps);
  const out = interpolate(frame, [end - 4, end + 2], [1, 0], clampOpts);
  return (
    <div style={{ position: "absolute", top: 170, width: "100%", textAlign: "center", opacity: out, scale: String(0.6 + 0.4 * k) }}>
      <div style={{ font: "900 92px/1 Archivo", color: "#fff", WebkitTextStroke: "0px", textShadow: "0 6px 0 #000, 0 0 30px rgba(0,0,0,.6)" }}>HAY AUTOS QUE</div>
      <div style={{ font: "900 112px/1.05 Archivo", color: AMBER, textShadow: "0 7px 0 #000, 0 0 40px rgba(245,166,35,.5)", rotate: "-3deg" }}>
        REJUVENECEN
      </div>
    </div>
  );
};

const Chip: React.FC<{ from: number; to: number; top: number; bg?: string; children: React.ReactNode; size?: number }> = ({
  from,
  to,
  top,
  bg = "rgba(14,14,20,.88)",
  children,
  size = 54,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < from - 1 || frame > to + 8) return null;
  const k = pop(frame, from, fps);
  const out = interpolate(frame, [to, to + 6], [1, 0], clampOpts);
  return (
    <div style={{ position: "absolute", top, width: "100%", display: "flex", justifyContent: "center", opacity: Math.min(1, k * 1.4) * out }}>
      <div
        style={{
          font: `900 ${size}px/1.1 Archivo`,
          color: "#fff",
          background: bg,
          padding: "20px 38px",
          borderRadius: 28,
          border: `3px solid ${AMBER}`,
          boxShadow: "0 20px 50px rgba(0,0,0,.5)",
          scale: String(0.5 + 0.5 * k),
          translate: `0px ${(1 - k) * 40}px`,
          textAlign: "center",
        }}
      >
        {children}
      </div>
    </div>
  );
};

const fmt = (n: number) => Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
const Odometer: React.FC<{ from: number; to: number; a: number; b: number; up?: boolean; label: string; top?: number }> = ({
  from,
  to,
  a,
  b,
  up,
  label,
  top = 1600,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < from - 1 || frame > to + 8) return null;
  const k = pop(frame, from, fps);
  const out = interpolate(frame, [to, to + 6], [1, 0], clampOpts);
  const v = interpolate(frame, [from + 6, to - 10], [a, b], { ...clampOpts, easing: Easing.inOut(Easing.cubic) });
  const col = up ? GREEN : RED;
  const shake = !up && frame < to - 10 ? (random(`o${frame}`) - 0.5) * 6 : 0;
  return (
    <div style={{ position: "absolute", top, width: "100%", display: "flex", justifyContent: "center", opacity: out }}>
      <div
        style={{
          background: "linear-gradient(#15161c,#0b0b10)",
          border: `4px solid ${col}`,
          borderRadius: 34,
          padding: "22px 40px 26px",
          boxShadow: `0 0 60px ${col}66, 0 20px 50px rgba(0,0,0,.6)`,
          scale: String(0.6 + 0.4 * k),
          translate: `${shake}px ${(1 - k) * 60}px`,
          textAlign: "center",
        }}
      >
        <div style={{ font: "800 34px Barlow", color: col, letterSpacing: 3 }}>{label}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 22, marginTop: 6 }}>
          <span style={{ font: "800 104px Mono", color: "#fff", letterSpacing: 4 }}>{fmt(v)}</span>
          <span style={{ font: "800 44px Barlow", color: "#aaa" }}>km</span>
          <span style={{ font: "900 92px Archivo", color: col }}>{up ? "↑" : "↓"}</span>
        </div>
      </div>
    </div>
  );
};

const Stamp: React.FC<{ from: number; to: number; children: React.ReactNode; color?: string; top?: number }> = ({ from, to, children, color = AMBER, top = 230 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < from - 1 || frame > to + 8) return null;
  const k = spring({ frame: frame - from, fps, config: { damping: 9, stiffness: 220 } });
  const out = interpolate(frame, [to, to + 6], [1, 0], clampOpts);
  return (
    <div style={{ position: "absolute", top, width: "100%", display: "flex", justifyContent: "center", opacity: out }}>
      <div
        style={{
          font: "900 120px/1 Archivo",
          color,
          border: `10px solid ${color}`,
          borderRadius: 30,
          padding: "18px 40px",
          background: "rgba(10,10,14,.75)",
          rotate: "-6deg",
          scale: String(interpolate(k, [0, 1], [2.6, 1])),
          opacity: Math.min(1, k * 2),
          textShadow: "0 6px 0 #000",
          display: "flex",
          alignItems: "center",
          gap: 26,
        }}
      >
        {children}
      </div>
    </div>
  );
};

const EmojiPop: React.FC<{ from: number; to: number; emoji: string }> = ({ from, to, emoji }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < from - 1 || frame > to + 6) return null;
  const k = spring({ frame: frame - from, fps, config: { damping: 8, stiffness: 200 } });
  const out = interpolate(frame, [to, to + 6], [1, 0], clampOpts);
  return (
    <div style={{ position: "absolute", top: 260, right: 90, fontSize: 210, opacity: out, scale: String(k), rotate: `${12 - 12 * k}deg` }}>{emoji}</div>
  );
};

const Flash: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [at - 1, at, at + 4], [0, 0.28, 0], clampOpts);
  if (o <= 0) return null;
  return <AbsoluteFill style={{ background: "#fff", opacity: o }} />;
};

const Confetti: React.FC<{ from: number }> = ({ from }) => {
  const frame = useCurrentFrame();
  const d = (frame - from) / FPS;
  if (d < 0 || d > 1.8) return null;
  return (
    <AbsoluteFill>
      {Array.from({ length: 70 }, (_, i) => {
        const ang = random(`ca${i}`) * Math.PI * 2;
        const sp = 600 + random(`cs${i}`) * 900;
        const x = 540 + Math.cos(ang) * sp * d;
        const y = 760 + Math.sin(ang) * sp * d + 900 * d * d;
        const colors = [AMBER, GREEN, "#fff", "#ff5fb0", "#3fa9ff"];
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: 18,
              height: 30,
              background: colors[i % colors.length],
              rotate: `${d * 720 * (random(`cr${i}`) - 0.5)}deg`,
              opacity: interpolate(d, [1.2, 1.8], [1, 0], clampOpts),
              borderRadius: 4,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ---------- subtítulos ----------
const KEY = new Set(["rejuvenecen", "vecina", "filtros", "wachiturro", "15", "años", "kilómetros", "bajar", "libreta", "taller", "adelante", "borrar", "historial", "tenelo", "gratis", "libretaapp.com", "comprar", "vender"]);
type Wd = (typeof W)[number];
const groups: Wd[][] = [];
{
  let g: Wd[] = [];
  for (const w of W) {
    if (w.clip === 1) continue; // el gancho ya está como título
    if (g.length && g[0].clip !== w.clip) {
      groups.push(g);
      g = [];
    }
    g.push(w);
    const txt = g.map((x) => x.w).join(" ");
    if (g.length === 3 || /[.,!?]$/.test(w.w) || txt.length > 12) {
      groups.push(g);
      g = [];
    }
  }
  if (g.length) groups.push(g);
}

const Captions = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  if (t > plan.total) return null;
  const gi = groups.findIndex((g, i) => {
    const nxt = groups[i + 1];
    const end = nxt && nxt[0].clip === g[0].clip ? nxt[0].s : g[g.length - 1].e + 0.2;
    return t >= g[0].s - 0.03 && t < end;
  });
  if (gi < 0) return null;
  const g = groups[gi];
  const k = interpolate(t, [g[0].s - 0.03, g[0].s + 0.1], [0.8, 1], { ...clampOpts, easing: Easing.out(Easing.back(2)) });
  return (
    <div style={{ position: "absolute", top: 1370, width: "100%", display: "flex", justifyContent: "center", flexWrap: "wrap", gap: "0 0px", padding: "0 40px", scale: String(k) }}>
      {g.map((w, i) => {
        const active = t >= w.s && t < w.e + 0.05;
        const key = KEY.has(norm(w.w).replace(/[¡!]/g, ""));
        return (
          <span
            key={i}
            style={{
              font: "900 86px/1.12 Archivo",
              margin: "0 17px",
              color: key ? AMBER : "#fff",
              WebkitTextStroke: "14px #000",
              paintOrder: "stroke fill",
              textShadow: "0 8px 18px rgba(0,0,0,.55)",
              scale: active ? "1.08" : "1",
              display: "inline-block",
            }}
          >
            {w.w.toUpperCase().replace(/[,.]$/, "")}
          </span>
        );
      })}
    </div>
  );
};

const Progress = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return <div style={{ position: "absolute", top: 0, left: 0, height: 14, width: `${(frame / durationInFrames) * 100}%`, background: AMBER, boxShadow: `0 0 18px ${AMBER}` }} />;
};

const UrlBar: React.FC<{ from: number; to: number }> = ({ from, to }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < from - 1 || frame > to + 6) return null;
  const k = pop(frame, from, fps);
  const url = "libretaapp.com";
  const n = Math.round(interpolate(frame, [from + 4, from + 4 + url.length * 1.6], [0, url.length], clampOpts));
  const out = interpolate(frame, [to, to + 6], [1, 0], clampOpts);
  return (
    <div style={{ position: "absolute", top: 1530, width: "100%", display: "flex", justifyContent: "center", opacity: out }}>
      <div style={{ background: "#fff", borderRadius: 60, padding: "22px 44px", display: "flex", alignItems: "center", gap: 20, scale: String(0.6 + 0.4 * k), boxShadow: `0 0 50px ${AMBER}88` }}>
        <Img src={staticFile("logo.png")} style={{ width: 70, height: 70, borderRadius: 16 }} />
        <span style={{ font: "800 66px Barlow", color: "#111" }}>
          {url.slice(0, n)}
          <span style={{ opacity: frame % 16 < 8 ? 1 : 0, color: AMBER }}>|</span>
        </span>
      </div>
    </div>
  );
};

const EndCard = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = (d: number) => spring({ frame: frame - d, fps, config: { damping: 12 } });
  return (
    <AbsoluteFill style={{ background: "rgba(8,8,14,.6)", alignItems: "center", justifyContent: "center", opacity: interpolate(frame, [0, 8], [0, 1], clampOpts) }}>
      <Img src={staticFile("logo.png")} style={{ width: 230, height: 230, borderRadius: 50, scale: String(k(0)), boxShadow: `0 0 80px ${AMBER}aa` }} />
      <div style={{ font: "900 120px/1 Archivo", color: "#fff", marginTop: 50, scale: String(k(4)) }}>PROBALA</div>
      <div style={{ font: "900 150px/1 Archivo", color: AMBER, scale: String(k(8)), rotate: "-3deg" }}>GRATIS</div>
      <div style={{ font: "800 86px Barlow", color: "#fff", marginTop: 40, scale: String(k(12)) }}>libretaapp.com</div>
      <div style={{ font: "800 44px Barlow", color: "#fff", background: GREEN, padding: "16px 40px", borderRadius: 50, marginTop: 30, scale: String(k(16)) }}>Link en mi perfil</div>
    </AbsoluteFill>
  );
};

const Sfx: React.FC<{ at: number; src: string; vol?: number }> = ({ at, src, vol = 0.5 }) => (
  <Sequence from={Math.max(0, at)} durationInFrames={40} layout="none">
    <Audio src={staticFile(src)} volume={vol} />
  </Sequence>
);

export const MaxiKm: React.FC<Props> = () => {
  const c = (n: number) => F(clipStart(n));
  const ce = (n: number) => F(clipEnd(n));
  const p4b = F(P.filter((p) => p.clip === 4)[1].o);
  const p5b = F(P.filter((p) => p.clip === 5)[1].o);
  const tLibreta = F(wordAt("libreta", 5));
  const tAdelante = F(wordAt("adelante", 6));
  const tKm6 = F(W.filter((w) => w.clip === 6 && norm(w.w) === "kilómetros")[0].s);
  const tBorrar = F(wordAt("borrar", 7));
  const tGratis = F(wordAt("gratis", 10));
  const tUrl = F(wordAt("libretaapp.com", 11));
  const endF = F(plan.total);
  // cortes con cambio de ángulo: whoosh suave
  const cuts = P.slice(1).filter((p, i) => p.clip !== P[i].clip).map((p) => F(p.o));
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <FontFaces />
      <Base />
      <FilterFx />
      <Headline />
      <EmojiPop from={F(wordAt("vecina", 2))} to={ce(2) + 4} emoji="🤭" />
      <Chip from={c(4)} to={p4b + 6} top={200}>
        <span style={{ color: AMBER }}>15 AÑOS</span> VENDIENDO AUTOS
      </Chip>
      <Odometer from={p4b + 10} to={p5b} a={186420} b={89300} label="KILÓMETROS “RETOCADOS”" />
      <Stamp from={tLibreta} to={ce(5) + 4}>
        <Img src={staticFile("logo.png")} style={{ width: 120, height: 120, borderRadius: 26 }} />
        LIBRETA NO
      </Stamp>
      <Chip from={c(6)} to={tKm6 + 30} top={200}>
        Lo carga el <span style={{ color: AMBER }}>TALLER</span> <span style={{ color: GREEN }}>✓</span>
      </Chip>
      <Odometer from={tKm6} to={ce(6) + 6} a={87450} b={97450} up label="SOLO PARA ADELANTE" />
      <Chip from={c(7) + 6} to={ce(7)} top={190} bg="rgba(120,10,20,.9)">
        <span style={{ color: RED }}>✕</span> NO SE BAJA
      </Chip>
      <Chip from={tBorrar} to={ce(7)} top={330} bg="rgba(120,10,20,.9)">
        <span style={{ color: RED }}>✕</span> NO SE BORRA
      </Chip>
      <Chip from={c(8) + 4} to={ce(8)} top={200} size={58}>
        ¿COMPRÁS? <span style={{ color: AMBER }}>PEDÍ EL HISTORIAL</span>
      </Chip>
      <Chip from={c(9) + 4} to={ce(9)} top={200} size={58}>
        ¿VENDÉS? <span style={{ color: AMBER }}>TENELO</span>
      </Chip>
      <Stamp from={tGratis - 2} to={ce(10) + 24} color={GREEN} top={230}>
        GRATIS
      </Stamp>
      <Confetti from={tGratis} />
      <UrlBar from={tUrl - 4} to={endF} />
      {cuts.map((f) => (
        <Flash key={f} at={f} />
      ))}
      <Captions />
      <Sequence from={endF}>
        <EndCard />
      </Sequence>
      <Progress />
      {/* sonidos */}
      <Sfx at={0} src="whoosh.wav" vol={0.35} />
      <Sfx at={F(wordAt("vecina", 2))} src="boom.wav" vol={0.6} />
      <Sfx at={c(3)} src="sparkle.wav" vol={0.35} />
      <Sfx at={p4b + 10} src="whoosh.wav" vol={0.3} />
      <Sfx at={tLibreta} src="boom.wav" vol={0.7} />
      <Sfx at={tAdelante} src="ding.wav" vol={0.35} />
      <Sfx at={c(7) + 6} src="pop.wav" vol={0.5} />
      <Sfx at={tBorrar} src="pop.wav" vol={0.5} />
      <Sfx at={tGratis} src="ding.wav" vol={0.5} />
      <Sfx at={endF} src="whoosh.wav" vol={0.35} />
      {cuts
        .filter((_, i) => i % 2 === 1)
        .map((f) => (
          <Sfx key={`w${f}`} at={f - 3} src="whoosh.wav" vol={0.12} />
        ))}
    </AbsoluteFill>
  );
};
