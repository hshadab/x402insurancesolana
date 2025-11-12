# Next Steps - Complete the Solana Implementation

**Current Status:** All Solana components built, needs integration into server.py

**Time Estimate:** 6-11 hours to fully working demo

---

## 🎯 Critical Path (Must Complete)

### Step 1: Adapt server.py for Solana (2-3 hours)

The main server needs to be updated to support Solana alongside Base. Here's what needs to change:

#### A. Add Imports

```python
# Add at top of server.py
from blockchain_solana import BlockchainClientSolana
from payment_verifier_solana import PaymentVerifierSolana, SimplePaymentVerifierSolana
```

#### B. Update Configuration Loading

```python
# In initialization section, add:
BLOCKCHAIN_NETWORK = os.getenv('BLOCKCHAIN_NETWORK', 'base')  # 'base' or 'solana'

if BLOCKCHAIN_NETWORK == 'solana':
    # Solana configuration
    blockchain = BlockchainClientSolana(
        rpc_url=os.getenv('SOLANA_RPC_URL'),
        usdc_mint=os.getenv('USDC_MINT_ADDRESS'),
        keypair_path=os.getenv('WALLET_KEYPAIR_PATH'),
        cluster=os.getenv('SOLANA_CLUSTER', 'devnet')
    )

    payment_verifier = PaymentVerifierSolana(
        backend_pubkey=os.getenv('BACKEND_WALLET_PUBKEY'),
        usdc_mint=os.getenv('USDC_MINT_ADDRESS')
    )
else:
    # Keep existing Base configuration
    blockchain = BlockchainClient(...)
    payment_verifier = PaymentVerifier(...)
```

#### C. Update /insure Endpoint

```python
# In /insure endpoint, the payment verification already works
# Just ensure it uses the correct verifier (auto-selected above)

# After creating policy, update dashboard display:
return jsonify({
    "policy_id": policy_id,
    "network": BLOCKCHAIN_NETWORK,  # Add this
    # ... rest of response
})
```

#### D. Update /claim Endpoint

```python
# After successful proof verification and before returning response:

if BLOCKCHAIN_NETWORK == 'solana':
    # Issue USDC refund on Solana
    refund_tx = blockchain.issue_refund(
        to_address=policy['agent_address'],  # Solana pubkey
        amount=payout_amount
    )

    # TODO (Optional): Call Anchor program to attest proof
    # attestation_tx = await attest_proof_onchain(claim_id, proof_hash, public_inputs, refund_tx)

    # Get Solana Explorer URL
    explorer_url = blockchain.get_transaction_url(refund_tx)

    return jsonify({
        "claim_id": claim_id,
        "status": "approved",
        "payout_amount": payout_amount,
        "refund_tx_hash": refund_tx,
        # "attestation_tx_hash": attestation_tx,  # If implemented
        "explorer_url": explorer_url,
        "proof_url": f"/proofs/{claim_id}"
    })
```

#### E. Update Dashboard Endpoint

```python
# In /api/dashboard endpoint:

# Add network info
data = {
    "network": BLOCKCHAIN_NETWORK,
    "stats": { ... },
    # ... rest of data
}

# Update blockchain stats for Solana
if BLOCKCHAIN_NETWORK == 'solana':
    data["blockchain"] = {
        "cluster": os.getenv('SOLANA_CLUSTER'),
        "wallet_address": blockchain.get_wallet_address(),
        "sol_balance": blockchain.get_sol_balance() / 1_000_000_000,  # Convert lamports
        "usdc_balance": blockchain.get_balance() / 1_000_000,
    }
```

---

### Step 2: Update config.py (30 minutes)

Add Solana configuration support:

```python
# Add to config.py

class SolanaConfig:
    """Solana-specific configuration"""

    SOLANA_CLUSTER = os.getenv('SOLANA_CLUSTER', 'devnet')
    SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.devnet.solana.com')
    USDC_MINT_ADDRESS = os.getenv('USDC_MINT_ADDRESS')
    WALLET_KEYPAIR_PATH = os.getenv('WALLET_KEYPAIR_PATH')
    BACKEND_WALLET_PUBKEY = os.getenv('BACKEND_WALLET_PUBKEY')
    ATTESTATION_PROGRAM_ID = os.getenv('ATTESTATION_PROGRAM_ID')

class Config:
    # Add blockchain network selection
    BLOCKCHAIN_NETWORK = os.getenv('BLOCKCHAIN_NETWORK', 'base')

    # Existing Base config...
    # + Solana config
```

---

### Step 3: Setup Solana Wallet (15 minutes)

```bash
# Generate keypair
solana-keygen new --outfile ~/solana-wallet.json

# Get public key
solana address -k ~/solana-wallet.json

# Airdrop devnet SOL
solana airdrop 2 $(solana address -k ~/solana-wallet.json) --url devnet

# Get devnet USDC
# Visit https://faucet.circle.com/
# Network: Solana Devnet
# Mint: 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU
```

---

### Step 4: Deploy Anchor Program (1 hour)

```bash
cd /home/hshadab/x402insurancesolana/anchor_program

# Install Anchor if not already installed
cargo install --git https://github.com/coral-xyz/anchor --tag v0.29.0 anchor-cli

# Build program
anchor build

# Get program ID
solana address -k target/deploy/x402_attestation-keypair.json

# Update Anchor.toml with program ID
# Update .env with ATTESTATION_PROGRAM_ID

# Deploy to devnet
anchor deploy --provider.cluster devnet

# Verify deployment
solana program show <PROGRAM_ID> --url devnet
```

