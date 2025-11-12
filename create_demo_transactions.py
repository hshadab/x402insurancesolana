#!/usr/bin/env python3
"""
Create demo Solana transactions for x402 Insurance
This script will:
1. Create a policy with a real Solana payment transaction
2. Submit a claim with real on-chain attestation
3. Pay out the claim with a real USDC refund

This will populate the Solana Activity feed on the dashboard.
"""

import sys
import requests
import time
import json
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000"

def create_policy():
    """Create a new policy"""
    print("\n📋 Creating new policy...")

    # Create policy request
    policy_data = {
        "agent_address": "BAikRH6xfHd6YG777XFQw85LGEEehTeqRtDiVpJLJiBo",
        "merchant_url": "https://httpstat.us/503",
        "coverage_amount": 0.01,  # 0.01 USDC
        "payment_signature": "demo-sig-" + str(int(time.time()))  # Simple mode
    }

    response = requests.post(
        f"{API_BASE}/api/policies",
        json=policy_data,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 201:
        policy = response.json()
        print(f"✅ Policy created: {policy['id']}")
        print(f"   Coverage: {policy['coverage_amount']} USDC")
        print(f"   Premium: {policy['premium']} USDC")
        return policy
    else:
        print(f"❌ Failed to create policy: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def submit_claim(policy_id):
    """Submit a claim for the policy"""
    print(f"\n🔮 Submitting claim for policy {policy_id}...")

    # Submit claim
    claim_data = {
        "policy_id": policy_id,
        "url": "https://httpstat.us/503"
    }

    response = requests.post(
        f"{API_BASE}/api/claims",
        json=claim_data,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 201:
        claim = response.json()
        print(f"✅ Claim submitted: {claim['id']}")
        print(f"   Status: {claim['status']}")
        print(f"   Payout: {claim.get('payout_amount', 'N/A')} USDC")
        if 'attestation_tx_hash' in claim:
            print(f"   Attestation TX: {claim['attestation_tx_hash'][:16]}...")
        if 'refund_tx_hash' in claim:
            print(f"   Refund TX: {claim['refund_tx_hash'][:16]}...")
        return claim
    else:
        print(f"❌ Failed to submit claim: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def check_dashboard():
    """Check dashboard to see Solana Activity"""
    print("\n📊 Checking dashboard...")

    response = requests.get(f"{API_BASE}/api/dashboard")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Dashboard data retrieved")
        print(f"   Total policies: {data['stats']['total_policies']}")
        print(f"   Total claims: {data['stats']['total_claims']}")
        print(f"   SOL balance: {data['blockchain_stats']['sol_balance']}")
        print(f"   USDC balance: {data['blockchain_stats']['usdc_balance']}")

        # Show recent claims
        if data['recent_claims']:
            print(f"\n   Recent claims:")
            for claim in data['recent_claims'][:3]:
                print(f"     - {claim['id']}: {claim['status']}")
                if 'attestation_tx_hash' in claim:
                    print(f"       Attestation: {claim['attestation_tx_hash'][:16]}...")
                if 'refund_tx_hash' in claim:
                    print(f"       Refund: {claim['refund_tx_hash'][:16]}...")

        return data
    else:
        print(f"❌ Failed to get dashboard: {response.status_code}")
        return None

def main():
    print("=" * 60)
    print("x402 Insurance - Solana Demo Transaction Generator")
    print("=" * 60)

    # Check server is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            sys.exit(1)
    except:
        print("❌ Server is not running. Please start it first:")
        print("   cd /home/hshadab/x402insurancesolana && ./venv/bin/python3 server.py")
        sys.exit(1)

    print("✅ Server is running")

    # Create policy
    policy = create_policy()
    if not policy:
        print("\n❌ Failed to create policy. Exiting.")
        sys.exit(1)

    # Wait a bit
    print("\n⏳ Waiting 2 seconds...")
    time.sleep(2)

    # Submit claim
    claim = submit_claim(policy['id'])
    if not claim:
        print("\n❌ Failed to submit claim. Exiting.")
        sys.exit(1)

    # Wait a bit
    print("\n⏳ Waiting 2 seconds...")
    time.sleep(2)

    # Check dashboard
    check_dashboard()

    print("\n" + "=" * 60)
    print("✅ Demo completed!")
    print("=" * 60)
    print("\n🌐 Open dashboard: http://localhost:8000/")
    print("   Look for 'Solana Activity' section showing:")
    print("   - 📥 Premium Payment transaction")
    print("   - 🔮 Proof Attestation transaction")
    print("   - 💸 USDC Refund transaction")
    print()

if __name__ == "__main__":
    main()
