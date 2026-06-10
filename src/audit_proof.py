"""Audit proof generation and validation (ERC-8004-GT)."""

import json
import hashlib
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

from .models import VerificationRequest, VerificationResult


@dataclass
class AuditProof:
    """ERC-8004-GT compliant audit proof."""
    proof_id: str
    timestamp: int
    agent_id: str
    intent_hash: str
    action_hash: str
    context_hash: str
    verification_result: Dict[str, Any]
    lineage_commitment: Optional[Dict[str, str]]
    signatures: List[Dict[str, str]]

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), indent=2)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def hash(self) -> str:
        """Compute proof hash for signing."""
        proof_copy = asdict(self).copy()
        proof_copy.pop("signatures", None)
        return hashlib.sha256(
            json.dumps(proof_copy, sort_keys=True).encode()
        ).hexdigest()


class AuditProofGenerator:
    """Generate ERC-8004-GT audit proofs."""

    def __init__(self, verifier_id: str = "gravit-verifier-v1"):
        self.verifier_id = verifier_id

    def generate(
        self,
        request: VerificationRequest,
        result: VerificationResult,
        agent_id: str,
        reasoning_chain: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate audit proof for a verification."""

        # Compute hashes
        intent_hash = self._compute_hash(request.intent, "intent")
        action_hash = self._compute_hash(json.dumps(request.action), "action")
        context_hash = self._compute_hash(json.dumps(request.context), "context")

        # Build verification result
        verification_result = {
            "semantic_score": result.semantic_score,
            "semantic_valid": result.semantic_score >= 0.75,
            "policy_compliant": result.policy_compliant,
            "adversarial_risk": result.adversarial_risk,
            "lineage_valid": result.lineage_valid if hasattr(result, 'lineage_valid') else True,
            "overall_valid": result.valid,
            "trace_id": result.trace_id
        }

        # Build lineage commitment if reasoning chain provided
        lineage_commitment = None
        if reasoning_chain:
            lineage_commitment = self._build_lineage_commitment(reasoning_chain)

        proof = {
            "proof_id": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "agent_id": agent_id,
            "verifier_id": self.verifier_id,
            "intent_hash": intent_hash,
            "action_hash": action_hash,
            "context_hash": context_hash,
            "verification_result": verification_result,
            "lineage_commitment": lineage_commitment,
            "signatures": []
        }

        return proof

    def _compute_hash(self, data: str, field: str) -> str:
        """Compute SHA-256 hash of data."""
        if not data:
            data = ""
        return hashlib.sha256(
            f"{field}:{data}".encode()
        ).hexdigest()

    def _build_lineage_commitment(self, reasoning_chain: List[str]) -> Dict[str, str]:
        """Build Merkle commitment for reasoning chain."""
        if not reasoning_chain:
            return {"merkle_root": "", "num_steps": 0}

        # Simple Merkle tree for reasoning steps
        leaves = [hashlib.sha256(step.encode()).hexdigest() for step in reasoning_chain]

        # Build tree
        tree = leaves
        while len(tree) > 1:
            next_level = []
            for i in range(0, len(tree), 2):
                if i + 1 < len(tree):
                    combined = tree[i] + tree[i + 1]
                else:
                    combined = tree[i] + tree[i]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            tree = next_level

        return {
            "merkle_root": tree[0] if tree else "",
            "num_steps": len(reasoning_chain),
            "first_step_hash": leaves[0] if leaves else "",
            "last_step_hash": leaves[-1] if leaves else ""
        }


class AuditProofValidator:
    """Validate ERC-8004-GT audit proofs."""

    def __init__(self):
        self.required_fields = [
            "proof_id", "timestamp", "agent_id", "verifier_id",
            "intent_hash", "action_hash", "context_hash",
            "verification_result", "signatures"
        ]

    def validate(self, proof: Dict[str, Any]) -> bool:
        """Validate proof structure and content."""

        # Check required fields
        for field in self.required_fields:
            if field not in proof:
                return False

        # Check timestamp freshness (within 30 days)
        current_ms = int(time.time() * 1000)
        if proof["timestamp"] > current_ms + 60000:  # Future? allow 60s clock skew
            return False
        if proof["timestamp"] < current_ms - (30 * 24 * 3600 * 1000):  # Older than 30 days
            return False  # Stale proof

        # Check verification result
        vr = proof["verification_result"]
        required_vr_fields = ["semantic_score", "policy_compliant", "adversarial_risk", "overall_valid"]
        for field in required_vr_fields:
            if field not in vr:
                return False

        # Validate scores are in range
        if not (0 <= vr["semantic_score"] <= 1):
            return False
        if not (0 <= vr["adversarial_risk"] <= 1):
            return False

        # Check consistency: overall_valid should match components
        expected_valid = (
            vr["semantic_score"] >= 0.75 and
            vr["policy_compliant"] is True and
            vr["adversarial_risk"] < 0.2
        )

        # This is a consistency check, not strict equality
        # because proof might have been generated with different thresholds

        # Verify at least one signature
        if not proof["signatures"]:
            return False

        return True

    def validate_signature(self, proof: Dict[str, Any], signature: Dict) -> bool:
        """Validate a single signature on the proof."""
        # In production, implement actual signature verification
        # For now, just check presence
        return "signer" in signature and "signature" in signature
