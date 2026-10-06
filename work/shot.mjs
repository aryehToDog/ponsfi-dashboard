import { createRequire } from "node:module";

const MOD = "/Users/alasijiadegou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/";
const require = createRequire(MOD);
const { chromium } = require("playwright");

const OUT = "/Users/alasijiadegou/Documents/Codex/2026-09-28/https-x-com-ponsdotfamily-https-x/outputs";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const SITE = "https://stonk1000x.top/";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await chromium.launch({
  executablePath: CHROME,
  headless: true,
  args: ["--hide-scrollbars", "--mute-audio", "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--disable-background-networking", "--no-proxy-server", "--proxy-bypass-list=*"],
});

async function makePage(vp, mobile) {
  const ctx = await browser.newContext({
    viewport: vp,
    deviceScaleFactor: 2,
    locale: "zh-CN",
    isMobile: !!mobile,
    hasTouch: !!mobile,
    userAgent: mobile
      ? "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
      : undefined,
  });
  await ctx.addInitScript(() => {
    try { HTMLMediaElement.prototype.play = function () { return Promise.resolve(); }; } catch (e) {}
  });
  return ctx;
}

async function load(page) {
  await page.goto(SITE, { waitUntil: "domcontentloaded", timeout: 30000 });
  try { await page.waitForLoadState("networkidle", { timeout: 15000 }); } catch (e) {}
  await sleep(6000);
}

const log = [];
try {
  // 图 1：桌面首页
  {
    const ctx = await makePage({ width: 1600, height: 1000 }, false);
    const page = await ctx.newPage();
    await load(page);
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(1500);
    const title = await page.title();
    await page.screenshot({ path: OUT + "/推特-图1-桌面.png", animations: "disabled" });
    log.push("图1 ok title=" + title);
    await ctx.close();
  }

  // 图 2：手机端
  {
    const ctx = await makePage({ width: 390, height: 844 }, true);
    const page = await ctx.newPage();
    await load(page);
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(1500);
    await page.screenshot({ path: OUT + "/推特-图2-手机.png", animations: "disabled" });
    log.push("图2 ok");
    await ctx.close();
  }

  // 图 3：小时监控板块（切到「收入」Tab）
  {
    const ctx = await makePage({ width: 1600, height: 1000 }, false);
    const page = await ctx.newPage();
    await load(page);
    const clicked = await page.evaluate(() => {
      const tabs = document.querySelectorAll("#hourlyTabs .tab");
      if (tabs.length >= 2) { tabs[1].click(); return "clicked-tab2"; }
      return "no-tabs(" + tabs.length + ")";
    });
    await sleep(2000);
    const sec = await page.$("#st-hourly");
    if (sec) { await sec.scrollIntoViewIfNeeded(); } else { log.push("WARN no #st-hourly"); }
    await sleep(1500);
    await page.screenshot({ path: OUT + "/推特-图3-监控板块.png", animations: "disabled" });
    log.push("图3 ok " + clicked);
    await ctx.close();
  }
} catch (e) {
  log.push("ERR " + String(e).slice(0, 400));
} finally {
  await browser.close().catch(() => {});
}
console.log(log.join("\n"));
