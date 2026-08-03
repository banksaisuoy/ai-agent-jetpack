import pytest
import os
import sys

# Ensure src and day_1 directories are in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Sets up mock environment variables for tests."""
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "mock_secret")
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "mock_token")
    monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")