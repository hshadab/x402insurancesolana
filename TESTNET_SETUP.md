# Solana Testnet Setup Guide

**Network:** Solana Testnet
**Time Required:** 15-20 minutes
**Status:** ✅ Fully Supported

---

## Why Testnet?

Testnet is ideal for:
- ✅ More stable than devnet (less resets)
- ✅ Better for hackathon demos
- ✅ Closer to mainnet experience
- ✅ Still free (testnet SOL + USDC)
- ✅ Public explorers available

---

## Quick Setup (3 Steps)

### Step 1: Create Testnet Wallet (2 minutes)

```bash
# Create new keypair for testnet
solana-keygen new --outfile ~/solana-testnet-wallet.json

# Set Solana CLI to use testnet
solana config set --url testnet

# Get your public key
solana address -k ~/solana-testnet-wallet.json
# Copy this address - you'll need it!
```

**Save your public key!** Example: `5Xm8aR...k9Tp2`

---

### Step 2: Get Testnet Funds (5 minutes)

#### A. Get Testnet SOL (for transaction fees)

```bash
# Option 1: CLI airdrop
solana airdrop 2 $(solana address -k ~/solana-testnet-wallet.json) --url testnet

# Option 2: Web faucet
# Visit: https://faucet.solana.com/
# Select "Testnet" and paste your address
```

**Verify SOL balance:**
```bash
solana balance -k ~/solana-testnet-wallet.json --url testnet
# Should show: 2 SOL
```

#### B. Get Testnet USDC (for insurance payments)

**Option 1: Circle Faucet (Recommended)**
1. Visit: https://faucet.circle.com/
2. Select **"Solana Testnet"** from network dropdown
3. Paste your wallet address
4. Select USDC mint: `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU`
5. Click "Request Testnet Funds"
6. You'll receive 10 USDC

**Option 2: SPL Token Faucet**
```bash
# Create USDC token account
spl-token create-account 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU \
  --owner ~/solana-testnet-wallet.json \
  --url testnet

# Check USDC balance
spl-token balance 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU \
  --owner ~/solana-testnet-wallet.json \
  --url testnet
```

---

### Step 3: Configure Server (3 minutes)

```bash
cd /home/hshadab/x402insurancesolana

# Copy testnet configuration
cp .env.solana.testnet .env

# Edit configuration
nano .env
```

**Update these 2 lines:**
```bash
WALLET_KEYPAIR_PATH=/home/youruser/solana-testnet-wallet.json
BACKEND_WALLET_PUBKEY=YOUR_PUBKEY_FROM_STEP_1
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

---

## Start Server

```bash
cd /home/hshadab/x402insurancesolana

# Activate virtual environment
source venv/bin/activate

# Start server
python server.py
```

**Expected output:**
```
2025-11-09 09:12:51,100 - x402insurance - INFO - ============================================================
2025-11-09 09:12:51,101 - x402insurance - INFO - Network: SOLANA
2025-11-09 09:12:51,101 - x402insurance - INFO - Cluster: testnet
2025-11-09 09:12:51,101 - x402insurance - INFO - RPC: https://api.testnet.solana.com
2025-11-09 09:12:51,101 - x402insurance - INFO - USDC Mint: 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU
2025-11-09 09:12:51,101 - x402insurance - INFO - Wallet: 5Xm8aR...k9Tp2
 * Running on http://127.0.0.1:8000
```

**Access Dashboard:** http://localhost:8000

---

## Test the API

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Dashboard Stats
```bash
curl http://localhost:8000/api/dashboard
```

### 3. Create Insurance Policy (using demo script)
```bash
cd /home/hshadab/x402insurancesolana
python examples/agent_buy_policy.py
```

### 4. Submit Claim (using demo script)
```bash
python examples/agent_claim.py
```

---

## Testnet vs Devnet vs Mainnet

| Feature | Devnet | Testnet | Mainnet |
|---------|--------|---------|---------|
| **Stability** | Low (frequent resets) | Medium | High |
| **Uptime** | ~95% | ~98% | 99.9% |
| **Speed** | Fast | Fast | Fast |
| **Cost** | Free | Free | Real SOL |
| **Faucets** | Yes | Yes | No |
| **Explorer** | explorer.solana.com | explorer.solana.com | explorer.solana.com |
| **Best For** | Quick testing | Hackathons, demos | Production |

**Recommendation for Hackathon:** Use **Testnet** for stability and better demo experience.

---

## Testnet Endpoints

### RPC Endpoints
```bash
# Public (Free)
https://api.testnet.solana.com

# GenesysGo (Free)
https://testnet.genesysgo.net/

# Helius (Free tier)
https://rpc-testnet.helius.xyz/
```

To use different RPC in `.env`:
```bash
SOLANA_RPC_URL=https://testnet.genesysgo.net/
```

### Block Explorers
- **Solana Explorer:** https://explorer.solana.com/?cluster=testnet
- **Solscan:** https://solscan.io/?cluster=testnet
- **Solana Beach:** https://solanabeach.io/testnet

---

## Testnet USDC Details

**Mint Address:** `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU`
- Same mint used for devnet and testnet
- 6 decimals (1 USDC = 1,000,000 micro-USDC)
- Compatible with Circle's faucet
- No real value

**Contract Info:**
- Token Program: `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`
- Associated Token Program: `ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL`

---

## Troubleshooting

### Issue: "Insufficient SOL"
```bash
# Get more testnet SOL
solana airdrop 2 $(solana address -k ~/solana-testnet-wallet.json) --url testnet

# Check balance
solana balance -k ~/solana-testnet-wallet.json --url testnet
```

### Issue: "Insufficient USDC"
Visit Circle faucet again: https://faucet.circle.com/
- Can request multiple times (wait 24 hours between requests)

### Issue: "RPC node not responding"
Try different RPC endpoint in `.env`:
```bash
# Option 1: GenesysGo
SOLANA_RPC_URL=https://testnet.genesysgo.net/

