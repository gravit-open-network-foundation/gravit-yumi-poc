#!/usr/bin/env python3
"""
EpistemicCreditProof - Core cryptographic artifact for Gravit
Combines trust score, consensus data, evidence, and reasoning
"""

import json
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum


class TrustLevel(Enum):
    CRITICAL = 0
    SUSPICIOUS = 1
    NEUTRAL = 2
    TRUSTED = 3
    VERIFIED = 4
    MAX = 5


@dataclass
class ModelConsensus:
    model_name: str
    raw_score: float
    confidence: float
    anomalies_detected: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EpistemicCreditProof:
    proof_id: str
    trace_id: str
    timestamp: datetime
    trust_score: float          # 0.0 - 1.0
    fraud_probability: float
    consensus_confidence: float
    borrower_id: str
    requested_amount: float
    currency: str = "USD"
    decision: str               # approve, deny, review
    reasoning_summary: str
    failed_checks: List[str] = field(default_factory=list)
    models_consensus: List[ModelConsensus] = field(default_factory=list)
    proof_hash: str = ""
    signature: Optional[str] = None
    full_reasoning_chain: List[str] = field(default_factory=list)
    verifier_version: str = "1.0.0"

    def __post_init__(self):
        if not self.proof_hash:
            self.proof_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = {
            "proof_id": self.proof_id,
            "trace_id": self.trace_id,
            "trust_score": self.trust_score,
            "borrower_id": self.borrower_id,
            "decision": self.decision
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:32]

    def verify(self, expected_hash: Optional[str] = None) -> bool:
        target = expected_hash or self.proof_hash
        return hmac.compare_digest(self._compute_hash(), target)

    def to_dict(self) -> Dict:
        return {
            "proof_id": self.proof_id,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "trust_score": self.trust_score,
            "fraud_probability": self.fraud_probability,
            "consensus_confidence": self.consensus_confidence,
            "decision": self.decision,
            "reasoning_summary": self.reasoning_summary,
            "proof_hash": self.proof_hash
        }
