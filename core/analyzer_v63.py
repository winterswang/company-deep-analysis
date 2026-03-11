"""
V6.3 完整数据集成分析器

集成所有数据源：
- AkShare (P0)
- 雪球爬虫 (P0)
- 本地数据 (P0)
- Tavily (P2)
- Exa (P2)
"""

import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analyzer_v62 import DialecticalAnalyzerV62, DataPoint
from scripts.data_collector_v63 import IntegratedDataCollector


class DialecticalAnalyzerV63(DialecticalAnalyzerV62):
    """V6.3 完整数据集成分析器"""
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.collector = IntegratedDataCollector()
    
    def analyze_with_data_collection(
        self, 
        company: str, 
        ticker: str = None, 
        market: str = "us"
    ) -> Tuple[str, bool]:
        """使用自动数据收集进行分析"""
        
        print("\n" + "=" * 70)
        print("V6.3 辩证式投资分析（完整数据集成）")
        print("=" * 70)
        print(f"目标公司: {company}")
        print(f"股票代码: {ticker or '未提供'}")
        print(f"市场: {market}")
        print("=" * 70)
        
        # 自动收集数据
        print("\n【步骤1: 自动数据收集】")
        data_points = self.collector.collect_all(company, ticker, market)
        
        # 数据质量统计
        summary = self.collector.get_summary()
        print("\n【数据收集统计】")
        print(f"  总数据: {summary['total']} 条")
        print(f"  有效数据: {summary['valid']} 条 (P2及以上)")
        print(f"  低质量数据: {summary['invalid']} 条 (已丢弃)")
        
        # 按来源显示
        print("\n【数据来源分布】")
        for source, count in summary['by_source'].items():
            print(f"  {source}: {count} 条")
        
        # 调用V6.2分析逻辑
        return self.analyze(company, data_points)


def main():
    """测试V6.3分析器"""
    
    # 创建分析器
    analyzer = DialecticalAnalyzerV63({
        "min_valid_data": 6
    })
    
    # 分析任天堂
    report, success = analyzer.analyze_with_data_collection(
        company="Nintendo",
        ticker="NTDOY",
        market="us"
    )
    
    print("\n" + "=" * 70)
    print("分析结果:")
    print("=" * 70)
    print(report[:2000] if len(report) > 2000 else report)
    print(f"\n状态: {'成功' if success else '终止'}")


if __name__ == "__main__":
    main()