from typing import Optional, Dict, Any


class ModelAdapter:
	"""Minimal interface: render prompt and call model to get text."""

	name: str

	def __init__(self, name: str) -> None:
		self.name = name

	def render(self, user_prompt: str, template: Optional[str]) -> str:
		if template is None or template == "none":
			return user_prompt
		return template.replace("{PROMPT}", user_prompt)

	def generate(self, rendered_prompt: str, sampling: Optional[Dict[str, Any]] = None) -> str:
		raise NotImplementedError
