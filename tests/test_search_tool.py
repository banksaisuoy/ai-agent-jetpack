import pytest
from src.core.tools.search_tool import SearchWebTool

def test_search_web_tool_structured_results():
    tool = SearchWebTool()
    result = tool.execute(query="pytest")
    
    assert isinstance(result, dict)
    assert "query" in result
    assert result["query"] == "pytest"
    assert "results" in result
    assert isinstance(result["results"], list)
    assert len(result["results"]) > 0
    assert "title" in result["results"][0]
    assert "url" in result["results"][0]

def test_search_web_tool_empty_query():
    tool = SearchWebTool()
    
    with pytest.raises(ValueError, match="Query cannot be empty"):
        tool.execute(query="")
        
    with pytest.raises(ValueError, match="Query cannot be empty"):
        tool.execute(query="   ")

def test_search_web_tool_api_failure():
    tool = SearchWebTool()
    
    with pytest.raises(Exception, match="API failure"):
        tool.execute(query="simulate_api_failure")