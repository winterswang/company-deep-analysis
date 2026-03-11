#!/usr/bin/env python3
"""
V6.3 完整数据集成分析运行脚本

使用方法:
    python3 scripts/run_v63_analysis.py --company Nintendo --ticker NTDOY --market us
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analyzer_v63 import DialecticalAnalyzerV63


def run_analysis(
    company: str,
    ticker: str = None,
    market: str = "us",
    min_valid_data: int = 8,
    output_dir: str = "reports/v63"
):
    """运行V6.3分析"""
    
    print("=" * 70)
    print("Company Deep Analysis V6.3")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"公司: {company}")
    print(f"代码: {ticker or '未提供'}")
    print("=" * 70)
    
    # 创建分析器
    analyzer = DialecticalAnalyzerV63({
        "min_valid_data": min_valid_data
    })
    
    # 执行分析
    report, success = analyzer.analyze_with_data_collection(
        company=company,
        ticker=ticker,
        market=market
    )
    
    # 保存报告
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_path / f"{company}_v63_report_{timestamp}.md"
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n" + "=" * 70)
    print("分析完成!")
    print("=" * 70)
    print(f"报告已保存: {report_file}")
    print(f"状态: {'成功' if success else '终止'}")
    
    return report, success, report_file


def main():
    parser = argparse.ArgumentParser(description="V6.3 完整数据集成分析")
    parser.add_argument("--company", required=True, help="公司名称")
    parser.add_argument("--ticker", default=None, help="股票代码")
    parser.add_argument("--market", default="us", help="市场 (us/cn)")
    parser.add_argument("--min-valid-data", type=int, default=8, help="最少有效数据数")
    parser.add_argument("--output", default="reports/v63", help="输出目录")
    
    args = parser.parse_args()
    
    run_analysis(
        company=args.company,
        ticker=args.ticker,
        market=args.market,
        min_valid_data=args.min_valid_data,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()