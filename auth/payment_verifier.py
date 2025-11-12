"""
x402 Payment Verification Module

Handles proper verification of x402 payments including:
- EIP-712 signature verification
- Timestamp/expiry validation
- Replay attack prevention
- Amount verification
"""
from eth_account import Account
from eth_account.messages import encode_structured_data
from web3 import Web3
import time
import logging
import json
import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("x402insurance.payment_verifier")


@dataclass
class PaymentDetails:
    """Verified payment details"""
    payer: str
    amount_units: int
    asset: str
    pay_to: str
    timestamp: int
    nonce: str
    signature: str
    is_valid: bool


class PaymentVerifier:
    """Verify x402 payments with proper signature validation"""

    def __init__(self, backend_address: str, usdc_address: str, data_dir: Path = None):
        self.backend_address = Web3.to_checksum_address(backend_address)
        self.usdc_address = Web3.to_checksum_address(usdc_address)

        # Persistent nonce storage (survives server restarts)
        self.data_dir = data_dir or Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.nonce_file = self.data_dir / "nonce_cache.json"

        # Load existing nonces from persistent storage
        self.nonce_cache = self._load_nonces()
        self.cache_cleanup_interval = 3600  # Clean up old nonces every hour
        self.last_cleanup = time.time()

    def verify_payment(
        self,
        payment_header: str,
        payer_address: Optional[str],
        required_amount: int,
        max_age_seconds: int = 300  # 5 minutes
    ) -> PaymentDetails:
        """
        Verify x402 payment from headers

        Args:
            payment_header: X-Payment header value
            payer_address: X-Payer or X-From-Address header value
            required_amount: Expected payment amount in USDC units (6 decimals)
            max_age_seconds: Maximum age of payment timestamp

        Returns:
            PaymentDetails with is_valid flag
        """
        try:
            # Parse payment header
            payment_data = self._parse_payment_header(payment_header)

            if not payment_data:
                return PaymentDetails(
                    payer="", amount_units=0, asset="", pay_to="",
                    timestamp=0, nonce="", signature="", is_valid=False
                )

            # Extract fields
            payer = payment_data.get('payer', payer_address or '')
            amount = int(payment_data.get('amount', 0))
            asset = payment_data.get('asset', self.usdc_address)
            pay_to = payment_data.get('payTo', self.backend_address)
            timestamp = int(payment_data.get('timestamp', 0))
            nonce = payment_data.get('nonce', '')
            signature = payment_data.get('signature', '')

            # Validate basic fields
            if not all([payer, amount, asset, pay_to, timestamp, nonce, signature]):
                logger.warning("Missing required payment fields")
                return PaymentDetails(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Validate amount matches
            if amount != required_amount:
                logger.warning(
                    "Payment amount mismatch: provided=%s required=%s",
                    amount, required_amount
                )
                return PaymentDetails(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Validate recipient
            if Web3.to_checksum_address(pay_to) != self.backend_address:
                logger.warning(
                    "Payment recipient mismatch: provided=%s expected=%s",
                    pay_to, self.backend_address
                )
                return PaymentDetails(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Validate asset
            if Web3.to_checksum_address(asset) != self.usdc_address:
                logger.warning(
                    "Payment asset mismatch: provided=%s expected=%s",
                    asset, self.usdc_address
                )
                return PaymentDetails(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Validate timestamp (not too old, not in future)
            current_time = int(time.time())
            if timestamp > current_time + 60:  # Allow 60s clock skew
                logger.warning("Payment timestamp in future: %s", timestamp)
                return PaymentDetails(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            if current_time - timestamp > max_age_seconds:
                logger.warning(
                    "Payment timestamp too old: %s (max age: %s)",
                    current_time - timestamp, max_age_seconds
                )
                return PaymentDetails(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Check for replay attack (nonce reuse)
            if self._is_nonce_used(payer, nonce):
                logger.warning("Nonce already used: payer=%s nonce=%s", payer, nonce)
                return PaymentDetails(
                    payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                    timestamp=timestamp, nonce=nonce, signature=signature, is_valid=False
                )

            # Verify EIP-712 signature
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
                # Mark nonce as used
                self._mark_nonce_used(payer, nonce, timestamp)
                logger.info("Payment verified successfully: payer=%s amount=%s", payer, amount)
            else:
                logger.warning("Payment signature verification failed: payer=%s", payer)

            return PaymentDetails(
                payer=payer, amount_units=amount, asset=asset, pay_to=pay_to,
                timestamp=timestamp, nonce=nonce, signature=signature, is_valid=is_valid
            )

        except Exception as e:
            logger.exception("Payment verification error: %s", e)
            return PaymentDetails(
                payer="", amount_units=0, asset="", pay_to="",
                timestamp=0, nonce="", signature="", is_valid=False
            )

    def _parse_payment_header(self, payment_header: str) -> Optional[Dict]:
        """Parse x402 payment header"""
        try:
            # Simple comma-separated format: key=value,key=value
            parts = {}
            for item in payment_header.split(','):
                if '=' in item:
                    key, value = item.split('=', 1)
                    parts[key.strip()] = value.strip()
            return parts
        except Exception as e:
            logger.exception("Error parsing payment header: %s", e)
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
        Verify EIP-712 signature for x402 payment

        This implements a simplified EIP-712 signature verification.
        In production, use the exact domain and message structure from x402 spec.
        """
        try:
            # Define EIP-712 domain
            domain_data = {
                "name": "x402 Payment",
                "version": "1",
                "chainId": 8453,  # Base Mainnet
            }

            # Define message structure
            message_types = {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                ],
                "Payment": [
                    {"name": "payer", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "asset", "type": "address"},
                    {"name": "payTo", "type": "address"},
                    {"name": "timestamp", "type": "uint256"},
                    {"name": "nonce", "type": "string"},
                ]
            }

            message_data = {
                "payer": Web3.to_checksum_address(payer),
                "amount": amount,
                "asset": Web3.to_checksum_address(asset),
                "payTo": Web3.to_checksum_address(pay_to),
                "timestamp": timestamp,
                "nonce": nonce,
            }

            # Encode structured data
            structured_msg = {
                "types": message_types,
                "primaryType": "Payment",
                "domain": domain_data,
                "message": message_data,
            }

            encoded_msg = encode_structured_data(structured_msg)

            # Recover signer address from signature
            recovered_address = Account.recover_message(encoded_msg, signature=signature)

            # Verify recovered address matches payer
            is_valid = recovered_address.lower() == payer.lower()

            return is_valid

        except Exception as e:
            logger.exception("Signature verification error: %s", e)
            return False

    def _is_nonce_used(self, payer: str, nonce: str) -> bool:
        """Check if nonce has been used (replay attack prevention)"""
        key = f"{payer.lower()}:{nonce}"

        # Cleanup old nonces periodically
        if time.time() - self.last_cleanup > self.cache_cleanup_interval:
            self._cleanup_old_nonces()

        return key in self.nonce_cache

    def _load_nonces(self) -> dict:
        """Load nonces from persistent storage"""
        if not self.nonce_file.exists():
            logger.info("No existing nonce cache found, starting fresh")
            return {}
        try:
            with open(self.nonce_file, 'r') as f:
                nonces = json.load(f)
            logger.info("Loaded %d nonces from persistent storage", len(nonces))
            return nonces
        except Exception as e:
            logger.exception("Failed to load nonce cache: %s", e)
            return {}

    def _save_nonces(self):
        """Save nonces to persistent storage"""
        try:
            import tempfile
            # Atomic write using temp file
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self.nonce_file.parent,
                prefix=f".{self.nonce_file.name}.",
                suffix=".tmp",
                text=True
            )
            try:
                with os.fdopen(temp_fd, 'w') as f:
                    json.dump(self.nonce_cache, f, indent=2)
                os.replace(temp_path, self.nonce_file)
                logger.debug("Saved %d nonces to persistent storage", len(self.nonce_cache))
            except Exception:
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass
                raise
        except Exception as e:
            logger.exception("Failed to save nonce cache: %s", e)

    def _mark_nonce_used(self, payer: str, nonce: str, timestamp: int):
        """Mark nonce as used and persist to disk"""
        key = f"{payer.lower()}:{nonce}"
        self.nonce_cache[key] = timestamp
        # Save immediately to prevent replay attacks across restarts
        self._save_nonces()

    def _cleanup_old_nonces(self):
        """Remove nonces older than 1 hour and persist"""
        current_time = int(time.time())
        cutoff_time = current_time - 3600  # 1 hour ago

        old_nonces = [
            key for key, timestamp in self.nonce_cache.items()
            if timestamp < cutoff_time
        ]

        for key in old_nonces:
            del self.nonce_cache[key]

        self.last_cleanup = current_time
        logger.info("Cleaned up %d old nonces", len(old_nonces))

        # Save after cleanup
        if old_nonces:
            self._save_nonces()


class SimplePaymentVerifier:
    """
    Simplified payment verifier for testing/development

    Only validates amount and basic fields, skips signature verification.
    Use PaymentVerifier for production.
    """

    def __init__(self, backend_address: str, usdc_address: str):
        self.backend_address = backend_address
        self.usdc_address = usdc_address

    def verify_payment(
        self,
        payment_header: str,
        payer_address: Optional[str],
        required_amount: int,
        max_age_seconds: int = 300
    ) -> PaymentDetails:
        """Simple payment verification for testing"""
        try:
            # Parse simple format: token=...,amount=...,signature=...
            parts = {}
            for item in payment_header.split(','):
                if '=' in item:
                    key, value = item.split('=', 1)
                    parts[key.strip().lower()] = value.strip()

            amount = int(parts.get('amount', 0)) if parts.get('amount') else None

            if amount is None or amount != required_amount:
                return PaymentDetails(
                    payer=payer_address or "",
                    amount_units=amount or 0,
                    asset=self.usdc_address,
                    pay_to=self.backend_address,
                    timestamp=int(time.time()),
                    nonce="",
                    signature=parts.get('signature', ''),
                    is_valid=False
                )

            return PaymentDetails(
                payer=payer_address or "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                amount_units=amount,
                asset=self.usdc_address,
                pay_to=self.backend_address,
                timestamp=int(time.time()),
                nonce=parts.get('token', ''),
                signature=parts.get('signature', ''),
                is_valid=True
            )

        except Exception as e:
            logger.exception("Simple payment verification error: %s", e)
            return PaymentDetails(
                payer="", amount_units=0, asset="", pay_to="",
                timestamp=0, nonce="", signature="", is_valid=False
            )
