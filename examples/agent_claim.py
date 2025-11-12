#!/usr/bin/env python3
"""
Example: AI Agent Filing Insurance Claim on Solana

This demonstrates how an autonomous agent would:
1. Detect merchant failure (503, empty response, etc.)
2. Submit fraud claim with evidence
3. Receive USDC refund
4. Verify proof attestation on-chain
"""
import requests
import time
import sys


class ClaimAgent:
    """AI agent that files insurance claims"""

    def __init__(self, insurance_url: str, policy_id: str):
        self.insurance_url = insurance_url
        self.policy_id = policy_id

    def detect_fraud(self, merchant_url: str) -> tuple[bool, int, str]:
        """
        Call merchant API and detect fraud

        Returns:
            (is_fraud, http_status, response_body)
        """
        print(f"📡 Calling merchant API: {merchant_url}")

        try:
            response = requests.get(merchant_url, timeout=10)
            status = response.status_code
            body = response.text

            print(f"📊 HTTP Status: {status}")
            print(f"📄 Response Size: {len(body)} bytes")

            # Fraud detection logic (same as zkEngine)
            is_fraud = False

            if status >= 500:
                print("⚠️  FRAUD DETECTED: Server error (5xx)")
                is_fraud = True
            elif len(body) == 0:
                print("⚠️  FRAUD DETECTED: Empty response")
                is_fraud = True
            else:
                print("✅ No fraud detected")

            return is_fraud, status, body

        except requests.RequestException as e:
            print(f"❌ Request failed: {e}")
            return True, 503, ""

    def file_claim(self, http_status: int, response_body: str) -> dict:
        """
        Submit insurance claim

        Args:
            http_status: HTTP status code from merchant
            response_body: Response body from merchant

        Returns:
            Claim result with refund details
        """
        print()
        print("📝 Filing insurance claim...")

        response = requests.post(
            f"{self.insurance_url}/claim",
            json={
                "policy_id": self.policy_id,
                "http_status": http_status,
                "response_body": response_body[:1000],  # Limit size
                "timestamp": int(time.time())
            }
        )

        if response.status_code == 200:
            claim = response.json()

            print()
            print("✅ CLAIM APPROVED!")
            print(f"💰 Refund: ${claim['payout_amount'] / 1_000_000:.2f} USDC")
            print(f"🔗 TX: {claim.get('refund_tx_hash', 'N/A')[:32]}...")

            if 'attestation_tx_hash' in claim:
                print(f"📜 Attestation: {claim['attestation_tx_hash'][:32]}...")
                print(f"🌐 Explorer: {claim.get('explorer_url', 'N/A')}")

            print(f"🔐 Proof: {claim.get('proof_url', 'N/A')}")

            return claim
        elif response.status_code == 400:
            error = response.json()
            print(f"❌ Claim rejected: {error.get('error', 'Unknown')}")
            return {}
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return {}

    def verify_proof(self, claim_id: str) -> bool:
        """
        Independently verify the zkEngine proof

        Args:
            claim_id: Claim ID to verify

        Returns:
            True if proof is valid
        """
        print()
        print("🔍 Verifying proof independently...")

        # Get proof data
        response = requests.get(f"{self.insurance_url}/proofs/{claim_id}")

        if response.status_code != 200:
            print("❌ Could not retrieve proof")
            return False

        proof_data = response.json()

        # Verify proof
        verify_response = requests.post(
            f"{self.insurance_url}/verify",
            json={
                "proof": proof_data.get("proof"),
                "public_inputs": proof_data.get("public_inputs")
            }
        )

        if verify_response.status_code == 200:
            result = verify_response.json()
            if result.get("valid"):
                print("✅ Proof verified successfully!")
                print(f"   Message: {result.get('message')}")
                return True

        print("❌ Proof verification failed")
        return False


def main():
    """Demo: Agent detects fraud and files claim"""

    if len(sys.argv) < 2:
        print("Usage: python agent_claim.py <policy_id>")
        print()
        print("Example:")
        print("  python agent_claim.py abc123...")
        sys.exit(1)

    # Configuration
    INSURANCE_URL = "http://localhost:8000"
    POLICY_ID = sys.argv[1]

    # Test with a merchant that returns 503
    MERCHANT_URL = "https://httpbin.org/status/503"

    print("=" * 60)
    print("🤖 AI AGENT: FILING INSURANCE CLAIM ON SOLANA")
    print("=" * 60)
    print(f"📋 Policy ID: {POLICY_ID}")
    print()

    # Create claim agent
    agent = ClaimAgent(INSURANCE_URL, POLICY_ID)

    # Step 1: Call merchant and detect fraud
    is_fraud, status, body = agent.detect_fraud(MERCHANT_URL)

    if not is_fraud:
        print()
        print("ℹ️  No fraud detected. Claim not needed.")
        sys.exit(0)

    # Step 2: File claim
    claim = agent.file_claim(status, body)

    if not claim:
        sys.exit(1)

    # Step 3: Verify proof
    claim_id = claim.get("claim_id")
    if claim_id:
        verified = agent.verify_proof(claim_id)

        if verified:
            print()
            print("=" * 60)
            print("✅ CLAIM SUCCESSFUL - REFUND RECEIVED")
            print("=" * 60)
            print()
            print("📋 Summary:")
            print(f"   Claim ID: {claim_id}")
            print(f"   Payout: ${claim['payout_amount'] / 1_000_000:.2f} USDC")
            print(f"   Status: PAID")
            print()
            print("🔗 View on Solana Explorer:")
            print(f"   {claim.get('explorer_url', 'N/A')}")


if __name__ == "__main__":
    main()
