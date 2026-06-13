#!/usr/bin/env python3
"""
Audit Proof generation and verification with real cryptographic signatures
"""

import json
import hashlib
import hmac
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


@dataclass
class AuditProof:
    """Cryptographic audit trail with real signatures"""
    trace_id: str
    timestamp: datetime
    decision: str
    trust_score: int
    confidence: float
    reasoning_chain: List[str]
    model_agreement: Dict[str, float]
    signature: Optional[str] = None
    public_key_pem: Optional[str] = None

    def to_json(self) -> str:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return json.dumps(data, indent=2)

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "decision": self.decision,
            "trust_score": self.trust_score,
            "confidence": self.confidence,
            "signature": self.signature[:32] + "..." if self.signature else None
        }

    def compute_hash(self) -> bytes:
        """Compute hash of proof data for signing"""
        data = {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "decision": self.decision,
            "trust_score": self.trust_score,
            "reasoning_chain": self.reasoning_chain[:5]  # Limit for hash
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).digest()

    def sign(self, private_key_pem: str) -> str:
        """Sign the proof with EC private key"""
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None
            )
            signature = private_key.sign(
                self.compute_hash(),
                ec.ECDSA(hashes.SHA256())
            )
            self.signature = signature.hex()

            # Store public key
            public_key = private_key.public_key()
            self.public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()

            return self.signature
        except Exception as e:
            raise RuntimeError(f"Failed to sign proof: {e}")

    def verify(self) -> bool:
        """Verify the signature"""
        if not self.signature or not self.public_key_pem:
            return False

        try:
            public_key = serialization.load_pem_public_key(
                self.public_key_pem.encode()
            )
            signature_bytes = bytes.fromhex(self.signature)
            public_key.verify(
                signature_bytes,
                self.compute_hash(),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except (InvalidSignature, Exception):
            return False


class AuditStorage:
    """Persistent storage for audit proofs"""

    def __init__(self, storage_path: str = "./audit_logs", use_redis: bool = False, redis_url: str = None):
        self.storage_path = storage_path
        self.use_redis = use_redis
        self.redis_client = None

        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)

    async def initialize(self):
        """Initialize Redis connection if enabled"""
        if self.use_redis:
            try:
                import redis.asyncio as redis
                self.redis_client = await redis.from_url(redis_url)
                await self.redis_client.ping()
                print("Redis connected for audit storage")
            except Exception as e:
                print(f"Redis connection failed, falling back to filesystem: {e}")
                self.use_redis = False

    async def store(self, proof: AuditProof):
        """Store audit proof"""
        proof_json = proof.to_json()

        if self.redis_client:
            await self.redis_client.setex(
                f"audit:{proof.trace_id}",
                86400 * 90,  # 90 days retention
                proof_json
            )

        # Always store to filesystem as backup
        filepath = os.path.join(self.storage_path, f"{proof.trace_id}.json")
        with open(filepath, "w") as f:
            f.write(proof_json)

    async def get(self, trace_id: str) -> Optional[AuditProof]:
        """Retrieve audit proof by trace_id"""
        proof_json = None

        if self.redis_client:
            proof_json = await self.redis_client.get(f"audit:{trace_id}")

        if not proof_json:
            filepath = os.path.join(self.storage_path, f"{trace_id}.json")
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    proof_json = f.read()

        if proof_json:
            data = json.loads(proof_json)
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            return AuditProof(**data)

        return None

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
