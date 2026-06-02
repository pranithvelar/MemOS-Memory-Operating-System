import pytest
from src.agent.privacy import PrivacyManager
from src.security.filters import SafetyFilter

def test_privacy_manager():
    pm = PrivacyManager()
    assert pm.is_session_visible("general_chat_123") is True
    assert pm.is_session_visible("private_chat_456") is False
    assert pm.is_session_visible("incognito_session") is False

def test_safety_filter():
    sf = SafetyFilter()
    text = "My email is test@example.com and card is 4111111111111111"
    res = sf.sanitize_content(text)
    assert "test@example.com" not in res
    assert "[EMAIL REDACTED]" in res
    assert "4111111111111111" not in res
    assert "[CC REDACTED]" in res
