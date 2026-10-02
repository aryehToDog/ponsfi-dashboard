const BUNDLE = /*__DATA__*/;

/* ==================== 多语言 / i18n ==================== */
const I18N = {
zh:{
  docTitle:'Pons · StonkFun 收入与回购监控面板',
  h1:'Pons · StonkFun 收入与回购监控面板',
  secRules:'规则引擎 · 加仓与止损信号',
  secChart:'趋势图',
  secTable:'日度明细（最近 20 天）',
  secGuide:'指标说明 · 每个数字怎么读',
  refresh:'刷新数据',
  loading:'加载中…', fetching:'拉取中…',
  live:'● 实时数据', offline:'● 内置快照（联网失败）', liveAt:'● 实时数据 · ',
  updatedAt:'数据时间 ',
  burned:'已销毁 ', mcap:'市值 ', fromAth:'距 ATH ',
  perDay:' /天',
  kAvg7:'7 日均收入', kMom:'环比上 7 日', kLast:'最新单日收入', kPeak:'单日收入峰值',
  kPs7:'P/S 年化 (7日)', kPs30:'P/S 年化 (30日)', kFromPeak:'距收入峰值',
  kBurnYield:'回购年化收益率', kBurn7:'最近 7 日回购', kBurnForce:'回购力度',
  kVol24:'24h 成交额', kTurnover:'日换手率',
  tipPs:'市值 ÷ 一年收入，越小越便宜', tipPs30:'用 30 日均收入算的 P/S，比 7 日平滑',
  tipBurnYield:'7 日回购 × 52 ÷ 市值：一年能买掉市值的百分之几',
  tipBurnForce:'最近 7 日回购 ÷ 最近 7 日成交额：≥5% 才算有效买盘', tipVol:'24 小时成交额',
  stBad:'收入已跌破止损线，退出观察', stWarn:'收入低于警戒线，暂停加仓',
  stMom:'收入环比骤降，只观察不动手', stUp:'收入企稳回升，可考虑分批加仓',
  stFlat:'收入横盘企稳，持有观察',
  lvOk:'正常', lvWarn:'警戒', lvBad:'危险',
  legendOk:'条件满足，按原计划持有', legendWarn:'接近阈值，暂停加仓、盯紧',
  legendBad:'规则已触发，看每条下面的「建议」',
  cmpHead:(n,m)=>n+'/'+m+' 条正常',
  verdict:'对比：', verdictTie:'两家基本打平', verdictNoData:'数据不足', verdictWin:t=>t+' ',
  advice:'建议：',
  vFloor:'缓冲更厚', vMom:'更抗跌', vBurn:'更积极', vBurnpower:'回购占比更高', vPs:'更便宜',
  dimFloorL:'收入是否跌破止损线', dimFloorH:'7 日均低于离场线＝该走',
  dimMomL:'收入环比是否骤降', dimMomH:'连续下跌是最早的坏消息',
  dimBurnL:'回购是否持续', dimBurnH:'回购停＝最重要的离场信号',
  dimBpL:'回购能不能托住价格', dimBpH:'回购 ÷ 成交额，＜2% 基本可忽略',
  dimPsL:'估值贵不贵（P/S）', dimPsH:'越低越便宜',
  dimFloorS:'止损', dimMomS:'环比', dimBurnS:'回购', dimBpS:'力度', dimPsS:'估值',
  conclusion:'综合结论',
  priority:t=>'资金优先级：'+t+'（P/S 更低、安全垫更厚）；另一方等环比止跌、估值回落再考虑加仓。',
  priorityNone:'数据不足，暂不给资金优先级建议。',
  actFloorBad:'已跌破离场线：建议分批减仓或清仓，不要补仓',
  actFloorWarn:'低于警戒线：暂停加仓，每天盯住这条线',
  actFloorOk:v=>'高出警戒线 '+v+'%，可继续持有',
  sFloor:(a,b,c)=>'7 日均 '+a+'/天　·　离场线 '+b+'　·　警戒线 '+c,
  actMomBad:'环比骤降超 25%：暂停一切加仓，等连续 3 天回升再考虑',
  actMomWarn:'环比走弱：只观察、不加仓',
  actMomUp:'环比回升：可考虑分批加仓',
  actMomFlat:'环比平稳：维持现有仓位',
  sMom:(d)=>'本周 vs 上周 '+d+'%　·　触发线 −25%',
  actBurnOff:'回购已停止：先减仓，等回购恢复再谈加仓',
  actBurnOn:v=>'回购在持续，7 日回购≈同期收入的 '+v+'%',
  sBurn:(a,b)=>'最近 7 日回购 '+a+'　·　'+b,
  actBpNone:'缺少成交额数据，无法判断回购的影响力',
  actBpOk:v=>'回购占成交额 '+v+'%：买盘足够重，能真正托住价格',
  actBpWarn:v=>'回购占成交额 '+v+'%：能减缓下跌，但改变不了方向',
  actBpBad:v=>'回购只占成交额 '+v+'%：杯水车薪，别指望回购托底',
  sBp:(a,b)=>'最近 7 日回购 '+a+' ÷ 7 日成交额 '+b+'　·　≥5% 才算有效买盘',
  actPsNone:'没有收入数据，暂时无法估值',
  actPsCheap:v=>v+'x 便宜：安全垫厚，可分批加仓',
  actPsFair:v=>v+'x 合理：持有观察，不追高',
  actPsDear:v=>v+'x 偏贵：不追高，等回调或收入涨上来',
  sPs:v=>'P/S 年化(7日) '+v+'　·　<1.5x 便宜 · >4x 偏贵　·　参照 pump.fun 4.45x',
  tabRev:'日收入', tabRev7:'7 日均线收入', tabCum:'累计回购销毁', tabPrice:'价格对比（归一）',
  base100:'基准 100', start100:'起点=100', stopLoss:t=>t+' 止损线',
  cumName:n=>n+' 累计回购（窗口内）',
  thDate:'日期', thRev:'日收入', thBurn:'回购销毁', thPrice:'币价', thAvg7:'近 7 日均',
  gPsT:'P/S 年化 —— 你花多少钱，买它一年的收入',
  gPsF:'P/S ＝ 市值 ÷ (日均收入 × 365 天)',
  gPsL:'数字越小越便宜，可以理解成"按现在的赚钱速度要几年回本"。它把"公司贵不贵"和"币价高低"分开看——币价低不代表便宜，要看它每年能赚多少。',
  gPsCap:t=>'算给你看（'+t+'）',
  gPsLine:(mc,avg,year,ps,yrs)=>'市值 '+mc+'　÷　(7 日均收入 '+avg+'/天 × 365 天 ＝ '+year+')'+
      '<br>＝ <b>'+ps+'</b><br>→ 假设收入不变，你花 '+ps+' 买它 1 年的收入，要 <b>'+yrs+' 年</b>才回本',
  gPsCompare:(name,mc,year,ps,cheaper,gap)=>'对照 '+name+'：'+mc+' ÷ '+year+' ＝ <b>'+ps+'</b>'+(gap?('　→　'+cheaper+' 便宜 <b>'+gap+' 倍</b>'):''),
  gPsBands:[['&lt; 1.5x','g-ok','便宜 —— 安全垫厚，可分批加仓'],['1.5x – 4x','','合理 —— 持有观察，不追高'],['&gt; 4x','g-warn','偏贵 —— 需要收入增长来消化估值']],
  gPsNote:'注意：P/S 只反映"现在"，不反映"未来"。收入正在下滑时，看起来很便宜的 P/S 可能只是假象（分母迟早会变小）。',
  g730T:'为什么 P/S 要同时看 7 日和 30 日',
  g730F:'7 日 ＝ 最新速度　·　30 日 ＝ 近一个月平均',
  g730L:'7 日灵敏、能最早发现拐点；30 日平滑、不会被单日噪声骗。两个数字差得越大，说明收入变化越剧烈 —— 这正是判断"拐点"的关键。',
  g730Note:'记法：7 日 P/S 明显高于 30 日 P/S ＝ 收入在掉；反过来 ＝ 收入在涨。',
  psLine:(p,ps7,ps30,div,txt)=>p+'：7日 <b>'+ps7+'</b> vs 30日 <b>'+ps30+'</b>　→　相差 '+div+' 倍<br><span class="%C%">↳ '+txt+'</span>',
  divFast:(pct)=>({c:'g-bad', t:'收入正在快速下滑 —— 最近 7 天的收入只有过去一个月平均的 '+pct+'%'}),
  divSoft:()=>({c:'g-warn', t:'收入比月均低，正在走弱'}),
  divUp:(n)=>({c:'', t:'收入比月均高 '+n+' 倍，正在加速'}),
  divFlat:()=>({c:'', t:'收入和月均基本持平，节奏稳定'}),
  gBpT:'回购力度 —— 回购到底有没有用',
  gBpF:'回购力度 ＝ 最近 7 日回购 ÷ 最近 7 日成交额',
  gBpL:'不要看"回购了多少钱"，要看它占市场成交量的比例。买盘再大，如果同期有几十倍的筹码在换手，也改变不了价格方向。这是判断回购能否托底唯一有效的口径。',
  gBpBands:[['≥ 5%','g-ok','回购足够重，能真正托住价格'],['2% – 5%','g-warn','能减缓下跌，但改变不了方向'],['&lt; 2%','g-bad','杯水车薪，别指望回购托底']],
  gBpNote:'典型对照：为什么有的币回购了还在跌？回购占成交量太低，只是给卖盘提供流动性而已。',
  gBpLine:(a,x,b,y)=>a+'：最近 7 日回购 '+x+' ÷ 7 日成交额 '+y+' ＝ <b>'+b+'</b>',
  gBpFoot:'↑ 两个都在 2% 以下 —— 这就是"回购了但涨不动"的直接原因',
  gToT:'换手率 & 回购年化收益率',
  gToF:'换手率 ＝ 24h 成交额 ÷ 市值　·　回购年化 ＝ 7 日回购 × 52 ÷ 市值',
  gToL:'换手率告诉你筹码有多"活跃"：越高说明短线资金越多、波动越大，回购的影响也越小。回购年化告诉你：如果回购速度不变，一年能买掉市值的百分之几。',
  gToBands:[['换手 &lt; 3%','g-ok','筹码稳定，回购效果好'],['换手 3% – 8%','g-warn','偏活跃，回购效果一般'],['换手 &gt; 8%','g-bad','高频换手，回购效果被稀释']],
  gToNote:'重要：回购年化收益率高 ≠ 一定涨。它建立在"收入不跌"的假设上；收入一旦下滑，这个数字会跟着一起缩水。',
  gToLine:(a,ta,ya,b,tb,yb)=>'当前：'+a+' 换手 <b>'+ta+'/天</b> · 回购年化 <b>'+ya+'</b><br>　　　'+b+' 换手 <b>'+tb+'/天</b> · 回购年化 <b>'+yb+'</b>',
  gToFoot:'每天 1 成以上的筹码在换手 → 短线资金主导，回购对价格的影响被稀释',
  gMomT:'收入环比 —— 最灵敏的预警',
  gMomF:'收入环比 ＝ 最近 7 日均收入 vs 前 7 日均收入',
  gMomL:'这是所有指标里最早报警的一个。因为回购是"收入"的下游：收入 ↓ → 回购金额 ↓ → 买盘 ↓ → 价格失去支撑。盯收入，比盯回购更提前。',
  gMomBands:[['&gt; −15%','g-ok','收入平稳，维持仓位'],['−15% ~ −25%','g-warn','走弱，只观察不加仓'],['&lt; −25%','g-bad','骤降，暂停一切加仓']],
  gMomFoot:'两家都在 −35% 附近 → 已越过 −25% 触发线，按规则＝暂停加仓',
  foot1:'数据源：收入/回购＝DefiLlama（fees/revenue/holders-revenue API）；成交额/市值＝CoinGecko。Pons 收入=协议留存收入（创作者与 Uniswap 分成已扣除）；StonkFun 收入=其自留交易费（费用=收入）。P/S 年化 = 市值 ÷ (日均收入 × 365)，越低越便宜。参照系：pump.fun 30 日收入 $4,528 万、市值 $24.6 亿 → 4.45x。',
  foot2:'规则阈值：Pons 日收入 7 日均 &lt; $10 万＝离场，&lt; $15 万＝暂停加仓；StonkFun &lt; $20 万＝离场，&lt; $28 万＝暂停加仓。本面板仅为研究工具，不构成投资建议。'
},
en:{
  docTitle:'Pons · StonkFun Revenue & Buyback Monitor',
  h1:'Pons · StonkFun Revenue & Buyback Monitor',
  secRules:'Rule engine · entry & stop signals',
  secChart:'Trends',
  secTable:'Daily detail (last 20 days)',
  secGuide:'How to read every number',
  refresh:'Refresh',
  loading:'Loading…', fetching:'Fetching…',
  live:'● Live data', offline:'● Snapshot (offline)', liveAt:'● Live · ',
  updatedAt:'Updated ',
  burned:'burned ', mcap:'Mcap ', fromAth:'From ATH ',
  perDay:' /day',
  kAvg7:'7-day avg revenue', kMom:'vs prior 7 days', kLast:'Latest daily revenue', kPeak:'Peak daily revenue',
  kPs7:'Annualized P/S (7d)', kPs30:'Annualized P/S (30d)', kFromPeak:'Below peak revenue',
  kBurnYield:'Buyback yield (ann.)', kBurn7:'Buyback, last 7d', kBurnForce:'Buyback vs volume',
  kVol24:'24h volume', kTurnover:'Daily turnover',
  tipPs:'Market cap ÷ annualized revenue — lower is cheaper', tipPs30:'P/S using 30-day average revenue (smoother)',
  tipBurnYield:'7d buyback × 52 ÷ mcap — % of mcap repurchased per year',
  tipBurnForce:'7d buyback ÷ 7d volume — ≥5% is a real bid', tipVol:'24-hour trading volume',
  stBad:'Revenue fell below the exit line — step aside', stWarn:'Revenue below the warning line — no new buys',
  stMom:'Revenue dropped sharply QoQ — watch only', stUp:'Revenue stabilising — consider scaling in',
  stFlat:'Revenue flat — hold and watch',
  lvOk:'OK', lvWarn:'Watch', lvBad:'Alert',
  legendOk:'Conditions met, hold as planned', legendWarn:'Near a threshold — pause buys, watch closely',
  legendBad:'Rule triggered — read the advice under each row',
  cmpHead:(n,m)=>n+'/'+m+' rules OK',
  verdict:'', verdictTie:'even', verdictNoData:'not enough data', verdictWin:t=>t,
  advice:'Action: ',
  vFloor:'thicker buffer', vMom:'more resilient', vBurn:'more active', vBurnpower:'higher buyback share', vPs:'cheaper',
  dimFloorL:'Revenue vs stop-loss line', dimFloorH:'7-day avg below the exit line = get out',
  dimMomL:'Revenue change vs prior week', dimMomH:'A sustained decline is the earliest warning',
  dimBurnL:'Is the buyback still running?', dimBurnH:'Buyback stopping = the most important exit signal',
  dimBpL:'Can the buyback support price?', dimBpH:'Buyback ÷ volume — under 2% is noise',
  dimPsL:'Is it cheap? (P/S)', dimPsH:'Lower is cheaper',
  dimFloorS:'Stop', dimMomS:'MoM', dimBurnS:'Burn', dimBpS:'Force', dimPsS:'P/S',
  conclusion:'Bottom line',
  priority:t=>'Prefer '+t+' (lower P/S, thicker buffer); wait for the other one to stop bleeding before adding.',
  priorityNone:'Not enough data for an allocation call.',
  actFloorBad:'Below the exit line: trim in tranches or exit, do not average down',
  actFloorWarn:'Below the warning line: no new buys, watch this line daily',
  actFloorOk:v=>'Sits '+v+'% above the warning line — keep holding',
  sFloor:(a,b,c)=>'7-day avg '+a+'/day　·　exit '+b+'　·　warning '+c,
  actMomBad:'Down more than 25% QoQ: pause all buying until 3 straight up days',
  actMomWarn:'Weakening QoQ: watch only, no adds',
  actMomUp:'Recovering QoQ: consider scaling in',
  actMomFlat:'Flat QoQ: keep current position',
  sMom:(d)=>'This week vs last '+d+'%　·　trigger −25%',
  actBurnOff:'Buyback has stopped: reduce first, only add after it resumes',
  actBurnOn:v=>'Buyback running: 7d buyback ≈ '+v+'% of revenue',
  sBurn:(a,b)=>'7d buyback '+a+'　·　'+b,
  actBpNone:'No volume data — cannot judge buyback impact',
  actBpOk:v=>'Buyback is '+v+'% of volume: heavy enough to support price',
  actBpWarn:v=>'Buyback is '+v+'% of volume: cushions drops but cannot reverse them',
  actBpBad:v=>'Buyback is only '+v+'% of volume: too small to support the price',
  sBp:(a,b)=>'7d buyback '+a+' ÷ 7d volume '+b+'　·　≥5% is a real bid',
  actPsNone:'No revenue data — cannot value it yet',
  actPsCheap:v=>v+'x is cheap: thick buffer, scale in gradually',
  actPsFair:v=>v+'x is fair: hold and watch, do not chase',
  actPsDear:v=>v+'x is rich: do not chase, wait for a dip or revenue growth',
  sPs:v=>'Annualized P/S (7d) '+v+'　·　<1.5x cheap · >4x rich　·　pump.fun 4.45x',
  tabRev:'Daily revenue', tabRev7:'7-day average', tabCum:'Cumulative buyback', tabPrice:'Price (rebased)',
  base100:'Base 100', start100:'start = 100', stopLoss:t=>t+' stop-loss',
  cumName:n=>n+' cumulative buyback (window)',
  thDate:'Date', thRev:'Revenue', thBurn:'Buyback', thPrice:'Price', thAvg7:'7-day avg',
  gPsT:'Annualized P/S — what you pay for one year of revenue',
  gPsF:'P/S = market cap ÷ (daily revenue × 365)',
  gPsL:'The lower the number, the cheaper it is: how many years of today\'s earnings you are paying for. It separates "is the business expensive" from "is the token price high".',
  gPsCap:t=>'Worked example ('+t+')',
  gPsLine:(mc,avg,year,ps,yrs)=>'Market cap '+mc+'　÷　(7-day avg '+avg+'/day × 365 = '+year+')'+
      '<br>= <b>'+ps+'</b><br>→ Revenue held flat, you pay 1 year of revenue for <b>'+yrs+' years</b> to break even',
  gPsCompare:(name,mc,year,ps,cheaper,gap)=>'vs '+name+': '+mc+' ÷ '+year+' = <b>'+ps+'</b>'+(gap?('　→　'+cheaper+' is <b>'+gap+'× cheaper</b>'):''),
  gPsBands:[['&lt; 1.5x','g-ok','Cheap — thick buffer, scale in'],['1.5x – 4x','','Fair — hold, do not chase'],['&gt; 4x','g-warn','Rich — needs revenue growth to grow into']],
  gPsNote:'Note: P/S only describes "now", not the future. When revenue is falling, a cheap-looking P/S can be an illusion — the denominator shrinks next.',
  g730T:'Why read P/S on both 7d and 30d',
  g730F:'7-day = latest speed　·　30-day = one-month average',
  g730L:'The 7-day is sensitive and spots turning points first; the 30-day is smooth and immune to one-off spikes. The wider the gap between them, the more violent the revenue swing — that gap is exactly what marks a turning point.',
  g730Note:'Rule of thumb: 7d P/S well above 30d P/S = revenue falling; the reverse = revenue rising.',
  psLine:(p,ps7,ps30,div,txt)=>p+': 7d <b>'+ps7+'</b> vs 30d <b>'+ps30+'</b>　→　'+div+'× apart<br><span class="%C%">↳ '+txt+'</span>',
  divFast:(pct)=>({c:'g-bad', t:'Revenue is falling fast — the last 7 days are only '+pct+'% of the monthly average'}),
  divSoft:()=>({c:'g-warn', t:'Below the monthly average and softening'}),
  divUp:(n)=>({c:'', t:'Running '+n+'× above the monthly average and accelerating'}),
  divFlat:()=>({c:'', t:'In line with the monthly average, steady'}),
  gBpT:'Buyback force — does the buyback actually matter?',
  gBpF:'Buyback force = 7-day buyback ÷ 7-day volume',
  gBpL:'Do not look at how many dollars were bought back — look at the share of market volume. However big the bid, if tens of times more supply is changing hands, it will not move the price. This is the only meaningful way to judge whether a buyback can support price.',
  gBpBands:[['≥ 5%','g-ok','Heavy enough to genuinely support price'],['2% – 5%','g-warn','Slows declines, cannot reverse them'],['&lt; 2%','g-bad','A drop in the bucket']],
  gBpNote:'Classic case: why do some tokens keep falling while buying back? Because the buyback is tiny relative to volume — it just provides liquidity to sellers.',
  gBpLine:(a,x,b,y)=>a+': 7d buyback '+x+' ÷ 7d volume '+y+' = <b>'+b+'</b>',
  gBpFoot:'↑ Both are below 2% — the direct reason a buyback does not lift the price',
  gToT:'Turnover & buyback yield',
  gToF:'Turnover = 24h volume ÷ mcap　·　Buyback yield = 7d buyback × 52 ÷ mcap',
  gToL:'Turnover shows how "active" the float is: the higher it is, the more short-term money is in it, the bigger the swings, and the less a buyback matters. Buyback yield tells you what percentage of the market cap would be repurchased in a year at the current pace.',
  gToBands:[['Turnover &lt; 3%','g-ok','Stable float, buyback works well'],['Turnover 3% – 8%','g-warn','Fairly active, buyback diluted'],['Turnover &gt; 8%','g-bad','High churn, buyback mostly diluted']],
  gToNote:'Important: a high buyback yield does not guarantee a higher price. It assumes revenue holds; if revenue falls, the number shrinks with it.',
  gToLine:(a,ta,ya,b,tb,yb)=>'Now: '+a+' turnover <b>'+ta+'/day</b> · buyback yield <b>'+ya+'</b><br>　　　'+b+' turnover <b>'+tb+'/day</b> · buyback yield <b>'+yb+'</b>',
  gToFoot:'More than 10% of the float trades every day → short-term money dominates and dilutes the buyback',
  gMomT:'Revenue QoQ — the earliest warning',
  gMomF:'Revenue QoQ = last 7 days vs the 7 days before',
  gMomL:'This is the first indicator to flash. The buyback sits downstream of revenue: revenue ↓ → buyback ↓ → bid ↓ → price loses support. Watch revenue to get ahead of the buyback.',
  gMomBands:[['&gt; −15%','g-ok','Stable — keep position'],['−15% ~ −25%','g-warn','Weakening — watch, do not add'],['&lt; −25%','g-bad','Sharp drop — pause all buying']],
  gMomFoot:'Both are near −35% → past the −25% trigger, which means: pause all buying',
  foot1:'Sources: revenue/buyback = DefiLlama (fees / revenue / holders-revenue APIs); volume & market cap = CoinGecko. Pons revenue = protocol-retained revenue (creator and Uniswap splits already deducted); StonkFun revenue = its retained trading fees (fees = revenue). Annualized P/S = mcap ÷ (daily revenue × 365), lower is cheaper. Reference point: pump.fun 30-day revenue $45.28M, mcap $2.46B → 4.45x.',
  foot2:'Thresholds: Pons 7-day avg revenue &lt; $100K = exit, &lt; $150K = pause buying; StonkFun &lt; $200K = exit, &lt; $280K = pause buying. Research tool only — not investment advice.'
}
};
let LANG=(function(){ try{ var s=localStorage.getItem('pons-lang'); if(s==='zh'||s==='en') return s; }catch(e){}
  return ((navigator.language||navigator.userLanguage||'').toLowerCase().indexOf('zh')===0)?'zh':'en'; })();
