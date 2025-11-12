#!/usr/bin/env python3
"""
Create a Solana wallet keypair for testnet
"""
from solders.keypair import Keypair
import json
import os

def create_wallet(output_path):
    """Create a new Solana keypair and save to file"""
    # Generate new keypair
    keypair = Keypair()

    # Get the FULL keypair as bytes (64 bytes: 32 secret + 32 public)
    # Using bytes(keypair) gives us the full 64-byte keypair
    keypair_bytes = bytes(keypair)

    # Convert to list for JSON serialization (Solana CLI format)
    keypair_list = list(keypair_bytes)

    # Get public key
    pubkey = str(keypair.pubkey())

    # Save to file in Solana CLI format
    with open(output_path, 'w') as f:
        json.dump(keypair_list, f)

    print(f"DEBUG: Saved {len(keypair_list)} bytes to {output_path}")

    # Set permissions
    os.chmod(output_path, 0o600)

    print("✅ Solana Wallet Created!")
    print("=" * 60)
    print(f"📁 Wallet file: {output_path}")
    print(f"🔑 Public Key: {pubkey}")
    print("=" * 60)
    print()
    print("🚀 Next Steps:")
    print()
    print("1. Get Testnet SOL (for transaction fees):")
    print(f"   solana airdrop 2 {pubkey} --url testnet")
    print("   OR visit: https://faucet.solana.com/ (select Testnet)")
    print()
    print("2. Get Testnet USDC (for insurance payments):")
    print("   Visit: https://faucet.circle.com/")
    print("   - Network: Solana Testnet")
    print("   - Mint: 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")
    print(f"   - Address: {pubkey}")
    print()
    print("3. Update .env with your public key:")
    print(f"   BACKEND_WALLET_PUBKEY={pubkey}")
    print()
    print("4. Restart the server to see Solana network!")
    print("=" * 60)

    return pubkey

if __name__ == "__main__":
    wallet_path = os.path.expanduser("~/solana-testnet-wallet.json")
    pubkey = create_wallet(wallet_path)
