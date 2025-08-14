from typing import Optional, Dict, Any
from .base import ModelAdapter


class EchoAdapter(ModelAdapter):
	def __init__(self) -> None:
		super().__init__(name="echo")

	def generate(self, rendered_prompt: str, sampling: Optional[Dict[str, Any]] = None) -> str:
		return f"[echo]\n{rendered_prompt}"
