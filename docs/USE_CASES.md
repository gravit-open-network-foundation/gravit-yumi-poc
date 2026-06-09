# Use Cases: Gravit × Yumi

## Use Case 1: B2B BNPL (Buy Now, Pay Later)

**Scenario:** SME purchases equipment from supplier, requests BNPL financing.

**Without Gravit:**

- Supplier submits invoice
- Yumi risk engine analyzes
- Manual verification may take days

**With Gravit:**

```python
# Automated verification (sub-200ms typical)
result = gravit.verify_credit(
    invoice=invoice_payload,
    borrower=borrower_profile
)

if result.decision == "approve":
    approve_credit()
```

**Outcome:** Instant approval, reduced fraud, audit trail for regulators.

---

## Use Case 2: Trade Finance (Cross-Border)

**Scenario:** Indian supplier exports to German buyer, needs invoice financing.

**Without Gravit:**

- Bank takes 5–7 days to verify
- High manual cost
- Limited to large transactions

**With Gravit:**

```python
result = gravit.verify_trade_finance(
    invoice=export_invoice,
    letter_of_credit=lc_document
)
```

**Outcome:** 24‑hour approval, lower minimum transaction size, verifiable proof for all parties.

---

## Use Case 3: Unsecured Credit Line

**Scenario:** SMB requests unsecured credit line based on business performance.

**Without Gravit:**

- Relies on self‑reported data
- High default risk
- Limited to established businesses

**With Gravit:**

```python
result = gravit.verify_business_health(
    bank_statements=statements,
    tax_returns=tax_docs,
    cash_flow=cash_flow_data
)
```

**Outcome:** Access for newer businesses, verifiable risk assessment, increased institutional LP confidence.

---

## Comparison: With vs Without Gravit

| Aspect               | Without Gravit                | With Gravit                        |
|:--------------------:|:-----------------------------:|:----------------------------------:|
| Verification time     | 1–7 days                      | < 2 seconds                        |
| Fraud detection       | Manual review                 | Multi‑AI consensus                 |
| Audit trail           | Limited                       | Cryptographic proof                |
| Institutional capital | Difficult                     | Built‑in compliance                |
| Regulatory approval   | Per jurisdiction              | Basel / MiCA compatible            |

---
