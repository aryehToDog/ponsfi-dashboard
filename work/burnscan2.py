import json, urllib.request, concurrent.futures
RPC="https://rpc.mainnet.chain.robinhood.com"
TOK="0x39dBED3a2bd333467115dE45665cC57F813C4571"
DEAD="0x"+"dead".rjust(64,"0")
TR="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def logs(t):
    a,b=t
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"address":TOK,"fromBlock":hex(a),"toBlock":hex(b),"topics":[TR,None,DEAD]}]}).encode()
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"curl/8"})
    try:
        j=json.load(urllib.request.urlopen(req,timeout=60)); return j.get("result") or []
    except Exception: return []
ranges=[(a,a+499999) for a in range(10000000, 74800000, 500000)]
ev=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    for lg in ex.map(logs, ranges):
        for l in lg: ev.append((int(l["blockNumber"],16), int(l["data"],16)/1e18, l["topics"][1]))
ev.sort()
json.dump(ev, open("burn_events.json","w"))
day=848684.0
def dt(blk): return round((blk-9000000)/day,1)
print("events:", len(ev), "total burned:", "{:,.0f}".format(sum(v for _,v,_ in ev)))
buckets={}
for blk,v,_ in ev: buckets[blk//2000000]=buckets.get(blk//2000000,0)+v
print("\nburn by 2M-block bucket (blk, approx days after Jul13):")
for k in sorted(buckets): print(f"  {k*2000000:>11,} (+{dt(k*2000000):>5}d) : {buckets[k]:>15,.0f}   cum={sum(buckets[j] for j in sorted(buckets) if j<=k):>15,.0f}")
snd={}
for blk,v,f in ev: snd[f]=snd.get(f,0)+v
print("\ntop senders:")
for k,v in sorted(snd.items(), key=lambda x:-x[1])[:6]:
    blks=[b for b,_,f in ev if f==k]
    print(f"  {k}  {v:>15,.0f}  blocks {min(blks):,}(+{dt(min(blks))}d) -> {max(blks):,}(+{dt(max(blks))}d)")