function t(k){
  var v=I18N[LANG][k];
  if(v===undefined) v=I18N.zh[k];
  return v===undefined? k : v;
}
function tx(v){ return (v && typeof v==='object')? (v[LANG] || v.zh) : v; }
function setLang(l){
  LANG = (l==='en')?'en':'zh';
  try{ localStorage.setItem('pons-lang',LANG); }catch(e){}
  document.documentElement.lang = (LANG==='zh'?'zh-CN':'en');
  document.title = t('docTitle');
  var b=document.getElementById('lbtn');
  if(b) b.textContent = (LANG==='zh'?'EN':'中文');
  renderStatic(); renderAll();
}
function cycleLang(){ setLang(LANG==='zh'?'en':'zh'); }

const PROJECTS = [
  { id:'pons', seriesKey:'pons', name:'Pons', ticker:'PONS', chain:'Robinhood Chain',
    color:'#8b7cff', supply:682770000, maxSupply:1000000000, burned:317230421,
    mcapFallback:365777975,
    burnEvent:{zh:'80% 协议费用 TWAP 回购销毁（官方注明尚未 immutable）',
               en:'80% of protocol fees → TWAP buyback &amp; burn (not immutable yet)'},
    danger:100000, warn:150000, baseline:220000 },
  { id:'stonkfun', seriesKey:'stonkfun', name:'StonkFun', ticker:'STONK', chain:'Solana',
    color:'#2ee6a8', supply:814583323, maxSupply:1000000000, burned:185416677,
    mcapFallback:207358628,
    burnEvent:{zh:'约 60% 平台收入公开市场回购销毁 + 生态飞轮',
               en:'~60% of platform revenue → open-market buyback &amp; burn + ecosystem flywheel'},
    danger:200000, warn:280000, baseline:34400 }
];

