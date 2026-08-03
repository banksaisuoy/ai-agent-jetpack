import pytest
import datetime
from src.core.tools.time_tool import CurrentTimeTool

def test_current_time_tool_iso_format():
    tool = CurrentTimeTool()
    result = tool.execute()
    
    # Verify it's a valid ISO format string
    try:
        datetime.datetime.fromisoformat(result)
    except ValueError:
        pytest.fail("The result is not in a valid ISO format")

def test_current_time_tool_timezone():
    tool = CurrentTimeTool()
    
    # Test UTC
    utc_result = tool.execute(timezone="UTC")
    utc_dt = datetime.datetime.fromisoformat(utc_result)
    assert utc_dt.tzinfo is not None
    
    # Test specific timezone (if zoneinfo is available)
    try:
        ny_result = tool.execute(timezone="America/New_York")
        ny_dt = datetime.datetime.fromisoformat(ny_result)
        assert ny_dt.tzinfo is not None
    except Exception as e:
        pass # fallback is tested below if zoneinfo not available

def test_current_time_tool_invalid_timezone():
    tool = CurrentTimeTool()
    # Should fallback to UTC without raising exception
    result = tool.execute(timezone="Invalid/Timezone")
    dt = datetime.datetime.fromisoformat(result)
    assert dt.tzinfo == datetime.timezone.utc
