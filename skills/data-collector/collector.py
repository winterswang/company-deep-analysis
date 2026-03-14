"""Main data collector."""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from scoring.quality_scorer import QualityScorer
from evaluation.llm_evaluator import LLMEvaluator

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Unified data collection service.
    
    Collects data from multiple sources, performs quality assessment,
    and outputs standardized JSON.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize DataCollector.
        
        Args:
            llm_client: Optional LLM client for advanced evaluation
        """
        self.quality_scorer = QualityScorer()
        self.llm_evaluator = LLMEvaluator(llm_client)
        if llm_client:
            self.llm_evaluator.set_llm_client(llm_client)
        
        self.adapters = {}
        self._register_adapters()
    
    def _register_adapters(self):
        """Register available data source adapters."""
        try:
            from sources.akshare_adapter import AkShareAdapter
            self.adapters["akshare"] = AkShareAdapter()
            logger.info("Registered AkShare adapter")
        except ImportError as e:
            logger.warning(f"Could not register AkShare adapter: {e}")
        
        try:
            from sources.tavily_adapter import TavilyAdapter
            self.adapters["tavily"] = TavilyAdapter()
            logger.info("Registered Tavily adapter")
        except ImportError as e:
            logger.warning(f"Could not register Tavily adapter: {e}")
    
    async def collect(self, query: str, context: dict = None) -> dict:
        """
        Collect data based on natural language query.
        
        Args:
            query: Natural language query (e.g., "PDD 2024 财务数据")
            context: Optional context information
        
        Returns:
            Standardized JSON output
        """
        # Parse query to determine what to collect
        parsed = self._parse_query(query)
        
        # Collect from all available sources
        all_data = []
        sources_used = []
        
        for source_name, adapter in self.adapters.items():
            try:
                result = await adapter.fetch(parsed)
                if result.success:
                    all_data.extend(result.data)
                    sources_used.append({
                        "name": result.source_name,
                        "type": result.source_type,
                        "count": len(result.data),
                        "success": True
                    })
                else:
                    sources_used.append({
                        "name": result.source_name,
                        "error": result.error,
                        "success": False
                    })
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
                sources_used.append({
                    "name": source_name,
                    "error": str(e),
                    "success": False
                })
        
        # Quality assessment
        quality_assessment = self._assess_quality(all_data, sources_used)
        
        # Build output
        output = {
            "skill": "data-collector",
            "version": "1.0",
            "query": query,
            "collected_at": datetime.utcnow().isoformat() + "Z",
            "company": parsed.get("company", ""),
            "ticker": parsed.get("ticker", ""),
            "market": parsed.get("market", "cn"),
            "data": all_data,
            "sources_used": sources_used,
            "quality_assessment": quality_assessment
        }
        
        return output
    
    def _parse_query(self, query: str) -> dict:
        """
        Parse natural language query to extract parameters.
        """
        result = {
            "company": "",
            "ticker": "",
            "market": "cn"
        }
        
        query_lower = query.lower()
        
        us_tickers = ["pdd", "aapl", "msft", "googl", "amzn", "tsla", "nvidia"]
        for ticker in us_tickers:
            if ticker in query_lower:
                result["ticker"] = ticker.upper()
                result["market"] = "us"
                break
        
        words = query.split()
        for word in words:
            if word and not word.isdigit() and len(word) > 2:
                if word.upper() not in ["USD", "CNY", "2024", "2023"]:
                    result["company"] = word
                    break
        
        return result
    
    def _assess_quality(self, data: list[dict], sources_used: list[dict]) -> dict:
        """Assess data quality."""
        source_ratings = {}
        for source in sources_used:
            if source.get("success"):
                score = self.quality_scorer.score_source(source["name"])
                source_ratings[source["name"]] = score
        
        cross_validation_score = self.quality_scorer.score_cross_validation(data)
        
        return {
            "layer1_source_rating": source_ratings,
            "layer2_cross_validation": {
                "score": cross_validation_score,
                "note": "0.7 = single source, 1.0 = multiple sources"
            },
            "layer3_llm_evaluation": {"summary": "Not evaluated"},
            "overall_score": sum(source_ratings.values()) / len(source_ratings) if source_ratings else 0,
            "data_points": len(data)
        }
    
    async def collect_and_save(self, query: str, output_dir: str) -> dict:
        """Collect data and save to files."""
        result = await self.collect(query)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        json_path = output_path / "data.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        result["output_files"] = {"data_json": str(json_path)}
        
        return result