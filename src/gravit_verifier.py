#!/usr/bin/env python3
"""
Gravit Epistemic Verifier – Core Trust Engine
Production-grade verification for credit decisions
"""

import os
import json
import hashlib
import hmac
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import IntEnum

import requests
from dotenv import load_dotenv

load_dotenv()


class TrustScore(IntEnum):
    """Trust score thresholds (0-255)"""
    CRITICAL = 0      # Definitely fraudulent
    SUSPICIOUS = 64    # High risk
    NEUTRAL = 128      # Needs review
    TRUSTED = 192      # Low risk
    VERIFIED = 224     # Cryptographically verified
    MAX = 255          # Perfect trust


@dataclass
class AuditProof:
    """Cryptographic audit trail for regulatory compliance"""
    trace_id: str
    timestamp: str
    decision: str
    trust_score: int
    confidence: float
    reasoning_chain: List[str]
    model_agreement: Dict[str, float]
    cryptographic_hash: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    def verify(self) -> bool:
        """Verify cryptographic integrity of audit proof"""
        expected_hash = hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True).encode()
        ).hexdigest()
        return hmac.compare_digest(expected_hash, self.cryptographic_hash)


class GravitVerifier:
    """
    Production verification engine for financial decisions.
    Compatible with banks, DeFi protocols, and credit platforms.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_key = api_key or os.getenv("GRAVIT_API_KEY")
        self.base_url = base_url or os.getenv("GRAVIT_VERIFIER_URL", "http://localhost:8080/v1")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def verify_credit(
        self,
        borrower_id: str,
        requested_amount: float,
        reasoning_chain: List[str],
        context: Dict[str, Any],
        agent_id: str = "underwriting_agent"
    ) -> Dict[str, Any]:
        """
        Verify a credit underwriting decision.

        Returns:
            {
                "decision": "approve" | "deny" | "review",
                "trust_score": int (0-255),
                "trace_id": str,
                "audit_proof": str
            }
        """

        payload = {
            "action": "issue_credit",
            "agent_id": agent_id,
            "borrower_id": borrower_id,
            "requested_amount": requested_amount,
            "reasoning_chain": reasoning_chain,
            "context": context,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/verify",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            return {
                "decision": "deny",
                "trust_score": TrustScore.CRITICAL,
                "trace_id": f"error_{int(time.time())}",
                "error": str(e)
            }

        # Transform result
        trust_score = int(result.get("score", 0) * 255)

        if result.get("status") == "passed" and result.get("decision") == "allowed":
            if trust_score >= TrustScore.VERIFIED:
                decision = "approve"
            elif trust_score >= TrustScore.TRUSTED:
                decision = "approve_with_review"
            else:
                decision = "review"
        else:
            decision = "deny"

        return {
            "decision": decision,
            "trust_score": trust_score,
            "confidence": result.get("score", 0),
            "trace_id": result.get("trace_id", ""),
            "audit_proof": result.get("audit_proof", ""),
            "checks_passed": result.get("checks", {})
        }

    def verify_invoice(
        self,
        invoice_id: str,
        supplier_id: str,
        buyer_id: str,
        amount: float,
        invoice_text: str,
        llm_analysis: Optional[str] = None
    ) -> Dict[str, Any]:
        """Specialized verification for trade finance invoices."""

        reasoning = [
            f"Invoice {invoice_id} from {supplier_id} to {buyer_id}",
            f"Amount: {amount}",
            "Verifying semantic consistency and fraud patterns"
        ]

        if llm_analysis:
            reasoning.append(f"LLM analysis: {llm_analysis[:200]}")

        context = {
            "supplier_id": supplier_id,
            "buyer_id": buyer_id,
            "invoice_text": invoice_text[:2000],
            "industry": "trade_finance"
        }

        return self.verify_credit(
            borrower_id=supplier_id,
            requested_amount=amount,
            reasoning_chain=reasoning,
            context=context,
            agent_id="invoice_verifier"
        )

    def get_audit_trail(self, trace_id: str) -> Dict[str, Any]:
        """Retrieve full audit trail for a verification."""

        try:
            response = self.session.get(
                f"{self.base_url}/audit/{trace_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "trace_id": trace_id}
