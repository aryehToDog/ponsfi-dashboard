#!/bin/bash
RPC="https://rpc.mainnet.chain.robinhood.com"
TOK="0x39dBED3a2bd333467115dE45665cC57F813C4571"
DEAD=$(python3 -c "print('0x'+'dead'.rjust(64,'0'))")
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
do_chunk() {
  from=$1
  to=$((from+999999))
  fb=$(printf '0x%x' "$from"); tb=$(printf '0x%x' "$to")
  echo -n "$from "
  curl -s -m 90 "$RPC" -H 'Content-Type: application/json' --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getLogs\",\"params\":[{\"address\":\"$TOK\",\"fromBlock\":\"$fb\",\"toBlock\":\"$tb\",\"topics\":[\"$TRANSFER\",null,\"$DEAD\"]}]}"
  echo
}
export -f do_chunk; export RPC TOK DEAD TRANSFER
python3 -c "[print(i) for i in range(8000000, 74700001, 1000000)]" | xargs -P 6 -I{} bash -c 'do_chunk {}'
