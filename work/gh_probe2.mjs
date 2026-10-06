import { createRequire } from "node:module";
const require = createRequire("/Users/alasijiadegou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/");
const { chromium } = require("playwright");
const browser = await chromium.connectOverCDP("http://127.0.0.1:9223");
const ctx = browser.contexts()[0];
const page = ctx.pages()[0] || await ctx.newPage();
await page.setViewportSize({ width: 1400, height: 1000 });
await page.goto("https://github.com/aryehToDog/ponsfi-dashboard", { waitUntil: "load", timeout: 60000 });
await new Promise(r => setTimeout(r, 5000));
const info = await page.evaluate(() => ({
  url: location.href,
  title: document.title.slice(0, 120),
  hasSignIn: !!Array.from(document.querySelectorAll("a")).find(a => /^sign in$/i.test(a.textContent.trim())),
  hasMeta: Array.from(document.querySelectorAll("meta")).map(m => m.getAttribute("name")).filter(Boolean).slice(0, 20),
  loggedInText: (document.querySelector('summary[aria-label*="View profile"], [aria-label*="profile"]') || {}).outerHTML?.slice(0,150) || "n/a",
  h1: (document.querySelector("h1")||{}).innerText || "",
}));
console.log(JSON.stringify(info, null, 2));
process.exit(0);
