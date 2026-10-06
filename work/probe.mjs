import { createRequire } from "node:module";
const require = createRequire("/Users/alasijiadegou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/");
const { chromium } = require("playwright");
const browser = await chromium.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: true,
  args: ["--hide-scrollbars", "--mute-audio", "--no-proxy-server", "--proxy-bypass-list=*"],
});
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 }, locale: "zh-CN" });
const page = await ctx.newPage();
await page.goto("https://stonk1000x.top/", { waitUntil: "domcontentloaded", timeout: 30000 });
try { await page.waitForLoadState("networkidle", { timeout: 15000 }); } catch (e) {}
await new Promise(r => setTimeout(r, 6000));
const dump = await page.evaluate(() => {
  const txt = (sel) => { const e = document.querySelector(sel); return e ? e.textContent.replace(/\s+/g, " ").trim().slice(0, 220) : "[无此元素]"; };
  return {
    title: document.title,
    h1: txt("h1"),
    cards: Array.from(document.querySelectorAll("[class*=card],[class*=kpi],[class*=stat]")).slice(0, 8).map(e => e.textContent.replace(/\s+/g, " ").trim().slice(0, 90)),
    bodySample: document.body.textContent.replace(/\s+/g, " ").trim().slice(0, 700),
  };
});
console.log(JSON.stringify(dump, null, 2));
await browser.close();
