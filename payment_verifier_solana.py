"""
x402 Payment Verification Module for Solana

Handles verification of x402 payments on Solana including:
- ed25519 signature verification
- Timestamp/expiry validation
- Replay attack prevention
- Amount verification
"""
from solders.pubkey import Pubkey
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import base58
import time
import logging
import json
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger("x402insurance.payment_verifier_solana")


@dataclass
class PaymentDetailsSolana:
    """Verified payment details for Solana"""
    payer: str  # Base58 public key
    amount_units: int  # Micro-USDC (6 decimals)
    asset: str  # USDC mint address
    pay_to: str  # Backend public key
    timestamp: int
    nonce: str
    signature: str
    is_valid: bool


class PaymentVerifierSolana:
    """Verify x402 payments on Solana with ed25519 signatures"""

    def __init__(self, backend_pubkey: str, usdc_mint: str):
        """
        Initialize Solana payment verifier

        Args:
            backend_pubkey: Backend wallet public key (base58)
            usdc_mint: USDC SPL token mint address (base58)
        """
        self.backend_pubkey = backend_pubkey
        self.usdc_mint = usdc_mint
        self.nonce_cache = {}  # In-memory nonce tracking
        self.cache_cleanup_interval = 3600  # Clean up every hour
        self.last_cleanup = time.time()

    def verify_payment(
        self,
        payment_header: str,
        payer_address: Optional[str],
        required_amount: int,
        max_age_seconds: int = 300  # 5 minutes
    ) -> PaymentDetailsSolana:
        """
        Verify x402 payment from Solana wallet

        Args:
            payment_header: X-Payment header value
            payer_address: X-Payer header (Solana public key, base58)
            required_amount: Expected payment in micro-USDC (6 decimals)
            max_age_seconds: Maximum timestamp age

        Returns:
            PaymentDetailsSolana with is_valid flag
        """
        try:
            # Parse payment header
            payment_data = self._parse_payment_header(payment_header)

            if not payment_data:
                return PaymentDetailsSolana(
                    payer="", amount_units=0, asset="", pay_to="",
                    timestamp=0, nonce="", signature="", is_valid=False
                )

            # Extract fields
            payer = payment_data.get('payer', payer_address or '')
            amount = int(payment_data.get('amount', 0))
            asset = payment_data.get('asset', self.usdc_mint)
            pay_to = payment_data.get('payTo', self.backend_pubkey)
            timestamp = int(payment_data.get('timestamp', 0))
            nonce = payment_data.get('nonce', '')
            signature = payment_data.get('signature', '')

            # Validate basic fields
            if not all([payer, amount, asset, pay_to, timestamp, nonce, signature]):
                logger.warning("Missing required payment fields")
                return PaymentDetailsSolana(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Validate amount
            if amount != required_amount:
                logger.warning(
                    f"Payment amount mismatch: provided={amount} required={required_amount}"
                )
                return PaymentDetailsSolana(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Validate recipient
            if pay_to != self.backend_pubkey:
                logger.warning(
                    f"Payment recipient mismatch: provided={pay_to} expected={self.backend_pubkey}"
                )
                return PaymentDetailsSolana(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Validate asset (USDC mint)
            if asset != self.usdc_mint:
                logger.warning(
                    f"Payment asset mismatch: provided={asset} expected={self.usdc_mint}"
                )
                return PaymentDetailsSolana(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Validate timestamp
            current_time = int(time.time())
            if timestamp > current_time + 60:  # Allow 60s clock skew
                logger.warning(f"Payment timestamp in future: {timestamp}")
                return PaymentDetailsSolana(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            if current_time - timestamp > max_age_seconds:
                logger.warning(
                    f"Payment timestamp too old: {current_time - timestamp}s (max: {max_age_seconds}s)"
                )
                return PaymentDetailsSolana(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Check for replay attack
            if self._is_nonce_used(payer, nonce):
                logger.warning(f"Nonce already used: payer={payer} nonce={nonce}")
                return PaymentDetailsSolana(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Verify ed25519 signature
            is_valid = self._verify_signature(
                payer=payer,
                amount=amount,
                asset=asset,
                pay_to=pay_to,
                timestamp=timestamp,
                nonce=nonce,
                signature=signature
            )

            if is_valid:
                self._mark_nonce_used(payer, nonce, timestamp)
                logger.info(f"Payment verified successfully: payer={payer} amount={amount}")
            else:
                logger.warning(f"Payment signature verification failed: payer={payer}")

            return PaymentDetailsSolana(
                payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                timestamp=timestamp, nonce=nonce, signature=signature, is_valid=is_valid
            )

        except Exception as e:
            logger.exception(f"Payment verification error: {e}")
            return PaymentDetailsSolana(
                payer="", amount_units=0, asset="", pay_to="",
                timestamp=0, nonce="", signature="", is_valid=False
            )

    def _parse_payment_header(self, payment_header: str) -> Optional[Dict]:
        """Parse x402 payment header"""
        try:
            # Format: key=value,key=value
            parts = {}
            for item in payment_header.split(','):
                if '=' in item:
                    key, value = item.split('=', 1)
                    parts[key.strip()] = value.strip()
            return parts
        except Exception as e:
            logger.exception(f"Error parsing payment header: {e}")
            return None

    def _verify_signature(
        self,
        payer: str,
        amount: int,
        asset: str,
        pay_to: str,
        timestamp: int,
        nonce: str,
        signature: str
    ) -> bool:
        """
        Verify ed25519 signature for Solana payment

        Message format (JSON):
        {
            "payer": "<base58_pubkey>",
            "amount": 1000000,
            "asset": "<usdc_mint>",
            "payTo": "<backend_pubkey>",
            "timestamp": 1699999999,
            "nonce": "unique_nonce"
        }
        """
        try:
            # Construct message to verify
            message_data = {
                "payer": payer,
                "amount": amount,
                "asset": asset,
                "payTo": pay_to,
                "timestamp": timestamp,
                "nonce": nonce
            }

            # Serialize to JSON (deterministic order)
            message = json.dumps(message_data, sort_keys=True)
            message_bytes = message.encode('utf-8')

            # Decode signature from base58
            try:
                signature_bytes = base58.b58decode(signature)
            except Exception as e:
                logger.warning(f"Failed to decode signature from base58: {e}")
                return False

            # Decode payer public key from base58
            try:
                payer_pubkey_bytes = base58.b58decode(payer)
            except Exception as e:
                logger.warning(f"Failed to decode payer pubkey from base58: {e}")
                return False

            # Verify signature using ed25519
            verify_key = VerifyKey(payer_pubkey_bytes)

            try:
                verify_key.verify(message_bytes, signature_bytes)
                return True
            except BadSignatureError:
                logger.warning("Signature verification failed: bad signature")
                return False

        except Exception as e:
            logger.exception(f"Signature verification error: {e}")
            return False

    def _is_nonce_used(self, payer: str, nonce: str) -> bool:
        """Check if nonce has been used"""
        key = f"{payer}:{nonce}"

        # Cleanup old nonces periodically
        if time.time() - self.last_cleanup > self.cache_cleanup_interval:
            self._cleanup_old_nonces()

        return key in self.nonce_cache

    def _mark_nonce_used(self, payer: str, nonce: str, timestamp: int):
        """Mark nonce as used"""
        key = f"{payer}:{nonce}"
        self.nonce_cache[key] = timestamp

    def _cleanup_old_nonces(self):
        """Remove nonces older than 1 hour"""
        current_time = int(time.time())
        cutoff_time = current_time - 3600

        old_nonces = [
            key for key, ts in self.nonce_cache.items()
            if ts < cutoff_time
        ]

        for key in old_nonces:
            del self.nonce_cache[key]

        self.last_cleanup = current_time
        logger.info(f"Cleaned up {len(old_nonces)} old nonces")


class SimplePaymentVerifierSolana:
    """
    Simplified payment verifier for Solana testing/development

    Only validates amount and basic fields, skips signature verification.
    Use PaymentVerifierSolana for production.
    """

    def __init__(self, backend_pubkey: str, usdc_mint: str):
        self.backend_pubkey = backend_pubkey
        self.usdc_mint = usdc_mint

    def verify_payment(
        self,
        payment_header: str,
        payer_address: Optional[str],
        required_amount: int,
        max_age_seconds: int = 300
    ) -> PaymentDetailsSolana:
        """Simple payment verification for testing"""
        try:
            # Parse simple format
            parts = {}
            for item in payment_header.split(','):
                if '=' in item:
                    key, value = item.split('=', 1)
                    parts[key.strip().lower()] = value.strip()

            amount = int(parts.get('amount', 0)) if parts.get('amount') else None

            if amount is None or amount != required_amount:
                return PaymentDetailsSolana(
                    payer=payer_address or "",
                    amount_units=amount or 0,
                    asset=self.usdc_mint,
                    pay_to=self.backend_pubkey,
                    timestamp=int(time.time()),
                    nonce="",
                    signature=parts.get('signature', ''),
                    is_valid=False
                )

            # Mock successful verification
            return PaymentDetailsSolana(
                payer=payer_address or "11111111111111111111111111111111",  # Default Solana pubkey
                amount_units=amount,
                asset=self.usdc_mint,
                pay_to=self.backend_pubkey,
                timestamp=int(time.time()),
                nonce=parts.get('token', ''),
                signature=parts.get('signature', ''),
                is_valid=True
            )

        except Exception as e:
            logger.exception(f"Simple payment verification error: {e}")
            return PaymentDetailsSolana(
                payer="", amount_units=0, asset="", pay_to="",
                timestamp=0, nonce="", signature="", is_valid=False
            )
