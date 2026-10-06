import { createRequire } from "node:module";
const require = createRequire("/Users/alasijiadegou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/");
const { chromium } = require("playwright");
const browser = await chromium.connectOverCDP("http://127.0.0.1:9223");
const ctx = browser.contexts()[0];
const page = ctx.pages()[0] || await ctx.newPage();
await page.goto("https://github.com/aryehToDog/ponsfi-dashboard", { waitUntil: "domcontentloaded", timeout: 45000 });
await new Promise(r => setTimeout(r, 4000));

const out = await page.evaluate(() => {
  const res = { csrf: !!document.querySelector('meta[name="csrf-token"]'), candidates: [], aboutText: "" };
  // 找 About 区域的编辑按钮
  document.querySelectorAll("button, a").forEach(el => {
    const label = (el.getAttribute("aria-label") || "") + " | " + (el.getAttribute("title") || "") + " | " + (el.textContent || "").trim().slice(0, 40);
    const href = el.getAttribute("href") || "";
    if (/edit|Edit|编辑|settings|topic|description|about/i.test(label) || /settings/i.test(href)) {
      res.candidates.push({ tag: el.tagName, cls: (el.className || "").toString().slice(0, 60), label: label.slice(0, 110), href: href.slice(0, 80) });
    }
  });
  const about = document.querySelector(".BorderGrid-row, [class*=about]");
  if (about) res.aboutText = about.innerText.replace(/\s+/g, " ").slice(0, 400);
  return res;
});
console.log(JSON.stringify(out, null, 2).slice(0, 4000));
process.exit(0);
