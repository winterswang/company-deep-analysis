"""Tests for data collector skill."""

import asyncio
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_collection():
    """Test basic data collection."""
    from skills.data_collector import DataCollector
    
    collector = DataCollector()
    
    # Test with PDD
    result = await collector.collect("PDD Holdings 财务数据")
    
    print("\n=== Collection Result ===")
    print(f"Query: {result.get('query')}")
    print(f"Company: {result.get('company')}")
    print(f"Ticker: {result.get('ticker')}")
    print(f"Market: {result.get('market')}")
    print(f"Data points: {len(result.get('data', []))}")
    print(f"Sources used: {len(result.get('sources_used', []))}")
    
    # Quality assessment
    qa = result.get("quality_assessment", {})
    print(f"\n=== Quality Assessment ===")
    print(f"Overall score: {qa.get('overall_score', 0):.2f}")
    print(f"Data points: {qa.get('data_points', 0)}")
    print(f"Source ratings: {qa.get('layer1_source_rating', {})}")
    
    return result


async def test_save_output():
    """Test collection and save."""
    from skills.data_collector import DataCollector
    
    collector = DataCollector()
    
    output_dir = "/tmp/data_collector_test"
    result = await collector.collect_and_save("PDD 财务数据", output_dir)
    
    print(f"\n=== Saved Files ===")
    print(f"Output directory: {output_dir}")
    print(f"Files: {result.get('output_files', {})}")
    
    # Verify file exists
    data_file = Path(output_dir) / "data.json"
    if data_file.exists():
        with open(data_file) as f:
            saved = json.load(f)
        print(f"Saved data keys: {list(saved.keys())}")
    
    return result


async def test_quality_scorer():
    """Test quality scorer."""
    from skills.data_collector.scoring.quality_scorer import QualityScorer
    
    scorer = QualityScorer()
    
    # Test source scoring
    print("\n=== Source Quality Scores ===")
    for source in ["AkShare", "年报", "雪球", "Tavily"]:
        score = scorer.score_source(source)
        print(f"{source}: {score}")
    
    # Test cross validation
    data = [
        {"source": "AkShare", "data": {"value": 100}},
        {"source": "年报", "data": {"value": 100}}
    ]
    cross_score = scorer.score_cross_validation(data)
    print(f"\nCross validation (2 sources): {cross_score}")
    
    # Test completeness
    test_data = {"year": 2024, "revenue": 100}
    completeness = scorer.score_completeness(test_data, ["year", "revenue"])
    print(f"Completeness: {completeness}")


async def main():
    """Run all tests."""
    logger.info("Starting data collector tests...")
    
    # Test 1: Quality scorer
    await test_quality_scorer()
    
    # Test 2: Basic collection
    try:
        result = await test_basic_collection()
    except Exception as e:
        logger.error(f"Basic collection test failed: {e}")
    
    # Test 3: Save output
    try:
        result = await test_save_output()
    except Exception as e:
        logger.error(f"Save output test failed: {e}")
    
    logger.info("Tests completed!")


if __name__ == "__main__":
    asyncio.run(main())