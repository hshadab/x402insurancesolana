# Tests Directory

## Structure

### Unit Tests (`tests/unit/`)
Automated tests that run in CI/CD. These tests are fast and have no external dependencies.

- `test_blockchain.py` - Tests for Solana blockchain client
- `test_database.py` - Tests for database backend

**Run with:** `pytest tests/unit/`

### Manual Tests
Standalone scripts for manual testing. These are NOT run by pytest.

- `manual_transaction_test.py` - Test Solana transaction building (requires devnet connection)
- `manual_e2e_test.py` - End-to-end flow test (requires running server on localhost:8000)

**Run manually:**
```bash
python tests/manual_transaction_test.py
python tests/manual_e2e_test.py
```

### Integration Tests (`tests/integration/`)
Integration tests that may require external services or setup.

## Running Tests

### Run all unit tests (CI/CD)
```bash
pytest tests/unit/ -v
```

### Run with coverage
```bash
pytest tests/unit/ -v --cov=. --cov-report=term
```

### Run specific test file
```bash
pytest tests/unit/test_blockchain.py -v
```

### Run specific test
```bash
pytest tests/unit/test_blockchain.py::TestBlockchainClientSolana::test_initialization_devnet -v
```
