// 生成「像素画」站点 Logo（2026-10-07 · v3.23）
// ---------------------------------------------------------------------------
// 输入：work/brand/pixel-source.webp（作者提供的 800×800 像素画，原文件拷贝）
// 输出（全部落在 work/brand/）：
//   pixel-source.png  —— 原画 PNG 重编码（800×800；服务器分享图 logo-pixel.png 的母版）
//   logo-pix-32.png   —— 标签页图标
//   logo-pix-52.png   —— 页头品牌标（26px 显示 × 2 倍图，视网膜屏也清晰）
//   logo-pix-180.png  —— 苹果触屏图标
//   logo-pix-256.png  —— 文档 / README 展示
//   logo-pix-512.png  —— 分享图备份位（服务器 logo-512.png 覆盖用）
//   以及 outputs/logo-预览-v323.png —— 浅色/深色背景 × 多尺寸预览
// 跑法：node work/brand/render_pixel.mjs
//       node work/brand/render_pixel.mjs --ascii  只打印色块字符自检（不写文件）
//
// 说明：缩放一律用最近邻（imageSmoothingEnabled=false）保持像素画的硬边风格；
//       800→32 正好是 25 倍整数比，图标最干净。
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(path.dirname(HERE));

function loadPlaywright() {
  const candidates = [
    process.env.PLAYWRIGHT_DIR,
    "/Users/alasijiadegou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/",
    path.join(HERE, "node_modules/"),
  ].filter(Boolean);
  for (const dir of candidates) {
    try { return createRequire(path.join(dir, "noop.js"))("playwright"); } catch (e) {}
  }
  return createRequire(import.meta.url)("playwright");
}
const { chromium } = loadPlaywright();
const CHROME = process.env.CHROME_BIN || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const DATA = "data:image/webp;base64," + fs.readFileSync(path.join(HERE, "pixel-source.webp")).toString("base64");

const browser = await chromium.launch({ headless: true, executablePath: CHROME, args: ["--no-proxy-server", "--hide-scrollbars", "--mute-audio"] });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

const SIZES = [32, 52, 180, 256, 512, 800];

const renderAll = () => page.evaluate(async ({ DATA, SIZES }) => {
  const img = new Image();
  await new Promise((res, rej) => { img.onload = res; img.onerror = () => rej(new Error("图片解码失败")); img.src = DATA; });
  const out = {};
  for (const n of SIZES) {
    const c = document.createElement("canvas"); c.width = n; c.height = n;
    const g = c.getContext("2d");
    g.imageSmoothingEnabled = false;
    g.drawImage(img, 0, 0, n, n);
    out[n] = c.toDataURL("image/png");
  }
  return out;
}, { DATA, SIZES });

const classify = (N) => page.evaluate(async ({ DATA, N }) => {
  const img = new Image();
  await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = DATA; });
  const c = document.createElement("canvas"); c.width = N; c.height = N;
  const g = c.getContext("2d"); g.imageSmoothingEnabled = false; g.drawImage(img, 0, 0, N, N);
  const d = g.getImageData(0, 0, N, N).data; const rows = [];
  for (let y = 0; y < N; y++) { let s = "";
    for (let x = 0; x < N; x++) {
      const i = (y * N + x) * 4, r = d[i], gr = d[i + 1], b = d[i + 2];
      const lum = (0.2126 * r + 0.7152 * gr + 0.0722 * b) / 255;
      let ch;
      if (lum < 0.16) ch = "K";
      else if (b > r + 24 && b > gr + 12) ch = "B";
      else if (gr > r + 16 && gr > b + 16) ch = "G";
      else if (r > 170 && gr > 140 && b < 130 && r - b > 70) ch = "Y";
      else if (r > gr + 40 && r > b + 40) ch = "R";
      else if (lum > 0.82) ch = ".";
      else ch = "o";
      s += ch;
    }
    rows.push(s);
  }
  return rows.join("\n");
}, { DATA, N });

if (process.argv.includes("--ascii")) {
  console.log("== 32px 色块自检（B蓝 G绿 R红 Y黄 K深 .亮 o其他）==\n" + await classify(32));
  console.log("\n== 16px 色块自检 ==\n" + await classify(16));
  await browser.close();
  process.exit(0);
}

const shots = await renderAll();
const report = [];
for (const n of SIZES) {
  const buf = Buffer.from(shots[n].split(",")[1], "base64");
  const name = n === 800 ? "pixel-source.png" : `logo-pix-${n}.png`;
  fs.writeFileSync(path.join(HERE, name), buf);
  report.push(`${name} ${buf.length}B`);
}
console.log("已生成：" + report.join(" | "));

// 预览图：浅色 / 深色两栏 × 多尺寸平铺 + 页头圆角芯片样例
const previewPng = await page.evaluate(async ({ DATA }) => {
  const img = new Image();
  await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = DATA; });
  const W = 1440, H = 820, band = H / 2;
  const c = document.createElement("canvas"); c.width = W; c.height = H;
  const g = c.getContext("2d");
  g.imageSmoothingEnabled = false;
  const draw = (x, y, n, round) => {
    if (round) { g.save(); g.beginPath(); g.roundRect(x, y, n, n, n * 0.23); g.clip(); }
    g.drawImage(img, x, y, n, n);
    if (round) {
      g.restore();
      g.save(); g.beginPath(); g.roundRect(x + 0.75, y + 0.75, n - 1.5, n - 1.5, n * 0.21);
      g.strokeStyle = "rgba(139,124,255,.9)"; g.lineWidth = 1.5; g.stroke(); g.restore();
    }
  };
  const sizes = [16, 26, 32, 48, 96, 180];
  const bands = [[0, "#f2f4f9", "#3f4552"], [band, "#0a0c11", "#c3cad6"]];
  for (const [top, bg, fg] of bands) {
    g.fillStyle = bg; g.fillRect(0, top, W, band);
    g.font = "600 40px -apple-system, 'PingFang SC', Arial"; g.fillStyle = fg;
    g.fillText("新 Logo · 像素画（v3.23）", 64, top + 88);
    g.font = "400 18px -apple-system, 'PingFang SC', Arial";
    g.fillStyle = top === 0 ? "#7c8494" : "#8b93a2";
    g.fillText("作者提供的 800×800 像素画 · 最近邻缩放（保像素块）", 64, top + 121);
    let x = 64;
    const bottom = top + band - 64;
    for (const n of sizes) {
      draw(x, bottom - n, n, n === 26);
      g.font = "500 15px -apple-system, 'PingFang SC', Arial"; g.fillStyle = fg;
      const label = n === 26 ? "26 · 页头" : n === 32 ? "32 · 标签页" : n === 180 ? "180 · 触屏" : String(n);
      g.fillText(label, x, top + band - 26);
      x += Math.max(n, 46) + 46;
    }
  }
  return c.toDataURL("image/png");
}, { DATA });
const pv = Buffer.from(previewPng.split(",")[1], "base64");
fs.writeFileSync(path.join(ROOT, "outputs", "logo-预览-v323.png"), pv);
console.log(`outputs/logo-预览-v323.png ${pv.length}B`);

await browser.close();
console.log("done");
process.exit(0);
