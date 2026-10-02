#!/bin/bash
RPC="https://rpc.mainnet.chain.robinhood.com"
TOK="0x39dBED3a2bd333467115dE45665cC57F813C4571"
DEAD="0x000000000000000000000000000000000000000000000000000000000000dead"
PAD="000000000000000000000000000000000000000000000000000000000000dead"
sample() {
  b=$1; hex=$(printf '0x%x' "$b")
  bal=$(curl -s -m 30 "$RPC" -H 'Content-Type: application/json' --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_call\",\"params\":[{\"to\":\"$TOK\",\"data\":\"0x70a08231$PAD\"},\"$hex\"]}" | python3 -c "import sys,json;r=json.load(sys.stdin).get('result','0x0');print(int(r,16)//10**18)")
  ts=$(curl -s -m 30 "$RPC" -H 'Content-Type: application/json' --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getBlockByNumber\",\"params\":[\"$hex\",false]}" | python3 -c "import sys,json;d=json.load(sys.stdin).get('result') or {};print(int(d.get('timestamp','0x0'),16))")
  echo "$b $ts $bal"
}
export -f sample; export RPC TOK PAD
python3 -c "[print(i) for i in range(9000000, 74790001, 1500000)]" | xargs -P 6 -I{} bash -c 'sample {}'
