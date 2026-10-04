# ponsfi.xyz · Pons & StonkFun 收入与回购监控看板

> 一块给社区看的实时数据面板：**Pons（$PONS · Robinhood Chain）** 与 **StonkFun（$STONK · Solana）** 的
> 收入、回购销毁、估值（P/S）、行业排名与小时级资金动向 —— 全部来自公开数据源，每小时自动刷新。

🌐 在线看板：**https://ponsfi.xyz** ｜ 作者：[@arych_kun](https://x.com/arych_kun)

---

## 中文

### 这个看板做什么

- **关键指标**：市值、年化收入、P/S 年化（7 日 / 30 日）、回购力度、环比走势 —— 一眼看懂"贵不贵、回购有没有力"。
- **小时监控（最近 72 小时）**：交易量 / 收入 / 销毁 三个维度切换，一根柱子一小时；鼠标划过或手机点按柱子即可读取该小时数值，右上角常驻"当前小时"卡会自动让位避免重复。
- **回购与销毁**：24 小时 / 30 天回购榜（含全市场对照），Pons 链上销毁逐区块核对。
- **收入排行**：这两个项目在全行业收入榜（DefiLlama）里的位置与变化。
- **趋势图与日度明细**：日收入 / 回购曲线 + 逐日数据表。
- **辅助内容**：规则引擎（离场线 / 警戒线 / 机会线提示）、涨跌歌单 BGM、歌词、共勉与点赞、访问统计 —— 好看也好玩。
- 深色 / 浅色自动适配；中英双语随浏览器语言自动切换。

### 数据来源（全部公开）

| 数据 | 来源 |
| --- | --- |
| 日收入 / 回购（每日） | DefiLlama Fees API |
| 市值 / 价格 | DefiLlama Protocol API · coins.llama.fi |
| 小时交易量 | GeckoTerminal OHLCV（PONS/WETH、STONK/SOL） |
| Pons 链上销毁 | Robinhood Chain RPC（逐区块读取销毁事件） |
| StonkFun 官方收入 / 回购 | `stonkfun.xyz/api/revenue` 官方累计值逐小时做差 |
| 全行业排行 | defillama.com/revenue |

> 数据每小时自动刷新；源站延迟会如实标注（如"数据滞后 N 天"），不做修饰。
> 本看板仅做数据展示，**不构成任何投资建议**。

### 目录结构

```
work/       采集 / 渲染 / 上线脚本（template.html 是页面唯一母版）
outputs/    构建产物（无人值守管线每小时生成 pons-stonkfun-monitor.html）
deploy/     服务器侧文件（nginx 配置、访问计数服务、音频、部署说明）
backups/    历史版本备份包（不进版本库）
work/看板维护说明.md   详细的维护 / 改动指南
```

### 快速开始

```bash
# 只用现有数据快照重新渲染页面（不联网，最快）
python3 work/render_only.py        # 产出 outputs/pons-stonkfun-monitor.html

# 手动跑一次完整刷新（拉数据 → 渲染 → 上线）
python3 work/hourly_check.py
```

自动化：本机由 LaunchAgent `com.ponspulse.hourly` 每小时第 5 分钟执行一次
`work/hourly_check.py`；上线成功后自动调用 `work/git_sync.py` 同步到本仓库
（源文件 → main，整站快照 → snapshots 分支，并自动打带更新说明的版本标签）。

### 版本与发版

- 版本标签形如 `v3.5`（功能版）与 `v3.5.1`（补丁版），标签说明自动生成（提交清单 + 改动文件）。
- 历史版本可在本仓库 **Tags** 页逐版回看；想手动发版：改 `work/render_only.py` 里的 `VER` 后正常上线一次即可。

### 支持作者

看板由我一个人利用业余时间开发维护。如果它对你有帮助，欢迎请我喝杯咖啡 ☕

- EVM：`0xa7f6cc31b6b5454b0eb705e5b56ebfc320e7b5b9`
- Solana：`EEchRHEuNiMZrHaEVgW1UxtGZwHx4S4JEhW12uGuuQKq`

---

## English

### What is this

A community dashboard for **Pons ($PONS · Robinhood Chain)** and **StonkFun ($STONK · Solana)**:
revenue, buybacks & burns, valuation (P/S), industry ranking, and hour-by-hour flows — all from
public data sources, refreshed automatically every hour.

🌐 Live: **https://ponsfi.xyz** ｜ Built by [@arych_kun](https://x.com/arych_kun)

### Features

- **Key metrics** — market cap, annualized revenue, P/S (7d / 30d), buyback intensity, week-over-week trend.
- **Hourly monitor (last 72h)** — volume / revenue / burn tabs, one bar per hour; hover or tap a bar to read
  that hour's numbers for both tokens (the pinned "current hour" card gets out of the way automatically).
- **Buybacks & burns** — 24h / 30d buyback board with market-wide comparison; Pons on-chain burns verified block by block.
- **Revenue ranking** — where these two projects sit on DefiLlama's protocol revenue leaderboard.
- **Charts & daily tables** — daily revenue / buyback curves and per-day detail.
- **Extras** — rule engine alerts (exit / warning / opportunity lines), market-mood music player with lyrics,
  quotes wall with likes, page-view stats.
- Auto light / dark theme; auto Chinese / English based on browser language.

### Data sources (all public)

| Data | Source |
| --- | --- |
| Daily revenue / buybacks | DefiLlama Fees API |
| Market cap / price | DefiLlama Protocol API · coins.llama.fi |
| Hourly volume | GeckoTerminal OHLCV (PONS/WETH, STONK/SOL) |
| Pons on-chain burns | Robinhood Chain RPC (burn events, block by block) |
| StonkFun official revenue / buybacks | `stonkfun.xyz/api/revenue` cumulative counters, diffed hourly |
| Industry ranking | defillama.com/revenue |

> Refreshed hourly; stale source data is labeled honestly (e.g. "N days behind") and never smoothed over.
> This dashboard is for informational purposes only and **is not financial advice**.

### Repository layout

```
work/       collection / rendering / deployment scripts (template.html is the single source of truth)
outputs/    build artifacts (pons-stonkfun-monitor.html, regenerated hourly)
deploy/     server-side files (nginx config, visit counter, audio, deployment docs)
backups/    historical release bundles (not tracked in git)
```

### Quick start

```bash
python3 work/render_only.py    # re-render the page from the latest data snapshot (offline)
python3 work/hourly_check.py   # full refresh: fetch -> render -> deploy -> sync
```

### Versioning

Release tags look like `v3.5` (features) or `v3.5.1` (patches); each tag ships with an auto-generated
changelog (commit list + changed files). Browse them on this repo's **Tags** page.

### Support the author

Built and maintained solo in spare time. If it helps you, a coffee is appreciated ☕

- EVM: `0xa7f6cc31b6b5454b0eb705e5b56ebfc320e7b5b9`
- Solana: `EEchRHEuNiMZrHaEVgW1UxtGZwHx4S4JEhW12uGuuQKq`
