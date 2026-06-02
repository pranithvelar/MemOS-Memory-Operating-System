import pytest
from datetime import datetime, timezone
from src.memory.promotion import clamp_score, calculate_consolidation_component, evaluate_promotion_candidate

def test_clamp_score():
    assert clamp_score(1.5) == 1.0
    assert clamp_score(-0.5) == 0.0
    assert clamp_score(0.5) == 0.5

def test_calculate_consolidation_component():
    assert calculate_consolidation_component([]) == 0.0
    assert calculate_consolidation_component(["2026-05-10"]) == 0.2
    
    # Needs chronological testing
    score = calculate_consolidation_component(["2026-05-01", "2026-05-05", "2026-05-10"])
    assert score > 0.2
    
def test_evaluate_promotion_candidate():
    now_dt = datetime(2026, 5, 10, tzinfo=timezone.utc)
    now_ms = now_dt.timestamp() * 1000
    
    entry = {
        "recallCount": 5,
        "dailyCount": 2,
        "groundedCount": 0,
        "totalScore": 6.5,
        "queryHashes": ["h1", "h2", "h3"],
        "recallDays": ["2026-05-01", "2026-05-07"],
        "lastRecalledAt": "2026-05-09T00:00:00Z",
        "conceptTags": ["python", "app", "dev"]
    }
    
    res = evaluate_promotion_candidate(entry, now_ms)
    assert res["valid"] is True
    assert res["score"] > 0
    assert res["components"]["relevance"] == 6.5 / 7.0  # signal_count=7
    assert res["components"]["frequency"] > 0
    assert res["uniqueQueries"] == 3
