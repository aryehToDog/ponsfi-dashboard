import { createRequire } from "node:module";
const require = createRequire("/Users/alasijiadegou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/");
const { chromium } = require("playwright");
const browser = await chromium.connectOverCDP("http://127.0.0.1:9223");
const ctx = browser.contexts()[0];
const cookies = await ctx.cookies("https://github.com");
console.log("github.com cookie 数量:", cookies.length);
for (const c of cookies.slice(0, 25)) {
  console.log(`  ${c.name}  domain=${c.domain}  httpOnly=${c.httpOnly}  value长度=${(c.value||"").length}  值前缀=${(c.value||"").slice(0,4)}`);
}
process.exit(0);
