"""Tests for ERC-8004-GT audit proof generation and validation."""

import pytest
import json
import hashlib
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.models import VerificationResult, VerificationRequest
from src.audit_proof import AuditProofGenerator, AuditProofValidator


class TestAuditProofGeneration:
    """Test audit proof generation."""

    def test_generate_basic_proof(self):
        generator = AuditProofGenerator()

        result = VerificationResult(
            valid=True,
            semantic_score=0.94,
            policy_compliant=True,
            adversarial_risk=0.04,
            trace_id="trace_123",
            proof=None
        )

        request = VerificationRequest(
            intent="Send 100 EURAU to Alice",
            action={"type": "transfer", "to": "Alice", "amount": 100},
            context={"balance": 500}
        )

        proof = generator.generate(request, result, agent_id="agent_001")

        assert proof["proof_id"] is not None
        assert proof["timestamp"] > 0
        assert proof["agent_id"] == "agent_001"
        assert "intent_hash" in proof
        assert "verification_result" in proof
        assert proof["verification_result"]["semantic_score"] == 0.94

    def test_proof_hashes_are_deterministic(self):
        generator = AuditProofGenerator()

        intent = "Send 100 EURAU to Alice"
        hash1 = generator._compute_hash(intent, "intent")
        hash2 = generator._compute_hash(intent, "intent")

        assert hash1 == hash2


class TestAuditProofValidation:
    """Test audit proof validation."""

    def test_valid_proof_passes_validation(self):
        generator = AuditProofGenerator()
        validator = AuditProofValidator()

        result = VerificationResult(
            valid=True, semantic_score=0.94,
            policy_compliant=True, adversarial_risk=0.04,
            trace_id="trace_123", proof=None
        )

        request = VerificationRequest(
            intent="Send 100 EURAU to Alice",
            action={"type": "transfer", "to": "Alice", "amount": 100},
            context={"balance": 500}
        )

        proof = generator.generate(request, result, agent_id="agent_001")

        proof["signatures"].append({
            "signer": "test_verifier",
            "algorithm": "secp256k1",
            "signature": "0x" + "00" * 32,
            "signed_message": json.dumps({k: v for k, v in proof.items() if k != "signatures"})
        })

        is_valid = validator.validate(proof)
        assert is_valid is True

    def test_tampered_proof_fails_validation(self):
        generator = AuditProofGenerator()
        validator = AuditProofValidator()

        result = VerificationResult(
            valid=True, semantic_score=0.94,
            policy_compliant=True, adversarial_risk=0.04,
            trace_id="trace_123", proof=None
        )

        request = VerificationRequest(
            intent="Send 100 EURAU to Alice",
            action={"type": "transfer", "to": "Alice", "amount": 100},
            context={"balance": 500}
        )

        proof = generator.generate(request, result, agent_id="agent_001")
        proof["verification_result"]["semantic_score"] = 0.99

        is_valid = validator.validate(proof)
        assert is_valid is False
