# Security & Reliability Bug Report

**Date:** 2025-11-09
**Repository:** x402insurancesolana
**Status:** ❌ **4 CRITICAL BUGS CONFIRMED**

---

## Executive Summary

All 4 critical bugs from the original x402insurance repository **EXIST** in this Solana fork:

| Bug # | Severity | Type | Status | Location |
|-------|----------|------|--------|----------|
| **Bug 1** | 🔴 Critical | Runtime Crash | ❌ Present | `server.py` |
| **Bug 2** | 🔴 Critical | Data Corruption | ❌ Present | `database.py:109-122` |
| **Bug 3** | 🔴 Critical | SQL Injection | ❌ Present | `database.py:423` |
| **Bug 4** | 🔴 Critical | Security | ❌ Present | `auth/payment_verifier.py:41,280` |

**Impact:** Production deployment is unsafe without fixes.

---

## Bug #1: Missing save_data() Function (Runtime Crash)

### Severity: 🔴 **CRITICAL** - Server crashes on claim processing

### Location
- **File:** `server.py`
- **Lines:** 294, 315, 325, 352, 357, 370, 1239, 1369, 1465, 1469

### Issue
The `save_data()` function is **called but never defined**:

```python
# Line 221: Comment mentions backward compatibility
# Backward compatibility: keep old load_data/save_data for dashboard

# Line 228: load_data exists
def load_data(file_path: Path):
    """Backward compatibility - load JSON file"""
    if not file_path.exists():
        return {}
    # ...

# ❌ save_data() is NEVER DEFINED!

# Line 294: Used in process_claim_async()
save_data(CLAIMS_FILE, claims)  # NameError: name 'save_data' is not defined
```

### Impact
**Server crashes** when processing claims asynchronously:
```
NameError: name 'save_data' is not defined
```

All async claim processing fails, causing:
- No refunds issued
- No claims saved to database
- Data loss for in-progress claims
- Server instability

### Reproduction
1. Start server
2. Submit a claim via `/claim` endpoint
3. Server spawns async worker thread
4. Worker crashes with `NameError` on line 294

### Fix Required
Add the missing function in `server.py` after `load_data()`:

```python
def save_data(file_path: Path, data: dict):
    """Backward compatibility - save JSON file atomically"""
    import tempfile
    temp_fd, temp_path = tempfile.mkstemp(dir=file_path.parent, text=True)
    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
```

---

## Bug #2: File Locking Race Condition (Data Corruption)

### Severity: 🔴 **CRITICAL** - Data corruption under concurrent writes

### Location
- **File:** `database.py`
- **Function:** `JSONBackend._save_json()`
- **Lines:** 109-122

### Issue
Incorrect file locking implementation allows race conditions:

```python
def _save_json(self, file_path: Path, data: Dict):
    """Save JSON atomically"""
    content = json.dumps(data, indent=2, default=str)
    try:
        # ❌ BUG: Opens file in 'a+' mode, locks it, then NEVER WRITES TO IT
        with open(file_path, 'a+') as f:
            try:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX)  # Lock acquired
            except Exception:
                pass
        # ❌ Lock is RELEASED here (file closed)

        # ❌ Then writes WITHOUT the lock (race condition!)
        self._atomic_write(file_path, content)
    except Exception as e:
        logger.exception("Failed to save %s: %s", file_path, e)
        raise
```

### Problem
1. Opens file in append mode (`'a+'`) - doesn't make sense for JSON
2. Acquires exclusive lock
3. **Immediately closes file** (releasing lock)
4. **Then** calls `_atomic_write()` **without any lock**
5. Multiple concurrent writes can corrupt data

### Impact
**Data corruption** when multiple requests happen simultaneously:
- Claim A starts processing
- Claim B starts processing
- Both try to save to `claims.json`
- Race condition: whoever writes last wins
- **Previous claim data lost**

### Vulnerable Scenarios
- Multiple agents submit claims at the same time
- Async claim processing + new claim submission
- High-traffic periods
- Concurrent policy creation

### Fix Required
Use dedicated lock files with proper lock-write-unlock sequence:

```python
def _save_json(self, file_path: Path, data: Dict):
    """Save JSON atomically with proper locking"""
    lock_file = Path(str(file_path) + '.lock')
    lock_fd = None

    try:
        # Create lock file
        lock_fd = os.open(lock_file, os.O_CREAT | os.O_RDWR)

        # Acquire exclusive lock
        import fcntl
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        # Write data atomically WHILE HOLDING LOCK
        content = json.dumps(data, indent=2, default=str)
        self._atomic_write(file_path, content)

        # Release lock (in finally block)
    finally:
        if lock_fd is not None:
            try:
                import fcntl
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
            except Exception:
                pass
```

---

## Bug #3: SQL Injection Vulnerability

### Severity: 🔴 **CRITICAL** - SQL injection attack vector

