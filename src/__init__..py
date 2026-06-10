"""Gravit Epistemic Verifier - Core package."""

__version__ = "0.1.0"
__author__ = "Gravit Open Network Foundation"

from .verifier import EpistemicVerifier
from .models import VerificationRequest, VerificationResult

__all__ = [
    "EpistemicVerifier",
    "VerificationRequest",
    "VerificationResult",
]
