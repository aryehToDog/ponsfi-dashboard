// 生成「卡通狗」站点 logo（2026-10-07 · v3.22）
// ---------------------------------------------------------------------------
// 输入：work/brand/dog.svg（小狗形象母版，64×64）
// 输出：
//   logo.svg                    —— 站点图标（SVG favicon；页头内联也用同一形状，由 embed_icon.py 注入）
//   logo-16/32/180/192/512.png  —— 位图版本（标签页 / 苹果触屏 / 分享图）
// 跑法：node work/brand/render_dog.mjs          生成全部产物
//       node work/brand/render_dog.mjs --ascii  只打印字符预览（白底 + 深底，自检形状/可辨识度）
//
// 设计：深色圆角底板（#101421）+ 紫→绿描边，把小狗衬出来 —— 深色/浅色标签页都清楚。
// 注意：底板的渐变 id 用 pg、小狗的用 dogG，注入页面时不会和站内其它 id 冲突。
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));

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

const raw = fs.readFileSync(path.join(HERE, "dog.svg"), "utf-8").trim();
const inner = raw
  .replace(/^<svg[^>]*>/, "")
  .replace(/<\/svg>\s*$/, "")
  .replace(/id="g"/g, 'id="dogG"')
  .replace(/url\(#g\)/g, "url(#dogG)");

const plate = (scale) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
<defs><linearGradient id="pg" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#8b7cff"/><stop offset="1" stop-color="#2ee6a8"/></linearGradient></defs>
<rect x="0" y="0" width="64" height="64" rx="15" fill="#101421"/>
<rect x="1.15" y="1.15" width="61.7" height="61.7" rx="14" fill="none" stroke="url(#pg)" stroke-width="1.7" opacity=".55"/>
<g transform="translate(32,32) scale(${scale}) translate(-32,-32)">
${inner}
</g></svg>`;

// 页头内联版：宽度写死 26，其余与站点图标一致（embed_icon.py 读取）
const headerSvg = plate(0.88).replace('width="64" height="64"', 'width="26" height="26"');

const SIZES = [
  [16, 0.94], [32, 0.92], [180, 0.88], [192, 0.88], [512, 0.88],
];

const browser = await chromium.launch({ headless: true, executablePath: CHROME, args: ["--no-proxy-server", "--hide-scrollbars", "--mute-audio"] });
const page = await browser.newPage({ viewport: { width: 640, height: 640 } });

const rasterize = async (svg, N) => {
  await page.setContent(`<body style="margin:0">${svg}</body>`);
  return await page.evaluate(async (N) => {
    const el = document.querySelector("svg");
    const xml = new XMLSerializer().serializeToString(el);
    const img = new Image();
    await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(xml))); });
    const c = document.createElement("canvas"); c.width = N; c.height = N;
    const g = c.getContext("2d"); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = "high";
    g.drawImage(img, 0, 0, N, N);
    return c.toDataURL("image/png");
  }, N);
};

if (process.argv.includes("--ascii")) {
  const grid = async (svg, N, bg) => {
    await page.setContent(`<body style="margin:0;background:${bg}">${svg}</body>`);
    const txt = await page.evaluate(async ({ N, bg }) => {
      const el = document.querySelector("svg");
      const xml = new XMLSerializer().serializeToString(el);
      const img = new Image();
      await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(xml))); });
      const c = document.createElement("canvas"); c.width = N; c.height = N;
      const g = c.getContext("2d"); g.drawImage(img, 0, 0, N, N);
      const d = g.getImageData(0, 0, N, N).data; const out = [];
      for (let y = 0; y < N; y++) { let row = "";
        for (let x = 0; x < N; x++) { const i = (y * N + x) * 4;
          const a = d[i + 3] / 255, r = d[i] * a + 255 * (1 - a), gg = d[i + 1] * a + 255 * (1 - a), bb = d[i + 2] * a + 255 * (1 - a);
          const lum = (0.2126 * r + 0.7152 * gg + 0.0722 * bb) / 255;
          row += lum > 0.9 ? " " : lum > 0.72 ? "." : lum > 0.52 ? ":" : lum > 0.34 ? "o" : lum > 0.18 ? "O" : "#"; }
        out.push(row); }
      return out.join("\n");
    }, { N, bg });
    return txt;
  };
  console.log("== 64px 白底 ==\n" + await grid(plate(0.88), 64, "#ffffff"));
  console.log("== 32px 白底 ==\n" + await grid(plate(0.92), 32, "#ffffff"));
  console.log("== 32px 深底 ==\n" + await grid(plate(0.92), 32, "#202634"));
  console.log("== 26px 白底（页头实际尺寸）==\n" + await grid(headerSvg, 26, "#ffffff"));
  await browser.close();
  process.exit(0);
}

fs.writeFileSync(path.join(HERE, "logo.svg"), plate(0.88) + "\n", "utf-8");
fs.writeFileSync(path.join(HERE, "header-dog.svg"), headerSvg + "\n", "utf-8");
const manifest = [];
for (const [n, scale] of SIZES) {
  const png = await rasterize(plate(scale), n);
  const buf = Buffer.from(png.split(",")[1], "base64");
  fs.writeFileSync(path.join(HERE, `logo-${n}.png`), buf);
  manifest.push(`logo-${n}.png ${buf.length}B`);
}
await browser.close();
console.log("done:", manifest.join(" | "));
process.exit(0);