### Location
- **File:** `database.py`
- **Class:** `PostgreSQLBackend`
- **Functions:** `update_claim()` (line 423), `update_policy()` (similar)
- **Line:** 423, 429

### Issue
Dynamic SQL construction with user-controlled column names:

```python
def update_claim(self, claim_id: str, updates: Dict) -> bool:
    try:
        # ❌ BUG: Builds SQL query from user-provided dict keys
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [claim_id]

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # ❌ SQL INJECTION: f-string interpolates column names
                cur.execute(
                    f"UPDATE claims SET {set_clause}, updated_at = NOW() WHERE claim_id = %s",
                    values
                )
        return True
    except Exception as e:
        logger.exception("Failed to update claim: %s", e)
        return False
```

### Attack Vector
Attacker sends malicious update payload:

```python
# Malicious request to /claim endpoint
updates = {
    "status = 'paid', payout_amount = 999999 WHERE claim_id = 'ATTACKER_CLAIM_ID'; --": "hacked"
}

# Generated SQL:
# UPDATE claims SET status = 'paid', payout_amount = 999999 WHERE claim_id = 'ATTACKER_CLAIM_ID'; -- = %s, updated_at = NOW() WHERE claim_id = %s
```

Result: Attacker gives themselves a huge payout!

### Impact
- **Arbitrary SQL execution**
- Data theft (steal all claims/policies)
- Data manipulation (change payout amounts)
- Privilege escalation
- Database destruction (DROP TABLE)

### Fix Required
Whitelist allowed column names:

```python
def update_claim(self, claim_id: str, updates: Dict) -> bool:
    try:
        # ✅ Whitelist allowed columns
        ALLOWED_COLUMNS = {
            'status', 'proof', 'public_inputs', 'verification_result',
            'payout_amount', 'payout_amount_units', 'refund_tx_hash',
            'recipient_address', 'paid_at', 'http_status', 'http_body_hash'
        }

        # ✅ Filter updates to only allowed columns
        safe_updates = {k: v for k, v in updates.items() if k in ALLOWED_COLUMNS}

        if not safe_updates:
            return False

        # ✅ Build safe query
        set_clause = ", ".join([f"{k} = %s" for k in safe_updates.keys()])
        values = list(safe_updates.values()) + [claim_id]

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE claims SET {set_clause}, updated_at = NOW() WHERE claim_id = %s",
                    values
                )
        return True
    except Exception as e:
        logger.exception("Failed to update claim: %s", e)
        return False
```

**Also fix `update_policy()` the same way!**

---

## Bug #4: Nonce Replay Attack Vulnerability

### Severity: 🔴 **CRITICAL** - Payment replay attacks possible

### Location
- **File:** `auth/payment_verifier.py`
- **Class:** `PaymentVerifier`
- **Lines:** 41 (initialization), 280 (storage)

### Issue
Nonce cache is **in-memory only** and doesn't persist across server restarts:

```python
class PaymentVerifier:
    """Verify x402 payments with proper signature validation"""

    def __init__(self, backend_address: str, usdc_address: str):
        self.backend_address = Web3.to_checksum_address(backend_address)
        self.usdc_address = Web3.to_checksum_address(usdc_address)
        # ❌ BUG: In-memory dict - lost on restart!
        self.nonce_cache = {}  # In-memory nonce tracking (use Redis in production)
        self.cache_cleanup_interval = 3600
        self.last_cleanup = time.time()

# Line 280: Stores nonce in memory
def _mark_nonce_used(self, payer: str, nonce: str, timestamp: int):
    """Mark nonce as used"""
    key = f"{payer.lower()}:{nonce}"
    self.nonce_cache[key] = timestamp  # ❌ In-memory only!
```

### Attack Scenario

**Normal flow:**
1. Agent creates policy, gets premium signature
2. Server accepts payment, stores nonce in memory
3. Policy created

**Attack after server restart:**
1. Server restarts (deploy, crash, maintenance)
2. Nonce cache is **empty** (lost from memory)
3. Attacker replays the same payment signature
4. Server thinks it's a new payment (nonce not in cache)
5. **Attacker creates policy without paying again!**

### Impact
- **Replay attacks** after server restarts
- **Free policies** by reusing old payments
- **Financial loss** for insurance provider
- Can be automated (bot restarts server, replays all cached signatures)

### Vulnerable Window
**Every time the server restarts**, all previous payment nonces are forgotten. Attackers can:
- Monitor server uptime
- Cache valid payment signatures
- Replay them after restart
- Create unlimited free policies

### Fix Required
Use persistent storage for nonces:

