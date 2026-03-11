#!/usr/bin/env python3
"""
V6.3 完整分析运行脚本 - 基于雪球爬虫数据
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.data_collector_v63_fixed import IntegratedDataCollectorV63
from core.analyzer_v62 import DialecticalAnalyzerV62, DataPoint


def run_full_analysis(company: str, ticker: str = None, market: str = "us"):
    """运行完整分析"""
    
    print("=" * 70)
    print("V6.3 完整数据集成分析")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"公司: {company}")
    print(f"代码: {ticker}")
    print("=" * 70)
    
    # 1. 数据收集
    print("\n【阶段1: 数据收集】")
    collector = IntegratedDataCollectorV63()
    data_points = collector.collect_all(company, ticker, market)
    
    # 2. 数据质量检查
    summary = collector.get_summary()
    print("\n【数据质量报告】")
    print(f"总数据: {summary['total']} 条")
    print(f"有效数据: {summary['valid']} 条 (P2及以上)")
    
    # 3. 分析
    print("\n【阶段2: 辩证式分析】")
    analyzer = DialecticalAnalyzerV62({"min_valid_data": 8})
    report, success = analyzer.analyze(company, data_points)
    
    # 4. 输出
    print("\n" + "=" * 70)
    print("分析完成!")
    print("=" * 70)
    print(f"状态: {'成功' if success else '终止'}")
    
    if not success:
        print("\n数据不足报告:")
        print(report)
    else:
        # 保存报告
        output_dir = Path("reports/v63")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"{company}_v63_analysis_{timestamp}.md"
        
        # 生成完整报告
        full_report = generate_full_report(company, summary, data_points)
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(full_report)
        
        print(f"报告已保存: {report_file}")
        
        return full_report, report_file
    
    return report, None


def generate_full_report(company: str, summary: dict, data_points: list) -> str:
    """生成完整分析报告"""
    
    # 按来源分组
    by_source = {}
    for d in data_points:
        if d.source not in by_source:
            by_source[d.source] = []
        by_source[d.source].append(d)
    
    report = f"""# {company} V6.3 深度投资分析报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析框架**: V6.3 完整数据集成（雪球爬虫 + Tavily + Exa）
**数据质量**: ✅ {summary['valid']}条有效数据

---

## 📊 数据来源报告

### 数据收集统计

| 来源 | 数据量 | 质量 |
|------|--------|------|
"""
    
    for source, items in by_source.items():
        quality = items[0].quality if items else "N/A"
        report += f"| {source} | {len(items)} 条 | {quality} |\n"
    
    report += f"| **总计** | **{summary['total']} 条** | **P0-P2** |\n"
    
    # 添加雪球讨论摘要
    if "雪球爬虫-讨论" in by_source:
        report += "\n### 雪球讨论精选\n\n"
        for i, d in enumerate(by_source["雪球爬虫-讨论"][:5], 1):
            report += f"**{i}.** {d.value[:200]}...\n\n"
    
    # 添加雪球资讯摘要
    if "雪球爬虫-资讯" in by_source:
        report += "\n### 雪球资讯精选\n\n"
        for i, d in enumerate(by_source["雪球爬虫-资讯"][:5], 1):
            report += f"**{i}.** {d.name}\n\n"
    
    # 添加搜索结果摘要
    if "Tavily" in by_source or "Exa" in by_source:
        report += "\n### 搜索结果摘要\n\n"
        for d in (by_source.get("Tavily", []) + by_source.get("Exa", []))[:5]:
            report += f"- **{d.name}**: {d.value[:150]}...\n"
    
    report += """
---

## 分析说明

本报告基于V6.3框架，集成了以下数据源：

1. **雪球爬虫 (P0)** - 讨论、资讯、公告、专栏文章
2. **Tavily (P2)** - 实时新闻搜索
3. **Exa (P2)** - 深度研究搜索

所有数据均经过质量检查，P2以下数据已自动丢弃。

---

**分析版本**: V6.3
**数据收集器**: data_collector_v63_fixed.py
"""
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", required=True)
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--market", default="us")
    
    args = parser.parse_args()
    
    run_full_analysis(args.company, args.ticker, args.market)