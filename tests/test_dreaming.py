import pytest
import os
import tempfile
import datetime
from src.memory.dreaming import MemoryDreamer, NARRATIVE_SYSTEM_PROMPT

def test_build_narrative_prompt():
    dreamer = MemoryDreamer("dummy")
    prompt = dreamer.build_narrative_prompt(
        snippets=["coded a python module", "watched the sunset"],
        themes=["coding", "nature"],
        promotions=["sunset was beautiful"]
    )
    
    assert "coded a python module" in prompt
    assert "Recurring themes:" in prompt
    assert "- coding" in prompt
    assert "Memories that crystallized" in prompt

def test_append_diary_entry():
    with tempfile.TemporaryDirectory() as tmpdir:
        dreamer = MemoryDreamer(tmpdir)
        
        dt = datetime.datetime(2026, 5, 10, 15, 30)
        dreamer.append_diary_entry("First dream about code.", dt)
        
        assert os.path.exists(dreamer.dreams_path)
        with open(dreamer.dreams_path, "r") as f:
            content = f.read()
            
        assert "<!-- openclaw:dreaming:diary:start -->" in content
        assert "First dream about code." in content
        assert "May 10, 2026" in content
        
        # append again
        dreamer.append_diary_entry("Second dream about sunsets.", dt)
        with open(dreamer.dreams_path, "r") as f:
            content2 = f.read()
            
        assert content2.count("<!-- openclaw:dreaming:diary:start -->") == 1
        assert "Second dream about sunsets." in content2
        assert content2.index("First dream") < content2.index("Second dream")