```python
import json
from pathlib import Path

class PaymentVerifier:
    def __init__(self, backend_address: str, usdc_address: str, data_dir: Path = None):
        self.backend_address = Web3.to_checksum_address(backend_address)
        self.usdc_address = Web3.to_checksum_address(usdc_address)

        # ✅ Persistent nonce storage
        self.data_dir = data_dir or Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.nonce_file = self.data_dir / "nonce_cache.json"

        # ✅ Load existing nonces from disk
        self.nonce_cache = self._load_nonces()
        self.cache_cleanup_interval = 3600
        self.last_cleanup = time.time()

    def _load_nonces(self) -> dict:
        """Load nonces from persistent storage"""
        if not self.nonce_file.exists():
            return {}
        try:
            with open(self.nonce_file, 'r') as f:
                return json.load(f)
        except Exception:
            logger.exception("Failed to load nonce cache")
            return {}

    def _save_nonces(self):
        """Save nonces to persistent storage"""
        try:
            with open(self.nonce_file, 'w') as f:
                json.dump(self.nonce_cache, f, indent=2)
        except Exception:
            logger.exception("Failed to save nonce cache")

    def _mark_nonce_used(self, payer: str, nonce: str, timestamp: int):
        """Mark nonce as used (persists to disk)"""
        key = f"{payer.lower()}:{nonce}"
        self.nonce_cache[key] = timestamp
        # ✅ Save to disk immediately
        self._save_nonces()
```

**Alternative:** Use Redis for production (as the comment suggests).

---

## Testing the Bugs

### Test Bug #1 (save_data crash)
```bash
# Start server
cd /home/hshadab/x402insurancesolana
source venv/bin/activate
python server.py

# In another terminal, submit claim
curl -X POST http://localhost:8000/claim \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "test-policy",
    "merchant_url": "https://httpstat.us/503"
  }'

# Check logs - will see NameError
```

### Test Bug #2 (race condition)
```bash
# Run concurrent claim submissions
for i in {1..10}; do
  curl -X POST http://localhost:8000/claim \
    -H "Content-Type: application/json" \
    -d "{\"policy_id\": \"test-$i\", \"merchant_url\": \"https://httpstat.us/503\"}" &
done
wait

# Check data/claims.json - may see corruption or missing claims
```

### Test Bug #3 (SQL injection)
```python
# If using PostgreSQL backend
updates = {
    "status = 'paid'; DROP TABLE claims; --": "evil"
}
db.update_claim("some-id", updates)
# Would execute: UPDATE claims SET status = 'paid'; DROP TABLE claims; -- = %s ...
```

### Test Bug #4 (nonce replay)
```bash
# 1. Create policy with payment
curl -X POST http://localhost:8000/insure \
  -H "X-Payment: payer=0x123,amount=1000,payTo=0x456,timestamp=1234567890,nonce=ABC123,signature=0xSIG" \
  -d '{"coverage_amount": 0.1, "agent_address": "0x123"}'

# 2. Restart server
kill <SERVER_PID>
python server.py

# 3. Replay same payment (should be rejected but ISN'T)
curl -X POST http://localhost:8000/insure \
  -H "X-Payment: payer=0x123,amount=1000,payTo=0x456,timestamp=1234567890,nonce=ABC123,signature=0xSIG" \
  -d '{"coverage_amount": 0.1, "agent_address": "0x123"}'

# ❌ Creates second policy with same payment!
```

---

## Recommended Fix Priority

| Priority | Bug | Reason |
|----------|-----|--------|
| **P0** | Bug #1 | Server crashes immediately on claim processing |
| **P0** | Bug #4 | Active exploit - financial loss |
| **P1** | Bug #2 | Data corruption on concurrent access |
| **P1** | Bug #3 | SQL injection (if using PostgreSQL) |

---

## Next Steps

### Immediate (Before Hackathon Demo)
1. ✅ **Fix Bug #1** - Add save_data() function (5 min)
2. ✅ **Fix Bug #4** - Add persistent nonce storage (10 min)
3. ⏳ Use JSON backend (not PostgreSQL) to avoid Bug #3

### Before Production
1. ✅ **Fix Bug #2** - Proper file locking (15 min)
2. ✅ **Fix Bug #3** - Column name whitelisting (10 min)
3. ✅ Add comprehensive tests for all 4 bugs
4. ✅ Security audit before mainnet deployment

---

## Files Affected

- `server.py` - Missing save_data() function
- `database.py` - File locking + SQL injection
- `auth/payment_verifier.py` - Nonce replay vulnerability

---

## References

- Original bug fixes: (mentioned in your message)
- Solana fork copied from: /home/hshadab/x402insurance

---

**Status:** ❌ **UNSAFE FOR PRODUCTION**

**Recommendation:** Fix all 4 bugs before deploying to testnet/mainnet or accepting real funds.

**For Hackathon Demo:** Fix Bug #1 and Bug #4 at minimum (server crashes + replay attacks).

---

**Last Updated:** 2025-11-09
**Reported By:** Code Review Analysis
