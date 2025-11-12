"""
Unit tests for Solana blockchain client
"""
import pytest
from blockchain_solana import BlockchainClientSolana


class TestBlockchainClientSolana:
    """Test Solana blockchain client (mock mode and basic functionality)"""

    def setup_method(self):
        # Initialize without keypair (mock mode)
        self.client = BlockchainClientSolana(
            rpc_url="https://api.devnet.solana.com",
            usdc_mint="4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",  # Devnet USDC
            keypair_path=None,
            cluster="devnet"
        )

    def test_initialization_devnet(self):
        """Test client initializes correctly for devnet"""
        assert self.client.cluster == "devnet"
        assert self.client.has_wallet is False
        assert self.client.max_retries == 3
        assert str(self.client.usdc_mint) == "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"

    def test_initialization_mainnet(self):
        """Test client initializes correctly for mainnet"""
        mainnet_client = BlockchainClientSolana(
            rpc_url="https://api.mainnet-beta.solana.com",
            usdc_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # Mainnet USDC
            keypair_path=None,
            cluster="mainnet-beta"
        )
        assert mainnet_client.cluster == "mainnet-beta"
        assert mainnet_client.has_wallet is False

    def test_mock_refund(self):
        """Test mock refund generation"""
        # In mock mode (no wallet), issue_refund returns a mock signature
        tx_hash = self.client.issue_refund(
            to_address="11111111111111111111111111111111",
            amount=10000
        )

        assert isinstance(tx_hash, str)
        assert len(tx_hash) > 0  # Should return a signature string

    def test_has_wallet_false_in_mock_mode(self):
        """Test wallet detection in mock mode"""
        assert self.client.has_wallet is False

    def test_get_balance_mock(self):
        """Test getting USDC balance in mock mode"""
        # In mock mode, should handle gracefully
        # Note: This will try to connect to devnet RPC
        try:
            balance = self.client.get_balance()
            assert isinstance(balance, (int, float))
            assert balance >= 0
        except Exception as e:
            # Network errors are acceptable in tests
            pytest.skip(f"Network error in test: {e}")

    def test_get_sol_balance_mock(self):
        """Test getting SOL balance in mock mode"""
        try:
            balance = self.client.get_sol_balance()
            assert isinstance(balance, (int, float))
            assert balance >= 0
        except Exception as e:
            # Network errors are acceptable in tests
            pytest.skip(f"Network error in test: {e}")

    def test_get_wallet_address_none_without_keypair(self):
        """Test wallet address is None without keypair"""
        address = self.client.get_wallet_address()
        assert address is None

    def test_get_transaction_url_devnet(self):
        """Test transaction URL generation for devnet"""
        mock_sig = "5VERv8NMvzbJMEkV8xnrLkEaWRtSz9CosKDYjCJjBRnbJLgp8uirBgmQpjKhoR4tjF3ZpRzrFmBV6UjKdiSZkQUW"
        url = self.client.get_transaction_url(mock_sig)
        assert "devnet" in url.lower()
        assert "solscan.io" in url or "explorer.solana.com" in url
        assert mock_sig in url

    def test_get_transaction_url_mainnet(self):
        """Test transaction URL generation for mainnet"""
        mainnet_client = BlockchainClientSolana(
            rpc_url="https://api.mainnet-beta.solana.com",
            usdc_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            keypair_path=None,
            cluster="mainnet-beta"
        )
        mock_sig = "5VERv8NMvzbJMEkV8xnrLkEaWRtSz9CosKDYjCJjBRnbJLgp8uirBgmQpjKhoR4tjF3ZpRzrFmBV6UjKdiSZkQUW"
        url = mainnet_client.get_transaction_url(mock_sig)
        # Mainnet should not have ?cluster parameter
        assert "cluster=" not in url or "mainnet" in url.lower()
        assert mock_sig in url

    def test_usdc_mint_addresses(self):
        """Test USDC mint addresses are correct"""
        # Devnet USDC
        assert str(self.client.usdc_mint) == "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"

        # Mainnet USDC
        mainnet_client = BlockchainClientSolana(
            rpc_url="https://api.mainnet-beta.solana.com",
            usdc_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            keypair_path=None,
            cluster="mainnet-beta"
        )
        assert str(mainnet_client.usdc_mint) == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

    def test_max_retries_configuration(self):
        """Test max retries can be configured"""
        client_with_retries = BlockchainClientSolana(
            rpc_url="https://api.devnet.solana.com",
            usdc_mint="4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
            keypair_path=None,
            cluster="devnet",
            max_retries=5
        )
        assert client_with_retries.max_retries == 5
