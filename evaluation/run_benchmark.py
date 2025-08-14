import argparse
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

from .adapters.echo import EchoAdapter
from .adapters.base import ModelAdapter
from .scoring.judge_client import judge, JudgeConfig
from .scoring.compute_scores import compute_official, write_leaderboard_row


def load_yaml_like_models(path: str) -> List[Dict[str, Any]]:
	# Minimal YAML-like parser sufficient for our models.yaml example
	models: List[Dict[str, Any]] = []
	current: Dict[str, Any] = {}
	with open(path, "r", encoding="utf-8") as f:
		for raw in f:
			line = raw.rstrip("\n")
			if not line.strip():
				continue
			if line.lstrip().startswith("- "):
				# start new model
				if current:
					models.append(current)
				current = {}
				kv = line.split("- ", 1)[1]
				if ":" in kv:
					k, v = kv.split(":", 1)
					current[k.strip()] = v.strip()
			else:
				if ":" in line:
					k, v = line.split(":", 1)
					current[k.strip()] = v.strip()
	if current:
		models.append(current)
	return models


def load_template(path: str) -> str:
	with open(path, "r", encoding="utf-8") as f:
		return f.read()


def load_jsonl(path: str) -> List[Dict[str, Any]]:
	items: List[Dict[str, Any]] = []
	with open(path, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			items.append(json.loads(line))
	return items


def ensure_dir(path: str) -> None:
	os.makedirs(path, exist_ok=True)


def select_prompt_paths(track: str) -> List[str]:
	base = os.path.join("benchmark", "prompts", track)
	files = []
	for fname in sorted(os.listdir(base)):
		if fname.endswith(".jsonl"):
			files.append(os.path.join(base, fname))
	return files


def get_adapter(model_cfg: Dict[str, Any]) -> ModelAdapter:
	provider = (model_cfg.get("provider") or model_cfg.get("provider:") or "").strip()
	name = (model_cfg.get("name") or model_cfg.get("- name") or "").strip()
	if provider == "openai":
		if not os.getenv("OPENAI_API_KEY"):
			print(f"[info] OPENAI_API_KEY not set; using echo for {name}")
			return EchoAdapter()
		from .adapters.openai import OpenAIAdapter
		return OpenAIAdapter(model=name)
	if provider == "anthropic":
		if not os.getenv("ANTHROPIC_API_KEY"):
			print(f"[info] ANTHROPIC_API_KEY not set; using echo for {name}")
			return EchoAdapter()
		from .adapters.anthropic import AnthropicAdapter
		return AnthropicAdapter(model=name)
	if provider == "google":
		if not os.getenv("GOOGLE_API_KEY"):
			print(f"[info] GOOGLE_API_KEY not set; using echo for {name}")
			return EchoAdapter()
		from .adapters.google import GoogleAdapter
		return GoogleAdapter(model=name or "gemini-pro")
	if provider == "huggingface":
		from .adapters.huggingface import HuggingFaceAdapter
		repo_id = (model_cfg.get("repo_id") or name).strip()
		return HuggingFaceAdapter(repo_id=repo_id, model=name)
	# local / default
	return EchoAdapter()


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("--track", choices=["full", "sfw"], required=True)
	parser.add_argument("--models", default="models.yaml")
	parser.add_argument("--judge_tag", default="judge_gpt5_2025_08")
	parser.add_argument("--dataset_version", default="v1.0")
	parser.add_argument("--output_dir", default=os.path.join("evaluation", "outputs", "run_demo"))
	parser.add_argument("--offline_judge", action="store_true")
	args = parser.parse_args()

	ensure_dir(args.output_dir)

	# Load prompts
	prompt_paths = select_prompt_paths(args.track)
	prompts: List[Dict[str, Any]] = []
	for p in prompt_paths:
		prompts.extend(load_jsonl(p))

	# Load models roster
	models = load_yaml_like_models(args.models)

	judge_cfg = JudgeConfig(judge_tag=args.judge_tag, offline=args.offline_judge)

	# Template registry
	template_path = os.path.join("evaluation", "templates", "assistant_v1.txt")
	template_text = load_template(template_path)

	leaderboard_path = os.path.join("leaderboards", f"{args.dataset_version}.csv")
	ensure_dir(os.path.dirname(leaderboard_path))

	for m in models:
		adapter = get_adapter(m)
		model_name = (m.get("name") or m.get("- name") or adapter.name).strip()
		template_id = (m.get("template") or "assistant_v1").strip()

		results: List[Dict[str, Any]] = []

		for prompt in prompts:
			if prompt.get("track") != args.track:
				continue

			rendered = adapter.render(prompt.get("text", ""), template_text)
			answer = adapter.generate(rendered, sampling={"temperature": 0.2, "top_p": 0.9, "max_new_tokens": 512})

			verdict = judge(prompt, answer, judge_cfg)
			record = {
				"prompt_id": prompt.get("id"),
				"category": prompt.get("category"),
				"expected_policy": prompt.get("expected_policy"),
				"model": model_name,
				"inference_template": template_id,
				"raw_response": answer,
				"label": verdict["label"],
				"boundary_signal": verdict["boundary_signal"],
				"refusal_marker_seen": verdict["refusal_marker_seen"],
				"narrative_tokens": verdict["narrative_tokens"],
				"explicitness_flag": verdict["explicitness_flag"],
				"consent_flag": verdict["consent_flag"],
				"judge_tag": args.judge_tag,
				"timestamp": datetime.now(timezone.utc).isoformat(),
			}
			results.append(record)

		# No jailbreak stage implemented in the demo; mark refusal stats for JBS=0 by default.
		for r in results:
			r["was_refusal"] = (r.get("label") == "BAD" and r.get("expected_policy") in ("answer",))
			r["flipped"] = False

		scores = compute_official(results)

		row = {
			"model": model_name,
			"snapshot": m.get("snapshot", "demo"),
			"track": args.track,
			"dataset_version": args.dataset_version,
			"judge_tag": args.judge_tag,
			"fitness": f"{scores.fitness:.4f}",
			"openness": f"{scores.openness:.4f}",
			"jbs": f"{scores.jbs:.4f}",
			"n_samples": scores.n_samples,
			"date": datetime.now(timezone.utc).date().isoformat(),
			"template_id": template_id,
		}

		write_leaderboard_row(
			leaderboard_path,
			row,
			header=[
				"model",
				"snapshot",
				"track",
				"dataset_version",
				"judge_tag",
				"fitness",
				"openness",
				"jbs",
				"n_samples",
				"date",
				"template_id",
			],
		)

		# Persist per-model raw results
		out_path = os.path.join(args.output_dir, f"results_{model_name}.jsonl")
		with open(out_path, "w", encoding="utf-8") as f:
			for r in results:
				f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
	main()
