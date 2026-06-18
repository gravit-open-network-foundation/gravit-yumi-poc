#!/usr/bin/env python3
"""
FastAPI server for Gravit Epistemic Verifier
Provides a REST API for AI agent verification
"""

import json
import os
import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Depends, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, field_validator
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import settings
from src.verifier import EpistemicVerifier

# Logging configuration
logging.basicConfig(
    level=getattr(logging, settings.log_level.value),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gravit-api")

# API Key authentication
API_KEY = os.getenv("GRAVIT_API_KEY", "")
if not API_KEY and settings.is_production:
    raise ValueError("GRAVIT_API_KEY must be set in production")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    if not API_KEY:
        return api_key  # No auth in development
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Global instances
verifier: Optional[EpistemicVerifier] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global verifier

    # Startup
    logger.info(f"Starting Gravit Epistemic Verifier API")
    logger.info(f"Environment: {settings.environment.value}")
    logger.info(f"LLM Provider: {settings.llm_provider.value}")
    logger.info(f"Semantic threshold: {settings.semantic_threshold}")

    verifier = EpistemicVerifier()
    await verifier.initialize()

    logger.info("API server ready")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await verifier.shutdown()


# Create the FastAPI application
app = FastAPI(
    title="Gravit Epistemic Verifier",
    description="Production-grade epistemic verification for AI agents",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None
)

# Rate limit exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)


# ============================================================================
# Pydantic Models
# ============================================================================

class VerificationRequest(BaseModel):
    """Verification request"""
    action: str = Field(..., description="Agent action")
    agent_id: str = Field(..., description="Agent ID")
    reasoning_chain: List[str] = Field(..., description="Reasoning chain")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context")

    @field_validator("reasoning_chain")
    @classmethod
    def reasoning_not_empty(cls, v):
        if not v:
            raise ValueError("reasoning_chain cannot be empty")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "action": "transfer_funds",
                "agent_id": "agent_42",
                "reasoning_chain": [
                    "User requested to send 100 GRAVIT",
                    "Wallet belongs to known recipient",
                    "Sufficient balance available"
                ],
                "context": {
                    "user_id": "user_7",
                    "balance": 550
                }
            }
        }


class VerificationResponse(BaseModel):
    """Verification response"""
    status: str
    decision: str
    score: float
    checks: Dict[str, bool]
    trace_id: str
    audit_proof: Optional[str] = None
    latency_ms: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str
    llm_provider: str
    uptime_seconds: float


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.environment.value,
        llm_provider=settings.llm_provider.value,
        uptime_seconds=time.time() - app.state.start_time if hasattr(app.state, "start_time") else 0
    )


@app.post("/v1/verify",
          response_model=VerificationResponse,
          tags=["Verification"],
          dependencies=[Depends(verify_api_key)])
@limiter.limit("100/minute")
async def verify(request: VerificationRequest, request_obj: Request):
    """
    Verify an AI agent action.

    Checks:
    - Semantic alignment with the intent
    - Policy compliance
    - Resistance to adversarial attacks
    - Integrity of the reasoning chain

    Returns a cryptographic proof for audit purposes.
    """
    if not verifier:
        raise HTTPException(status_code=503, detail="Verifier not initialized")

    start_time = time.time()

    try:
        result = verifier.verify(request.model_dump())

        latency_ms = int((time.time() - start_time) * 1000)

        audit_proof = None
        if result.proof:
            audit_proof = json.dumps(result.proof, indent=2)

        return VerificationResponse(
            status="passed" if result.valid else "failed",
            decision="allowed" if result.valid else "denied",
            score=result.semantic_score,
            checks={
                "semantic_compliance": result.semantic_score >= settings.semantic_threshold,
                "policy_compliance": result.policy_compliant,
                "adversarial_risk": result.adversarial_risk > 0.5,
                "reasoning_lineage": result.lineage_valid,
            },
            trace_id=result.trace_id,
            audit_proof=audit_proof,
            latency_ms=latency_ms
        )

    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal verification error. Check logs for details."
        )


@app.get("/v1/audit/{trace_id}", tags=["Audit"], dependencies=[Depends(verify_api_key)])
async def get_audit_trail(trace_id: str):
    """Get the full audit trail for a trace_id"""
    from src.audit_proof import AuditStorage

    storage = AuditStorage()
    proof = await storage.get(trace_id)

    if not proof:
        raise HTTPException(status_code=404, detail="Trace ID not found")

    return proof.to_dict()


@app.get("/metrics", tags=["System"])
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Store startup time
app.state.start_time = time.time()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.value.lower()
    )
