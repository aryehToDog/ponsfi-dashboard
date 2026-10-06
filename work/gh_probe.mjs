import { createRequire } from "node:module";
const require = createRequire("/Users/alasijiadegou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/");
const { chromium } = require("playwright");

const browser = await chromium.connectOverCDP("http://127.0.0.1:9223");
const ctx = browser.contexts()[0];
const page = ctx.pages()[0] || await ctx.newPage();
await page.goto("https://github.com/aryehToDog/ponsfi-dashboard", { waitUntil: "domcontentloaded", timeout: 45000 });
await new Promise(r => setTimeout(r, 3000));
const info = await page.evaluate(() => {
  const csrf = document.querySelector('meta[name="csrf-token"]');
  const title = document.title;
  const body = document.body.innerText.slice(0, 300).replace(/\s+/g, " ");
  const loggedIn = !document.body.innerText.includes("Sign in to GitHub");
  return {
    title,
    url: location.href,
    csrf: csrf ? "有 (" + csrf.content.length + "字符)" : "无",
    loggedIn,
    bodySample: body,
  };
});
console.log(JSON.stringify(info, null, 2));
process.exit(0);
