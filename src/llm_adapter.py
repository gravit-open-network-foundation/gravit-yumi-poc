"""LLM adapter for reasoning chain extraction and verification."""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ReasoningChain:
    """Extracted reasoning chain from LLM output."""
    steps: List[str]
    confidence: float
    model_name: str
    raw_output: str


class LLMAdapter(ABC):
    """Abstract adapter for different LLM providers."""

    @abstractmethod
    def extract_reasoning(self, prompt: str, response: str) -> ReasoningChain:
        pass

    @abstractmethod
    def verify_consistency(self, reasoning: ReasoningChain) -> float:
        pass


class ClaudeAdapter(LLMAdapter):
    """Adapter for Anthropic Claude."""

    def extract_reasoning(self, prompt: str, response: str) -> ReasoningChain:
        steps = []
        lines = response.split('\n')

        for line in lines:
            if line.strip().startswith(('Step', '1.', '2.', '3.', '-', '•')):
                steps.append(line.strip())

        if not steps:
            import re
            sentences = re.split(r'[.!?]+', response)
            steps = [s.strip() for s in sentences if len(s.strip()) > 20][:5]

        return ReasoningChain(
            steps=steps,
            confidence=0.8,
            model_name="claude-3.5-sonnet",
            raw_output=response
        )

    def verify_consistency(self, reasoning: ReasoningChain) -> float:
        if len(reasoning.steps) < 2:
            return 0.5
        return 0.85


class GPTAdapter(LLMAdapter):
    """Adapter for OpenAI GPT."""

    def extract_reasoning(self, prompt: str, response: str) -> ReasoningChain:
        steps = []
        import re
        pattern = r'\d+\.\s+([^\n]+)'
        matches = re.findall(pattern, response)

        if matches:
            steps = matches
        else:
            sentences = response.split('. ')
            steps = [s.strip() for s in sentences if len(s.strip()) > 30][:5]

        return ReasoningChain(
            steps=steps,
            confidence=0.75,
            model_name="gpt-4-turbo",
            raw_output=response
        )

    def verify_consistency(self, reasoning: ReasoningChain) -> float:
        if len(reasoning.steps) < 2:
            return 0.5

        consistency = 1.0
        negative_keywords = ['however', 'but', 'although']
        for step in reasoning.steps:
            if any(kw in step.lower() for kw in negative_keywords):
                consistency -= 0.1

        return max(0.3, min(0.95, consistency))


class LLMAdapterFactory:
    """Factory for creating LLM adapters."""

    @staticmethod
    def create(model_type: str, **kwargs) -> LLMAdapter:
        adapters = {
            "claude": ClaudeAdapter,
            "gpt": GPTAdapter,
        }
        adapter_class = adapters.get(model_type.lower())
        if not adapter_class:
            raise ValueError(f"Unknown model type: {model_type}")
        return adapter_class(**kwargs)