const CG_IDS = {pons:'pons', stonkfun:'stonk-3'};
const LLAMA_IDS = {pons:'robinhood:0x39dBED3a2bd333467115dE45665cC57F813C4571',
                   stonkfun:'solana:6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx'};
let DATA = JSON.parse(JSON.stringify(BUNDLE));
let MODE = 'rev7';

/* ---------- utils ---------- */
const fmtU = v => {
  if (v === null || v === undefined || isNaN(v)) return '—';
  const a = Math.abs(v);
  if (a >= 1e9) return '$' + (v/1e9).toFixed(2) + 'B';
  if (a >= 1e6) return '$' + (v/1e6).toFixed(2) + 'M';
  if (a >= 1e3) return '$' + (v/1e3).toFixed(1) + 'K';
  return '$' + v.toFixed(0);
};
const fmtN = (v,d=2) => (v===null||isNaN(v))?'—':v.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const dayKey = ts => new Date(ts*1000).toISOString().slice(0,10);
const toMap = arr => { const m={}; (arr||[]).forEach(([ts,v])=>{ const k=dayKey(ts); m[k]=(m[k]||0)+v; }); return m; };
const sortedKeys = m => Object.keys(m).sort();
const smaAt = (vals,i,n) => { if (i<n-1) return null; let s=0; for(let j=i-n+1;j<=i;j++) s+=vals[j]; return s/n; };

