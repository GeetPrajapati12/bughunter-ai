"""
ai/llm_client.py
----------------
Universal LLM Client for BugHunter AI.

Supports:
  - Anthropic  (Claude)
  - OpenAI     (GPT-4o, GPT-4 Turbo, etc.)
  - Google     (Gemini 1.5 Pro, Flash)
  - Groq       (Llama 3, Mixtral — free tier available)
  - Ollama     (any local model — completely free, no key needed)

All agents import ONLY this module. Switching providers requires
only a change in .env — zero code changes anywhere else.
"""

from __future__ import annotations

from loguru import logger

from config.settings import (
    AI_PROVIDER,
    AI_MODEL,
    AI_MAX_TOKENS,
    AI_TEMPERATURE,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    OLLAMA_BASE_URL,
)


class LLMClient:
    """
    Universal LLM client.
    Call `.chat(prompt)` and get a string response back.
    The provider is selected from AI_PROVIDER in .env.
    """

    def __init__(self) -> None:
        self.provider = AI_PROVIDER.lower().strip()
        self.model    = AI_MODEL
        self._client  = self._build_client()
        logger.info("LLMClient initialised — provider={} model={}", self.provider, self.model)

    def chat(self, prompt: str, max_tokens: int | None = None) -> str:
        """
        Send a prompt and return the response text.
        Raises RuntimeError if the provider call fails.
        """
        tokens = max_tokens or AI_MAX_TOKENS
        try:
            if self.provider == "anthropic":
                return self._chat_anthropic(prompt, tokens)
            elif self.provider == "openai":
                return self._chat_openai(prompt, tokens)
            elif self.provider == "gemini":
                return self._chat_gemini(prompt, tokens)
            elif self.provider == "groq":
                return self._chat_groq(prompt, tokens)
            elif self.provider == "ollama":
                return self._chat_ollama(prompt, tokens)
            else:
                raise ValueError(
                    f"Unknown AI_PROVIDER: '{self.provider}'. "
                    "Choose from: anthropic, openai, gemini, groq, ollama"
                )
        except Exception as exc:
            logger.error("LLMClient [{}] error: {}", self.provider, exc)
            raise

    def is_available(self) -> bool:
        """Return True if the provider is configured (key present, etc.)."""
        if self.provider == "anthropic":
            return bool(ANTHROPIC_API_KEY)
        elif self.provider == "openai":
            return bool(OPENAI_API_KEY)
        elif self.provider == "gemini":
            return bool(GEMINI_API_KEY)
        elif self.provider == "groq":
            return bool(GROQ_API_KEY)
        elif self.provider == "ollama":
            return True   # no key needed
        return False

    # ── Provider builders ──────────────────────────────────────────────────────

    def _build_client(self) -> object:
        if self.provider == "anthropic":
            try:
                import anthropic
                return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            except ImportError:
                raise ImportError("Run: pip install anthropic")

        elif self.provider == "openai":
            try:
                from openai import OpenAI
                return OpenAI(api_key=OPENAI_API_KEY)
            except ImportError:
                raise ImportError("Run: pip install openai")

        elif self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                return genai.GenerativeModel(self.model)
            except ImportError:
                raise ImportError("Run: pip install google-generativeai")

        elif self.provider == "groq":
            try:
                from groq import Groq
                return Groq(api_key=GROQ_API_KEY)
            except ImportError:
                raise ImportError("Run: pip install groq")

        elif self.provider == "ollama":
            # No client object needed — uses requests directly
            return None

        else:
            raise ValueError(f"Unknown AI_PROVIDER: '{self.provider}'")

    # ── Provider chat methods ──────────────────────────────────────────────────

    def _chat_anthropic(self, prompt: str, max_tokens: int) -> str:
        response = self._client.messages.create(  # type: ignore
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _chat_openai(self, prompt: str, max_tokens: int) -> str:
        response = self._client.chat.completions.create(  # type: ignore
            model=self.model,
            max_tokens=max_tokens,
            temperature=AI_TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    def _chat_gemini(self, prompt: str, max_tokens: int) -> str:
        import google.generativeai as genai
        config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=AI_TEMPERATURE,
        )
        response = self._client.generate_content(prompt, generation_config=config)  # type: ignore
        return response.text

    def _chat_groq(self, prompt: str, max_tokens: int) -> str:
        response = self._client.chat.completions.create(  # type: ignore
            model=self.model,
            max_tokens=max_tokens,
            temperature=AI_TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    def _chat_ollama(self, prompt: str, max_tokens: int) -> str:
        import requests
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model":  self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": AI_TEMPERATURE,
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"]
