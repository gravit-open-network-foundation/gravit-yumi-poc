"""LLM adapter with a safe mock fallback.

The verifier should be usable even when no external LLM SDK is installed.
"""

from typing import Optional

try:
    import litellm
except ImportError:  # pragma: no cover - optional dependency
    litellm = None


class RealLLMAdapter:
    def __init__(self, model: str = "gpt-4"):
        self.model = model

    def analyze(self, prompt: str) -> str:
        if litellm is None:
            return f"LLM_UNAVAILABLE: {prompt[:80]}"

        try:
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM_ERROR: {e}"


class LLMAdapter:
    def __init__(self, provider: str = "mock", model: str = "gpt-4"):
        self.provider = provider
        self.model = model
        self._real_adapter = RealLLMAdapter(model=model) if provider != "mock" else None

    def analyze(self, prompt: str) -> str:
        if self._real_adapter is None:
            return prompt
        return self._real_adapter.analyze(prompt)