/* ---------- build unified daily table ---------- */
function build(){
  const rev = {}, hold = {}, fee = {}, price = {};
  PROJECTS.forEach(p=>{
    rev[p.id]  = toMap(DATA.series[p.seriesKey+'.dailyRevenue']);
    hold[p.id] = toMap(DATA.series[p.seriesKey+'.dailyHoldersRevenue']);
    fee[p.id]  = toMap(DATA.series[p.seriesKey+'.dailyFees']);
    price[p.id]= toMap(DATA.priceSeries[p.id]);
  });
  const all = new Set();
  Object.values(rev).forEach(m=>Object.keys(m).forEach(k=>all.add(k)));
  Object.values(price).forEach(m=>Object.keys(m).forEach(k=>all.add(k)));
  const days = [...all].sort();
  const rows = days.map(d=>{
    const r = { date:d };
    PROJECTS.forEach(p=>{
      r[p.id+'_rev']   = rev[p.id][d]  ?? null;
      r[p.id+'_hold']  = hold[p.id][d] ?? null;
      r[p.id+'_fee']   = fee[p.id][d]  ?? null;
      r[p.id+'_price'] = price[p.id][d] ?? null;
    });
    return r;
  });
  return rows;
}

/* ---------- stats ---------- */
function stats(rows, p){
  const rev = rows.map(r=>r[p.id+'_rev']).map(v=>v??0);
  const hold= rows.map(r=>r[p.id+'_hold']).map(v=>v??0);
  const idxValid = rows.map((r,i)=>r[p.id+'_rev']!==null?i:-1).filter(i=>i>=0);
  const last = idxValid[idxValid.length-1];
  const sum = (a,b)=>{ let s=0,n=0; for(let i=Math.max(0,a);i<=b;i++){ if(rows[i][p.id+'_rev']!==null){s+=rev[i];n++;} } return {s,n}; };
  const w7  = sum(last-6, last), w7p = sum(last-13, last-7), w30 = sum(last-29, last);
  const avg7 = w7.n? w7.s/w7.n : 0, avg7p = w7p.n? w7p.s/w7p.n : 0, avg30 = w30.n? w30.s/w30.n : 0;
  let holdSum7=0; for(let i=Math.max(0,last-6);i<=last;i++) holdSum7 += hold[i]||0;
  const peak = Math.max(...idxValid.map(i=>rev[i]));
  const peakDay = rows[idxValid[idxValid.findIndex(i=>rev[i]===peak)]].date;
  const mcap = DATA.meta[p.id]?.mcap || p.mcapFallback;
  const priceNow = DATA.price?.[p.id] ?? rows[last][p.id+'_price'];
  const priceArr = rows.map(r=>r[p.id+'_price']).filter(v=>v!==null);
  const ath = priceArr.length? Math.max(...priceArr) : null;
  const retrace = avg7p? (avg7-avg7p)/avg7p : 0;
  const win = idxValid.slice(-14).map(i=>({x:i, y:Math.log(Math.max(rev[i],1))}));
  let slope=0;
  if(win.length>3){
    const n=win.length, mx=win.reduce((a,b)=>a+b.x,0)/n, my=win.reduce((a,b)=>a+b.y,0)/n;
    let num=0,den=0; win.forEach(w=>{num+=(w.x-mx)*(w.y-my);den+=(w.x-mx)**2;});
    slope = num/den;
  }
  const mk = (DATA.market || {})[p.id] || {};
  const vol24 = mk.vol24h || null;
  const turnover  = (vol24 && mcap) ? vol24/mcap : null;
  const burnForce = (vol24 && vol24>0) ? holdSum7/(vol24*7) : null;
  const burnYield = mcap>0 ? holdSum7/mcap*52 : null;
  return {last, avg7, avg7p, avg30, holdSum7, peak, peakDay, lastRev:rev[last],
    psv: priceNow, mcap, ps7: avg7>0? mcap/(avg7*365):null, ps30: avg30>0? mcap/(avg30*365):null,
    retrace, slope, ath, priceArr, burnPct: p.burned/p.maxSupply, rows,
    vol24, volChange: (mk.change24h ?? null), turnover, burnForce, burnYield};
}

/* ---------- 静态文案 ---------- */
function renderStatic(){
  document.getElementById('h1t').textContent = t('h1');
  document.getElementById('st-rules').textContent = t('secRules');
  document.getElementById('st-chart').textContent = t('secChart');
  document.getElementById('st-table').textContent = t('secTable');
  document.getElementById('st-guide').textContent = t('secGuide');
  document.getElementById('btnRefresh').textContent = t('refresh');
  document.getElementById('rule-legend').innerHTML =
      '<span class="lg"><span class="tag ok">'+t('lvOk')+'</span>'+t('legendOk')+'</span>'+
      '<span class="lg"><span class="tag warn">'+t('lvWarn')+'</span>'+t('legendWarn')+'</span>'+
      '<span class="lg"><span class="tag bad">'+t('lvBad')+'</span>'+t('legendBad')+'</span>';
}

