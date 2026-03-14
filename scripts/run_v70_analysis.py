#!/usr/bin/env python3
"""
V7.0 深度投资分析

核心理念：
1. 财务数据质量是分析的基石（否定之否定验证）
2. 五层追问模型
3. 奖励函数驱动深度分析
4. 循环追问机制
5. 接受漫长，追求高质量

使用方法:
    python3 scripts/run_v70_analysis.py --company "PDD Holdings" --ticker PDD --market us
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analyzer_v70 import DeepAnalyzerV70


def run_analysis(
    company: str,
    ticker: str = None,
    market: str = "us",
    max_iterations: int = 10,
    quality_threshold: float = 6.0,
    reward_threshold: float = 10.0
):
    """运行V7.0分析"""
    
    print("=" * 70)
    print("Company Deep Analysis V7.0")
    print("财务数据质量验证 + 五层追问 + 奖励函数驱动")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"公司: {company}")
    print(f"代码: {ticker or '未提供'}")
    print(f"市场: {market}")
    print(f"最大迭代次数: {max_iterations}")
    print(f"质量阈值: {quality_threshold}")
    print(f"奖励阈值: {reward_threshold}")
    print("=" * 70)
    
    # 创建分析器
    analyzer = DeepAnalyzerV70({
        "max_iterations": max_iterations,
        "quality_threshold": quality_threshold,
        "reward_threshold": reward_threshold
    })
    
    # 执行分析
    report, success = analyzer.analyze(
        company=company,
        ticker=ticker,
        market=market
    )
    
    # 计算奖励函数值
    reward = analyzer.moat_engine.calculate_reward()
    
    print("\n" + "=" * 70)
    print("分析完成!")
    print("=" * 70)
    print(f"状态: {'成功 ✅' if success else '终止 ⚠️'}")
    print(f"奖励函数值: {reward:.2f}")
    print(f"追问层数: {len(analyzer.questioning_history)}")
    print("=" * 70)
    
    # 保存报告
    if success:
        output_dir = Path("reports/v70")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"{company}_v70_report_{timestamp}.md"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n报告已保存: {report_file}")
    
    return report, success


def main():
    parser = argparse.ArgumentParser(description="V7.0 深度投资分析")
    parser.add_argument("--company", required=True, help="公司名称")
    parser.add_argument("--ticker", default=None, help="股票代码")
    parser.add_argument("--market", default="us", help="市场 (us/cn)")
    parser.add_argument("--max-iterations", type=int, default=10, help="最大迭代次数")
    parser.add_argument("--quality-threshold", type=float, default=6.0, help="数据质量阈值")
    parser.add_argument("--reward-threshold", type=float, default=10.0, help="奖励函数阈值")
    
    args = parser.parse_args()
    
    run_analysis(
        company=args.company,
        ticker=args.ticker,
        market=args.market,
        max_iterations=args.max_iterations,
        quality_threshold=args.quality_threshold,
        reward_threshold=args.reward_threshold
    )


if __name__ == "__main__":
    main()