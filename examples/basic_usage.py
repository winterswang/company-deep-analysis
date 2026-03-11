#!/usr/bin/env python3
"""
使用示例：护城河辩证分析

演示如何使用 Company Deep Analysis Skill 进行三层辩证分析。
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.moat_dialectical_analyzer import MoatDialecticalAnalyzer


def example_basic_analysis():
    """基础分析示例"""
    print("=" * 60)
    print("示例1：基础护城河辩证分析")
    print("=" * 60)
    
    # 创建分析器
    analyzer = MoatDialecticalAnalyzer()
    
    # 准备财务数据（迈瑞医疗示例）
    financial_data = {
        "roe": 28.6,
        "gross_margin": 63.1,
        "asset_turnover": 0.8,
        "rd_ratio": 10.2,
        "industry_roe": 15,
        "years_stable": 8,
        "competitor_gap": 15,
        "one_time_income": 0.02,
        "tech_disruption_risk": 0.2,
        "competition_intensity": 0.5,
        "consumer_change": 0.3,
        "gross_margin_trend": -0.02,
        "market_share_trend": 0.01,
        "revenue_growth": 0.05,
        "rd_trend": 0.08,
        "user_growth": 0,
        "marketing_ratio": 0.12
    }
    
    # 生成评估报告
    report = analyzer.generate_assessment_report(financial_data, "迈瑞医疗")
    print(report)


def example_layer_analysis():
    """分层分析示例"""
    print("\n" + "=" * 60)
    print("示例2：分层详细分析")
    print("=" * 60)
    
    analyzer = MoatDialecticalAnalyzer()
    
    # 任天堂示例数据
    financial_data = {
        "roe": 20.0,
        "gross_margin": 50.9,
        "asset_turnover": 0.6,
        "rd_ratio": 5.0,
        "industry_roe": 12,
        "years_stable": 6,
        "competitor_gap": 20,
        "one_time_income": 0.05,
        "tech_disruption_risk": 0.3,
        "competition_intensity": 0.6,
        "consumer_change": 0.4,
        "gross_margin_trend": -0.05,
        "market_share_trend": -0.02,
        "revenue_growth": -0.10,
        "rd_trend": 0.02,
        "user_growth": 0,
        "marketing_ratio": 0.08
    }
    
    # 第二层：护城河本质辩证
    print("\n--- 第二层：护城河本质辩证 ---")
    layer2 = analyzer.analyze_layer2_reality(financial_data)
    print(f"护城河类型: {layer2['moat_type'].value}")
    print(f"真实性评分: {layer2['reality_score']:.1f}")
    print(f"真实性等级: {layer2['reality_grade'].value}")
    print(f"边界条件: {', '.join(layer2['boundary_conditions'])}")
    
    # 第三层：护城河延续性辩证
    print("\n--- 第三层：护城河延续性辩证 ---")
    layer3 = analyzer.analyze_layer3_continuity(
        financial_data,
        layer2['moat_type'],
        layer2['reality_score']
    )
    print(f"延续性评分: {layer3['continuity_score']:.1f}")
    print(f"延续性等级: {layer3['continuity_grade'].value}")
    print(f"预警等级: {layer3['warning_level'].value}")
    print(f"侵蚀评分: {layer3['erosion_score']:.1f}")
    print(f"强化评分: {layer3['strengthening_score']:.1f}")


def example_warning_levels():
    """预警等级示例"""
    print("\n" + "=" * 60)
    print("示例3：不同预警等级场景")
    print("=" * 60)
    
    analyzer = MoatDialecticalAnalyzer()
    
    scenarios = [
        {
            "name": "绿色预警（健康）",
            "data": {
                "roe": 30, "gross_margin": 60, "asset_turnover": 1.0, "rd_ratio": 10,
                "industry_roe": 12, "years_stable": 10, "competitor_gap": 25,
                "one_time_income": 0.01, "tech_disruption_risk": 0.1,
                "competition_intensity": 0.3, "consumer_change": 0.1,
                "gross_margin_trend": 0.02, "market_share_trend": 0.03,
                "revenue_growth": 0.15, "rd_trend": 0.1, "user_growth": 0.1,
                "marketing_ratio": 0.15
            }
        },
        {
            "name": "黄色预警（关注）",
            "data": {
                "roe": 20, "gross_margin": 45, "asset_turnover": 0.8, "rd_ratio": 5,
                "industry_roe": 15, "years_stable": 5, "competitor_gap": 10,
                "one_time_income": 0.05, "tech_disruption_risk": 0.3,
                "competition_intensity": 0.5, "consumer_change": 0.3,
                "gross_margin_trend": -0.02, "market_share_trend": -0.01,
                "revenue_growth": 0.03, "rd_trend": 0.02, "user_growth": 0,
                "marketing_ratio": 0.08
            }
        },
        {
            "name": "红色预警（危险）",
            "data": {
                "roe": 8, "gross_margin": 20, "asset_turnover": 0.4, "rd_ratio": 1,
                "industry_roe": 15, "years_stable": 1, "competitor_gap": 2,
                "one_time_income": 0.3, "tech_disruption_risk": 0.7,
                "competition_intensity": 0.9, "consumer_change": 0.6,
                "gross_margin_trend": -0.10, "market_share_trend": -0.08,
                "revenue_growth": -0.15, "rd_trend": -0.05, "user_growth": -0.20,
                "marketing_ratio": 0.02
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        report = analyzer.generate_assessment_report(scenario['data'], scenario['name'])
        # 只输出预警等级
        lines = report.split('\n')
        for line in lines:
            if '预警等级' in line or '综合判断' in line:
                print(line)


if __name__ == "__main__":
    # 运行所有示例
    example_basic_analysis()
    example_layer_analysis()
    example_warning_levels()
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)