import os
from typing import Optional, Dict, Any
from .base import ModelAdapter


class GoogleAdapter(ModelAdapter):
	def __init__(self, model: str) -> None:
		super().__init__(name=model)
		self.api_key = os.getenv("GOOGLE_API_KEY", "")

	def generate(self, rendered_prompt: str, sampling: Optional[Dict[str, Any]] = None) -> str:
		if not self.api_key:
			raise RuntimeError("GOOGLE_API_KEY not set")
		try:
			import google.generativeai as genai
		except Exception as e:
			raise RuntimeError("google-generativeai not installed. pip install google-generativeai") from e
		genai.configure(api_key=self.api_key)
		model_id = self.name or "gemini-pro"
		model = genai.GenerativeModel(model_id)
		resp = model.generate_content(rendered_prompt)
		return (getattr(resp, "text", None) or "").strip()
