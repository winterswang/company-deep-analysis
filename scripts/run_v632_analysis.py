#!/usr/bin/env python3
"""
V6.3.2 投资故事线 + 辩证式分析

使用方法:
    python3 scripts/run_v632_analysis.py --company "PDD Holdings" --ticker PDD --market us
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analyzer_v632 import DialecticalAnalyzerV632


def run_analysis(
    company: str,
    ticker: str = None,
    market: str = "us",
    min_valid_data: int = 8,
    max_iterations: int = 3,
    score_threshold: int = 85,
    output_dir: str = "reports/v632"
):
    """运行V6.3.2分析"""
    
    print("=" * 70)
    print("Company Deep Analysis V6.3.2")
    print("投资故事线 + 辩证式分析")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"公司: {company}")
    print(f"代码: {ticker or '未提供'}")
    print(f"市场: {market}")
    print(f"最大迭代轮数: {max_iterations}")
    print(f"评分阈值: {score_threshold}")
    print("=" * 70)
    
    # 创建分析器
    analyzer = DialecticalAnalyzerV632({
        "min_valid_data": min_valid_data,
        "max_iterations": max_iterations,
        "score_threshold": score_threshold
    })
    
    # 执行分析
    report, success = analyzer.analyze_with_data_collection(
        company=company,
        ticker=ticker,
        market=market
    )
    
    print("\n" + "=" * 70)
    print("分析完成!")
    print("=" * 70)
    print(f"状态: {'成功 ✅' if success else '终止 ⚠️'}")
    
    if success and analyzer.iterations:
        final_score = analyzer.iterations[-1].get("score", 0)
        print(f"最终评分: {final_score}/100")
    
    print("=" * 70)
    
    return report, success


def main():
    parser = argparse.ArgumentParser(description="V6.3.2 投资故事线 + 辩证式分析")
    parser.add_argument("--company", required=True, help="公司名称")
    parser.add_argument("--ticker", default=None, help="股票代码")
    parser.add_argument("--market", default="us", help="市场 (us/cn)")
    parser.add_argument("--min-valid-data", type=int, default=8, help="最少有效数据数")
    parser.add_argument("--max-iterations", type=int, default=3, help="最大迭代轮数")
    parser.add_argument("--score-threshold", type=int, default=85, help="评分阈值")
    parser.add_argument("--output", default="reports/v632", help="输出目录")
    
    args = parser.parse_args()
    
    run_analysis(
        company=args.company,
        ticker=args.ticker,
        market=args.market,
        min_valid_data=args.min_valid_data,
        max_iterations=args.max_iterations,
        score_threshold=args.score_threshold,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()