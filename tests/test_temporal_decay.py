import pytest
from src.memory.temporal_decay import calculate_temporal_decay_multiplier, is_evergreen_memory_path, parse_memory_date_from_path

def test_calculate_temporal_decay_multiplier():
    res = calculate_temporal_decay_multiplier(30.0, 30.0)
    assert round(res, 2) == 0.5 # half life => 0.5
    
    res = calculate_temporal_decay_multiplier(60.0, 30.0)
    assert round(res, 2) == 0.25
    
    res = calculate_temporal_decay_multiplier(0.0, 30.0)
    assert res == 1.0

def test_is_evergreen_memory_path():
    assert is_evergreen_memory_path("MEMORY.md")
    assert is_evergreen_memory_path("memory/topics.md")
    assert not is_evergreen_memory_path("memory/2026-05-10.md")
    
def test_parse_memory_date():
    dt = parse_memory_date_from_path("memory/2026-05-10.md")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 5
    assert dt.day == 10
    
    assert parse_memory_date_from_path("MEMORY.md") is None
