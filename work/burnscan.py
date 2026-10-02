import json, urllib.request, concurrent.futures, datetime
RPC="https://rpc.mainnet.chain.robinhood.com"
TOK="0x39dBED3a2bd333467115dE45665cC57F813C4571"
DEAD="0x"+"dead".rjust(64,"0")
TR="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def logs(a,b):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"address":TOK,"fromBlock":hex(a),"toBlock":hex(b),"topics":[TR,None,DEAD]}]}).encode()
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"curl/8"})
    try:
        j=json.load(urllib.request.urlopen(req,timeout=45))
        return a, b, j.get("result") or [], j.get("error")
    except Exception as e:
        return a,b,[],str(e)
ranges=[(a,a+249999) for a in range(10000000, 74800000, 250000)]
res=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    for r in ex.map(lambda t: logs(*t), ranges): res.append(r)
ev=[];errs=0;tot_range=0
for a,b,lg,e in res:
    if e: errs+=1; continue
    for l in lg:
        ev.append((int(l["blockNumber"],16), int(l["data"],16)/1e18, l["topics"][1]))
print("chunks:",len(ranges),"errors:",errs,"events:",len(ev))
ev.sort()
print("total burned in scan:", "{:,.0f}".format(sum(v for _,v,_ in ev)))
byday={}
for blk,v,frm in ev: byday[blk]=byday.get(blk,0)+v
# bucket by block ranges of 2M
buckets={}
for blk,v,frm in ev: buckets[blk//2000000]=buckets.get(blk//2000000,0)+v
print("\nburn by 2M-block bucket:")
for k in sorted(buckets): print(f"  blk {k*2000000:>10,}-{k*2000000+1999999:>10,}: {buckets[k]:>16,.0f}")
# sender concentration
snd={}
for blk,v,frm in ev: snd[frm]=snd.get(frm,0)+v
print("\ntop senders to burn:")
for k,v in sorted(snd.items(), key=lambda x:-x[1])[:12]:
    print(f"  {k}  {v:>16,.0f}")
