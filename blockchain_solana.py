"""
Blockchain service - USDC refunds on Solana

Features:
- SPL Token USDC transfers
- Solana transaction signing (ed25519)
- Balance checking
- Retry logic for failed transactions
- Support for both mainnet-beta and devnet
"""
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.transaction import Transaction
from solders.instruction import Instruction
from solders.system_program import TransferParams, transfer
from solders.compute_budget import set_compute_unit_price, set_compute_unit_limit
from spl.token.instructions import transfer_checked, TransferCheckedParams, get_associated_token_address
from spl.token.constants import TOKEN_PROGRAM_ID
import os
import json
import logging
import time
from typing import Optional
import base58


class BlockchainClientSolana:
    """Solana blockchain client for USDC transfers"""

    def __init__(
        self,
        rpc_url: str,
        usdc_mint: str,
        keypair_path: str = None,
        cluster: str = "devnet",
        max_retries: int = 3
    ):
        """
        Initialize Solana blockchain client

        Args:
            rpc_url: Solana RPC endpoint URL
            usdc_mint: USDC token mint address
            keypair_path: Path to keypair JSON file
            cluster: Solana cluster (mainnet-beta, devnet, testnet)
            max_retries: Maximum number of retry attempts
        """
        self.client = Client(rpc_url)
        self.cluster = cluster
        self.max_retries = max_retries
        self.has_wallet = bool(keypair_path)
        self.logger = logging.getLogger("x402insurance.blockchain_solana")

        # USDC mint address
        self.usdc_mint = Pubkey.from_string(usdc_mint)

        if self.has_wallet and keypair_path:
            try:
                # Load keypair from file
                with open(keypair_path, 'r') as f:
                    import json
                    secret_key = json.load(f)
                    if isinstance(secret_key, list):
                        # Convert list to bytes
                        secret_key = bytes(secret_key)

                        # Handle both 32-byte seeds and 64-byte keypairs
                    if len(secret_key) == 32:
                        # 32-byte seed - regenerate the full keypair
                        # Create a temporary keypair to get the full bytes
                        temp_kp = Keypair()
                        # Actually, we just use from_seed() - but solders doesn't have that!
                        # So we need to use the ed25519 library directly
                        from cryptography.hazmat.primitives.asymmetric import ed25519
                        from cryptography.hazmat.primitives import serialization

                        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_key)
                        # Get both private and public key bytes
                        private_bytes = private_key.private_bytes(
                            encoding=serialization.Encoding.Raw,
                            format=serialization.PrivateFormat.Raw,
                            encryption_algorithm=serialization.NoEncryption()
                        )
                        public_bytes = private_key.public_key().public_bytes(
                            encoding=serialization.Encoding.Raw,
                            format=serialization.PublicFormat.Raw
                        )
                        full_keypair = private_bytes + public_bytes
                        self.keypair = Keypair.from_bytes(full_keypair)
                    elif len(secret_key) == 64:
                        # Full 64-byte keypair
                        self.keypair = Keypair.from_bytes(secret_key)
                    else:
                        raise ValueError(f"Invalid keypair length: {len(secret_key)} (expected 32 or 64)")

                    self.pubkey = self.keypair.pubkey()
                    self.logger.info(f"Solana wallet initialized: {str(self.pubkey)}")
            except Exception as e:
                self.logger.error(f"Failed to load keypair: {e}")
                self.has_wallet = False
                self.logger.warning("Using MOCK mode for refunds")
        else:
            self.logger.warning("No keypair provided, using MOCK mode for refunds")

    def get_balance(self, address: Optional[str] = None) -> int:
        """
        Get USDC balance (SPL Token)

        Args:
            address: Public key to check (defaults to self)

        Returns:
            Balance in USDC units (6 decimals)
        """
        if not self.has_wallet:
            return 0

        try:
            # Get the address to check
            pubkey = Pubkey.from_string(address) if address else self.pubkey

            # Get associated token account for USDC
            ata = get_associated_token_address(pubkey, self.usdc_mint)

            # Get token account balance
            response = self.client.get_token_account_balance(ata)

            # Check if response is successful (has .value attribute)
            if hasattr(response, 'value') and response.value:
                # Return balance in raw units (micro USDC)
                return int(response.value.amount)

            # Token account doesn't exist or RPC error
            self.logger.debug(f"Token account not found or RPC error for {ata}")
            return 0

        except Exception as e:
            self.logger.debug(f"Error getting USDC balance: {e}")
            return 0

    def get_sol_balance(self, address: Optional[str] = None) -> int:
        """
        Get SOL balance in lamports

        Args:
            address: Public key to check (defaults to self)

        Returns:
            Balance in lamports (1 SOL = 10^9 lamports)
        """
        if not self.has_wallet:
            return 0

        try:
            pubkey = Pubkey.from_string(address) if address else self.pubkey
            response = self.client.get_balance(pubkey)
            return response.value if response.value else 0
        except Exception as e:
            self.logger.exception(f"Error getting SOL balance: {e}")
            return 0

    def issue_refund(self, to_address: str, amount: int) -> str:
        """
        Issue USDC refund via SPL Token transfer

        Args:
            to_address: Recipient Solana public key (base58)
            amount: Amount in USDC units (6 decimals, e.g., 1000000 = 1 USDC)

        Returns:
            Transaction signature (base58)

        Raises:
            Exception: If refund fails after retries
        """
        if not self.has_wallet:
            # Mock mode - generate a valid-looking Solana signature (base58, ~88 chars)
            self.logger.info(f"Mock refund to {to_address} for {amount} micro-USDC")
            import random
            import string
            # Generate a realistic looking base58 signature
            base58_chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
            mock_sig = ''.join(random.choice(base58_chars) for _ in range(88))
            return mock_sig

        to_pubkey = Pubkey.from_string(to_address)

        # Check USDC balance
        balance = self.get_balance()
        if balance < amount:
            raise Exception(
                f"Insufficient USDC balance: have {balance} micro-USDC, need {amount} micro-USDC"
            )

        # Check SOL balance for transaction fees
        sol_balance = self.get_sol_balance()
        min_sol_balance = 5000  # 0.000005 SOL minimum for fees
        if sol_balance < min_sol_balance:
            raise Exception(
                f"Insufficient SOL for transaction fees: have {sol_balance} lamports"
            )

        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt + 1}/{self.max_retries}")
                    time.sleep(2 ** attempt)  # Exponential backoff

                tx_sig = self._send_usdc_transfer(to_pubkey, amount)
                self.logger.info(f"Refund successful: tx={tx_sig}")
                return tx_sig

            except Exception as e:
                last_error = e
                self.logger.warning(f"Transaction failed on attempt {attempt + 1}: {e}")
                continue

        # All retries failed
        raise Exception(f"Refund failed after {self.max_retries} attempts: {last_error}")

    def _send_usdc_transfer(self, to_pubkey: Pubkey, amount: int) -> str:
        """
        Internal method to send USDC via SPL Token transfer

        Args:
            to_pubkey: Recipient public key
            amount: Amount in micro-USDC

        Returns:
            Transaction signature (base58)
        """
        # Get associated token accounts
        from_ata = get_associated_token_address(self.pubkey, self.usdc_mint)
        to_ata = get_associated_token_address(to_pubkey, self.usdc_mint)

        # Build SPL token transfer instruction
        transfer_ix = transfer_checked(
            TransferCheckedParams(
                program_id=TOKEN_PROGRAM_ID,
                source=from_ata,
                mint=self.usdc_mint,
                dest=to_ata,
                owner=self.pubkey,
                amount=amount,
                decimals=6,  # USDC has 6 decimals
            )
        )

        # Add compute budget instructions for priority fees
        compute_price_ix = set_compute_unit_price(1000)  # 0.000001 SOL per CU
        compute_limit_ix = set_compute_unit_limit(200_000)  # Max 200k compute units

        # Get recent blockhash
        blockhash_resp = self.client.get_latest_blockhash()
        recent_blockhash = blockhash_resp.value.blockhash

        # Build transaction with blockhash included
        transaction = Transaction.new_signed_with_payer(
            [compute_price_ix, compute_limit_ix, transfer_ix],
            self.pubkey,
            [self.keypair],
            recent_blockhash
        )

        # Send transaction as raw bytes (already signed)
        serialized_tx = bytes(transaction)
        tx_resp = self.client.send_raw_transaction(serialized_tx)

        tx_sig = str(tx_resp.value)
        self.logger.info(f"Transaction sent: {tx_sig}")

        # Wait for confirmation - convert string to Signature object
        tx_sig_obj = Signature.from_string(tx_sig)
        confirm_resp = self.client.confirm_transaction(
            tx_sig_obj,
            commitment=Confirmed
        )

        if not confirm_resp.value:
            raise Exception(f"Transaction failed to confirm: {tx_sig}")

        self.logger.info(f"Transaction confirmed: {tx_sig}")
        return tx_sig

    def get_transaction_url(self, tx_sig: str) -> str:
        """
        Get Solana Explorer URL for transaction

        Args:
            tx_sig: Transaction signature

        Returns:
            Explorer URL
        """
        cluster_param = "" if self.cluster == "mainnet-beta" else f"?cluster={self.cluster}"
        return f"https://explorer.solana.com/tx/{tx_sig}{cluster_param}"

    def get_wallet_address(self) -> Optional[str]:
        """Get wallet public key as base58 string"""
        if self.has_wallet:
            return str(self.pubkey)
        return None

    def store_proof_on_chain(
        self,
        claim_id: str,
        proof_hash: str,
        http_status: int,
        payout_amount: int
    ) -> str:
        """
        Store proof attestation data on Solana blockchain using Memo program.
        This creates a publicly viewable, immutable record of the ZKP verification.

        Args:
            claim_id: UUID of the claim
            proof_hash: Blake3 hash of the zkEngine proof (hex string)
            http_status: HTTP status code from failed API (e.g., 503)
            payout_amount: Payout in micro-USDC (e.g., 10000 = 0.01 USDC)

        Returns:
            Transaction signature (base58 string)

        Raises:
            Exception: If transaction fails
        """
        if not self.has_wallet:
            raise Exception("No wallet configured - cannot store proof on-chain")

        # Solana Memo program ID
        MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")

        # Create attestation data (publicly viewable JSON)
        attestation = {
            "type": "x402_proof_attestation",
            "version": "1.0",
            "claim_id": claim_id,
            "proof_hash": proof_hash,
            "http_status": http_status,
            "payout_amount": payout_amount,
            "payout_usdc": f"{payout_amount / 1_000_000:.6f}",
            "timestamp": int(time.time())
        }

        # Convert to UTF-8 bytes for memo
        memo_data = json.dumps(attestation, separators=(',', ':')).encode('utf-8')

        self.logger.info(f"Storing proof attestation on-chain: claim_id={claim_id}, size={len(memo_data)} bytes")

        # Create memo instruction
        memo_ix = Instruction(
            program_id=MEMO_PROGRAM_ID,
            data=memo_data,
            accounts=[]
        )

        # Send transaction with retry logic
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Sending proof attestation transaction (attempt {attempt + 1}/{self.max_retries})")

                # Get fresh blockhash for each attempt
                recent_blockhash = self.client.get_latest_blockhash().value.blockhash

                # Build and sign transaction (no compute budget needed for memo)
                tx = Transaction.new_signed_with_payer(
                    [memo_ix],
                    self.pubkey,
                    [self.keypair],
                    recent_blockhash
                )

                # Serialize the signed transaction and send as raw
                serialized_tx = bytes(tx)
                result = self.client.send_raw_transaction(serialized_tx)

                tx_sig = str(result.value)
                self.logger.info(f"Proof attestation transaction sent: {tx_sig}")

                # Wait for confirmation
                max_wait = 30
                start_time = time.time()

                while time.time() - start_time < max_wait:
                    # Convert string signature to Signature object for API call
                    tx_sig_obj = Signature.from_string(tx_sig)
                    status = self.client.get_signature_statuses([tx_sig_obj]).value[0]

                    if status is not None:
                        # Get confirmation status (it's an enum object, need to convert to string)
                        conf_status = status.confirmation_status
                        if conf_status:
                            # Convert enum to lowercase string for comparison
                            conf_status_str = str(conf_status).split('.')[-1].lower()

                            if conf_status_str in ["confirmed", "finalized"]:
                                self.logger.info(f"Proof attestation {conf_status_str}: {tx_sig}")
                                self.logger.info(f"View on explorer: {self.get_transaction_url(tx_sig)}")
                                return tx_sig

                        if status.err:
                            raise Exception(f"Transaction failed: {status.err}")

                    time.sleep(0.5)

                # If we got here, transaction didn't confirm in time
                self.logger.warning(f"Proof attestation not confirmed after {max_wait}s, retrying...")

            except Exception as e:
                import traceback
                self.logger.error(f"Proof attestation attempt {attempt + 1} failed: {e}")
                self.logger.error(f"Traceback:\n{traceback.format_exc()}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

        raise Exception(f"Failed to store proof on-chain after {self.max_retries} attempts")