/* ---------- render cards ---------- */
function renderCards(){
  const rows = build();
  const el = document.getElementById('cards');
  el.innerHTML = PROJECTS.map(p=>{
    const s = stats(rows,p);
    const d = (s.avg7-s.avg7p)/(s.avg7p||1);
    const status = s.avg7 < p.danger ? ['bad',t('stBad')]
                 : s.avg7 < p.warn   ? ['warn',t('stWarn')]
                 : (d<-0.25)         ? ['warn',t('stMom')]
                 : (d>0.05)          ? ['good',t('stUp')]
                 : ['good',t('stFlat')];
    const pct = v => v===null||isNaN(v)? '—' : (v>=0?'+':'')+(v*100).toFixed(1)+'%';
    const dd = s.ath? (s.psv-s.ath)/s.ath : null;
    const stTxt = status[0]==='bad'? ('● '+t('lvBad')) : status[0]==='warn'? ('● '+t('lvWarn')) : ('● '+t('lvOk'));
    return `<div class="card">
      <div class="proj-head">
        <div>
          <div class="proj-name"><span class="dot" style="background:${p.color};color:${p.color}"></span>${p.name}<span class="tick">${p.ticker}</span></div>
          <div style="color:var(--mut);font-size:11.5px;margin-top:3px">${p.chain} · ${t('burned')}${(s.burnPct*100).toFixed(1)}% (${fmtN(p.burned/1e6,1)}M ${p.ticker})</div>
        </div>
        <div class="price">
          <div class="p mono" id="px-${p.id}">$${fmtN(s.psv,4)}</div>
          <div class="m">${t('mcap')}${fmtU(s.mcap)}</div>
          <div class="pill ${dd>=0?'up':'down'}">${t('fromAth')}${pct(dd)}</div>
        </div>
      </div>
      <div class="kv">
        <div><div class="k">${t('kAvg7')}</div><div class="v">${fmtU(s.avg7)}<small>${t('perDay')}</small></div></div>
        <div><div class="k">${t('kMom')}</div><div class="v" style="color:${d>=0?'var(--up)':'var(--down)'}">${pct(d)}</div></div>
        <div><div class="k">${t('kLast')}</div><div class="v">${fmtU(s.lastRev)}</div></div>
        <div><div class="k">${t('kPeak')}</div><div class="v">${fmtU(s.peak)}</div></div>
        <div title="${t('tipPs')}"><div class="k">${t('kPs7')} <span class="qi">?</span></div><div class="v">${s.ps7?fmtN(s.ps7,2)+'x':'—'}</div></div>
        <div title="${t('tipPs30')}"><div class="k">${t('kPs30')} <span class="qi">?</span></div><div class="v">${s.ps30?fmtN(s.ps30,2)+'x':'—'}</div></div>
        <div><div class="k">${t('kFromPeak')}</div><div class="v" style="color:var(--down)">${s.peak?((s.lastRev-s.peak)/s.peak*100).toFixed(0)+'%':'—'}</div></div>
        <div title="${t('tipBurnYield')}"><div class="k">${t('kBurnYield')} <span class="qi">?</span></div><div class="v">${s.burnYield!==null?fmtN(s.burnYield*100,0)+'%':'—'}</div></div>
        <div><div class="k">${t('kBurn7')}</div><div class="v">${fmtU(s.holdSum7)}</div></div>
        <div title="${t('tipBurnForce')}"><div class="k">${t('kBurnForce')} <span class="qi">?</span></div><div class="v" style="color:${s.burnForce===null?'inherit':s.burnForce>=0.05?'var(--up)':s.burnForce>=0.02?'var(--warn)':'var(--down)'}">${s.burnForce===null?'—':(s.burnForce*100).toFixed(2)+'%'}</div></div>
        <div title="${t('tipVol')}"><div class="k">${t('kVol24')}</div><div class="v">${fmtU(s.vol24)}</div></div>
        <div title="${t('tipVol')}"><div class="k">${t('kTurnover')} <span class="qi">?</span></div><div class="v">${s.turnover!==null?(s.turnover*100).toFixed(1)+'%':'—'}</div></div>
      </div>
      <div class="status ${status[0]}"><span class="lbl">${stTxt}</span><span>${status[1]}</span></div>
    </div>`;
  }).join('');
}

/* ---------- rules ---------- */
function dims(){ return [
  {key:'floor',     short:t('dimFloorS'), label:t('dimFloorL'), hint:t('dimFloorH')},
  {key:'mom',       short:t('dimMomS'),   label:t('dimMomL'),   hint:t('dimMomH')},
  {key:'burn',      short:t('dimBurnS'),  label:t('dimBurnL'),  hint:t('dimBurnH')},
  {key:'burnpower', short:t('dimBpS'),    label:t('dimBpL'),    hint:t('dimBpH')},
  {key:'ps',        short:t('dimPsS'),    label:t('dimPsL'),    hint:t('dimPsH')}
];}

function ruleItems(rows, p){
  const s = stats(rows,p);
  const d = (s.avg7-s.avg7p)/(s.avg7p||1);
  const ps = s.ps7;
  const it = {};
  let lvl, act;

  if(s.avg7 < p.danger){ lvl='bad'; act=t('actFloorBad'); }
  else if(s.avg7 < p.warn){ lvl='warn'; act=t('actFloorWarn'); }
  else { lvl='ok'; act=t('actFloorOk')(fmtN((s.avg7-p.warn)/p.warn*100,0)); }
  it.floor = {level:lvl, act, score:(s.avg7-p.danger)/p.danger,
    s:t('sFloor')(fmtU(s.avg7), fmtU(p.danger), fmtU(p.warn))};

  if(d < -0.25){ lvl='bad'; act=t('actMomBad'); }
  else if(d < -0.15){ lvl='warn'; act=t('actMomWarn'); }
  else if(d > 0.05){ lvl='ok'; act=t('actMomUp'); }
  else { lvl='ok'; act=t('actMomFlat'); }
  it.mom = {level:lvl, act, score:d, s:t('sMom')((d*100).toFixed(1))};

  const burnRatio = s.avg7>0? s.holdSum7/(s.avg7*7) : 0;
  if(s.holdSum7 <= 0){ lvl='bad'; act=t('actBurnOff'); }
  else { lvl='ok'; act=t('actBurnOn')((burnRatio*100).toFixed(0)); }
  it.burn = {level:lvl, act, score:burnRatio,
    s:t('sBurn')(fmtU(s.holdSum7), tx(p.burnEvent))};

  const bf = s.burnForce;
  if(bf===null||!isFinite(bf)){ lvl='warn'; act=t('actBpNone'); }
  else if(bf >= 0.05){ lvl='ok';   act=t('actBpOk')((bf*100).toFixed(1)); }
  else if(bf >= 0.02){ lvl='warn'; act=t('actBpWarn')((bf*100).toFixed(1)); }
  else {               lvl='bad';  act=t('actBpBad')((bf*100).toFixed(2)); }
  it.burnpower = {level:lvl, act, score:(bf===null||!isFinite(bf))? null : bf,
    s:t('sBp')(fmtU(s.holdSum7), fmtU(s.vol24? s.vol24*7 : null))};

  if(ps===null||!isFinite(ps)){ lvl='warn'; act=t('actPsNone'); }
  else if(ps < 1.5){ lvl='ok'; act=t('actPsCheap')(fmtN(ps,2)); }
  else if(ps <= 4){ lvl='ok'; act=t('actPsFair')(fmtN(ps,2)); }
  else { lvl='warn'; act=t('actPsDear')(fmtN(ps,2)); }
  it.ps = {level:lvl, act, score:(ps===null||!isFinite(ps))? null : -ps,
    s:t('sPs')((ps===null||!isFinite(ps))?'—':fmtN(ps,2)+'x')};

  return {s, d, it, ok:Object.values(it).filter(x=>x.level==='ok').length};
}

