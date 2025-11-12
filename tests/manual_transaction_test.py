#!/usr/bin/env python3
"""
Manual test script for Solana transaction building

This is NOT a pytest test - it's a standalone script for manual testing.
Run directly with: python tests/manual_transaction_test.py
"""
from solders.transaction import Transaction
from solders.keypair import Keypair
from solders.compute_budget import set_compute_unit_price, set_compute_unit_limit
from solana.rpc.api import Client

# Create dummy instruction
compute_price_ix = set_compute_unit_price(1000)
compute_limit_ix = set_compute_unit_limit(200_000)

# Create dummy keypair
keypair = Keypair()

# Get recent blockhash from devnet
client = Client("https://api.devnet.solana.com")
blockhash_resp = client.get_latest_blockhash()
recent_blockhash = blockhash_resp.value.blockhash

print("Testing Transaction.new_signed_with_payer()...")
try:
    transaction = Transaction.new_signed_with_payer(
        [compute_price_ix, compute_limit_ix],
        keypair.pubkey(),
        [keypair],
        recent_blockhash
    )
    print("SUCCESS! Transaction created:")
    print(f"  Signatures: {len(transaction.signatures)}")
    print(f"  Message instructions: {len(transaction.message().instructions)}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
