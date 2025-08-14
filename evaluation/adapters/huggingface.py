import os
from typing import Optional, Dict, Any
from .base import ModelAdapter


class HuggingFaceAdapter(ModelAdapter):
	def __init__(self, repo_id: str, model: str) -> None:
		super().__init__(name=model or repo_id)
		self.api_token = os.getenv("HF_API_TOKEN", "")
		self.repo_id = repo_id

	def generate(self, rendered_prompt: str, sampling: Optional[Dict[str, Any]] = None) -> str:
		try:
			from huggingface_hub import InferenceClient
			client = InferenceClient(self.repo_id, token=(self.api_token or None), provider="hf-inference")
			params = sampling or {}
			text = client.text_generation(
				prompt=rendered_prompt,
				max_new_tokens=int(params.get("max_new_tokens", 512)),
				temperature=float(params.get("temperature", 0.2)),
				top_p=float(params.get("top_p", 0.9)),
				stream=False,
			)
			return (text or "").strip()
		except Exception:
			return "[huggingface placeholder response]"