function renderRules(){
  const rows = build();
  const A = PROJECTS[0], B = PROJECTS[1];
  const ra = ruleItems(rows, A), rb = ruleItems(rows, B);
  const DIMS = dims();
  const VKEY={floor:'vFloor',mom:'vMom',burn:'vBurn',burnpower:'vBurnpower',ps:'vPs'};

  const verdict = {};
  DIMS.forEach(dim=>{
    const x = ra.it[dim.key].score, y = rb.it[dim.key].score;
    if(x===null||y===null||!isFinite(x)||!isFinite(y)){ verdict[dim.key]={text:t('verdictNoData'), tie:true}; return; }
    const rel = Math.abs(x-y)/(Math.abs(x)+Math.abs(y)||1);
    if(rel < 0.10){ verdict[dim.key]={text:t('verdictTie'), tie:true}; return; }
    const w = x>y ? A : B;
    verdict[dim.key] = {text:t('verdictWin')(w.ticker+' '+t(VKEY[dim.key])), tie:false};
  });
  const card = (p, item) =>
    `<div class="rule ${item.level}">
       <div class="rtop"><span class="tag ${item.level}">${t(item.level==='ok'?'lvOk':item.level==='warn'?'lvWarn':'lvBad')}</span><span class="pname" style="color:${p.color}">● ${p.name}</span></div>
       <div class="s">${item.s}</div>
       <div class="act ${item.level}">${t('advice')}${item.act}</div>
     </div>`;

  const head = `<div class="cmp-head">
      <div class="col"><span class="dot" style="background:${A.color};color:${A.color}"></span>${A.name}<span class="tick">${A.ticker}</span><span class="cnt">${t('cmpHead')(ra.ok, Object.keys(ra.it).length)}</span></div>
      <div class="col"><span class="dot" style="background:${B.color};color:${B.color}"></span>${B.name}<span class="tick">${B.ticker}</span><span class="cnt">${t('cmpHead')(rb.ok, Object.keys(rb.it).length)}</span></div>
    </div>`;

  const body = DIMS.map((dim,i)=>{
    const v = verdict[dim.key];
    return `<div class="cmp-row">
      <div class="cmp-label"><b>${i+1}. ${dim.label}</b><span class="hint">${dim.hint}</span>
        <span class="verdict${v.tie?'':' win'}">${t('verdict')}${v.text}</span></div>
      <div class="cmp-pair">${card(A, ra.it[dim.key])}${card(B, rb.it[dim.key])}</div>
    </div>`;
  }).join('');

  const summary = DIMS.map(d=>`${d.short} ${verdict[d.key].text}`).join('　·　');
  const cheaper = (ra.s.ps7 && rb.s.ps7) ? (ra.s.ps7 < rb.s.ps7 ? A : B) : null;
  const action = cheaper ? t('priority')(cheaper.ticker) : t('priorityNone');

  document.getElementById('rules').innerHTML = head + body +
    `<div class="cmp-row">
      <div class="cmp-label"><b>${t('conclusion')}</b></div>
      <div class="rule sum"><div class="s">${summary}</div><div class="act">${action}</div></div>
    </div>`;
}

/* ---------- chart ---------- */
function tabs(){ return [
  {id:'rev',  label:t('tabRev')},
  {id:'rev7', label:t('tabRev7')},
  {id:'cum',  label:t('tabCum')},
  {id:'price',label:t('tabPrice')}
];}
function renderTabs(){
  document.getElementById('tabs').innerHTML = tabs().map(x=>
    `<div class="tab ${x.id===MODE?'on':''}" onclick="MODE='${x.id}';renderTabs();renderChart()">${x.label}</div>`).join('');
}
function renderChart(){
  const rows = build();
  const N = MODE==='price'? 90 : 60;
  const sub = rows.slice(-N);
  const svg = document.getElementById('chart');
  const W=1200,H=340, P={l:64,r:16,t:14,b:30};
  const iw = W-P.l-P.r, ih = H-P.t-P.b;
  let series=[], thresholds=[], yfmt = fmtU;

  if(MODE==='price'){
    let base = {};
    PROJECTS.forEach(p=>{
      const first = sub.find(r=>r[p.id+'_price']!==null);
      base[p.id] = first? first[p.id+'_price'] : null;
    });
    series = PROJECTS.map(p=>({name:p.name,color:p.color,
      pts: sub.map((r,i)=>({i, v: r[p.id+'_price']!==null&&base[p.id]? r[p.id+'_price']/base[p.id]*100 : null}))}));
    yfmt = v => fmtN(v,0);
    thresholds=[{v:100,label:'基准 100',color:'#4b5468'}];
  } else if(MODE==='cum'){
    let cum = {}; PROJECTS.forEach(p=>cum[p.id]=0);
    const allRows = rows;
    const start = allRows.length - sub.length;
    series = PROJECTS.map(p=>{
      let c=0; const pts=[];
      allRows.forEach((r,gi)=>{ if(gi>=start) pts.push({i:gi-start, v:(c+= (r[p.id+'_hold']||0))}); });
      const first = pts.length? pts[0].v : 0;
      return {name:t('cumName')(p.name), color:p.color, pts: pts.map(x=>({i:x.i, v:x.v-first}))};
    });
  } else {
    series = PROJECTS.map(p=>{
      const vals = sub.map(r=>r[p.id+'_rev']);
      const filled = vals.map((v,i)=> v===null? null : (MODE==='rev7'? smaAt(vals.map(x=>x??0), i, 7) : v));
      return {name:p.name, color:p.color, pts: filled.map((v,i)=>({i, v}))};
    });
    PROJECTS.forEach(p=>thresholds.push({v:p.danger,label:t('stopLoss')(p.ticker),color:p.colorDim}));
  }

  const allV = series.flatMap(s=>s.pts.map(p=>p.v)).filter(v=>v!==null&&isFinite(v));
  let max = Math.max(...allV), min = MODE==='price'? Math.min(...allV) : 0;
  if(MODE!=='price'){ max = Math.max(max, ...thresholds.map(t=>t.v||0)); }
  const pad = (max-min)*0.08 || 1;
  max += pad; min = MODE==='price'? min-pad*1.5 : 0;
  const X = i => P.l + (sub.length<=1?0:(i/(sub.length-1))*iw);
  const Y = v => P.t + ih - ((v-min)/(max-min))*ih;

  let g='';
  const TICKS=5;
  for(let k=0;k<=TICKS;k++){
    const v = min + (max-min)*k/TICKS, y = Y(v);
    g += `<line x1="${P.l}" x2="${W-P.r}" y1="${y}" y2="${y}" style="stroke:var(--grid)"/>`;
    g += `<text x="${P.l-9}" y="${y+4}" style="fill:var(--mut2)" font-size="11" text-anchor="end" font-family="ui-monospace,monospace">${yfmt(v)}</text>`;
  }
  const step = Math.max(1, Math.round(sub.length/7));
  sub.forEach((r,i)=>{ if(i%step===0||i===sub.length-1){
    g += `<text x="${X(i)}" y="${H-9}" style="fill:var(--mut2)" font-size="10.5" text-anchor="middle">${r.date.slice(5)}</text>`;
  }});
  thresholds.forEach(th=>{
    if(th.v===undefined||th.v===null) return;
    const y=Y(th.v);
    g += `<line x1="${P.l}" x2="${W-P.r}" y1="${y}" y2="${y}" style="stroke:${th.color}" class="warnline"/>`;
    g += `<text x="${W-P.r-4}" y="${y-5}" style="fill:${th.color}" font-size="10.5" text-anchor="end">${th.label}</text>`;
  });
  series.forEach(s=>{
    let d='', started=false;
    s.pts.forEach(pt=>{
      if(pt.v===null||!isFinite(pt.v)){ started=false; return; }
      d += (started?' L':'M') + X(pt.i).toFixed(1) + ' ' + Y(pt.v).toFixed(1);
      started=true;
    });
    g += `<path d="${d}" fill="none" style="stroke:${s.color}" stroke-width="2" stroke-linejoin="round"/>`;
    const lastPt = [...s.pts].reverse().find(p=>p.v!==null&&isFinite(p.v));
    if(lastPt){ g += `<circle cx="${X(lastPt.i)}" cy="${Y(lastPt.v)}" r="3.5" style="fill:${s.color}"/>`; }
  });
  svg.innerHTML = g;
  document.getElementById('legend').innerHTML = series.map(s=>
    `<span><i style="background:${s.color}"></i>${s.name}</span>`).join('') +
    (MODE==='price'?'<span style="color:var(--mut2)">'+t('start100')+'</span>':'');

  const tip = document.getElementById('tip');
  svg.onmousemove = e => {
    const r = svg.getBoundingClientRect();
    const relX = (e.clientX - r.left)/r.width*W;
    const i = Math.round((relX-P.l)/iw*(sub.length-1));
    if(i<0||i>=sub.length){ tip.style.display='none'; return; }
    const row = sub[i];
    let html = `<div class="d">${row.date}</div>`;
    series.forEach(s=>{
      const pt = s.pts.find(p=>p.i===i);
      if(pt && pt.v!==null && isFinite(pt.v))
        html += `<div class="r"><span style="color:${s.color}">${s.name.split(' cumulative')[0]}</span><b>${MODE==='price'?fmtN(pt.v,1):fmtU(pt.v)}</b></div>`;
    });
    tip.innerHTML = html;
    tip.style.display='block';
    const px = X(i)/W*r.width;
    tip.style.left = Math.min(px+14, r.width-190)+'px';
    tip.style.top = (e.clientY - r.top - 20)+'px';
  };
  svg.onmouseleave = ()=> tip.style.display='none';
}

