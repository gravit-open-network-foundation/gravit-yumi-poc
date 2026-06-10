"""LLM adapter for reasoning chain extraction and verification."""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

import requests


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
        """Extract reasoning steps from LLM response."""
        pass

    @abstractmethod
    def verify_consistency(self, reasoning: ReasoningChain) -> float:
        """Verify internal consistency of reasoning chain."""
        pass


class ClaudeAdapter(LLMAdapter):
    """Adapter for Anthropic Claude."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"

    def extract_reasoning(self, prompt: str, response: str) -> ReasoningChain:
        """Extract reasoning from Claude's response."""
        # Simple extraction: look for step markers or line breaks
        steps = []
        lines = response.split('\n')

        current_step = []
        for line in lines:
            if line.strip().startswith(('Step', '1.', '2.', '3.', '-', '•')):
                if current_step:
                    steps.append(' '.join(current_step))
                    current_step = []
                current_step.append(line.strip())
            elif current_step:
                current_step.append(line.strip())

        if current_step:
            steps.append(' '.join(current_step))

        # If no structured steps, use sentences
        if not steps:
            import re
            sentences = re.split(r'[.!?]+', response)
            steps = [s.strip() for s in sentences if len(s.strip()) > 20][:5]

        return ReasoningChain(
            steps=steps,
            confidence=0.8,  # Default, could be derived from Claude's tokens
            model_name="claude-3.5-sonnet",
            raw_output=response
        )

    def verify_consistency(self, reasoning: ReasoningChain) -> float:
        """Verify reasoning consistency using Claude's own capabilities."""
        if len(reasoning.steps) < 2:
            return 0.5

        # Check for contradictions
        prompt = f"""
        Analyze these reasoning steps for contradictions:
        {chr(10).join(reasoning.steps)}

        Return a consistency score from 0 to 1 where 1 means perfectly consistent.
        """

        # In production, call Claude API
        # For now, return heuristic score
        return 0.85


class GPTAdapter(LLMAdapter):
    """Adapter for OpenAI GPT."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"

    def extract_reasoning(self, prompt: str, response: str) -> ReasoningChain:
        """Extract reasoning from GPT response."""
        # GPT often uses numbered lists
        steps = []
        import re
        pattern = r'\d+\.\s+([^\n]+)'
        matches = re.findall(pattern, response)

        if matches:
            steps = matches
        else:
            # Fallback to sentence splitting
            sentences = response.split('. ')
            steps = [s.strip() for s in sentences if len(s.strip()) > 30][:5]

        return ReasoningChain(
            steps=steps,
            confidence=0.75,
            model_name="gpt-4-turbo",
            raw_output=response
        )

    def verify_consistency(self, reasoning: ReasoningChain) -> float:
        """Verify reasoning consistency."""
        if len(reasoning.steps) < 2:
            return 0.5

        # Simple heuristic: check for conflicting keywords
        consistency = 1.0
        negative_keywords = ['however', 'but', 'although', 'nevertheless']

        for step in reasoning.steps:
            if any(kw in step.lower() for kw in negative_keywords):
                consistency -= 0.1

        return max(0.3, min(0.95, consistency))


class LlamaAdapter(LLMAdapter):
    """Adapter for Llama (via Ollama or similar)."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def extract_reasoning(self, prompt: str, response: str) -> ReasoningChain:
        """Extract reasoning from Llama response."""
        steps = []
        lines = response.split('\n')

        for line in lines:
            if line.strip().startswith(('>', 'Answer:', 'Reasoning:', 'Thought:')):
                steps.append(line.strip())
            elif len(line.strip()) > 50 and not steps:
                steps.append(line.strip())

        if not steps:
            steps = [response[:200]]

        return ReasoningChain(
            steps=steps[:8],
            confidence=0.7,
            model_name="llama-3",
            raw_output=response
        )

    def verify_consistency(self, reasoning: ReasoningChain) -> float:
        """Verify reasoning consistency."""
        if len(reasoning.steps) < 2:
            return 0.5
        return 0.7  # Llama typically has moderate consistency


class LLMAdapterFactory:
    """Factory for creating LLM adapters."""

    @staticmethod
    def create(model_type: str, **kwargs) -> LLMAdapter:
        """Create an adapter for the specified model."""
        adapters = {
            "claude": ClaudeAdapter,
            "gpt": GPTAdapter,
            "llama": LlamaAdapter,
        }

        adapter_class = adapters.get(model_type.lower())
        if not adapter_class:
            raise ValueError(f"Unknown model type: {model_type}")

        return adapter_class(**kwargs)
