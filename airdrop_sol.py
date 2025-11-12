#!/usr/bin/env python3
"""
Airdrop SOL to agent wallet
"""
from solders.pubkey import Pubkey
from solana.rpc.api import Client

AGENT_PUBKEY = "3dKAYtqFPzxQjNMTRXmnW42QqExK7iMboEYCSkW92se3"
RPC_URL = "https://api.devnet.solana.com"

client = Client(RPC_URL)
pubkey = Pubkey.from_string(AGENT_PUBKEY)

print(f"Requesting airdrop for {AGENT_PUBKEY}...")

# Request 1 SOL airdrop
result = client.request_airdrop(pubkey, 1_000_000_000)  # 1 SOL in lamports
print(f"Airdrop transaction: {result.value}")

# Confirm
client.confirm_transaction(result.value)
print(f"✅ Airdrop confirmed!")

# Check balance
balance = client.get_balance(pubkey).value
print(f"New balance: {balance / 1_000_000_000} SOL")