/* ---------- table ---------- */
function renderTable(){
  const all  = build();
  const rows = all.slice(-20).reverse();
  const mx = {};
  ['pons_rev','pons_hold','stonkfun_rev','stonkfun_hold'].forEach(k=>{
    mx[k] = Math.max(1, ...rows.map(r=>+r[k]||0));
  });
  const w = (k,v)=> (!v||!isFinite(v)) ? 0 : Math.max(2, Math.round(v/mx[k]*100));
  const gc = p => p.id==='pons' ? 'pons' : 'stonk';
  const st = {}; PROJECTS.forEach(p=>{ st[p.id]=stats(all,p); });
  const priceTd = v => `<td class="mono v-px">${v?'$'+fmtN(v,4):'—'}</td>`;
  const dlt = (cur,prev)=>{
    if(!cur||!prev) return '';
    const d=(cur-prev)/prev;
    if(!isFinite(d)||Math.abs(d)<0.005) return '<span class="dlt flat">–</span>';
    return '<span class="dlt '+(d>0?'up':'dn')+'">'+(d>0?'▲':'▼')+Math.abs(d*100).toFixed(0)+'%</span>';
  };
  const cell = (cl,k,v,extra)=> `<td class="mono ${cl}"><span class="bar" style="--w:${w(k,v)}%"></span><span class="v">${fmtU(v)}</span>${extra||''}</td>`;

  document.getElementById('tbl').querySelector('thead').innerHTML =
    `<tr class="grp"><th class="c-date" rowspan="2">${t('thDate')}</th>`+
    `<th class="g-pons" colspan="3">PONS <span style="opacity:.45;font-weight:500;letter-spacing:0">· Robinhood</span></th>`+
    `<th class="g-stonk" colspan="3">STONK <span style="opacity:.45;font-weight:500;letter-spacing:0">· Solana</span></th></tr>`+
    `<tr class="sub"><th class="g-pons">${t('thRev')}</th><th class="g-pons">${t('thBurn')}</th><th class="g-pons">${t('thPrice')}</th>`+
    `<th class="g-stonk">${t('thRev')}</th><th class="g-stonk">${t('thBurn')}</th><th class="g-stonk">${t('thPrice')}</th></tr>`;

  const sum = `<tr class="sum"><td class="mono c-date">${t('thAvg7')}</td>`+
    PROJECTS.map(p=>{
      const s=st[p.id], g='g-'+gc(p);
      return cell(g+' v-rev', p.id+'_rev',  s.avg7) +
             cell(g+' v-bb',  p.id+'_hold', s.holdSum7/7) +
             priceTd(s.psv);
    }).join('') + `</tr>`;

  const body = rows.map((r,i)=>{
    const prev = rows[i+1] || {};
    return `<tr><td class="mono c-date">${r.date}</td>`+
      cell('g-pons v-rev','pons_rev',r.pons_rev, dlt(r.pons_rev, prev.pons_rev))+
      cell('g-pons v-bb','pons_hold',r.pons_hold)+
      priceTd(r.pons_price)+
      cell('g-stonk v-rev','stonkfun_rev',r.stonkfun_rev, dlt(r.stonkfun_rev, prev.stonkfun_rev))+
      cell('g-stonk v-bb','stonkfun_hold',r.stonkfun_hold)+
      priceTd(r.stonkfun_price)+`</tr>`;
  }).join('');

  document.getElementById('tbl').querySelector('tbody').innerHTML = sum + body;
}

/* ---------- guide ---------- */
function renderGuide(){
  const rows = build();
  const A = PROJECTS[0], B = PROJECTS[1];
  const sa = stats(rows,A), sb = stats(rows,B);
  const psx = v => (v===null||v===undefined||!isFinite(v))?'—':fmtN(v,2)+'x';
  const pcy = v => (v===null||!isFinite(v))?'—':(v*100).toFixed(2)+'%';
  const wk  = s => s.vol24? s.vol24*7 : null;

  const cheaper = (sa.ps7 && sb.ps7) ? (sa.ps7<sb.ps7 ? A : B) : null;
  const dearer  = cheaper ? (cheaper.id===A.id ? B : A) : null;
  const sc = cheaper? stats(rows,cheaper) : null, sd = dearer? stats(rows,dearer) : null;
  const gap = (sc&&sd&&sc.ps7&&sd.ps7)? sd.ps7/sc.ps7 : null;

  const divLine = (p, stT) => {
    if(!stT.ps7 || !stT.ps30) return '';
    const div = stT.ps7/stT.ps30;
    let tx2;
    if(div > 1.5) tx2 = t('divFast')(fmtN(100/div,0));
    else if(div > 1.15) tx2 = t('divSoft')();
    else if(div < 0.85) tx2 = t('divUp')((1/div).toFixed(1));
    else tx2 = t('divFlat')();
    return t('psLine')(p.name, psx(stT.ps7), psx(stT.ps30), div.toFixed(2), tx2.t).replace('%C%', tx2.c);
  };

  const item = (title, formula, lead, ex, bands, note) =>
    `<div class="gitem">
       <h3>${title}</h3>
       <div class="f">${formula}</div>
       <div class="lead">${lead}</div>
       ${ex?`<div class="ex">${ex}</div>`:''}
       ${bands?`<ul>${bands.map(b=>`<li><span class="band ${b[1]}">${b[0]}</span><span>${b[2]}</span></li>`).join('')}</ul>`:''}
       ${note?`<div class="note">${note}</div>`:''}
     </div>`;

  const ex1 = `<div class="cap">${t('gPsCap')(A.name)}</div>` +
    t('gPsLine')(fmtU(sa.mcap), fmtU(sa.avg7), fmtU(sa.avg7*365), psx(sa.ps7), fmtN(sa.ps7,1)) +
    (sb.ps7!==null ? `<div style="margin-top:7px;padding-top:7px;border-top:1px dashed var(--line2)">`+
      t('gPsCompare')(B.name, fmtU(sb.mcap), fmtU(sb.avg7*365), psx(sb.ps7), cheaper?cheaper.ticker:'', gap?gap.toFixed(1):'') + `</div>` : '');

  const ex3 = t('gBpLine')(A.name, fmtU(sa.holdSum7), pcy(sa.burnForce), fmtU(wk(sa))) +
    '<br>' + t('gBpLine')(B.name, fmtU(sb.holdSum7), pcy(sb.burnForce), fmtU(wk(sb))) +
    '<br><span style="color:var(--mut2)">' + t('gBpFoot') + '</span>';

  const ex4 = t('gToLine')(A.name,
      (sa.turnover!==null?(sa.turnover*100).toFixed(1)+'%':'—'),
      (sa.burnYield!==null?fmtN(sa.burnYield*100,0)+'%':'—'),
      B.name,
      (sb.turnover!==null?(sb.turnover*100).toFixed(1)+'%':'—'),
      (sb.burnYield!==null?fmtN(sb.burnYield*100,0)+'%':'—')) +
    '<br><span style="color:var(--mut2)">' + t('gToFoot') + '</span>';

  const momA = (sa.avg7-sa.avg7p)/(sa.avg7p||1), momB = (sb.avg7-sb.avg7p)/(sb.avg7p||1);
  const ex5 = A.name+' <b>'+(momA*100).toFixed(1)+'%</b>　·　'+B.name+' <b>'+(momB*100).toFixed(1)+'%</b>'+
    '<br><span style="color:var(--mut2)">'+t('gMomFoot')+'</span>';

  document.getElementById('guide').innerHTML =
    item(t('gPsT'), t('gPsF'), t('gPsL'), ex1, t('gPsBands'), t('gPsNote'))
  + item(t('g730T'), t('g730F'), t('g730L'),
         divLine(A,sa) + '<div style="margin-top:7px;padding-top:7px;border-top:1px dashed var(--line2)">' + divLine(B,sb) + '</div>',
         null, t('g730Note'))
  + item(t('gBpT'), t('gBpF'), t('gBpL'), ex3, t('gBpBands'), t('gBpNote'))
  + item(t('gToT'), t('gToF'), t('gToL'), ex4, t('gToBands'), t('gToNote'))
  + item(t('gMomT'), t('gMomF'), t('gMomL'), ex5, t('gMomBands'), null);
}