# Option 2: Helius
SOLANA_RPC_URL=https://rpc-testnet.helius.xyz/

# Option 3: Official
SOLANA_RPC_URL=https://api.testnet.solana.com
```

### Issue: "Transaction failed"
Check transaction on explorer:
```bash
# Server logs will show transaction signature
# Copy signature and check on:
https://explorer.solana.com/tx/<SIGNATURE>?cluster=testnet
```

### Issue: "USDC token account not found"
Create token account manually:
```bash
spl-token create-account 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU \
  --owner ~/solana-testnet-wallet.json \
  --url testnet
```

---

## Deploy Anchor Program to Testnet (Optional)

If you want on-chain proof attestation:

```bash
cd /home/hshadab/x402insurancesolana/anchor_program

# Install Anchor (if not already installed)
cargo install --git https://github.com/coral-xyz/anchor --tag v0.29.0 anchor-cli

# Build program
anchor build

# Get program ID
solana address -k target/deploy/x402_attestation-keypair.json

# Update Anchor.toml with program ID
# Update .env with ATTESTATION_PROGRAM_ID

# Deploy to testnet
anchor deploy --provider.cluster testnet --provider.wallet ~/solana-testnet-wallet.json

# Verify deployment
solana program show <PROGRAM_ID> --url testnet
```

**Program will cost:** ~1-2 SOL for deployment + ~0.001 SOL per attestation

---

## Example Full Workflow

```bash
# 1. Setup (one time)
solana-keygen new --outfile ~/solana-testnet-wallet.json
solana airdrop 2 $(solana address -k ~/solana-testnet-wallet.json) --url testnet
# Get USDC from https://faucet.circle.com/

# 2. Configure
cd /home/hshadab/x402insurancesolana
cp .env.solana.testnet .env
nano .env  # Update WALLET_KEYPAIR_PATH and BACKEND_WALLET_PUBKEY

# 3. Start server
source venv/bin/activate
python server.py

# 4. Test (in another terminal)
curl http://localhost:8000/health
python examples/full_demo.sh

# 5. View on explorer
# Check transactions at: https://explorer.solana.com/?cluster=testnet
```

---

## Configuration Files

### For Testnet
```bash
cp .env.solana.testnet .env
```

### For Devnet
```bash
cp .env.solana .env
```

### For Mainnet (after hackathon)
```bash
# Update .env manually:
SOLANA_CLUSTER=mainnet-beta
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
USDC_MINT_ADDRESS=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
```

---

## Network Switch Commands

```bash
# Switch to testnet
solana config set --url testnet

# Switch to devnet
solana config set --url devnet

# Switch to mainnet
solana config set --url mainnet-beta

# Check current network
solana config get
```

---

## Testnet Resources

### Faucets
- **SOL:** https://faucet.solana.com/
- **USDC:** https://faucet.circle.com/
- **SPL Tokens:** https://spl-token-faucet.com/

### Explorers
- https://explorer.solana.com/?cluster=testnet
- https://solscan.io/?cluster=testnet

### RPC Status
- https://status.solana.com/
- https://solana-status.com/

### Documentation
- Solana Testnet: https://docs.solana.com/clusters#testnet
- Circle USDC: https://developers.circle.com/stablecoins/docs/usdc-on-test-networks

---

## Performance Expectations

### Transaction Times
- Policy creation: ~400ms
- Claim submission: ~600ms (includes proof verification)
- USDC refund: ~400ms
- Total claim processing: ~1-2 seconds

### Costs (Testnet - Free!)
- Policy creation: ~0.00001 SOL (~$0.00)
- Claim submission: ~0.00001 SOL (~$0.00)
- USDC transfer: ~0.00001 SOL (~$0.00)
- On-chain attestation: ~0.001 SOL (~$0.00)

---

## Demo Script for Testnet

```bash
#!/bin/bash
# testnet_demo.sh

echo "🚀 x402 Insurance - Solana Testnet Demo"
echo "========================================"
echo ""

# Check wallet balance
echo "📊 Wallet Status:"
solana balance -k ~/solana-testnet-wallet.json --url testnet
spl-token balance 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU \
  --owner ~/solana-testnet-wallet.json --url testnet
echo ""

# Start server in background
echo "🔧 Starting server..."
cd /home/hshadab/x402insurancesolana
source venv/bin/activate
python server.py &
SERVER_PID=$!
sleep 5
echo ""

# Test health
echo "💚 Health Check:"
curl -s http://localhost:8000/health | jq
echo ""

# Create policy
echo "🛡️  Creating insurance policy..."
curl -s -X POST http://localhost:8000/insure \
  -H "Content-Type: application/json" \
  -d '{"coverage_amount": 0.01, "agent_address": "YOUR_WALLET_HERE"}' | jq
echo ""

# Submit claim
echo "⚡ Submitting fraud claim..."
# (Use actual policy_id from previous response)
curl -s -X POST http://localhost:8000/claim \
  -H "Content-Type: application/json" \
  -d '{"policy_id": "abc123", "merchant_url": "https://httpstat.us/503"}' | jq
echo ""

# Cleanup
kill $SERVER_PID

echo "✅ Demo complete!"
echo "View transactions: https://explorer.solana.com/?cluster=testnet"
```

---

**Status:** ✅ Ready for Testnet Deployment

**Next Steps:**
1. Run Step 1-3 above (~15 minutes)
2. Start server
3. Test with demo scripts
4. View transactions on testnet explorer

**Questions?** Check `README_SOLANA.md` for more details.

**Last Updated:** 2025-11-09
