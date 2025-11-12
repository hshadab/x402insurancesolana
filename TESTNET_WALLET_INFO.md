# Solana Testnet Wallet - Quick Reference

**Date Created:** 2025-11-10  
**Network:** Solana Testnet

---

## 🔑 Your Wallet

**Public Key (Address):**
```
FvhgYhav7wc514G7VtGNNDNKUMFTB21CwE517hdwPP7Y
```

**Keypair File:**
```
/home/hshadab/solana-testnet-wallet.json
```

**Configuration:**
- ✅ Switched to Solana Testnet
- ✅ Wallet created and configured in .env
- ⏳ Awaiting testnet funds

---

## 💰 Get Testnet Funds

### 1. Get SOL (Transaction Fees)

**Option A - Solana Faucet (Recommended):**
- Visit: https://faucet.solana.com/
- Select: **Testnet**
- Paste address: `FvhgYhav7wc514G7VtGNNDNKUMFTB21CwE517hdwPP7Y`
- Request: 2 SOL
- **Why:** Needed for all transaction fees on Solana

**Option B - Command Line (if Solana CLI installed):**
```bash
solana airdrop 2 FvhgYhav7wc514G7VtGNNDNKUMFTB21CwE517hdwPP7Y --url testnet
```

### 2. Get USDC (Insurance Payments)

**Circle USDC Faucet:**
- Visit: https://faucet.circle.com/
- Select Network: **Solana Testnet**
- USDC Mint: `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU`
- Paste address: `FvhgYhav7wc514G7VtGNNDNKUMFTB21CwE517hdwPP7Y`
- Request: 10 USDC
- **Why:** Needed for USDC refund payments to agents

---

## 🔗 Explorer Links

**Check your wallet balance:**
- Solana Explorer: https://explorer.solana.com/address/FvhgYhav7wc514G7VtGNNDNKUMFTB21CwE517hdwPP7Y?cluster=testnet
- SolScan: https://solscan.io/account/FvhgYhav7wc514G7VtGNNDNKUMFTB21CwE517hdwPP7Y?cluster=testnet

---

## 🚀 After Getting Funds

Once you have SOL and USDC in your wallet:

1. **Restart the server:**
   ```bash
   # Kill current server (Ctrl+C)
   cd /home/hshadab/x402insurancesolana
   source venv/bin/activate
   python server.py
   ```

2. **Open the dashboard:**
   - http://localhost:8000

3. **You should see:**
   - ✅ "Solana Network" status (green)
   - ✅ "Testnet • 400ms finality" label
   - ✅ Your SOL and USDC balances
   - ✅ Solana Explorer Widget with links
   - ✅ Purple/green Solana branding throughout

---

## 📊 Expected Server Output

When restarted with funds:
```
INFO - Network: SOLANA
INFO - Cluster: testnet
INFO - RPC: https://api.testnet.solana.com
INFO - USDC Mint: 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU
INFO - Wallet: FvhgYhav7wc514G7VtGNNDNKUMFTB21CwE517hdwPP7Y
INFO - SOL Balance: 2.00
INFO - USDC Balance: 10.00
```

---

## 🧪 Test the System

**Create a test policy:**
```bash
curl -X POST http://localhost:8000/insure \
  -H "X-Payment: amount=1000,signature=test" \
  -H "X-Payer: FvhgYhav7wc514G7VtGNNDNKUMFTB21CwE517hdwPP7Y" \
  -H "Content-Type: application/json" \
  -d '{
    "coverage_amount": 100000,
    "merchant_url": "https://httpbin.org/status/503"
  }'
```

**File a test claim:**
```bash
curl -X POST http://localhost:8000/claim \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "POLICY_ID_FROM_ABOVE",
    "http_response": {
      "status": 503,
      "body": "",
      "headers": {}
    }
  }'
```

The refund transaction will appear on Solana Testnet with explorer links!

---

## 🎨 UI Features You'll See

1. **Hero:** "x402 Insurance ⚡ Solana"
2. **Badges:** "Powered by Solana" with purple→green gradient
3. **Network Card:** Shows "Solana Network" with 400ms finality
4. **Explorer Widget:** Live stats + 3 explorer buttons
5. **Claims:** Each shows "Verified on Solana Testnet" with TX links

---

## 📝 Current Status

- ✅ Configuration: Solana Testnet
- ✅ Wallet: Created and configured
- ⏳ Funds: Awaiting SOL + USDC from faucets
- 🔄 Server: Running (needs restart after funding)

**Next:** Get testnet funds, then restart server to see full Solana experience!
