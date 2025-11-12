# Quick Start - Solana Testnet (15 minutes)

## Prerequisites ✅
- ✅ Dependencies installed
- ✅ Server tested and working
- ⏳ Need: Solana wallet + testnet funds

---

## 3-Step Setup

### 1️⃣ Create Wallet (2 min)
```bash
# Generate keypair
solana-keygen new --outfile ~/solana-testnet-wallet.json

# Save your public key
solana address -k ~/solana-testnet-wallet.json
```
**Copy the address that appears!** Example: `5Xm8aR2k9Tp2...`

---

### 2️⃣ Get Funds (5 min)

**Get SOL (transaction fees):**
```bash
solana airdrop 2 $(solana address -k ~/solana-testnet-wallet.json) --url testnet
```

**Get USDC (insurance payments):**
- Visit: https://faucet.circle.com/
- Network: **Solana Testnet**
- Mint: `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU`
- Paste your wallet address
- Click "Request Testnet Funds"
- You'll get 10 USDC

---

### 3️⃣ Configure & Start (3 min)

```bash
# Go to project directory
cd /home/hshadab/x402insurancesolana

# Copy testnet config
cp .env.solana.testnet .env

# Edit config
nano .env
```

**Update 2 lines:**
```bash
WALLET_KEYPAIR_PATH=/home/yourusername/solana-testnet-wallet.json
BACKEND_WALLET_PUBKEY=YOUR_ADDRESS_FROM_STEP_1
```

**Save:** `Ctrl+X`, `Y`, `Enter`

**Start server:**
```bash
source venv/bin/activate
python server.py
```

**Open dashboard:** http://localhost:8000

---

## Test It!

```bash
# In new terminal
curl http://localhost:8000/health
curl http://localhost:8000/api/dashboard

# Run demo
cd /home/hshadab/x402insurancesolana
python examples/full_demo.sh
```

**View transactions:** https://explorer.solana.com/?cluster=testnet

---

## Key Differences: Devnet vs Testnet

| | Devnet | Testnet |
|---|---|---|
| **Stability** | Frequent resets | More stable |
| **Best for** | Quick tests | Demos, hackathons |
| **RPC** | api.devnet.solana.com | api.testnet.solana.com |
| **USDC** | Same mint | Same mint |
| **Faucets** | Yes | Yes |

**Recommendation:** Use **testnet** for the hackathon demo!

---

## Configuration Files

- `.env.solana` - Devnet config
- `.env.solana.testnet` - Testnet config ⭐
- `.env` - Active config (copy one of the above)

---

## Expected Server Output

```
INFO - ============================================================
INFO - x402 Insurance Service initialized
INFO - ============================================================
INFO - Network: SOLANA
INFO - Cluster: testnet ⭐
INFO - RPC: https://api.testnet.solana.com
INFO - USDC Mint: 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU
INFO - Wallet: 5Xm8aR...k9Tp2
INFO - SOL Balance: 2.00
INFO - USDC Balance: 10.00
INFO - ============================================================
 * Running on http://127.0.0.1:8000
```

---

## Troubleshooting

**"Insufficient funds"**
```bash
# Get more SOL
solana airdrop 2 <YOUR_ADDRESS> --url testnet

# Get more USDC
# Visit https://faucet.circle.com/ again (wait 24h between requests)
```

**"Server won't start"**
```bash
# Check if dependencies installed
cd /home/hshadab/x402insurancesolana
./venv/bin/python3 -c "from blockchain_solana import BlockchainClientSolana; print('OK')"
```

**"RPC not responding"**
```bash
# Try different RPC in .env
SOLANA_RPC_URL=https://testnet.genesysgo.net/
```

---

## Resources

- **Faucets:** https://faucet.circle.com/ (USDC), https://faucet.solana.com/ (SOL)
- **Explorer:** https://explorer.solana.com/?cluster=testnet
- **Full Guide:** See `TESTNET_SETUP.md`
- **Solana Guide:** See `README_SOLANA.md`

---

**Time:** 15 minutes total
**Cost:** Free (testnet)
**Status:** ✅ Production ready

**Last Updated:** 2025-11-09
