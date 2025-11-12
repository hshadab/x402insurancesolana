#!/usr/bin/env python3
"""
Example: AI Agent Buying Insurance Policy on Solana

This demonstrates how an autonomous agent would:
1. Generate x402 payment signature
2. Purchase insurance policy
3. Receive policy confirmation
"""
import requests
import json
import time
from nacl.signing import SigningKey
import base58


class SolanaAgent:
    """Simulated AI agent with Solana wallet"""

    def __init__(self, private_key_bytes: bytes, insurance_url: str):
        self.signing_key = SigningKey(private_key_bytes)
        self.public_key = str(base58.b58encode(bytes(self.signing_key.verify_key)), 'utf-8')
        self.insurance_url = insurance_url

    def create_payment_signature(
        self,
        amount: int,
        backend_pubkey: str,
        usdc_mint: str
    ) -> tuple[str, str, int]:
        """
        Create ed25519 signature for x402 payment

        Args:
            amount: Payment amount in micro-USDC (6 decimals)
            backend_pubkey: Insurance backend public key
            usdc_mint: USDC SPL token mint address

        Returns:
            (payment_header, nonce, timestamp)
        """
        timestamp = int(time.time())
        nonce = f"policy_{timestamp}_{self.public_key[:8]}"

        # Create message to sign
        message_data = {
            "payer": self.public_key,
            "amount": amount,
            "asset": usdc_mint,
            "payTo": backend_pubkey,
            "timestamp": timestamp,
            "nonce": nonce
        }

        # Serialize to JSON (deterministic order)
        message = json.dumps(message_data, sort_keys=True)
        message_bytes = message.encode('utf-8')

        # Sign with ed25519
        signed = self.signing_key.sign(message_bytes)
        signature_b58 = base58.b58encode(signed.signature).decode('utf-8')

        # Create x402 payment header
        payment_header = (
            f"payer={self.public_key},"
            f"amount={amount},"
            f"asset={usdc_mint},"
            f"payTo={backend_pubkey},"
            f"timestamp={timestamp},"
            f"nonce={nonce},"
            f"signature={signature_b58}"
        )

        return payment_header, nonce, timestamp

    def buy_insurance(
        self,
        coverage_amount: int,
        merchant_url: str,
        backend_pubkey: str,
        usdc_mint: str
    ) -> dict:
        """
        Purchase insurance policy

        Args:
            coverage_amount: Amount to insure in micro-USDC
            merchant_url: API endpoint to protect
            backend_pubkey: Insurance backend wallet
            usdc_mint: USDC token mint address

        Returns:
            Policy details
        """
        # Calculate premium (1% of coverage)
        premium = int(coverage_amount * 0.01)

        # Create payment signature
        payment_header, nonce, timestamp = self.create_payment_signature(
            amount=premium,
            backend_pubkey=backend_pubkey,
            usdc_mint=usdc_mint
        )

        print(f"🤖 Agent: {self.public_key[:16]}...")
        print(f"💰 Coverage: {coverage_amount / 1_000_000:.2f} USDC")
        print(f"💵 Premium: {premium / 1_000_000:.4f} USDC (1%)")
        print(f"🔗 Merchant: {merchant_url}")
        print()

        # Send insurance request
        response = requests.post(
            f"{self.insurance_url}/insure",
            headers={
                "X-Payment": payment_header,
                "X-Payer": self.public_key,
                "Content-Type": "application/json"
            },
            json={
                "coverage_amount": coverage_amount,
                "merchant_url": merchant_url
            }
        )

        if response.status_code == 200:
            policy = response.json()
            print("✅ Insurance policy created!")
            print(f"📋 Policy ID: {policy['policy_id']}")
            print(f"⏰ Expires: {time.ctime(policy['expires_at'])}")
            print(f"🛡️ Coverage: {policy['coverage_amount'] / 1_000_000:.2f} USDC")
            return policy
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return {}


def main():
    """Demo: Agent buys insurance policy"""

    # Configuration (update these!)
    INSURANCE_URL = "http://localhost:8000"
    BACKEND_PUBKEY = "11111111111111111111111111111111"  # Replace with actual
    USDC_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"  # Devnet USDC

    # Generate test agent wallet (in production, load from file)
    agent_private_key = SigningKey.generate().encode()

    # Or load from keypair file:
    # with open('/path/to/agent-keypair.json', 'r') as f:
    #     import json
    #     secret = json.load(f)
    #     agent_private_key = bytes(secret)

    # Create agent
    agent = SolanaAgent(agent_private_key, INSURANCE_URL)

    print("=" * 60)
    print("🤖 AI AGENT: PURCHASING INSURANCE ON SOLANA")
    print("=" * 60)
    print()

    # Buy policy
    policy = agent.buy_insurance(
        coverage_amount=100_000,  # 0.1 USDC
        merchant_url="https://api.merchant.com/data",
        backend_pubkey=BACKEND_PUBKEY,
        usdc_mint=USDC_MINT
    )

    if policy:
        print()
        print("=" * 60)
        print("💾 SAVE THIS POLICY ID FOR CLAIMS:")
        print(f"   {policy['policy_id']}")
        print("=" * 60)


if __name__ == "__main__":
    main()
