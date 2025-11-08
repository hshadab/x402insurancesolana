"""
Blockchain service - USDC refunds on Base
"""
from web3 import Web3
import os

# ERC20 ABI (minimal - transfer and balanceOf)
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]


class BlockchainClient:
    def __init__(self, rpc_url: str, usdc_address: str, private_key: str = None):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        # Note: POA middleware removed for simplicity (add back if needed for Base)

        self.has_wallet = bool(private_key)

        if self.has_wallet:
            self.account = self.w3.eth.account.from_key(private_key)
            self.usdc_address = Web3.to_checksum_address(usdc_address)
            self.usdc = self.w3.eth.contract(address=self.usdc_address, abi=ERC20_ABI)
            print(f"✅ Blockchain initialized with wallet: {self.account.address}")
        else:
            print(f"⚠️  No private key, using MOCK mode for refunds")

    def issue_refund(self, to_address: str, amount: int) -> str:
        """
        Issue USDC refund

        Args:
            to_address: Recipient address
            amount: Amount in USDC (6 decimals)

        Returns:
            Transaction hash
        """
        if not self.has_wallet:
            # Mock mode
            return f"0xMOCK{amount:016x}1234567890abcdef" * 2

        to_address = Web3.to_checksum_address(to_address)

        # Build transaction
        tx = self.usdc.functions.transfer(
            to_address,
            amount
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price
        })

        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        # Handle both old and new web3.py versions
        raw_tx = signed_tx.raw_transaction if hasattr(signed_tx, 'raw_transaction') else signed_tx.rawTransaction
        tx_hash = self.w3.eth.send_raw_transaction(raw_tx)

        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status != 1:
            raise Exception(f"Transaction failed: {tx_hash.hex()}")

        return tx_hash.hex()
