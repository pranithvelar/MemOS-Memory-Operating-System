import pytest
from src.agent.prompts import PromptBuilder

def test_prompt_builder():
    builder = PromptBuilder("Jarvis", "A smart proxy.")
    builder.add_personalization_context("User Facts:\n- name: Alice")
    builder.add_tools_schema([{"name": "test_tool"}])
    
    prompt = builder.build()
    
    assert "You are Jarvis" in prompt
    assert "User Facts:" in prompt
    assert "Alice" in prompt
    assert "test_tool" in prompt
    assert "```json" in prompt
