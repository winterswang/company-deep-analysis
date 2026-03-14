"""Exa adapter for web search - using direct API calls."""

import sys
import os
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sources.base import DataSourceResult


class ExaAdapter:
    """Adapter for Exa search API."""
    
    def __init__(self):
        self.source_name = "Exa"
        self.source_type = "search"
        self.api_key = os.getenv("EXA_API_KEY", "")
        self.base_url = "https://api.exa.ai"
    
    async def fetch(self, query: dict) -> DataSourceResult:
        """Fetch data from Exa search using direct API."""
        try:
            search_query = query.get("search_query", query.get("company", ""))
            
            if not self.api_key:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="Exa API key not set (EXA_API_KEY)"
                )
            
            # Use Exa API directly
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": f"{search_query} 财务分析",
                "num_results": 10,
                "type": "auto"
            }
            
            response = requests.post(
                f"{self.base_url}/search",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error=f"Exa API error: {response.status_code}"
                )
            
            results = response.json()
            
            data = []
            for item in results.get("results", []):
                data.append({
                    "type": "search",
                    "source": "Exa",
                    "title": item.get("title", ""),
                    "content": item.get("text", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0)
                })
            
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=data,
                success=True
            )
            
        except ImportError as e:
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=f"requests not installed: {e}"
            )
        except Exception as e:
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=str(e)
            )
