#!/usr/bin/env python3
"""
Yumi Finance Adapter for Gravit Trust Layer
Connects Yumi credit engine to Gravit verification
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from gravit_verifier import GravitVerifier, TrustScore


@dataclass
class YumiCreditRequest:
    """Credit request from Yumi Finance"""
    borrower_id: str
    requested_amount: float
    invoice_text: Optional[str] = None
    credit_history: Optional[Dict] = None
    industry: str = "unknown"


class YumiGravitAdapter:
    """
    Adapter between Yumi Finance API and Gravit verifier.
    Handles request transformation, error handling, and logging.
    """

    def __init__(
        self,
        gravit: Optional[GravitVerifier] = None,
        min_trust_score: int = TrustScore.TRUSTED,
        require_audit_proof: bool = True
    ):
        self.gravit = gravit or GravitVerifier()
        self.min_trust_score = min_trust_score
        self.require_audit_proof = require_audit_proof

    async def process_credit_request(self, request: YumiCreditRequest) -> Dict[str, Any]:
        """
        Process a credit request through Gravit verification.

        Returns:
            {
                "approved": bool,
                "decision": str,
                "trust_score": int,
                "trace_id": str,
                "audit_proof": str (optional),
                "reason": str (if denied)
            }
        """

        # Build reasoning chain from Yumi data
        reasoning_chain = self._build_reasoning_chain(request)

        # Prepare context
        context = {
            "industry": request.industry,
            "credit_history": request.credit_history,
            "platform": "yumi_finance",
            "verification_timestamp": None  # Will be set by Gravit
        }

        if request.invoice_text:
            context["invoice_text"] = request.invoice_text[:2000]

        # Verify with Gravit
        if request.invoice_text:
            verification = self.gravit.verify_invoice(
                invoice_id=f"YUMI_{request.borrower_id}_{int(time.time())}",
                supplier_id=request.borrower_id,
                buyer_id="yumi_lender",
                amount=request.requested_amount,
                invoice_text=request.invoice_text,
                llm_analysis=self._generate_llm_analysis(request)
            )
        else:
            verification = self.gravit.verify_credit(
                borrower_id=request.borrower_id,
                requested_amount=request.requested_amount,
                reasoning_chain=reasoning_chain,
                context=context
            )

        # Apply Yumi-specific rules
        approved = (
            verification["decision"] != "deny" and
            verification["trust_score"] >= self.min_trust_score
        )

        result = {
            "approved": approved,
            "decision": verification["decision"],
            "trust_score": verification["trust_score"],
            "trace_id": verification.get("trace_id", ""),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        if self.require_audit_proof and "audit_proof" in verification:
            result["audit_proof"] = verification["audit_proof"]

        if not approved:
            result["reason"] = verification.get("error", "Trust score below threshold")

        return result

    def _build_reasoning_chain(self, request: YumiCreditRequest) -> list:
        """Build human-readable reasoning chain for audit"""
        chain = []

        if request.credit_history:
            if request.credit_history.get("loans_taken", 0) > 0:
                chain.append(f"Borrower has {request.credit_history.get('loans_taken')} previous loans")
                chain.append(f"Repayment rate: {request.credit_history.get('repayment_rate', 0)}%")

        if request.invoice_text:
            chain.append("Invoice-based financing request")
            chain.append("Verifying invoice authenticity via Gravit consensus")

        chain.append(f"Requested amount: {request.requested_amount}")
        chain.append(f"Industry: {request.industry}")

        return chain

    def _generate_llm_analysis(self, request: YumiCreditRequest) -> str:
        """Generate LLM analysis of invoice (simplified for PoC)"""
        if not request.invoice_text:
            return ""

        # In production, this would call Grok/Claude/GPT-4
        # For PoC, return a placeholder
        return f"Invoice analysis for {request.borrower_id}: Standard trade finance document structure detected."


# Example usage
if __name__ == "__main__":
    import asyncio
    import time

    async def demo():
        adapter = YumiGravitAdapter()

        # Test request
        request = YumiCreditRequest(
            borrower_id="SME_TEST_001",
            requested_amount=50000,
            invoice_text="INVOICE #TEST-001\nSupplier: Test GmbH\nAmount: €50,000",
            credit_history={"loans_taken": 3, "repayment_rate": 100},
            industry="manufacturing"
        )

        result = await adapter.process_credit_request(request)
        print(f"Result: {result}")

    asyncio.run(demo())
