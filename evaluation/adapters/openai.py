import os
from typing import Optional, Dict, Any
from .base import ModelAdapter


class OpenAIAdapter(ModelAdapter):
	def __init__(self, model: str) -> None:
		super().__init__(name=model)
		self.api_key = os.getenv("OPENAI_API_KEY", "")

	def generate(self, rendered_prompt: str, sampling: Optional[Dict[str, Any]] = None) -> str:
		if not self.api_key:
			raise RuntimeError("OPENAI_API_KEY not set")
		try:
			from openai import OpenAI
		except Exception as e:
			raise RuntimeError("openai package not installed. pip install openai") from e
		client = OpenAI(api_key=self.api_key)
		temperature = (sampling or {}).get("temperature", 0.2)
		top_p = (sampling or {}).get("top_p", 0.9)
		max_tokens = (sampling or {}).get("max_new_tokens", 512)
		resp = client.chat.completions.create(
			model=self.name,
			messages=[{"role": "user", "content": rendered_prompt}],
			temperature=temperature,
			top_p=top_p,
			max_tokens=max_tokens,
		)
		return (resp.choices[0].message.content or "").strip()
