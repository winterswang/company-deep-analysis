"""Quality scoring for data."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class QualityScorer:
    """Score data quality based on multiple dimensions."""
    
    # Source quality levels
    SOURCE_QUALITY = {
        "AkShare": "P0",
        "年报": "P0",
        "10-K": "P0",
        "雪球": "P1",
        "Tavily": "P2",
        "Exa": "P2",
        "Web": "P3",
    }
    
    # Quality to numeric score
    QUALITY_SCORES = {
        "P0": 1.0,
        "P1": 0.8,
        "P2": 0.6,
        "P3": 0.3,
        "P4": 0.1,
    }
    
    def __init__(self):
        pass
    
    def score_source(self, source_name: str) -> float:
        """Get base score from source name."""
        quality = self.SOURCE_QUALITY.get(source_name, "P3")
        return self.QUALITY_SCORES.get(quality, 0.3)
    
    def score_cross_validation(self, data_points: list[dict]) -> float:
        """
        Score cross-validation quality.
        
        Returns:
            1.0 if multiple sources agree, lower otherwise
        """
        if not data_points:
            return 0.5
        
        # Check if we have multiple sources
        sources = set()
        for dp in data_points:
            if isinstance(dp.get("data"), dict):
                sources.add(dp.get("data", {}).get("source", "unknown"))
        
        if len(sources) >= 2:
            return 1.0
        elif len(sources) == 1:
            return 0.7
        else:
            return 0.5
    
    def score_timeliness(self, data: dict) -> float:
        """
        Score data timeliness.
        
        Returns:
            1.0 for latest data, lower for older
        """
        # Check for year information
        year = data.get("year") or data.get("data", {}).get("报告期", "").split("-")[0]
        
        if not year:
            return 0.5
        
        try:
            year = int(year)
            current_year = 2026
            
            if year == current_year:
                return 1.0
            elif year == current_year - 1:
                return 0.85
            elif year == current_year - 2:
                return 0.7
            elif year >= current_year - 5:
                return 0.5
            else:
                return 0.3
        except:
            return 0.5
    
    def score_completeness(self, data: dict, required_fields: list[str]) -> float:
        """
        Score data completeness.
        
        Args:
            data: Data point to check
            required_fields: List of required field names
        
        Returns:
            1.0 if all fields present, lower otherwise
        """
        if not required_fields:
            return 1.0
        
        present = sum(1 for f in required_fields if f in data)
        return present / len(required_fields)
    
    def calculate_overall_score(
        self,
        source_name: str,
        data_points: list[dict],
        data: dict
    ) -> float:
        """
        Calculate overall quality score.
        
        Formula:
        Overall = Source × 0.4 + CrossValidation × 0.3 + Timeliness × 0.15 + Completeness × 0.15
        """
        source_score = self.score_source(source_name)
        cross_score = self.score_cross_validation(data_points)
        time_score = self.score_timeliness(data)
        
        # Assume completeness is good for now
        completeness_score = 0.9
        
        overall = (
            source_score * 0.4 +
            cross_score * 0.3 +
            time_score * 0.15 +
            completeness_score * 0.15
        )
        
        return round(overall, 2)
    
    def assess_data(self, data: list[dict]) -> dict:
        """
        Assess quality of a list of data points.
        
        Returns:
            Assessment result with scores and issues
        """
        if not data:
            return {
                "average_score": 0,
                "total_points": 0,
                "issues": ["No data to assess"]
            }
        
        scores = []
        for dp in data:
            if isinstance(dp.get("data"), dict):
                score = self.calculate_overall_score(
                    dp.get("source", "unknown"),
                    data,
                    dp.get("data", {})
                )
                scores.append(score)
        
        return {
            "average_score": sum(scores) / len(scores) if scores else 0,
            "total_points": len(data),
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "issues": []
        }