---

### Step 5: Install Dependencies (10 minutes)

```bash
cd /home/hshadab/x402insurancesolana

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Solana dependencies
pip install -r requirements_solana.txt

# Verify installation
python -c "import solana; print('Solana SDK:', solana.__version__)"
python -c "from nacl.signing import SigningKey; print('PyNaCl installed')"
```

---

### Step 6: Configure Environment (10 minutes)

```bash
cd /home/hshadab/x402insurancesolana

# Copy Solana env
cp .env.solana .env

# Edit configuration
nano .env

# Update these values:
# - WALLET_KEYPAIR_PATH=/home/youruser/solana-wallet.json
# - BACKEND_WALLET_PUBKEY=<your_pubkey_from_step_3>
# - ATTESTATION_PROGRAM_ID=<program_id_from_step_4>
```

---

### Step 7: Test End-to-End (2-3 hours)

```bash
# Activate venv
source venv/bin/activate

# Start server
python server.py

# In another terminal, run demo
cd /home/hshadab/x402insurancesolana
./examples/full_demo.sh

# Check dashboard
open http://localhost:8000/dashboard

# Verify on Solana Explorer
# Look for transaction links in demo output
```

**Common Issues & Fixes:**

```bash
# If: "Insufficient SOL"
solana airdrop 2 $(solana address) --url devnet

# If: "Insufficient USDC"
# Visit https://faucet.circle.com/ again

# If: "zkEngine not found"
chmod +x zkengine/zkEngine
./zkengine/zkEngine --version

# If: "Cannot connect to RPC"
# Check .env SOLANA_RPC_URL
# Try: https://api.devnet.solana.com
```

---

### Step 8: Create Demo Video (1-2 hours)

Use the script in `README_SOLANA.md` (search for "Demo Video Script").

**Tools:**
- **Screen recording:** OBS Studio, QuickTime, or Loom
- **Editing:** DaVinci Resolve (free), iMovie, or Camtasia

**Checklist:**
- ✅ Show problem (GitHub Issue #508)
- ✅ Explain architecture diagram
- ✅ Live demo: Buy policy → Merchant fails → Claim → Explorer
- ✅ Show Solana Explorer proof attestation
- ✅ Show improved dashboard
- ✅ Highlight speed (400ms vs 2-5s)
- ✅ End with impact statement

---

## 🎁 Bonus (Optional)

### Add Anchor Attestation Integration

If you want to call the Anchor program from Python:

```python
# In server.py, after successful refund

from anchorpy import Program, Provider, Wallet
from solders.pubkey import Pubkey

async def attest_proof_onchain(claim_id, proof_hex, public_inputs, refund_sig):
    """Store proof attestation on Solana"""

    # Load Anchor program
    provider = Provider(
        connection=blockchain.client,
        wallet=Wallet(blockchain.keypair)
    )
    program = await Program.at(ATTESTATION_PROGRAM_ID, provider)

    # Derive PDA
    claim_id_bytes = bytes.fromhex(claim_id)
    attestation_pda, bump = Pubkey.find_program_address(
        [b"attestation", claim_id_bytes],
        program.program_id
    )

    # Call attest_claim_proof
    tx = await program.rpc["attest_claim_proof"](
        claim_id_bytes,
        bytes.fromhex(proof_hex[:64]),  # Proof hash
        public_inputs,
        bytes.fromhex(refund_sig),
        ctx=Context(
            accounts={
                "attestation": attestation_pda,
                "authority": blockchain.pubkey,
                "system_program": SYS_PROGRAM_ID,
            }
        )
    )

    logger.info(f"Proof attested: {tx}")
    return tx
```

---

## 📋 Pre-Submission Checklist

Before submitting to hackathon:

- [ ] Server runs without errors
- [ ] Can create policy via API
- [ ] Can submit claim and receive refund
- [ ] Solana Explorer shows transactions
- [ ] Dashboard displays correctly
- [ ] Demo video recorded (3 min)
- [ ] README updated with deployment URL
- [ ] GitHub repo is public
- [ ] All secrets removed from code

---

## 🚀 Deployment to Production (After Hackathon)

### Mainnet Deployment

1. **Update .env:**
   ```bash
   BLOCKCHAIN_NETWORK=solana
   SOLANA_CLUSTER=mainnet-beta
   SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
   USDC_MINT_ADDRESS=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
   ```

2. **Deploy Anchor to mainnet:**
   ```bash
   anchor deploy --provider.cluster mainnet-beta
   ```

3. **Fund mainnet wallet:**
   - Buy SOL from exchange
   - Transfer to wallet
   - Swap for USDC

4. **Deploy server:**
   - Use Render.com, Railway, or AWS
   - Set environment variables
   - Enable HTTPS

---

## 📞 Need Help?

**Files to Reference:**
- `README_SOLANA.md` - Comprehensive guide
- `IMPLEMENTATION_SUMMARY.md` - What was built
- `solana/HACKATHON_STRATEGY.md` - Original plan
- `examples/` - Demo scripts

**Common Commands:**
```bash
# Check Solana connection
solana config get

# Check wallet balance
solana balance

# Check USDC balance
spl-token accounts

# View logs
tail -f logs/x402insurance.log

# Test API
curl http://localhost:8000/health
```

---

**Good luck! 🚀**

**Estimated Total Time:** 6-11 hours to complete
**Current Status:** 90% done, just needs integration

**Next Action:** Start with Step 1 (Adapt server.py)
