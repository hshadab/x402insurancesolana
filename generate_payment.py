#!/usr/bin/env python3
"""
Generate a properly signed x402 payment for Solana
"""
import json
import time
import base58
import uuid
from nacl.signing import SigningKey
from solders.keypair import Keypair

def generate_signed_payment(
    agent_keypair_path: str,
    backend_pubkey: str,
    usdc_mint: str,
    amount_micro_usdc: int
):
    """
    Generate a properly signed x402 payment

    Args:
        agent_keypair_path: Path to agent's Solana keypair JSON
        backend_pubkey: Backend wallet public key (base58)
        usdc_mint: USDC mint address
        amount_micro_usdc: Amount in micro-USDC (6 decimals, so 100 = $0.0001)

    Returns:
        tuple: (payment_header, payer_address)
    """
    # Load agent keypair
    with open(agent_keypair_path, 'r') as f:
        keypair_bytes = bytes(json.load(f))

    # Create Solana keypair to get public key
    solana_keypair = Keypair.from_bytes(keypair_bytes)
    payer_address = str(solana_keypair.pubkey())

    # Create signing key for ed25519 signature (need first 32 bytes - the seed)
    signing_key = SigningKey(keypair_bytes[:32])

    # Generate payment details
    timestamp = int(time.time())
    nonce = str(uuid.uuid4())

    # Construct message (must match server format exactly)
    message_data = {
        "payer": payer_address,
        "amount": amount_micro_usdc,
        "asset": usdc_mint,
        "payTo": backend_pubkey,
        "timestamp": timestamp,
        "nonce": nonce
    }

    # Serialize to JSON with sorted keys (deterministic)
    message = json.dumps(message_data, sort_keys=True)
    message_bytes = message.encode('utf-8')

    print(f"Signing message: {message}")

    # Sign with ed25519
    signed = signing_key.sign(message_bytes)
    signature_bytes = signed.signature

    # Base58 encode the signature
    signature_b58 = base58.b58encode(signature_bytes).decode('ascii')

    # Construct X-Payment header
    payment_header = f"payer={payer_address},amount={amount_micro_usdc},asset={usdc_mint},payTo={backend_pubkey},timestamp={timestamp},nonce={nonce},signature={signature_b58}"

    return payment_header, payer_address

if __name__ == "__main__":
    # Configuration
    AGENT_KEYPAIR = "/tmp/agent-keypair.json"
    BACKEND_PUBKEY = "BAikRH6xfHd6YG777XFQw85LGEEehTeqRtDiVpJLJiBo"
    USDC_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    AMOUNT = 100  # $0.0001 USDC (premium for $0.01 coverage at 1%)

    payment_header, payer = generate_signed_payment(
        AGENT_KEYPAIR,
        BACKEND_PUBKEY,
        USDC_MINT,
        AMOUNT
    )

    print(f"\n✅ Generated signed x402 payment:")
    print(f"X-Payment: {payment_header}")
    print(f"X-Payer: {payer}")
