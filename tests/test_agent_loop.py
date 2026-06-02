import pytest
from src.agent.loop import AgentLoop

class DummyResponse:
    def __init__(self, content):
        self.content = content
    def __getitem__(self, key):
        if key == 'message':
            return {'content': self.content}
        return None

def test_extract_action():
    loop = AgentLoop()
    text = """I should search memory.
```json
{
  "name": "search_memory",
  "arguments": {
    "query": "test query"
  }
}
```
Waiting.
"""
    action = loop._extract_action(text)
    assert action is not None
    assert action["name"] == "search_memory"
    assert action["arguments"]["query"] == "test query"

def test_extract_action_malformed():
    loop = AgentLoop()
    text = "Just talking, no action."
    assert loop._extract_action(text) is None
