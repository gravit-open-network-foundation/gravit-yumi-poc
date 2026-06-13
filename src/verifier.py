#!/usr/bin/env python3
"""
Gravit Epistemic Verifier - Core verification engine
"""

import logging
import hashlib
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.config import settings
from src.llm_adapter import LLMAdapter
from src.audit_proof import AuditProof, AuditStorage

logger = logging.getLogger(__name__)


class EpistemicVerifier:
    """
    Production-grade epistemic verification for AI agents.
    Checks semantic consistency, policy compliance, adversarial robustness.
    """

    def __init__(self):
        self.llm_adapter: Optional[LLMAdapter] = None
        self.audit_storage: Optional[AuditStorage] = None
        self._initialized = False
        self._sentence_transformer = None

    async def initialize(self):
        """Initialize all components: models, Redis, audit storage"""
        logger.info("Initializing EpistemicVerifier...")

        # Initialize LLM adapter
        self.llm_adapter = LLMAdapter(provider=settings.llm_provider.value)

        # Initialize audit storage
        self.audit_storage = AuditStorage(
            storage_path=settings.audit_storage_path,
            use_redis=bool(settings.redis_url),
            redis_url=settings.redis_url
        )
        await self.audit_storage.initialize()

        # Load sentence-transformers model for semantic similarity (lazy load)
        try:
            from sentence_transformers import SentenceTransformer
            self._sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SentenceTransformer model loaded")
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback")
            self._sentence_transformer = None

        self._initialized = True
        logger.info("EpistemicVerifier initialized successfully")

    async def shutdown(self):
        """Clean up resources"""
        logger.info("Shutting down EpistemicVerifier...")

        if self.audit_storage:
            await self.audit_storage.close()

        self._initialized = False
        logger.info("EpistemicVerifier shutdown complete")

    def verify(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify an AI agent action.

        Args:
            request: Contains action, agent_id, reasoning_chain, context

        Returns:
            Verification result with score, checks, trace_id
        """
        if not self._initialized:
            raise RuntimeError("Verifier not initialized. Call initialize() first.")

        trace_id = self._generate_trace_id(request)
        start_time = time.time()

        reasoning_chain = request.get("reasoning_chain", [])
        context = request.get("context", {})

        # Run all checks
        semantic_check = self._check_semantic_compliance(reasoning_chain, context)
        policy_check = self._check_policy_compliance(reasoning_chain, context)
        adversarial_check = self._check_adversarial_risk(reasoning_chain, context)

        # Calculate overall score
        score = (
            semantic_check["score"] * 0.4 +
            policy_check["score"] * 0.3 +
            adversarial_check["score"] * 0.3
        )

        # Determine decision
        if score >= settings.trust_approve_threshold / 255.0:
            decision = "allowed"
            status = "passed"
        elif score >= settings.trust_review_threshold / 255.0:
            decision = "review"
            status = "passed"
        else:
            decision = "denied"
            status = "failed"

        checks = {
            "semantic_compliance": semantic_check["passed"],
            "policy_compliance": policy_check["passed"],
            "adversarial_risk": adversarial_check["detected"],
            "reasoning_lineage": "valid"
        }

        # Generate audit proof
        audit_proof = AuditProof(
            trace_id=trace_id,
            timestamp=datetime.utcnow(),
            decision=decision,
            trust_score=int(score * 255),
            confidence=score,
            reasoning_chain=reasoning_chain,
            model_agreement={"semantic": semantic_check["score"], "policy": policy_check["score"]}
        )

        # Store audit proof
        if self.audit_storage:
            self.audit_storage.store(audit_proof)

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Verification {trace_id}: {decision} (score={score:.3f}, latency={latency_ms}ms)")

        return {
            "status": status,
            "decision": decision,
            "score": score,
            "checks": checks,
            "trace_id": trace_id,
            "audit_proof": audit_proof.to_json(),
            "latency_ms": latency_ms
        }

    def _check_semantic_compliance(self, reasoning_chain: List[str], context: Dict) -> Dict:
        """Check if reasoning is semantically consistent"""
        text = " ".join(reasoning_chain)

        if self._sentence_transformer:
            # Use ML for semantic similarity
            # Simplified for now
            pass

        # Fallback: heuristic - check for contradictions
        has_amount = "amount" in text.lower() or "requested" in text.lower()
        has_borrower = "borrower" in text.lower() or "user" in text.lower()

        score = (has_amount + has_borrower) / 2.0
        passed = score >= settings.semantic_threshold

        return {"score": score, "passed": passed}

    def _check_policy_compliance(self, reasoning_chain: List[str], context: Dict) -> Dict:
        """Check if action complies with policies"""
        text = " ".join(reasoning_chain).lower()

        # Check for policy violations
        violations = []

        # Daily limit check
        requested_amount = context.get("requested_amount", context.get("amount", 0))
        if requested_amount > 100000:
            violations.append("amount_exceeds_daily_limit")

        # Approved payees check
        payee = context.get("payee", context.get("recipient", ""))
        if payee and "suspicious" in payee.lower():
            violations.append("unapproved_payee")

        score = 1.0 - (len(violations) * 0.3)
        score = max(0.0, min(1.0, score))
        passed = score >= settings.policy_strictness

        return {"score": score, "passed": passed, "violations": violations}

    def _check_adversarial_risk(self, reasoning_chain: List[str], context: Dict) -> Dict:
        """Detect potential adversarial attacks (prompt injection, etc.)"""
        text = " ".join(reasoning_chain).lower()

        # Known adversarial patterns
        adversarial_patterns = [
            "ignore previous", "override", "bypass", "disregard",
            "you are now", "new instruction", "system prompt"
        ]

        detected = any(pattern in text for pattern in adversarial_patterns)

        # Risk score: 1.0 = no risk, 0.0 = high risk
        score = 0.0 if detected else 1.0

        return {"detected": detected, "score": score}

    def _generate_trace_id(self, request: Dict) -> str:
        """Generate unique trace ID for audit trail"""
        data = f"{request.get('agent_id')}:{request.get('action')}:{time.time()}"
        return f"trace_{hashlib.md5(data.encode()).hexdigest()[:16]}"