/* ---------- live ---------- */
async function fetchJSON(u){ const r=await fetch(u,{cache:'no-store'}); if(!r.ok) throw new Error(r.status); return r.json(); }

async function loadFees(){
  const reqs=[];
  ['pons','stonkfun'].forEach(s=>['dailyRevenue','dailyHoldersRevenue','dailyFees'].forEach(dt=>
    reqs.push(fetchJSON(`https://api.llama.fi/summary/fees/${s}?dataType=${dt}`).then(j=>({k:`${s}.${dt}`, j})))));
  reqs.push(fetchJSON('https://api.llama.fi/protocol/pons').then(j=>({k:'meta.pons',j})));
  reqs.push(fetchJSON('https://api.llama.fi/protocol/stonkfun').then(j=>({k:'meta.stonkfun',j})));
  const res = await Promise.all(reqs);
  res.forEach(({k,j})=>{
    if(k.startsWith('meta.')){ const id=k.slice(5);
      DATA.meta[id] = Object.assign({}, DATA.meta[id], {name:j.name, symbol:j.symbol, mcap:j.mcap || DATA.meta[id]?.mcap}); }
    else { DATA.series[k] = (j.totalDataChart||[]).map(([ts,v])=>[ts, v]); }
  });
}

/* 价格：DefiLlama 币价接口（Pons 在 Robinhood Chain、STONK 在 Solana，均按合约地址取） */
async function loadPrices(){
  const ids = Object.values(LLAMA_IDS).join(',');
  const j = await fetchJSON('https://coins.llama.fi/prices/current/'+ids);
  const coins = j.coins || {};
  const today = Math.floor(Date.now()/1000);
  let got = 0;
  Object.entries(LLAMA_IDS).forEach(([id,key])=>{
    const c = coins[key];
    if(!c || !c.price) return;
    got++;
    DATA.price = DATA.price || {};
    DATA.price[id] = c.price;
    DATA.priceSeries[id] = DATA.priceSeries[id] || [];
    const arr = DATA.priceSeries[id];
    const lastTs = arr.length? arr[arr.length-1][0] : 0;
    if(dayKey(lastTs) === dayKey(today)) arr[arr.length-1] = [lastTs, c.price];
    else arr.push([today, c.price]);
    const p = PROJECTS.find(x=>x.id===id);
    const mk = (DATA.market||{})[id];
    const mc = (mk && mk.mcap) ? mk.mcap : (p ? c.price * p.supply : null);
    if(mc) DATA.meta[id] = Object.assign({}, DATA.meta[id], {mcap: mc});
  });
  return got;
}

/* 成交额 / 市值：CoinGecko（失败不影响其他数据） */
async function loadMarket(){
  const j = await fetchJSON('https://api.coingecko.com/api/v3/simple/price?ids=' + Object.values(CG_IDS).join(',')
    + '&vs_currencies=usd&include_24hr_vol=true&include_market_cap=true&include_24hr_change=true');
  const mk = DATA.market || (DATA.market = {});
  Object.entries(CG_IDS).forEach(([name,cid])=>{
    const x = j[cid] || {};
    if(x.usd_24h_vol) mk[name] = {vol24h:x.usd_24h_vol, mcap:x.usd_market_cap||0, price:x.usd, change24h:x.usd_24h_change||0};
    if(x.usd) { DATA.price = DATA.price || {}; DATA.price[name] = x.usd; }
  });
  PROJECTS.forEach(p=>{
    const m = mk[p.id];
    if(m && m.mcap) DATA.meta[p.id] = Object.assign({}, DATA.meta[p.id], {mcap: m.mcap});
  });
}

let BUSY = false;
async function loadLive(){
  if(BUSY) return;
  BUSY = true;
  const b = document.getElementById('src');
  b.textContent = t('fetching'); b.className = 'badge';
  const btn = document.getElementById('btnRefresh');
  if(btn){ btn.disabled = true; btn.classList.add('busy'); }
  let ok = true, priceOk = 0;
  try{ await loadFees(); }catch(e){ ok = false; }
  try{ priceOk = await loadPrices(); }catch(e){}
  try{ ok = ok && true; await loadMarket(); }catch(e){}
  DATA.generated = new Date().toISOString();
  BUSY = false;
  if(btn){ btn.disabled = false; btn.classList.remove('busy'); }
  setSrc(ok, priceOk);
  renderAll();
  if(priceOk) flashPrices();
}
function setSrc(ok, priceOk){
  const b=document.getElementById('src');
  const time = new Date().toLocaleTimeString(LANG==='zh'?'zh-CN':'en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  if(ok){ b.textContent = t('liveAt') + time; b.className='badge live'; }
  else  { b.textContent = t('offline');        b.className='badge off'; }
}
function flashPrices(){
  PROJECTS.forEach(p=>{
    const el=document.getElementById('px-'+p.id);
    if(!el) return;
    el.classList.remove('flash');
    void el.offsetWidth;
    el.classList.add('flash');
    setTimeout(()=>el.classList.remove('flash'), 1600);
  });
}
function renderAll(){
  [renderCards, renderRules, renderTabs, renderChart, renderTable, renderGuide].forEach(function(fn){
    try{ fn(); }catch(e){ console.error('render failed:', fn.name, e); }
  });
  const g = DATA.generated || BUNDLE.generated;
  document.getElementById('gen').textContent = t('updatedAt') + new Date(g).toLocaleString(LANG==='zh'?'zh-CN':'en-GB');
  document.getElementById('foot').innerHTML = t('foot1') + '<br>' + t('foot2') + FOOT_AUTHOR[LANG];
}

/* ---------- 手机端：确保头像 / 关注按钮一定能跳转 X ---------- */
(function(){
  var XURL = 'https://x.com/arych_kun';
  var touch = ('ontouchstart' in window) || (navigator.maxTouchPoints>0);
  document.addEventListener('click', function(ev){
    var a = ev.target && ev.target.closest ? ev.target.closest('a[data-xlink]') : null;
    if(!a) return;
    if(ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.button>0) return;
    if(!touch) return;                     /* 桌面端保持原生行为 */
    ev.preventDefault();
    var w = null;
    try{ w = window.open(a.href, '_blank'); }catch(e){}
    if(!w || w.closed || typeof w.closed==='undefined'){ window.location.href = a.href; }
  }, true);
  void XURL;
})();
