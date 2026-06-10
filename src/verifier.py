"""Core epistemic verifier engine."""

import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .models import VerificationRequest, VerificationResult


class EpistemicVerifier:
    """Main epistemic verification engine."""

    def __init__(
        self,
        semantic_threshold: float = 0.75,
        adversarial_threshold: float = 0.2,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.semantic_threshold = semantic_threshold
        self.adversarial_threshold = adversarial_threshold
        self.model_name = model_name
        self._init_models()

    def _init_models(self):
        """Initialize ML models (lazy loading)."""
        try:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer(self.model_name)
            self._models_loaded = True
        except ImportError:
            self._models_loaded = False
            self.encoder = None

    def verify(self, request: VerificationRequest) -> VerificationResult:
        """Run epistemic verification on request."""
        trace_id = str(uuid.uuid4())

        # 1. Semantic consistency check
        semantic_score = self._check_semantic_consistency(request)
        semantic_valid = semantic_score >= self.semantic_threshold

        # 2. Policy compliance check
        policy_compliant = self._check_policies(request)

        # 3. Adversarial risk detection
        adversarial_risk = self._detect_adversarial(request)

        # 4. Overall validity
        overall_valid = semantic_valid and policy_compliant and (adversarial_risk < self.adversarial_threshold)

        # 5. Generate audit proof
        from .audit_proof import AuditProofGenerator
        proof_gen = AuditProofGenerator()
        proof = proof_gen.generate(
            request=request,
            result=VerificationResult(
                valid=overall_valid,
                semantic_score=semantic_score,
                policy_compliant=policy_compliant,
                adversarial_risk=adversarial_risk,
                trace_id=trace_id,
                proof=None
            ),
            agent_id=request.agent_id or "unknown",
            reasoning_chain=request.reasoning_chain
        )

        failure_reason = None
        if not overall_valid:
            reasons = []
            if not semantic_valid:
                reasons.append(f"semantic_score={semantic_score:.2f} < {self.semantic_threshold}")
            if not policy_compliant:
                reasons.append("policy_violation")
            if adversarial_risk >= self.adversarial_threshold:
                reasons.append(f"adversarial_risk={adversarial_risk:.2f} >= {self.adversarial_threshold}")
            failure_reason = "; ".join(reasons)

        return VerificationResult(
            valid=overall_valid,
            semantic_score=semantic_score,
            policy_compliant=policy_compliant,
            adversarial_risk=adversarial_risk,
            trace_id=trace_id,
            proof=proof,
            failure_reason=failure_reason
        )

    def _check_semantic_consistency(self, request: VerificationRequest) -> float:
        """Check semantic consistency between intent and action."""
        if not self._models_loaded or self.encoder is None:
            # Fallback to simple keyword matching
            intent_lower = request.intent.lower()
            action_str = str(request.action).lower()
            keywords = ["send", "transfer", "pay", "underwrite", "lend", "borrow"]
            matches = sum(1 for kw in keywords if kw in intent_lower and kw in action_str)
            return min(0.9, max(0.3, matches / 3.0))

        # Use sentence transformers
        intent_embedding = self.encoder.encode([request.intent])
        action_str = str(request.action)
        action_embedding = self.encoder.encode([action_str])

        from sklearn.metrics.pairwise import cosine_similarity
        score = cosine_similarity(intent_embedding, action_embedding)[0][0]

        return float(score)

    def _check_policies(self, request: VerificationRequest) -> bool:
        """Check policy compliance."""
        context = request.context
        action = request.action

        # Check daily limits
        if "daily_limit" in context and "amount" in action:
            spent_today = context.get("spent_today", 0)
            if action["amount"] + spent_today > context["daily_limit"]:
                return False

        # Check approved payees
        if "approved_payees" in context and "to" in action:
            if action["to"] not in context["approved_payees"]:
                return False

        # Check balance
        if "balance" in context and "amount" in action:
            if action["amount"] > context["balance"]:
                return False

        return True

    def _detect_adversarial(self, request: VerificationRequest) -> float:
        """Detect adversarial patterns."""
        risk = 0.0

        intent_lower = request.intent.lower()

        # Prompt injection patterns
        injection_patterns = [
            "ignore previous", "ignore instruction", "ignore all",
            "override", "bypass", "disregard"
        ]
        for pattern in injection_patterns:
            if pattern in intent_lower:
                risk += 0.3

        # Hidden intent patterns
        hidden_patterns = ["but actually", "in reality", "secretly"]
        for pattern in hidden_patterns:
            if pattern in intent_lower:
                risk += 0.2

        # Extreme action detection
        action_str = str(request.action).lower()
        if "all funds" in action_str or "entire" in action_str:
            risk += 0.25

        return min(risk, 1.0)
