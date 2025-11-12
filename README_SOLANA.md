# x402 Insurance on Solana

**Zero-knowledge proof verified insurance for x402 micropayments with onchain proof attestation**

Built for the [Solana x402 Hackathon](https://solana.com/x402/hackathon)

---

## 🎯 What's New in Solana Version

This is an enhanced version of x402 Insurance (originally on Base) adapted for Solana with:

✅ **400ms transaction finality** (vs 2-5s on Base)
✅ **Lower costs** (~$0.00005 vs $0.0001)
✅ **Onchain proof attestation** - Publicly auditable proof records stored on Solana
✅ **SPL Token USDC transfers**
✅ **Ed25519 signature verification** for x402 payments
✅ **Anchor program** for permanent proof storage
✅ **Production-ready security** - All critical bugs fixed

---

## 🔒 Security

**Status:** ✅ **All 4 critical security bugs fixed**

- ✅ Runtime crash prevention (missing save_data)
- ✅ Data corruption protection (proper file locking)
- ✅ SQL injection prevention (column whitelisting)
- ✅ Replay attack prevention (persistent nonce storage)

See `BUGS_FIXED.md` for complete details.

---

## 🏗️ Architecture

```
┌─────────────┐
│  AI Agent   │ (Solana wallet)
└──────┬──────┘
       │ x402 payment (ed25519 signed)
       ▼
┌──────────────────────────────────┐
│  Flask Server (Python)           │
│  - Policy creation               │
│  - Claim processing              │
│  - Off-chain zkEngine proofs     │
└──────┬───────────────────┬───────┘
       │                   │
       ▼                   ▼
┌──────────────┐   ┌──────────────────┐
│ Solana RPC   │   │ Anchor Program   │
│ - SPL USDC   │   │ (Attestation)    │
│   refunds    │   │ - Proof hash     │
│   (400ms)    │   │ - Public audit   │
└──────────────┘   └──────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

1. **Solana CLI** installed
   ```bash
   sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"
   ```

2. **Anchor** installed (for smart contract deployment)
   ```bash
   cargo install --git https://github.com/coral-xyz/anchor --tag v0.29.0 anchor-cli
   ```

3. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

### Setup Steps

#### 1. Create Solana Devnet Wallet

```bash
# Generate new keypair
solana-keygen new --outfile ~/solana-wallet.json

# Set Solana CLI to devnet
solana config set --url devnet

# Get your public key
solana address -k ~/solana-wallet.json

# Airdrop devnet SOL for gas fees
solana airdrop 2 $(solana address -k ~/solana-wallet.json) --url devnet
```

#### 2. Get Devnet USDC

Visit [Circle USDC Faucet](https://faucet.circle.com/) and request devnet USDC:
- Network: **Solana Devnet**
- Mint Address: `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU`
- Paste your public key from step 1

#### 3. Install Python Dependencies

```bash
cd /home/hshadab/x402insurancesolana

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_solana.txt
```

#### 4. Configure Environment

```bash
# Copy Solana env template
cp .env.solana .env

# Edit .env and update:
# - WALLET_KEYPAIR_PATH=/home/youruser/solana-wallet.json
# - BACKEND_WALLET_PUBKEY=<your_public_key_from_step_1>
nano .env
```

#### 5. Deploy Anchor Program (Optional)

```bash
cd anchor_program

# Build the program
anchor build

# Get program ID
solana address -k target/deploy/x402_attestation-keypair.json

# Update Anchor.toml with your program ID
# Update .env with ATTESTATION_PROGRAM_ID

# Deploy to devnet
anchor deploy --provider.cluster devnet

cd ..
```

#### 6. Run the Server

```bash
# Make sure you're in the venv
source venv/bin/activate

# Start Flask server
python server.py
```

The server will start on `http://localhost:8000`

---

## 📡 API Endpoints

All endpoints are the same as Base version, but accept Solana public keys instead of Ethereum addresses.

### Create Insurance Policy

```bash
POST /insure
Headers:
  X-Payment: payer=<solana_pubkey>,amount=1000,payTo=<backend_pubkey>,timestamp=<unix_ts>,nonce=<unique>,signature=<ed25519_sig>

Body:
{
  "coverage_amount": 100000,  // 0.1 USDC in micro-USDC
  "merchant_url": "https://api.example.com"
}

Response:
{
  "policy_id": "abc123...",
  "status": "active",
  "coverage_amount": 100000,
  "premium_paid": 1000,
  "expires_at": 1699999999
}
```

### Submit API Failure Claim

```bash
POST /claim
Body:
{
  "policy_id": "abc123...",
  "http_status": 503,
  "response_body": "",
  "timestamp": 1699999999
}

Response:
{
  "claim_id": "def456...",
  "status": "approved",
  "payout_amount": 100000,
  "refund_tx_hash": "<solana_tx_sig>",
  "attestation_tx_hash": "<attestation_tx_sig>",  // NEW!
  "proof_url": "/proofs/def456...",
  "explorer_url": "https://explorer.solana.com/tx/..."
}
```

### Verify Proof (Public)

```bash
POST /verify
Body:
{
  "proof": "<zkEngine_proof_hex>",
  "public_inputs": [1, 503, 0, 100000]
}

Response:
{
  "valid": true,
  "message": "Proof verified successfully"
}
```

---

## 🔐 Proof Attestation (On-Chain)

Every approved claim creates an **immutable record on Solana**:

```rust
pub struct ProofAttestation {
    claim_id: [u8; 32],           // Unique claim ID
    proof_hash: [u8; 32],         // Blake3 hash of zkEngine proof
    public_inputs: [u64; 4],      // [fraud, status, body_len, payout]
    refund_tx_sig: [u8; 64],      // Solana USDC refund tx signature
    attested_at: i64,             // Unix timestamp
    attester: Pubkey,             // Backend wallet
}
```

**Cost:** ~$0.20 per attestation (one-time rent)

**Benefits:**
- ✅ Publicly auditable via [Solana Explorer](https://explorer.solana.com/?cluster=devnet)
- ✅ Permanent proof of legitimate payouts
- ✅ Anyone can verify claims independently
- ✅ Builds trust in the insurance system

---

## 🧪 Testing

### Run Demo Flow

```bash
# Test policy creation
curl -X POST http://localhost:8000/insure \
  -H "X-Payment: amount=1000,signature=test" \
  -H "X-Payer: <your_solana_pubkey>" \
  -H "Content-Type: application/json" \
  -d '{
    "coverage_amount": 100000,
    "merchant_url": "https://httpbin.org/status/503"
  }'

# Test claim submission
curl -X POST http://localhost:8000/claim \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "<policy_id_from_above>",
    "http_status": 503,
    "response_body": "",
    "timestamp": '$(date +%s)'
  }'
```

### View Dashboard

Open [http://localhost:8000/dashboard](http://localhost:8000/dashboard) to see:
- Real-time stats
- Recent policies with expiry countdown
- Recent claims with detailed proof verification
- Blockchain status

---

## 📊 Comparison: Solana vs Base

| Feature | Solana (Devnet) | Base (Mainnet) |
|---------|-----------------|----------------|
| **Transaction Speed** | **400ms** | 2-5 seconds |
| **Gas Fees** | **~$0.00005** | ~$0.0001 |
| **USDC Transfer** | SPL Token | ERC20 |
| **Signature** | ed25519 | EIP-712 |
| **Proof Storage** | **Anchor Program (PDA)** | Off-chain only |
| **Public Auditability** | **On-chain attestation** | Centralized server |
| **Throughput** | **65,000 TPS** | ~10 TPS |

---

## 🎬 Demo Video Script

**Duration:** 3 minutes

### Part 1: Problem (0:00-0:30)
*Show GitHub Issue #508*
```
"AI agents make billions of x402 micropayments to APIs.
When merchants fail with 503 errors or go offline, agents
lose money with zero recourse. x402 Insurance solves this
with cryptographically verified refunds on Solana."
```

### Part 2: Architecture (0:30-1:00)
*Show architecture diagram*
```
"Agents pay 1% premium via x402 protocol.
When merchant fails, zkEngine generates zero-knowledge proof.
USDC refund processes in 400ms on Solana.
Proof attestation stored permanently on-chain."
```

### Part 3: Live Demo (1:00-2:30)
*Screen recording*
1. Create policy - Show payment signature (30s)
2. Merchant returns 503 error (10s)
3. Submit claim - zkEngine generates proof (20s)
4. USDC refund sent (5s)
5. **Show Solana Explorer** - Proof attestation PDA (25s)
6. **Show Dashboard** - Updated stats (10s)

### Part 4: Impact (2:30-3:00)
```
"First zkp-based insurance on Solana.
Sub-second refunds protect the autonomous agent economy.
Production-ready on Base, now optimized for Solana speed.
All proofs publicly auditable on-chain."
```

---

## 🏆 Hackathon Submission

### Target Category
**Best x402 Agent Application** ($20,000 prize)

### Key Differentiators
1. ✅ **First zkp insurance on Solana** - Novel combination
2. ✅ **Production proven** - Already working on Base (v2.2.0)
3. ✅ **Sub-second payouts** - Leverages Solana speed
4. ✅ **Agent-native** - Built for autonomous agents
5. ✅ **Failure-proof** - Zero-knowledge proofs prevent fake claims
6. ✅ **Public auditability** - On-chain attestation via Anchor

### Deliverables
- ✅ Working code (Python backend + Rust Anchor program)
- ✅ Live devnet deployment
- ✅ 3-minute demo video
- ✅ Comprehensive documentation
- ✅ Agent SDK examples

---

## 📁 File Structure

```
x402insurancesolana/
├── blockchain_solana.py           # Solana SPL token client
├── payment_verifier_solana.py     # Ed25519 payment verification
├── server.py                       # Main Flask server (adapted)
├── database.py                     # Policy/claim storage
├── zkengine_client.py             # Off-chain proof generation
├── config.py                       # Configuration
├── .env.solana                    # Solana environment config
├── requirements_solana.txt        # Python dependencies
│
├── anchor_program/                # Solana smart contract
│   ├── programs/x402_attestation/
│   │   └── src/lib.rs            # Proof attestation program
│   ├── Anchor.toml
│   └── Cargo.toml
│
├── static/
│   └── dashboard.html            # Improved UI (user-friendly)
│
├── examples/
│   ├── agent_buy_policy.py       # Demo: Buy insurance
│   └── agent_claim.py            # Demo: File claim
│
└── solana/                        # Original research docs
    ├── HACKATHON_STRATEGY.md
    ├── ZK_VERIFICATION_INVESTIGATION.md
    └── SOLANA_MIGRATION_PLAN.md
```

---

## 🔧 Troubleshooting

### Error: "Insufficient SOL for transaction fees"
```bash
# Airdrop more SOL
solana airdrop 2 $(solana address) --url devnet
```

### Error: "Insufficient USDC balance"
- Visit https://faucet.circle.com/ and request devnet USDC
- Ensure you're using devnet mint: `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU`

### Error: "Program not deployed"
```bash
# Deploy Anchor program first
cd anchor_program
anchor build
anchor deploy --provider.cluster devnet
```

### zkEngine Not Found
```bash
# Ensure zkEngine binary is in the correct location
chmod +x zkengine/zkEngine
./zkengine/zkEngine --version
```

---

## 🌐 Production Deployment

### Deploy to Mainnet

1. **Update .env:**
   ```bash
   SOLANA_CLUSTER=mainnet-beta
   SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
   USDC_MINT_ADDRESS=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
   ```

2. **Fund mainnet wallet:**
   - Buy SOL from an exchange
   - Transfer to your wallet
   - Swap for USDC via Jupiter/Raydium

3. **Deploy Anchor program to mainnet:**
   ```bash
   anchor deploy --provider.cluster mainnet-beta
   ```

4. **Update DNS and HTTPS:**
   - Point domain to server
   - Set up SSL certificate (Let's Encrypt)

---

## 📞 Support

- **GitHub:** https://github.com/hshadab/x402insurance
- **Documentation:** See `solana/` folder for research docs
- **x402 Protocol:** https://github.com/x402/x402

---

## 📜 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- **NovaNet** for zkEngine (Nebula/SuperNova proving scheme)
- **Solana Foundation** for the x402 hackathon
- **x402 Protocol** team for agent micropayments
- **Anchor Framework** for Solana development

---

**Built with ❤️ for the autonomous agent economy**
