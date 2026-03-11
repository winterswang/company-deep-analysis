#!/usr/bin/env python3
"""
V5.0 迭代式辩证分析 - 主入口
Usage: python run_v5_analysis.py --company FISV
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.iterative_analyzer import analyze_company, IterativeDialecticalAnalyzer
from core.models import AnalysisChain


def save_analysis_result(chain: AnalysisChain, output_dir: str):
    """保存分析结果"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    company = chain.company
    
    # 保存JSON
    json_path = output_dir / f"{company}_v5_analysis_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(chain.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"✓ 分析结果已保存: {json_path}")
    
    # 保存Markdown报告
    md_path = output_dir / f"{company}_v5_report_{timestamp}.md"
    report = generate_report(chain)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✓ 分析报告已保存: {md_path}")
    
    return json_path, md_path


def generate_report(chain: AnalysisChain) -> str:
    """生成Markdown报告"""
    lines = []
    
    lines.append(f"# {chain.company} 迭代式辩证分析报告 V5.0\n")
    lines.append(f"**分析时间**: {chain.start_time}\n")
    lines.append(f"**总轮数**: {chain.total_iterations}\n")
    lines.append(f"**最终评分**: {chain.final_score.total}/100\n" if chain.final_score else "")
    
    lines.append("---\n")
    
    # 假设演变
    lines.append("## 一、假设演变\n")
    for i, iteration in enumerate(chain.iterations, 1):
        lines.append(f"### V{iteration.hypothesis.version}\n")
        lines.append(f"{iteration.hypothesis.content}\n")
        lines.append(f"*评分: {iteration.score.total}/100*\n")
    
    # 疑点追踪
    lines.append("## 二、疑点追踪\n")
    lines.append("| ID | 类型 | 描述 | 状态 |\n")
    lines.append("|----|------|------|------|\n")
    for doubt in chain.all_doubts:
        lines.append(f"| {doubt.id} | {doubt.type.value} | {doubt.description[:30]}... | {doubt.status.value} |\n")
    
    # 证据来源
    lines.append("## 三、证据来源\n")
    lines.append("| ID | 来源 | 可信度 | 内容摘要 |\n")
    lines.append("|----|------|--------|----------|\n")
    for evidence in chain.all_evidences[:10]:  # 只显示前10条
        lines.append(f"| {evidence.id} | {evidence.source[:30]}... | {evidence.credibility.value} | {evidence.content[:50]}... |\n")
    
    # 最终结论
    lines.append("## 四、最终结论\n")
    if chain.final_hypothesis:
        lines.append(chain.final_hypothesis.content)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="V5.0 迭代式辩证分析")
    parser.add_argument("--company", "-c", required=True, help="公司名称或代码")
    parser.add_argument("--output", "-o", default="reports/v5", help="输出目录")
    parser.add_argument("--max-iterations", "-m", type=int, default=15, help="最大迭代次数")
    parser.add_argument("--score-threshold", "-s", type=int, default=85, help="评分终止阈值")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置环境变量
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ.setdefault(key, value)
    
    print(f"\n{'='*60}")
    print(f"V5.0 迭代式辩证分析")
    print(f"目标公司: {args.company}")
    print(f"最大轮数: {args.max_iterations}")
    print(f"评分阈值: {args.score_threshold}")
    print(f"{'='*60}\n")
    
    # 执行分析
    config = {
        "max_iterations": args.max_iterations,
        "score_threshold": args.score_threshold,
    }
    
    analyzer = IterativeDialecticalAnalyzer(config)
    chain = analyzer.analyze(args.company)
    
    # 保存结果
    json_path, md_path = save_analysis_result(chain, args.output)
    
    # 输出摘要
    print(f"\n{'='*60}")
    print("分析摘要")
    print(f"{'='*60}")
    print(f"总轮数: {chain.total_iterations}")
    print(f"最终评分: {chain.final_score.total}/100" if chain.final_score else "无评分")
    print(f"疑点解决率: {chain.resolution_rate:.1%}")
    print(f"\n最终假设:")
    if chain.final_hypothesis:
        print(chain.final_hypothesis.content)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())