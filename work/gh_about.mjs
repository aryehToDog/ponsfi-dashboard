import { createRequire } from "node:module";
const require = createRequire("/Users/alasijiadegou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/");
const { chromium } = require("playwright");

const ctx = await chromium.launchPersistentContext("/tmp/cpx", {
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: false,
  viewport: { width: 1440, height: 1000 },
  locale: "zh-CN",
  args: ["--no-first-run", "--no-default-browser-check", "--profile-directory=Profile 2", "--no-proxy-server"],
});
const page = ctx.pages()[0] || await ctx.newPage();
await page.goto("https://github.com/aryehToDog/ponsfi-dashboard", { waitUntil: "load", timeout: 60000 });
await new Promise(r => setTimeout(r, 4000));

const out = await page.evaluate(() => {
  const res = {};
  res.actorLogin = (document.querySelector('meta[name="octolytics-actor-login"]')||{}).content || "n/a";
  res.csrf = (document.querySelector('meta[name="csrf-token"]')||{}).content?.length || 0;
  const heads = Array.from(document.querySelectorAll("h2, h3"));
  const aboutHead = heads.find(h => /^about$/i.test(h.textContent.trim()));
  res.foundAbout = !!aboutHead;
  if (aboutHead) {
    let host = aboutHead;
    for (let i = 0; i < 4 && host.parentElement; i++) host = host.parentElement;
    res.hostHTML = host.outerHTML.replace(/\s+/g, " ").slice(0, 2000);
  }
  res.settingsLinks = Array.from(document.querySelectorAll('a[href*="/settings"]')).slice(0, 6).map(a => a.getAttribute("href"));
  return res;
});
console.log(JSON.stringify(out, null, 2).slice(0, 4000));
await ctx.close();
process.exit(0);
