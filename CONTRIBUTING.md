# Contributing to NuanceBench

We welcome contributions of prompts and jailbreaks, as well as adapters and evaluation improvements.

## Prompt submissions
- Provide: `id`, `category`, `track`, `expected_policy`, `safety_subtype`, `text`, and `meta` with source and license.
- Attest rights to share the text. Prefer original writing or public-domain content.
- No minors, PII, or copyrighted long excerpts in NSFW content.

## Jailbreak submissions
- Provide: target category, the initial refused output, jailbreak text, and the successful post-jailbreak output (sanitized).
- Include reproducibility notes: model name and snapshot.

## Code contributions
- Match existing code style and keep PRs focused.
- Document new adapters in `evaluation/adapters/` and add roster entries in `models.yaml`.
- Update docs if you change schemas or metrics.

By submitting a contribution, you agree to license code under MIT and prompts under CC-BY unless otherwise specified.
