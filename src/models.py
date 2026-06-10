"""Data models for verification requests and results."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class VerificationRequest:
    """Request for epistemic verification."""
    intent: str
    action: Dict[str, Any]
    context: Dict[str, Any]
    agent_id: Optional[str] = None
    reasoning_chain: Optional[List[str]] = None


@dataclass
class VerificationResult:
    """Result of epistemic verification."""
    valid: bool
    semantic_score: float
    policy_compliant: bool
    adversarial_risk: float
    trace_id: str
    proof: Optional[Dict[str, Any]] = None
    failure_reason: Optional[str] = None
    lineage_valid: bool = True
