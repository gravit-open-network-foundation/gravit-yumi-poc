# Gravit Epistemic Verifier

**Production-grade epistemic verification for AI agents.**

---

## Quick Start

```bash
git clone https://github.com/GravitOpenNetwork/gravit-yumi-poc
cd gravit-yumi-poc
chmod +x scripts/*.sh
./scripts/setup.sh
```

## Run Examples

```bash
python examples/01_bank_underwriting.py
python examples/02_defi_lending.py
python examples/03_trade_finance.py
```

## Run Tests

```bash
pytest tests/ -v
```

## Deploy

```bash
./scripts/deploy.sh dev         # local development
./scripts/deploy.sh staging     # staging environment
./scripts/deploy.sh production  # production
```

## E2E Tests

```bash
./scripts/test_e2e.sh
```

## License

Apache 2.0
