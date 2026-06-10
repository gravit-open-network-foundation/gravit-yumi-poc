"""Tests for ERC-8004-GT audit proof generation and validation."""

import pytest
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "proofs"))

from src.models import VerificationResult, VerificationRequest
from proofs.audit_proof import AuditProofGenerator, AuditProofValidator
from proofs.merkle_commitment import MerkleTree
from signatures.proof_signer import ProofSigner


class TestAuditProofGeneration:
    """Test audit proof generation."""

    def test_generate_basic_proof(self):
        """Test generation of basic audit proof."""
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

        # Check required fields
        assert proof["proof_id"] is not None
        assert proof["timestamp"] > 0
        assert proof["agent_id"] == "agent_001"
        assert "intent_hash" in proof
        assert "action_hash" in proof
        assert "context_hash" in proof
        assert "verification_result" in proof
        assert proof["verification_result"]["semantic_score"] == 0.94
        assert "signatures" in proof

    def test_proof_hashes_are_deterministic(self):
        """Test that same inputs produce same hashes."""
        generator = AuditProofGenerator()

        intent = "Send 100 EURAU to Alice"
        action = {"type": "transfer", "to": "Alice", "amount": 100}
        context = {"balance": 500}

        hash1 = generator._compute_hash(intent, "intent")
        hash2 = generator._compute_hash(intent, "intent")

        assert hash1 == hash2

        # Different intent → different hash
        hash3 = generator._compute_hash("Send 200 EURAU", "intent")
        assert hash1 != hash3

    def test_proof_includes_lineage_commitment(self):
        """Test that reasoning lineage is committed in proof."""
        generator = AuditProofGenerator()

        reasoning_chain = [
            "User requested payment of 100 EURAU",
            "Alice is on approved payee list",
            "Balance is sufficient (550 EURAU available)"
        ]

        tree = MerkleTree(reasoning_chain)
        merkle_root = tree.get_root()

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

        assert "lineage_commitment" in proof
        assert "merkle_root" in proof["lineage_commitment"]


class TestAuditProofValidation:
    """Test audit proof validation."""

    def test_valid_proof_passes_validation(self):
        """Test that a correctly generated proof validates."""
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

        # Add signature (mock)
        proof["signatures"].append({
            "signer": "test_verifier",
            "algorithm": "secp256k1",
            "signature": "0x" + "00" * 32,
            "signed_message": json.dumps({k: v for k, v in proof.items() if k != "signatures"})
        })

        is_valid = validator.validate(proof)
        assert is_valid is True

    def test_tampered_proof_fails_validation(self):
        """Test that tampered proof fails validation."""
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

        # Tamper with semantic score
        proof["verification_result"]["semantic_score"] = 0.99

        is_valid = validator.validate(proof)
        assert is_valid is False

    def test_missing_field_fails_validation(self):
        """Test that proof missing required field fails validation."""
        validator = AuditProofValidator()

        proof = {
            "proof_id": "test",
            "timestamp": 1234567890
            # Missing required fields
        }

        is_valid = validator.validate(proof)
        assert is_valid is False


class TestMerkleCommitment:
    """Test Merkle tree commitment for reasoning lineage."""

    def test_merkle_tree_construction(self):
        """Test Merkle tree construction from reasoning chain."""
        chain = ["step1", "step2", "step3", "step4"]

        tree = MerkleTree(chain)
        root = tree.get_root()

        assert root is not None
        assert len(root) == 64 or root.startswith("0x")

    def test_merkle_proof_verification(self):
        """Test that Merkle proof verifies correctly."""
        chain = ["A", "B", "C", "D"]

        tree = MerkleTree(chain)
        root = tree.get_root()

        # Get proof for leaf 1 (index 0)
        proof = tree.get_proof(0)

        # Verify
        leaf_hash = hashlib.sha256(chain[0].encode()).hexdigest()
        is_valid = tree.verify_proof(leaf_hash, proof, root)

        assert is_valid is True

    def test_tampered_leaf_fails_verification(self):
        """Test that tampered leaf fails Merkle verification."""
        chain = ["A", "B", "C", "D"]

        tree = MerkleTree(chain)
        root = tree.get_root()

        proof = tree.get_proof(0)

        # Tampered leaf
        tampered_hash = hashlib.sha256("X".encode()).hexdigest()
        is_valid = tree.verify_proof(tampered_hash, proof, root)

        assert is_valid is False


class TestProofSigning:
    """Test cryptographic signing of proofs."""

    def test_sign_and_verify(self):
        """Test signing a proof and verifying signature."""
        signer = ProofSigner()

        # Generate key pair (in test, use deterministic or mock)
        private_key = signer.generate_private_key()
        public_key = signer.get_public_key(private_key)

        proof = {
            "proof_id": "test_001",
            "timestamp": int(time.time()),
            "data": "test_data"
        }

        signature = signer.sign(proof, private_key)
        is_valid = signer.verify(proof, signature, public_key)

        assert is_valid is True

    def test_signature_fails_on_tampered_data(self):
        """Test that tampered data invalidates signature."""
        signer = ProofSigner()

        private_key = signer.generate_private_key()
        public_key = signer.get_public_key(private_key)

        proof = {"proof_id": "test_001", "value": 100}
        signature = signer.sign(proof, private_key)

        # Tamper
        proof["value"] = 999

        is_valid = signer.verify(proof, signature, public_key)
        assert is_valid is False


class TestComplianceExport:
    """Test compliance report export functionality."""

    def test_export_micar_report(self):
        """Test exporting proof as MiCAR-compliant report."""
        from compliance.micar_exporter import export_for_micar

        proof = {
            "proof_id": "micar_test_001",
            "timestamp": 1717200000000,
            "agent_id": "test_agent",
            "verification_result": {
                "semantic_score": 0.94,
                "policy_compliant": True,
                "adversarial_risk": 0.04
            },
            "signatures": [{"signer": "test_verifier", "signature": "0x..."}]
        }

        report = export_for_micar(proof)

        assert "transaction_id" in report
        assert "verification_timestamp" in report
        assert "outcome" in report
        assert "rationale" in report
        assert "audit_proof_reference" in report

    def test_export_bafin_format(self):
        """Test exporting proof for BaFin format."""
        from compliance.bafin_exporter import export_for_bafin

        proof = {
            "proof_id": "bafin_test_001",
            "timestamp": 1717200000000,
            "agent_id": "test_agent",
            "verification_result": {
                "semantic_score": 0.94,
                "policy_compliant": True,
                "adversarial_risk": 0.04
            }
        }

        report = export_for_bafin(proof)

        assert "pruefbericht" in report or "report_id" in report
        assert "entscheidung" in report  # decision in German
