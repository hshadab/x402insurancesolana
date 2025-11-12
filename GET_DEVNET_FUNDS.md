# Get Devnet Funds for x402 Insurance Demo

## Wallet Address
```
BAikRH6xfHd6YG777XFQw85LGEEehTeqRtDiVpJLJiBo
```

## Step 1: Get Devnet SOL (for transaction fees)

Visit any of these faucets and request **2 SOL**:

### Option 1: Official Solana Faucet (Recommended)
🔗 https://faucet.solana.com/

1. Select **Devnet** from the dropdown
2. Paste wallet address: `BAikRH6xfHd6YG777XFQw85LGEEehTeqRtDiVpJLJiBo`
3. Request 2 SOL
4. Solve CAPTCHA if required

### Option 2: QuickNode Faucet
🔗 https://faucet.quicknode.com/solana/devnet

### Option 3: SOLFaucet
🔗 https://solfaucet.com/

### Option 4: Stakely Faucet
🔗 https://stakely.io/faucet/solana-sol

---

## Step 2: Get Devnet USDC (for insurance payments)

### Circle USDC Faucet
🔗 https://faucet.circle.com/

1. Select **Solana Devnet** from network dropdown
2. Paste wallet address: `BAikRH6xfHd6YG777XFQw85LGEEehTeqRtDiVpJLJiBo`
3. Request USDC (20 USDC recommended)
4. Complete verification if required

**USDC Mint Address (Devnet):**
```
4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU
```

---

## Step 3: Verify Funds

After requesting from faucets, verify your balance:

```bash
cd /home/hshadab/x402insurancesolana
python3 request_devnet_airdrop.py
```

Or check manually:
- SOL Balance: https://explorer.solana.com/address/BAikRH6xfHd6YG777XFQw85LGEEehTeqRtDiVpJLJiBo?cluster=devnet
- USDC Balance: Check token accounts on the same Explorer page

---

## Step 4: Test Real Transactions

Once funded, your demo will execute **REAL on-chain transactions**:

1. Open: http://localhost:8000
2. Click **"▶ Start Demo Animation"**
3. Watch as 12 real Solana transactions execute:
   - 6 premium payments (policy creation)
   - 6 USDC payouts (claims)
4. Click the 🔍 **Explorer** or 📊 **SolScan** buttons to view transactions on-chain

**Expected Cost:**
- ~0.00006 SOL for transaction fees (12 transactions × 0.000005 SOL)
- ~$0.30 USDC for demo payments (premium + payout cycles)

---

## Current Configuration

✅ Wallet keypair: `/home/hshadab/solana-devnet-wallet.json`
✅ Network: Solana Devnet
✅ Server: Running on http://localhost:8000
✅ Real transactions: Enabled via `/api/demo/transaction` endpoint

---

## Troubleshooting

**If transactions fail:**
1. Check SOL balance (need at least 0.001 SOL)
2. Check USDC balance (need at least 1 USDC)
3. Verify wallet loaded: Check server logs for "Solana wallet initialized"
4. Fallback: Animation will use mock transactions if real ones fail

**Server logs:**
```bash
# Check if wallet loaded successfully
tail -50 /proc/$(pgrep -f "python.*server.py" | head -1)/fd/2 2>/dev/null | grep "Solana wallet"
```
