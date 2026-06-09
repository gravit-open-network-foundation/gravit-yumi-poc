# API Specification: Gravit × Yumi

## Base URL

- Development: [http://localhost:8080](http://localhost:8080/)
- Staging: [https://staging.gravit.network](https://staging.gravit.network/)
- Production: [https://api.gravit.network](https://api.gravit.network/)

---

## Endpoint: Verify Credit Decision

**POST** `/v1/verify/credit`

### Request

```json
{
  "borrower_id": "SME_DE_4421",
  "requested_amount": 500000,
  "currency": "EUR",
  "term_days": 30,
  "risk_score": 0.15,
  "reasoning_chain": [
    "Borrower has 8 years of positive operating history",
    "Debt-to-income ratio is 0.32 (below threshold of 0.40)",
    "Collateral value of €750,000 exceeds loan amount"
  ],
  "context": {
    "collateral_value": 750000,
    "debt_to_income": 0.32,
    "industry": "manufacturing",
    "years_in_business": 8
  }
}
```

### Response (Success)

```json
{
  "status": "verified",
  "decision": "approve",
  "trust_score": 242,
  "confidence": 0.94,
  "trace_id": "trace_xyz789_20260523_001",
  "audit_proof": "0x8a7b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b",
  "checks_passed": {
    "semantic_compliance": true,
    "policy_compliance": true,
    "adversarial_risk": false,
    "reasoning_lineage": "valid"
  },
  "timestamp": "2026-06-08T10:00:00Z"
}
```

### Response (Rejection)

```json
{
  "status": "rejected",
  "decision": "deny",
  "trust_score": 45,
  "reason": "Semantic inconsistency detected in invoice data",
  "trace_id": "trace_abc123_20260523_002",
  "failed_checks": {
    "semantic_compliance": false,
    "adversarial_risk": true
  }
}
```

---

## Endpoint: Verify Invoice (Trade Finance)

**POST** `/v1/verify/invoice`

### Request

```json
{
  "invoice_id": "INV-2026-8872",
  "supplier_id": "SolarTech_India",
  "buyer_id": "GreenEnergy_GmbH",
  "amount": 165700,
  "currency": "EUR",
  "invoice_text": "INVOICE #TF-2026-8872..."
}
```

### Response

```json
{
  "status": "verified",
  "invoice_valid": true,
  "fraud_risk": "low",
  "trust_score": 238,
  "anomalies_detected": [],
  "trace_id": "trace_inv_20260523_003"
}
```

---

## Endpoint: Get Audit Proof

**GET** `/v1/audit/{trace_id}`

### Response

```json
{
  "trace_id": "trace_xyz789_20260523_001",
  "timestamp": "2026-06-08T10:00:00Z",
  "decision": "approve",
  "trust_score": 242,
  "full_verification_trace": [
    "2026-06-08T10:00:00.123Z - Request received",
    "2026-06-08T10:00:00.234Z - Semantic analysis started",
    "2026-06-08T10:00:00.456Z - Grok analysis complete (score: 0.95)",
    "2026-06-08T10:00:00.567Z - Claude analysis complete (score: 0.93)",
    "2026-06-08T10:00:00.678Z - Consensus reached",
    "2026-06-08T10:00:00.789Z - Audit proof generated"
  ],
  "cryptographic_proof": "0x..."
}
```

---

## Error Codes

| Code | Description |
|:----:|:------------|
| 400  | Bad request – malformed JSON |
| 401  | Unauthorized – invalid API key  |
| 404  | Not found – trace_id doesn't exist |
| 429  | Too many requests – rate limit exceeded |
| 500  | Internal server error |
