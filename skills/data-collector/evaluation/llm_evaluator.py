"""LLM-based quality evaluation."""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class LLMEvaluator:
    """Use LLM for deeper data quality evaluation."""
    
    def __init__(self, llm_client=None):
        """
        Initialize with LLM client.
        
        Args:
            llm_client: Client for LLM API (e.g., OpenAI, Anthropic)
        """
        self.llm_client = llm_client
    
    def set_llm_client(self, llm_client):
        """Set LLM client after initialization."""
        self.llm_client = llm_client
    
    async def evaluate_anomalies(self, financial_data: list[dict]) -> dict:
        """
        Detect anomalies in financial data using LLM.
        
        Args:
            financial_data: List of financial data points
        
        Returns:
            Anomaly detection results
        """
        if not self.llm_client:
            return {
                "anomalies_found": [],
                "summary": "No LLM client available"
            }
        
        # Prepare prompt
        prompt = self._build_anomaly_prompt(financial_data)
        
        try:
            response = await self.llm_client.generate(prompt)
            result = json.loads(response)
            
            return {
                "anomalies_found": result.get("anomalies", []),
                "summary": result.get("summary", "")
            }
        except Exception as e:
            logger.error(f"Error in LLM anomaly evaluation: {e}")
            return {
                "anomalies_found": [],
                "error": str(e)
            }
    
    async def resolve_conflicts(self, conflicting_data: list[dict]) -> dict:
        """
        Resolve conflicts when multiple sources provide different data.
        
        Args:
            conflicting_data: List of data points with conflicts
        
        Returns:
            Resolution result with recommended source
        """
        if not self.llm_client:
            # Fall back to source priority
            return self._resolve_by_priority(conflicting_data)
        
        prompt = self._build_conflict_prompt(conflicting_data)
        
        try:
            response = await self.llm_client.generate(prompt)
            result = json.loads(response)
            
            return {
                "conflict_detected": True,
                "resolution": result.get("resolution", {}),
                "reason": result.get("reason", "")
            }
        except Exception as e:
            logger.error(f"Error in LLM conflict resolution: {e}")
            return self._resolve_by_priority(conflicting_data)
    
    def _resolve_by_priority(self, conflicting_data: list[dict]) -> dict:
        """Fallback: resolve by source priority."""
        # Priority: P0 > P1 > P2 > P3
        priority = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        
        best = min(
            conflicting_data,
            key=lambda x: priority.get(x.get("quality_level", "P3"), 99)
        )
        
        return {
            "conflict_detected": True,
            "resolution": {"use": best},
            "reason": "Resolved by source priority"
        }
    
    def _build_anomaly_prompt(self, financial_data: list[dict]) -> str:
        """Build prompt for anomaly detection."""
        data_str = json.dumps(financial_data[:10], ensure_ascii=False, indent=2)
        
        prompt = f"""
你是一位资深财务分析师，需要检测财务数据中的异常。

财务数据:
{data_str}

请分析以下方面:
1. 是否有异常的财务指标（如过高或过低的比率）
2. 趋势是否合理
3. 是否有需要关注的异常点

请返回JSON格式:
{{
    "anomalies": [
        {{
            "metric": "指标名",
            "value": 数值,
            "is_anomaly": true/false,
            "severity": "high/medium/low",
            "explanation": "解释"
        }}
    ],
    "summary": "总结"
}}
"""
        return prompt
    
    def _build_conflict_prompt(self, conflicting_data: list[dict]) -> str:
        """Build prompt for conflict resolution."""
        data_str = json.dumps(conflicting_data, ensure_ascii=False, indent=2)
        
        prompt = f"""
你是一位资深财务分析师，需要解决数据源之间的冲突。

冲突数据:
{data_str}

请分析:
1. 差异原因可能是什么？
2. 应该相信哪个数据源？
3. 如何标记这个数据点的质量？

请返回JSON格式:
{{
    "resolution": {{
        "use": "选择使用的数据源",
        "reason": "原因"
    }},
    "reason": "详细解释"
}}
"""
        return prompt
    
    async def evaluate_overall(self, assessment: dict) -> dict:
        """
        Evaluate overall data quality with LLM.
        
        Args:
            assessment: Basic assessment from QualityScorer
        
        Returns:
            Enhanced assessment with LLM insights
        """
        if not self.llm_client:
            return assessment
        
        # This can be extended for more comprehensive evaluation
        return assessment