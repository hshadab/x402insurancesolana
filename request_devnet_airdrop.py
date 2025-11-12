#!/usr/bin/env python3
"""
Request Solana devnet airdrop using RPC
"""
import requests
import json
import time

WALLET_ADDRESS = "BAikRH6xfHd6YG777XFQw85LGEEehTeqRtDiVpJLJiBo"
RPC_URL = "https://api.devnet.solana.com"

def check_balance():
    """Check SOL balance"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [WALLET_ADDRESS]
    }

    response = requests.post(RPC_URL, json=payload)
    data = response.json()

    if "result" in data:
        lamports = data["result"]["value"]
        sol = lamports / 1_000_000_000
        print(f"✅ Current balance: {sol} SOL ({lamports} lamports)")
        return sol
    else:
        print(f"❌ Error checking balance: {data}")
        return 0

def request_airdrop(amount_sol=1):
    """Request airdrop from devnet"""
    lamports = int(amount_sol * 1_000_000_000)

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "requestAirdrop",
        "params": [WALLET_ADDRESS, lamports]
    }

    print(f"\n🚰 Requesting {amount_sol} SOL airdrop...")

    try:
        response = requests.post(RPC_URL, json=payload, timeout=10)
        data = response.json()

        if "result" in data:
            signature = data["result"]
            print(f"✅ Airdrop requested successfully!")
            print(f"📝 Transaction signature: {signature}")
            print(f"🔗 Explorer: https://explorer.solana.com/tx/{signature}?cluster=devnet")

            # Wait for confirmation
            print("\n⏳ Waiting for confirmation...")
            time.sleep(5)

            return True
        elif "error" in data:
            error_msg = data["error"].get("message", "Unknown error")
            print(f"❌ Airdrop failed: {error_msg}")

            if "airdrop request limit" in error_msg.lower():
                print("\n💡 TIP: The RPC is rate-limited. Try these alternatives:")
                print("   1. https://faucet.solana.com/ (select Devnet)")
                print("   2. https://faucet.quicknode.com/solana/devnet")
                print("   3. https://solfaucet.com/")

            return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Solana Devnet Airdrop Request")
    print("=" * 60)
    print(f"Wallet: {WALLET_ADDRESS}")
    print(f"Network: Devnet")
    print("=" * 60)

    # Check initial balance
    print("\n📊 Checking current balance...")
    initial_balance = check_balance()

    # Request airdrop
    if request_airdrop(1):
        # Check new balance
        print("\n📊 Checking new balance...")
        new_balance = check_balance()

        if new_balance > initial_balance:
            print(f"\n🎉 Success! Received {new_balance - initial_balance} SOL")
        else:
            print("\n⚠️  Balance hasn't updated yet. Check again in a minute.")

    print("\n" + "=" * 60)
    print("Alternative Faucets:")
    print("=" * 60)
    print("1. https://faucet.solana.com/ (Official)")
    print("2. https://faucet.quicknode.com/solana/devnet")
    print("3. https://solfaucet.com/")
    print("4. https://stakely.io/faucet/solana-sol")
    print("=" * 60)

if __name__ == "__main__":
    main()
