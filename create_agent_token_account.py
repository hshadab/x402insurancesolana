#!/usr/bin/env python3
"""
Create an Associated Token Account (ATA) for the agent wallet to receive USDC
"""
import json
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.transaction import Transaction
from spl.token.instructions import get_associated_token_address, create_associated_token_account
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID

# Configuration
AGENT_KEYPAIR_PATH = "/tmp/agent-keypair.json"
USDC_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
RPC_URL = "https://api.devnet.solana.com"

def create_token_account():
    """Create USDC token account for agent wallet"""

    # Load agent keypair
    with open(AGENT_KEYPAIR_PATH, 'r') as f:
        keypair_bytes = bytes(json.load(f))
    agent_keypair = Keypair.from_bytes(keypair_bytes)
    agent_pubkey = agent_keypair.pubkey()

    print(f"Agent wallet: {agent_pubkey}")

    # Connect to Solana
    client = Client(RPC_URL)

    # Get USDC mint
    usdc_mint = Pubkey.from_string(USDC_MINT)

    # Calculate ATA address
    ata_address = get_associated_token_address(agent_pubkey, usdc_mint)
    print(f"Associated Token Account: {ata_address}")

    # Check if ATA already exists
    account_info = client.get_account_info(ata_address)
    if account_info.value is not None:
        print("✅ Token account already exists!")
        return str(ata_address)

    print("Creating Associated Token Account...")

    # Create ATA instruction
    create_ata_ix = create_associated_token_account(
        payer=agent_pubkey,
        owner=agent_pubkey,
        mint=usdc_mint
    )

    # Build and send transaction
    recent_blockhash = client.get_latest_blockhash().value.blockhash
    transaction = Transaction(recent_blockhash=recent_blockhash)
    transaction.add(create_ata_ix)
    transaction.sign(agent_keypair)

    # Send transaction
    result = client.send_transaction(transaction, agent_keypair)
    tx_sig = result.value
    print(f"Transaction sent: {tx_sig}")

    # Confirm transaction
    client.confirm_transaction(tx_sig)
    print(f"✅ Token account created successfully!")
    print(f"🔗 View on explorer: https://explorer.solana.com/tx/{tx_sig}?cluster=devnet")

    return str(ata_address)

if __name__ == "__main__":
    try:
        ata = create_token_account()
        print(f"\n✅ Agent wallet is now ready to receive USDC at: {ata}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
