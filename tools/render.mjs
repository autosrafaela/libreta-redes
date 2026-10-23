// Uso: node tools/render.mjs posts/<id>/spec.json
// Genera en la carpeta del spec: slide-1.jpg, slide-2.jpg… (carousel/image) o reel.mp4 + cover.jpg (reel)
import { chromium } from "playwright-core";
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync, readdirSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const specPath = resolve(process.argv[2]);
const out = dirname(specPath);
const spec = JSON.parse(readFileSync(specPath, "utf8"));
const mode = spec.format === "reel" ? "reel" : spec.format === "image" ? "image" : "carousel";

// Reels: siempre con voz en off. Cada escena dura lo que dura su frase (+ un respiro).
let voiceDurs = {};
if (mode === "reel") {
  if (!spec.scenes.some((s) => s.say)) throw new Error("El reel no tiene voz: cada escena lleva un 'say'");
  execFileSync("python3", [join(here, "voice.py"), specPath], { stdio: "inherit" });
  voiceDurs = JSON.parse(readFileSync(join(out, ".voice", "durations.json"), "utf8"));
  spec.scenes.forEach((s, i) => { s.dur = Math.max(s.dur || 2.4, (voiceDurs[i] || 0) + 0.75); });
}

function findChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const base = "/opt/pw-browsers";
  for (const d of readdirSync(base).filter((d) => d.startsWith("chromium-")).sort().reverse()) {
    for (const sub of ["chrome-linux", "chrome-linux64"]) {
      const p = join(base, d, sub, "chrome");
      if (existsSync(p)) return p;
    }
  }
  throw new Error("No encontré Chromium");
}

const html = readFileSync(join(here, "template.html"), "utf8").replace(
  "LOGO_SRC",
  "data:image/png;base64," + readFileSync(join(here, "..", "assets", "logo.png")).toString("base64"),
);
const browser = await chromium.launch({ executablePath: findChrome(), args: ["--no-sandbox", "--font-render-hinting=none"] });
const page = await browser.newPage({ viewport: { width: 1080, height: mode === "reel" ? 1920 : 1350 }, deviceScaleFactor: 1 });
// la página vive en tools/ para que las fuentes de node_modules carguen por ruta relativa
const tmp = join(here, ".page.html");
writeFileSync(tmp, html);
await page.goto("file://" + tmp, { waitUntil: "load" });
await page.evaluate(([s, m]) => setup(s, m), [spec, mode]);
await page.evaluate(() => document.fonts.ready);

if (mode !== "reel") {
  for (let i = 0; i < spec.slides.length; i++) {
    await page.evaluate((i) => showSlide(i), i);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: join(out, `slide-${i + 1}.jpg`), type: "jpeg", quality: 93 });
  }
  console.log(`OK ${spec.slides.length} imágenes en ${out}`);
} else {
  const fps = 30;
  const total = await page.evaluate(() => buildReel());
  await page.evaluate(() => document.fonts.ready);
  const fr = join(out, ".frames");
  rmSync(fr, { recursive: true, force: true });
  mkdirSync(fr, { recursive: true });
  const n = Math.round(total * fps);
  for (let f = 0; f < n; f++) {
    await page.evaluate((t) => setTime(t), f / fps);
    await page.screenshot({ path: join(fr, String(f).padStart(5, "0") + ".jpg"), type: "jpeg", quality: 90 });
  }
  // portada: primer escena ya armada
  await page.evaluate((t) => setTime(t), Math.min(spec.scenes[0].dur - 0.3, 2.2));
  await page.screenshot({ path: join(out, "cover.jpg"), type: "jpeg", quality: 93 });
  // voz: cada frase arranca 0.2 s después de que empieza su escena
  const ins = [], flt = [];
  let t0 = 0, k = 0;
  spec.scenes.forEach((s, i) => {
    if (voiceDurs[i]) { ins.push("-i", join(out, ".voice", `s${String(i).padStart(2, "0")}.wav`)); const ms = Math.round((t0 + 0.2) * 1000); flt.push(`[${k + 1}:a]aresample=44100,adelay=${ms}|${ms},apad[v${k}]`); k++; }
    t0 += s.dur;
  });
  const mix = flt.join(";") + ";" + Array.from({ length: k }, (_, j) => `[v${j}]`).join("") + `amix=inputs=${k}:normalize=0:duration=longest,atrim=0:${total},loudnorm=I=-14:TP=-1.5:LRA=7,aformat=channel_layouts=stereo[a]`;
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(fps), "-i", join(fr, "%05d.jpg"), ...ins, "-filter_complex", mix,
    "-map", "0:v", "-map", "[a]", "-t", String(total), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
    "-r", "30", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "160k", join(out, "reel.mp4")]);
  rmSync(join(out, ".voice"), { recursive: true, force: true });
  rmSync(fr, { recursive: true, force: true });
  console.log(`OK reel de ${total.toFixed(1)} s en ${out}`);
}
rmSync(tmp, { force: true });
await browser.close();
