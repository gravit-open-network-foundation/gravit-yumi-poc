"""Tests for Yumi Finance adapter integration."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "integrations" / "yumi"))

from src.verifier import EpistemicVerifier
from src.models import VerificationRequest


class TestYumiIntegration:
    """Test Yumi Finance specific integration scenarios."""

    @pytest.fixture
    def yumi_loan_request(self):
        return {
            "request_id": "loan_req_123",
            "type": "loan_underwriting",
            "amount": 500000,
            "borrower": "SME_Corp",
            "collateral": {"type": "real_estate", "value": 750000},
            "terms": {"duration_months": 12, "interest_rate": 0.08}
        }

    def test_yumi_loan_verification(self, yumi_loan_request):
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
            "risk_policies": {"max_loan_to_value": 0.8, "min_collateral_ratio": 1.2},
            "current_exposure": 2000000
        }

        request = VerificationRequest(intent=intent, action=action, context=context)
        result = verifier.verify(request)

        assert isinstance(result.valid, bool)
        assert isinstance(result.semantic_score, float)

    def test_yumi_defi_lending_verification(self):
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

        request = VerificationRequest(intent=intent, action=action, context=context)
        result = verifier.verify(request)

        assert result.policy_compliant is True or result.semantic_score > 0.7

    def test_yumi_trade_finance_verification(self):
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

        request = VerificationRequest(intent=intent, action=action, context=context)
        result = verifier.verify(request)

        if "certificate_of_origin" not in action["documents_validated"]:
            assert result.policy_compliant is False
