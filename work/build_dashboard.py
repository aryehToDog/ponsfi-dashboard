import json, urllib.request, datetime, os
def get(url):
    req=urllib.request.Request(url, headers={"User-Agent":"curl/8"})
    return json.load(urllib.request.urlopen(req, timeout=30))

bundle={"generated": datetime.datetime.utcnow().isoformat()+"Z", "series":{}, "meta":{}, "priceSeries":{}}
for slug in ["pons","stonkfun"]:
    for dt in ["dailyRevenue","dailyHoldersRevenue","dailyFees"]:
        try:
            j=get(f"https://api.llama.fi/summary/fees/{slug}?dataType={dt}")
            bundle["series"][f"{slug}.{dt}"]=[[int(ts), round(float(v),2)] for ts,v in (j.get("totalDataChart") or [])]
        except Exception as e: print("err",slug,dt,e)
    try:
        m=get(f"https://api.llama.fi/protocol/{slug}")
        bundle["meta"][slug]={"name":m.get("name"),"mcap":m.get("mcap"),"symbol":m.get("symbol")}
    except Exception as e: print("meta err",slug,e)
for name,key in [("pons","robinhood:0x39dBED3a2bd333467115dE45665cC57F813C4571"),("stonkfun","solana:6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx")]:
    try:
        j=get(f"https://coins.llama.fi/chart/{key}?span=90&period=1d")
        for k,v in j.get("coins",{}).items():
            bundle["priceSeries"][name]=[[int(x["timestamp"]), round(float(x["price"]),8)] for x in v.get("prices",[])]
    except Exception as e: print("price err",name,e)
try:
    p=get("https://coins.llama.fi/prices/current/robinhood:0x39dBED3a2bd333467115dE45665cC57F813C4571,solana:6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx")
    bundle["price"]={"pons":p["coins"]["robinhood:0x39dBED3a2bd333467115dE45665cC57F813C4571"]["price"],
                     "stonkfun":p["coins"]["solana:6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx"]["price"]}
except Exception as e: print("price err",e)
json.dump(bundle, open("work/dashboard-data.json","w"))
print("ok", {k:len(v) for k,v in bundle["series"].items()}, bundle.get("price"))
