"""
Main data collector - Application Module.

This module provides complete data collection with:
- Standardized JSON output
- Quality scoring for each data point
- Information index generation
- Multiple data sources integration
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from scoring.quality_scorer import QualityScorer
from evaluation.llm_evaluator import LLMEvaluator

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Unified data collection service.
    
    Outputs standardized data with quality scoring and information index.
    """
    
    def __init__(self, llm_client=None):
        """Initialize DataCollector."""
        self.quality_scorer = QualityScorer()
        self.llm_evaluator = LLMEvaluator(llm_client)
        
        self.adapters = {}
        self._register_adapters()
    
    def _register_adapters(self):
        """Register available data source adapters."""
        # Financial data sources
        try:
            from sources.akshare_adapter import AkShareAdapter
            self.adapters["akshare"] = AkShareAdapter()
            logger.info("Registered AkShare adapter (financial)")
        except ImportError as e:
            logger.warning(f"Could not register AkShare adapter: {e}")
        
        # Search sources
        try:
            from sources.tavily_adapter import TavilyAdapter
            self.adapters["tavily"] = TavilyAdapter()
            logger.info("Registered Tavily adapter (search)")
        except ImportError as e:
            logger.warning(f"Could not register Tavily adapter: {e}")
        
        try:
            from sources.exa_adapter import ExaAdapter
            self.adapters["exa"] = ExaAdapter()
            logger.info("Registered Exa adapter (search)")
        except ImportError as e:
            logger.warning(f"Could not register Exa adapter: {e}")
        
        # Crawler sources
        try:
            from sources.xueqiu_adapter import XueqiuAdapter
            self.adapters["xueqiu"] = XueqiuAdapter()
            logger.info("Registered Xueqiu adapter (crawler)")
        except ImportError as e:
            logger.warning(f"Could not register Xueqiu adapter: {e}")
        
        # Local cache
        try:
            from sources.local_file_adapter import LocalFileAdapter
            self.adapters["local"] = LocalFileAdapter()
            logger.info("Registered LocalFile adapter (cache)")
        except ImportError as e:
            logger.warning(f"Could not register LocalFile adapter: {e}")
    
    async def collect(self, query: str, context: dict = None) -> dict:
        """
        Collect data based on query and return standardized output.
        
        Returns:
            Complete output with:
            - data: Array of data points with quality scores
            - quality_assessment: Overall quality metrics
            - information_index: References to detailed data
        """
        # Parse query
        parsed = self._parse_query(query)
        
        # Collect from all sources
        all_data = []
        sources_used = []
        
        for adapter_key, adapter in self.adapters.items():
            try:
                result = await adapter.fetch(parsed)
                if result.success:
                    # Use result.source_name (e.g., "AkShare") not adapter_key (e.g., "akshare")
                    scored_data = self._score_data_points(result.data, result.source_name)
                    all_data.extend(scored_data)
                    
                    sources_used.append({
                        "name": result.source_name,
                        "type": result.source_type,
                        "count": len(result.data),
                        "success": True
                    })
                else:
                    sources_used.append({
                        "name": adapter.source_name,
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
        
        # Calculate derived metrics (ROE, ROIC, margins, etc.)
        enriched_data = self._calculate_derived_metrics(all_data)
        
        # Generate quality assessment
        quality_assessment = self._generate_quality_assessment(enriched_data, sources_used)
        
        # Build standardized output
        output = {
            "skill": "data-collector",
            "version": "2.0",
            "query": query,
            "collected_at": datetime.utcnow().isoformat() + "Z",
            "company": parsed.get("company", ""),
            "ticker": parsed.get("ticker", ""),
            "market": parsed.get("market", "cn"),
            
            # Main data - standardized format
            "data": enriched_data,
            
            # Source tracking
            "sources_used": sources_used,
            
            # Quality assessment - per data point and overall
            "quality_assessment": quality_assessment,
            
            # Information index - where detailed data is stored
            "information_index": self._generate_information_index(enriched_data, parsed)
        }
        
        return output
    
    def _score_data_points(self, data: list[dict], source_name: str) -> list[dict]:
        """Add quality scores to each data point."""
        scored = []
        
        for item in data:
            # Get base score from source
            source_score = self.quality_scorer.score_source(source_name)
            
            # Calculate overall score
            overall_score = self.quality_scorer.calculate_overall_score(
                source_name, data, item.get("metrics", {})
            )
            
            # Add quality metadata
            scored_item = {
                **item,
                "quality": {
                    "source": source_name,
                    "source_score": source_score,
                    "overall_score": overall_score,
                    "reliability": self._get_reliability_label(source_score)
                }
            }
            scored.append(scored_item)
        
        return scored
    
    def _get_reliability_label(self, score: float) -> str:
        """Convert score to reliability label."""
        if score >= 0.9:
            return "P0"
        elif score >= 0.7:
            return "P1"
        elif score >= 0.5:
            return "P2"
        else:
            return "P3"
    
    def _calculate_derived_metrics(self, data: list[dict]) -> list[dict]:
        """Calculate derived financial metrics (ROE, ROIC, margins, etc.)."""
        
        # Group by year
        by_year = {}
        for item in data:
            year = item.get("year")
            if year:
                if year not in by_year:
                    by_year[year] = {}
                by_year[year].update(item.get("metrics", {}))
        
        # Calculate ratios for each year
        result = []
        for year, metrics in sorted(by_year.items(), reverse=True):
            # Get base values (in yuan, convert to billion)
            revenue = metrics.get("主营收入", 0) / 1e9
            net_income = metrics.get("净利润", 0) / 1e9
            gross_profit = metrics.get("毛利", 0) / 1e9
            operating_profit = metrics.get("营业利润", 0) / 1e9
            pre_tax_income = metrics.get("持续经营税前利润", 0) / 1e9
            eps = metrics.get("基本每股收益-普通股", 0)
            
            # Calculate derived metrics
            derived = {}
            
            if revenue > 0:
                derived["gross_margin"] = round(gross_profit / revenue * 100, 2)  # %
                derived["operating_margin"] = round(operating_profit / revenue * 100, 2)  # %
                derived["net_margin"] = round(net_income / revenue * 100, 2)  # %
            
            # Calculate YoY growth
            year_int = int(year)
            prev_year = str(year_int - 1)
            if prev_year in by_year:
                prev_revenue = by_year[prev_year].get("主营收入", 0) / 1e9
                if prev_revenue > 0:
                    derived["revenue_growth_yoy"] = round((revenue - prev_revenue) / prev_revenue * 100, 2)
            
            # Build result
            for item in data:
                if item.get("year") == year:
                    new_item = {
                        **item,
                        "derived_metrics": derived,
                        "metrics_billion": {
                            "revenue": round(revenue, 2),
                            "net_income": round(net_income, 2),
                            "gross_profit": round(gross_profit, 2),
                            "operating_profit": round(operating_profit, 2),
                            "pre_tax_income": round(pre_tax_income, 2)
                        }
                    }
                    result.append(new_item)
        
        return result
    
    def _generate_quality_assessment(self, data: list[dict], sources_used: list[dict]) -> dict:
        """Generate comprehensive quality assessment."""
        
        # Layer 1: Source ratings
        source_ratings = {}
        for source in sources_used:
            if source.get("success"):
                score = self.quality_scorer.score_source(source["name"])
                source_ratings[source["name"]] = score
        
        # Layer 2: Cross validation
        cross_validation = self.quality_scorer.score_cross_validation(data)
        
        # Overall metrics
        if data:
            quality_scores = [item.get("quality", {}).get("overall_score", 0) for item in data]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            min_quality = min(quality_scores) if quality_scores else 0
            max_quality = max(quality_scores) if quality_scores else 0
        else:
            avg_quality = 0
            min_quality = 0
            max_quality = 0
        
        return {
            "layer1_source_rating": source_ratings,
            "layer2_cross_validation": {
                "score": cross_validation,
                "description": "0.7 = single source, 1.0 = multiple sources"
            },
            "layer3_llm_evaluation": {
                "status": "not_implemented",
                "note": "Requires LLM client"
            },
            "overall_metrics": {
                "average_score": round(avg_quality, 2),
                "min_score": round(min_quality, 2),
                "max_score": round(max_quality, 2),
                "total_data_points": len(data)
            },
            "reliability_distribution": {
                "P0": sum(1 for d in data if d.get("quality", {}).get("reliability") == "P0"),
                "P1": sum(1 for d in data if d.get("quality", {}).get("reliability") == "P1"),
                "P2": sum(1 for d in data if d.get("quality", {}).get("reliability") == "P2"),
                "P3": sum(1 for d in data if d.get("quality", {}).get("reliability") == "P3")
            }
        }
    
    def _generate_information_index(self, data: list[dict], parsed: dict) -> dict:
        """Generate information index - where detailed data is stored."""
        
        return {
            "version": "1.0",
            "company": parsed.get("company", ""),
            "ticker": parsed.get("ticker", ""),
            "market": parsed.get("market", ""),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            
            "data_files": {
                "financial_5y": {
                    "type": "financial_data",
                    "format": "json",
                    "path": "./data/financial_5y.json",
                    "description": "5-year financial data with derived metrics"
                },
                "quality_scores": {
                    "type": "quality_data", 
                    "format": "json",
                    "path": "./data/quality_scores.json",
                    "description": "Quality scores for each data point"
                }
            },
            
            "reference_structure": {
                "financial_data": {
                    "included": True,
                    "years": sorted([d.get("year") for d in data if d.get("year")], reverse=True),
                    "metrics_count": len(data)
                },
                "annual_reports": {"included": False},
                "news": {"included": False},
                "xueqiu_articles": {"included": False},
                "announcements": {"included": False}
            }
        }
    
    def _parse_query(self, query: str) -> dict:
        """Parse natural language query."""
        result = {
            "company": "",
            "ticker": "",
            "market": "cn"
        }
        
        query_lower = query.lower()
        
        # Known US stocks
        us_tickers = ["pdd", "aapl", "msft", "googl", "amzn", "tsla", "nvidia", "meta", "nvda"]
        for ticker in us_tickers:
            if ticker in query_lower:
                result["ticker"] = ticker.upper()
                result["market"] = "us"
                break
        
        # Extract company name
        words = query.split()
        for word in words:
            if word and not word.isdigit() and len(word) > 2:
                if word.upper() not in ["USD", "CNY", "2024", "2023", "财务", "数据", "分析"]:
                    result["company"] = word
                    break
        
        return result
    
    async def collect_and_save(self, query: str, output_dir: str) -> dict:
        """Collect data and save all output files."""
        
        # Collect data
        result = await self.collect(query)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save main data file
        data_file = output_path / "data.json"
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # Save financial data separately
        financial_data = {
            "company": result.get("company"),
            "ticker": result.get("ticker"),
            "market": result.get("market"),
            "years": []
        }
        
        for item in result.get("data", []):
            year_data = {
                "year": item.get("year"),
                "metrics": item.get("metrics", {}),
                "metrics_billion": item.get("metrics_billion", {}),
                "derived_metrics": item.get("derived_metrics", {}),
                "quality": item.get("quality", {})
            }
            financial_data["years"].append(year_data)
        
        financial_file = output_path / "data" / "financial_5y.json"
        financial_file.parent.mkdir(parents=True, exist_ok=True)
        with open(financial_file, "w", encoding="utf-8") as f:
            json.dump(financial_data, f, ensure_ascii=False, indent=2)
        
        # Save information index
        index_file = output_path / "data_index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(result.get("information_index", {}), f, ensure_ascii=False, indent=2)
        
        # Generate report markdown
        report = self._generate_report(result)
        report_file = output_path / "report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        result["output_files"] = {
            "data_json": str(data_file),
            "financial_json": str(financial_file),
            "index_json": str(index_file),
            "report_md": str(report_file)
        }
        
        return result
    
    def _generate_report(self, result: dict) -> str:
        """Generate markdown report."""
        
        lines = [
            f"# {result.get('company', 'N/A')} 财务数据报告",
            "",
            f"**生成时间**: {result.get('collected_at', '')}",
            f"**股票代码**: {result.get('ticker', 'N/A')}",
            f"**市场**: {result.get('market', 'N/A')}",
            "",
            "---",
            "",
            "## 一、核心财务指标 (5年)",
            "",
            "| 指标 | 2024 | 2023 | 2022 | 2021 | 2020 | 单位 |",
            "|------|------|------|------|------|------|------|"
        ]
        
        # Build table data
        years_data = {}
        for item in result.get("data", []):
            year = item.get("year")
            metrics = item.get("metrics_billion", {})
            years_data[year] = metrics
        
        # Add rows
        for metric, unit in [
            ("revenue", "亿元"),
            ("net_income", "亿元"),
            ("gross_profit", "亿元"),
            ("operating_profit", "亿元"),
            ("pre_tax_income", "亿元"),
            ("eps", "元")
        ]:
            row = [metric]
            for year in [2024, 2023, 2022, 2021, 2020]:
                val = years_data.get(year, {}).get(metric, "-")
                row.append(str(val))
            row.append(unit)
            lines.append("| " + " | ".join(row) + " |")
        
        # Quality section
        qa = result.get("quality_assessment", {})
        om = qa.get("overall_metrics", {})
        
        lines.extend([
            "",
            "---",
            "",
            "## 二、数据质量评估",
            "",
            f"- **平均质量分**: {om.get('average_score', 0):.2f}/1.00",
            f"- **数据点总数**: {om.get('total_data_points', 0)}",
            "",
            "### 2.1 来源评级",
            ""
        ])
        
        for source, score in qa.get("layer1_source_rating", {}).items():
            lines.append(f"- **{source}**: {score:.1f} ({self._get_reliability_label(score)})")
        
        lines.extend([
            "",
            "### 2.2 可靠性分布",
            "",
            f"- P0 (高): {qa.get('reliability_distribution', {}).get('P0', 0)}",
            f"- P1 (中): {qa.get('reliability_distribution', {}).get('P1', 0)}",
            f"- P2 (低): {qa.get('reliability_distribution', {}).get('P2', 0)}",
            "",
            "---",
            "",
            "*本报告由 data-collector 自动生成*"
        ])
        
        return "\n".join(lines)