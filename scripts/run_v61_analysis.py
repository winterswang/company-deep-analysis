#!/usr/bin/env python3
"""
V6.1 辩证式投资分析运行脚本

使用方法:
    python scripts/run_v61_analysis.py --company FISV --max-iterations 5
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analyzer_v61 import DialecticalAnalyzerV61
from search.search_engine import SearchEngine


def collect_initial_data(company: str) -> dict:
    """收集初始数据"""
    
    print("\n【阶段1: 数据收集】")
    print(f"获取 {company} 的初始数据...")
    
    data = {
        "financial_indicators": {},
        "search_results": [],
        "xueqiu_data": None
    }
    
    # 1. 尝试从雪球爬虫获取数据
    try:
        from xueqiu_analyzer.smart_crawler_v2 import SmartCrawlerV2
        
        print("  - 雪球数据爬取中...")
        crawler = SmartCrawlerV2()
        xueqiu_result = crawler.crawl(company)
        
        if xueqiu_result and "articles" in xueqiu_result:
            data["xueqiu_data"] = xueqiu_result
            print(f"    获取 {len(xueqiu_result['articles'])} 篇雪球文章")
    except Exception as e:
        print(f"    雪球数据获取失败: {e}")
    
    # 2. 尝试从AkShare获取财务数据
    try:
        from akshare_tools.financial_data import get_us_stock_financial
        
        print("  - AkShare财务数据获取中...")
        financial = get_us_stock_financial(company)
        
        if financial:
            data["financial_indicators"] = financial
            print(f"    获取财务数据: {len(financial)} 项指标")
    except Exception as e:
        print(f"    AkShare数据获取失败: {e}")
    
    # 3. 使用搜索引擎获取补充数据
    try:
        print("  - Tavily搜索中...")
        search_engine = MultiSourceSearchEngine()
        
        queries = [
            f"{company} business model revenue segments",
            f"{company} competitive advantage moat",
            f"{company} ROIC ROE financial performance",
            f"{company} management CEO strategy"
        ]
        
        for query in queries[:2]:  # 限制搜索次数
            results = search_engine.search(query, max_results=5)
            if results:
                data["search_results"].extend(results)
        
        print(f"    获取 {len(data['search_results'])} 条搜索结果")
    except Exception as e:
        print(f"    搜索引擎获取失败: {e}")
    
    return data


def run_analysis(company: str, max_iterations: int = 5, 
                 score_threshold: int = 85, output_dir: str = "reports/v61"):
    """运行V6.1分析"""
    
    # 收集初始数据
    initial_data = collect_initial_data(company)
    
    # 创建分析器
    config = {
        "max_iterations": max_iterations,
        "score_threshold": score_threshold
    }
    
    analyzer = DialecticalAnalyzerV61(config)
    
    # 执行分析
    final_report = analyzer.analyze(company, initial_data)
    
    # 保存最终报告
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存Markdown报告
    report_file = output_path / f"{company}_v61_report_{timestamp}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(final_report)
    print(f"\n报告已保存: {report_file}")
    
    # 保存分析链
    chain_file = output_path / f"{company}_v61_chain_{timestamp}.json"
    chain_data = {
        "company": company,
        "config": config,
        "iterations": [
            {
                "round": i.round_number,
                "report_length": len(i.analyst_report),
                "feedback_score": i.challenger_feedback.score.total if i.challenger_feedback else None,
                "todos_count": len(i.challenger_feedback.todos) if i.challenger_feedback else 0,
                "should_continue": i.challenger_feedback.should_continue if i.challenger_feedback else None
            }
            for i in analyzer.iterations
        ],
        "final_score": analyzer.iterations[-1].challenger_feedback.score.total if analyzer.iterations[-1].challenger_feedback else None,
        "timestamp": timestamp
    }
    
    with open(chain_file, "w", encoding="utf-8") as f:
        json.dump(chain_data, f, ensure_ascii=False, indent=2)
    
    return final_report, report_file


def main():
    parser = argparse.ArgumentParser(description="V6.1 辩证式投资分析")
    parser.add_argument("--company", required=True, help="公司代码或名称")
    parser.add_argument("--max-iterations", type=int, default=5, help="最大迭代轮数")
    parser.add_argument("--score-threshold", type=int, default=85, help="评分终止阈值")
    parser.add_argument("--output", default="reports/v61", help="输出目录")
    
    args = parser.parse_args()
    
    run_analysis(
        company=args.company,
        max_iterations=args.max_iterations,
        score_threshold=args.score_threshold,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()