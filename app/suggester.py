"""AI-assisted topic suggestion: ask an LLM for new candidate topics, then
drop anything that duplicates an existing (case-insensitive) topic.

LlmClient is a Protocol so tests can supply a fake without any real network
call or API key. A thin real implementation (e.g. calling an OpenAI-compatible
chat completions endpoint) would implement the same `complete(prompt) -> str`
method and return a JSON array of strings as text.
"""
import json
from typing import List, Protocol


class LlmClient(Protocol):
    def complete(self, prompt: str) -> str: ...


def build_prompt(list_name: str, description: str, existing_topics: List[str]) -> str:
    sample = existing_topics[-50:]  # bias toward recent entries, cap prompt size
    existing_block = '\n'.join(f'- {t}' for t in sample) or '(none yet)'
    return (
        f'You are helping curate a list of topics called "{list_name}".\n'
        f'Description: {description or "(none provided)"}\n\n'
        f'Existing topics (do not repeat these):\n{existing_block}\n\n'
        'Suggest 10 new topics that fit this list. '
        'Respond with a JSON array of strings only, no other text.'
    )


def parse_suggestions(raw_response: str) -> List[str]:
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item).strip() for item in parsed if str(item).strip()]


def suggest_topics(
    llm_client: LlmClient,
    list_name: str,
    description: str,
    existing_topics: List[str],
) -> List[str]:
    prompt = build_prompt(list_name, description, existing_topics)
    raw_response = llm_client.complete(prompt)
    suggestions = parse_suggestions(raw_response)

    existing_lower = {t.strip().lower() for t in existing_topics}
    deduped = []
    seen = set()
    for suggestion in suggestions:
        key = suggestion.lower()
        if key in existing_lower or key in seen:
            continue
        seen.add(key)
        deduped.append(suggestion)
    return deduped


class NullLlmClient:
    """Returns no suggestions -- used when no LLM is configured, instead of
    raising or silently pretending a real call succeeded."""

    def complete(self, prompt: str) -> str:
        return '[]'


def default_llm_client() -> LlmClient:
    # Wire up a real client here (OpenAI SDK, LiteLLM proxy, etc.) once
    # settings.llm_model / an API key / base URL are configured. Left as a
    # placeholder so this training example has no hard dependency on any
    # specific AI vendor's SDK.
    return NullLlmClient()
