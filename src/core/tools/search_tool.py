            "required": ["query"]
        }

    def execute(self, query: str = "", **kwargs) -> Any:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
            
        if query == "simulate_api_failure":
            raise Exception("API failure")
            
        return {
            "query": query,
            "results": [
                {"title": f"Result 1 for {query}", "url": "http://example.com/1"},
                {"title": f"Result 2 for {query}", "url": "http://example.com/2"}
            ]
        }