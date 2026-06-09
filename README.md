# Gravit × Yumi Finance – PoC

**Trust‑Native Credit Protocol — Where capital flows based on provable reality**

---

[![PoC Status](https://img.shields.io/badge/status-poc_ready-yellow)](https://github.com/GravitOpenNetwork/gravit-yumi-poc)
[![Integration](https://img.shields.io/badge/integration-yumi-blue)](https://yumi.finance)
[![License](https://img.shields.io/badge/license-Apache_2.0-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com)

---

## Overview

This PoC demonstrates the integration between two components:

| Component | Role |
|-----------|------|
| **Yumi Finance** | Credit execution layer (BNPL, trade credit, unsecured lending) |
| **Gravit Open Network** | Epistemic trust layer (verifiable AI decisions, audit trails) |

**Result:** A trust‑native credit protocol where every lending decision is cryptographically verifiable.

---

## Quick Start (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/GravitOpenNetwork/gravit-yumi-poc
cd gravit-yumi-poc

# 2. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run with Docker
docker-compose up -d

# 4. Run demo
python examples/04_yumi_integration.py
```

## What This PoC Demonstrates

| Capability                         | Status | Description                                 |
|-----------------------------------:|:------:|:--------------------------------------------|
| Invoice verification               | ✅     | Detect fake invoices before funding         |
| Credit underwriting verification    | ✅     | Verify AI scoring decisions                 |
| Multi‑LLM support                  | ✅     | Grok, Claude, GPT‑4                         |
| Audit trail generation             | ✅     | Cryptographic proof per decision            |
| Yumi API integration               | ✅     | Ready for production                        |

## Repository Structure

```
gravit-yumi-poc/
├── src/         # Core verification engine
├── examples/    # Runnable demos (banking, DeFi, trade)
├── tests/       # Unit and integration tests
├── docker/      # Container orchestration
├── k8s/         # Kubernetes manifests
├── contracts/   # Solidity smart contract
└── docs/        # Technical documentation
```

## Documentation

| Document            | Purpose                             |
|--------------------:|:------------------------------------|
| Architecture         | System design and data flow        |
| API Specification    | REST API details                   |
| Integration Guide    | Step‑by‑step for Yumi team         |
| Use Cases            | Banking, DeFi, Trade Finance       |
| Deployment           | Docker, K8s, on‑prem               |

## Next Steps with Yumi

- **Week 1:** Integrate Gravit verifier with Yumi credit API
- **Week 2:** Test on real invoice data
- **Deliverable:** Working PoC + investor demo

## Contact

Gravit Open Network – info@gravit.network

Dr. Alex Konviser – Founder

## License

Apache 2.0
