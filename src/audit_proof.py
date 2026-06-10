"""Audit proof generation and validation (ERC-8004-GT)."""

import json
import hashlib
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from .models import VerificationRequest, VerificationResult


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
        intent_hash = self._compute_hash(request.intent, "intent")
        action_hash = self._compute_hash(json.dumps(request.action), "action")
        context_hash = self._compute_hash(json.dumps(request.context), "context")

        verification_result = {
            "semantic_score": result.semantic_score,
            "semantic_valid": result.semantic_score >= 0.75,
            "policy_compliant": result.policy_compliant,
            "adversarial_risk": result.adversarial_risk,
            "overall_valid": result.valid,
            "trace_id": result.trace_id
        }

        lineage_commitment = None
        if reasoning_chain:
            lineage_commitment = self._build_lineage_commitment(reasoning_chain)

        return {
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

    def _compute_hash(self, data: str, field: str) -> str:
        if not data:
            data = ""
        return hashlib.sha256(f"{field}:{data}".encode()).hexdigest()

    def _build_lineage_commitment(self, reasoning_chain: List[str]) -> Dict[str, str]:
        if not reasoning_chain:
            return {"merkle_root": "", "num_steps": 0}

        leaves = [hashlib.sha256(step.encode()).hexdigest() for step in reasoning_chain]
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
        for field in self.required_fields:
            if field not in proof:
                return False

        current_ms = int(time.time() * 1000)
        if proof["timestamp"] > current_ms + 60000:
            return False
        if proof["timestamp"] < current_ms - (30 * 24 * 3600 * 1000):
            return False

        vr = proof["verification_result"]
        if not (0 <= vr["semantic_score"] <= 1):
            return False
        if not (0 <= vr["adversarial_risk"] <= 1):
            return False

        if not proof["signatures"]:
            return False

        return True
