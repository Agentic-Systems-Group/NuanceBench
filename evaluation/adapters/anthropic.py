import os
from typing import Optional, Dict, Any
from .base import ModelAdapter


class AnthropicAdapter(ModelAdapter):
	def __init__(self, model: str) -> None:
		super().__init__(name=model)
		self.api_key = os.getenv("ANTHROPIC_API_KEY", "")

	def generate(self, rendered_prompt: str, sampling: Optional[Dict[str, Any]] = None) -> str:
		if not self.api_key:
			raise RuntimeError("ANTHROPIC_API_KEY not set")
		try:
			import anthropic
		except Exception as e:
			raise RuntimeError("anthropic package not installed. pip install anthropic") from e
		client = anthropic.Anthropic(api_key=self.api_key)
		temperature = (sampling or {}).get("temperature", 0.2)
		max_tokens = (sampling or {}).get("max_new_tokens", 512)
		resp = client.messages.create(
			model=self.name,
			max_tokens=max_tokens,
			temperature=temperature,
			messages=[{"role": "user", "content": rendered_prompt}],
		)
		# Concatenate text blocks
		parts = []
		for block in resp.content:
			text = getattr(block, "text", None)
			if text:
				parts.append(text)
		return "".join(parts).strip()
