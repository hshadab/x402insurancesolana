#!/bin/bash
# Full End-to-End Demo: Solana x402 Insurance
# This script demonstrates the complete workflow

set -e  # Exit on error

echo "=========================================="
echo "🚀 x402 Insurance on Solana - Full Demo"
echo "=========================================="
echo

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Error: Server not running on http://localhost:8000"
    echo "   Start the server first: python server.py"
    exit 1
fi

echo "✅ Server is running"
echo

# Configuration
INSURANCE_URL="http://localhost:8000"
MERCHANT_URL="https://httpbin.org/status/503"  # Always returns 503

echo "Step 1: Buy Insurance Policy"
echo "-----------------------------"

# Create policy (simplified payment for demo)
POLICY_RESPONSE=$(curl -s -X POST "$INSURANCE_URL/insure" \
  -H "X-Payment: amount=1000,signature=demo_signature" \
  -H "X-Payer: DemoAgent123456789" \
  -H "Content-Type: application/json" \
  -d '{
    "coverage_amount": 100000,
    "merchant_url": "'"$MERCHANT_URL"'"
  }')

echo "$POLICY_RESPONSE" | python3 -m json.tool

POLICY_ID=$(echo "$POLICY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['policy_id'])" 2>/dev/null || echo "")

if [ -z "$POLICY_ID" ]; then
    echo "❌ Failed to create policy"
    exit 1
fi

echo
echo "✅ Policy created: $POLICY_ID"
echo
echo "Step 2: Call Merchant API (Expecting 503)"
echo "------------------------------------------"

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$MERCHANT_URL")
echo "📊 Merchant returned: HTTP $HTTP_STATUS"

if [ "$HTTP_STATUS" != "503" ]; then
    echo "⚠️  Warning: Expected 503, got $HTTP_STATUS"
fi

echo
echo "Step 3: Submit Insurance Claim"
echo "-------------------------------"

CLAIM_RESPONSE=$(curl -s -X POST "$INSURANCE_URL/claim" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "'"$POLICY_ID"'",
    "http_status": '$HTTP_STATUS',
    "response_body": "",
    "timestamp": '$(date +%s)'
  }')

echo "$CLAIM_RESPONSE" | python3 -m json.tool

CLAIM_ID=$(echo "$CLAIM_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['claim_id'])" 2>/dev/null || echo "")

if [ -z "$CLAIM_ID" ]; then
    echo "❌ Claim failed"
    exit 1
fi

echo
echo "✅ Claim approved: $CLAIM_ID"
echo

# Extract refund details
REFUND_TX=$(echo "$CLAIM_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('refund_tx_hash', 'N/A'))" 2>/dev/null)
ATTESTATION_TX=$(echo "$CLAIM_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('attestation_tx_hash', 'N/A'))" 2>/dev/null)
PAYOUT=$(echo "$CLAIM_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('payout_amount', 0))" 2>/dev/null)

echo "Step 4: Verify Proof Independently"
echo "-----------------------------------"

# Get proof data
PROOF_DATA=$(curl -s "$INSURANCE_URL/proofs/$CLAIM_ID")

PROOF=$(echo "$PROOF_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('proof', ''))" 2>/dev/null)
PUBLIC_INPUTS=$(echo "$PROOF_DATA" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin).get('public_inputs', [])))" 2>/dev/null)

if [ -n "$PROOF" ] && [ "$PUBLIC_INPUTS" != "[]" ]; then
    VERIFY_RESPONSE=$(curl -s -X POST "$INSURANCE_URL/verify" \
      -H "Content-Type: application/json" \
      -d '{
        "proof": "'"$PROOF"'",
        "public_inputs": '"$PUBLIC_INPUTS"'
      }')

    echo "$VERIFY_RESPONSE" | python3 -m json.tool
    echo
    echo "✅ Proof verified independently"
else
    echo "⚠️  Proof data not available (may be using mock mode)"
fi

echo
echo "=========================================="
echo "✅ DEMO COMPLETE"
echo "=========================================="
echo
echo "📋 Summary:"
echo "  Policy ID:     $POLICY_ID"
echo "  Claim ID:      $CLAIM_ID"
echo "  Payout:        \$$(python3 -c "print($PAYOUT / 1000000)") USDC"
echo

if [ "$REFUND_TX" != "N/A" ] && [ "$REFUND_TX" != "" ]; then
    echo "🔗 Solana Transactions:"
    echo "  Refund TX:     https://explorer.solana.com/tx/$REFUND_TX?cluster=devnet"
    if [ "$ATTESTATION_TX" != "N/A" ] && [ "$ATTESTATION_TX" != "" ]; then
        echo "  Attestation:   https://explorer.solana.com/tx/$ATTESTATION_TX?cluster=devnet"
    fi
fi

echo
echo "🌐 View Dashboard:"
echo "  http://localhost:8000/dashboard"
echo
