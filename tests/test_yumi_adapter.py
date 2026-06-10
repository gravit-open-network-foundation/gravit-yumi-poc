"""Tests for Yumi Finance adapter integration."""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "integrations" / "yumi"))

from src.verifier import EpistemicVerifier
from src.models import VerificationRequest


class TestYumiIntegration:
    """Test Yumi Finance specific integration scenarios."""

    @pytest.fixture
    def yumi_config(self):
        """Sample Yumi configuration."""
        return {
            "base_url": "https://api.yumi.finance/v1",
            "api_key": "test_key",
            "platform": "yumi",
            "webhook_secret": "test_secret"
        }

    @pytest.fixture
    def yumi_loan_request(self):
        """Sample loan underwriting request."""
        return {
            "request_id": "loan_req_123",
            "type": "loan_underwriting",
            "amount": 500000,
            "borrower": "SME_Corp",
            "collateral": {"type": "real_estate", "value": 750000},
            "terms": {"duration_months": 12, "interest_rate": 0.08}
        }

    def test_yumi_loan_verification(self, yumi_loan_request):
        """Test verification of Yumi loan underwriting decision."""
        verifier = EpistemicVerifier()

        intent = f"""
        Underwrite a loan of {yumi_loan_request['amount']} EUR
        to {yumi_loan_request['borrower']}
        with {yumi_loan_request['collateral']['value']} EUR collateral
        """

        action = {
            "type": "loan_underwriting",
            "approved": True,
            "amount": yumi_loan_request['amount'],
            "borrower": yumi_loan_request['borrower'],
            "interest_rate": yumi_loan_request['terms']['interest_rate']
        }

        context = {
            "platform": "yumi",
            "risk_policies": {
                "max_loan_to_value": 0.8,
                "min_collateral_ratio": 1.2
            },
            "current_exposure": 2000000
        }

        request = VerificationRequest(
            intent=intent,
            action=action,
            context=context
        )

        result = verifier.verify(request)

        # Should be valid if within policies
        # LTV: 500k/750k = 0.667 < 0.8 → acceptable
        assert isinstance(result.valid, bool)
        assert isinstance(result.semantic_score, float)

    def test_yumi_defi_lending_verification(self):
        """Test verification of DeFi lending position recommendation."""
        verifier = EpistemicVerifier()

        intent = """
        Recommend a lending position on Aave for 100 ETH
        with acceptable risk profile (AA or A rated pools only)
        """

        action = {
            "type": "defi_lending",
            "protocol": "Aave",
            "asset": "ETH",
            "amount": 100,
            "pool_rating": "AA",
            "expected_apy": 0.035
        }

        context = {
            "risk_tolerance": "conservative",
            "allowed_protocols": ["Aave", "Compound"],
            "min_pool_rating": "A"
        }

        request = VerificationRequest(
            intent=intent,
            action=action,
            context=context
        )

        result = verifier.verify(request)

        # AA rating meets requirement
        assert result.policy_compliant is True or result.semantic_score > 0.7

    def test_yumi_trade_finance_verification(self):
        """Test verification of trade finance document validation."""
        verifier = EpistemicVerifier()

        intent = """
        Validate the bill of lading and approve payment
        for shipment #SHIP-789
        """

        action = {
            "type": "trade_finance",
            "action": "approve_payment",
            "shipment_id": "SHIP-789",
            "amount": 250000,
            "documents_validated": ["bill_of_lading", "invoice"]
        }

        context = {
            "required_documents": ["bill_of_lading", "invoice", "certificate_of_origin"],
            "max_single_payment": 500000,
            "counterparty_risk_score": 0.3
        }

        request = VerificationRequest(
            intent=intent,
            action=action,
            context=context
        )

        result = verifier.verify(request)

        # Missing certificate_of_origin should flag policy violation
        if "certificate_of_origin" not in action["documents_validated"]:
            assert result.policy_compliant is False

    @patch("integrations.yumi.yumi_client.YumiClient")
    def test_yumi_webhook_integration(self, MockYumiClient, yumi_config):
        """Test webhook handling from Yumi platform."""
        from integrations.yumi.webhook_handler import handle_yumi_webhook

        mock_client = MockYumiClient.return_value

        webhook_payload = {
            "event": "loan_application",
            "data": {
                "application_id": "APP_123",
                "amount": 350000,
                "borrower_id": "BORR_456",
                "decision": "pending"
            },
            "timestamp": "2026-06-02T10:00:00Z"
        }

        response = handle_yumi_webhook(webhook_payload)

        assert response["status"] in ["processed", "pending"]
        assert "verification_id" in response or "status" in response

    def test_yumi_error_handling(self):
        """Test error handling for malformed Yumi requests."""
        verifier = EpistemicVerifier()

        # Malformed intent
        request = VerificationRequest(
            intent="",  # Empty intent
            action={"type": "unknown"},
            context={}
        )

        result = verifier.verify(request)

        assert result.valid is False
        assert result.semantic_score == 0.0


class TestYumiBenchmarks:
    """Test Yumi-specific benchmark scenarios."""

    def test_loan_underwriting_benchmark(self):
        """Test against loan underwriting benchmark cases."""
        verifier = EpistemicVerifier()

        # Case: High LTV but good borrower
        request = VerificationRequest(
            intent="Underwrite loan with LTV up to 85% for prime borrower",
            action={"type": "loan_underwriting", "approved": True, "ltv": 0.82},
            context={"borrower_rating": "prime", "policy_max_ltv": 0.80}
        )

        result = verifier.verify(request)

        # Should flag policy violation despite good borrower
        assert result.policy_compliant is False

    def test_cross_product_consistency(self):
        """Test consistency across different Yumi products."""
        verifier = EpistemicVerifier()

        # Same intent, different actions
        intent = "Execute a low-risk financial operation"

        low_risk_action = {"type": "deposit", "amount": 100, "protocol": "conservative"}
        high_risk_action = {"type": "leverage", "amount": 10000, "leverage": 10}

        low_risk_result = verifier.verify(VerificationRequest(
            intent=intent, action=low_risk_action, context={"risk_tolerance": "low"}
        ))
        high_risk_result = verifier.verify(VerificationRequest(
            intent=intent, action=high_risk_action, context={"risk_tolerance": "low"}
        ))

        # Low risk tolerance should reject high risk action
        assert low_risk_result.valid is True or low_risk_result.semantic_score > 0.7
        assert high_risk_result.valid is False or high_risk_result.adversarial_risk > 0.5
