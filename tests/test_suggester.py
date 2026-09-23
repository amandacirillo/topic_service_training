import json

from app.suggester import build_prompt, parse_suggestions, suggest_topics


class FakeLlmClient:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.last_prompt = None

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response_text


def test_build_prompt_includes_list_name_and_existing_topics():
    prompt = build_prompt('Animals', 'Fun animal facts', ['Lions', 'Tigers'])
    assert 'Animals' in prompt
    assert 'Lions' in prompt
    assert 'Tigers' in prompt


def test_parse_suggestions_valid_json_array():
    assert parse_suggestions(json.dumps(['Bears', 'Wolves'])) == ['Bears', 'Wolves']


def test_parse_suggestions_invalid_json_returns_empty():
    assert parse_suggestions('not json at all') == []


def test_parse_suggestions_non_list_json_returns_empty():
    assert parse_suggestions(json.dumps({'not': 'a list'})) == []


def test_suggest_topics_dedupes_case_insensitive_against_existing():
    client = FakeLlmClient(json.dumps(['Lions', 'lions', 'Bears', 'Tigers']))
    result = suggest_topics(client, 'Animals', 'desc', existing_topics=['tigers'])
    assert result == ['Lions', 'Bears']


def test_suggest_topics_dedupes_within_suggestions_too():
    client = FakeLlmClient(json.dumps(['Bears', 'BEARS', 'bears']))
    result = suggest_topics(client, 'Animals', 'desc', existing_topics=[])
    assert result == ['Bears']


def test_suggest_topics_handles_empty_response():
    client = FakeLlmClient('[]')
    result = suggest_topics(client, 'Animals', 'desc', existing_topics=['Lions'])
    assert result == []
