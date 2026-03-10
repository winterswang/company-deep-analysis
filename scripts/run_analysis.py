#!/usr/bin/env python3
"""
Company Deep Analysis Runner
调用 DeerFlow 或直接执行 V4.2 分析
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# 项目路径
SKILL_DIR = Path(__file__).parent.parent
AKSHARE_SERVICE = SKILL_DIR / "akshare_service"

def get_financial_data(company: str) -> dict:
    """获取财务数据"""
    # 添加 akshare_service 到路径
    sys.path.insert(0, str(SKILL_DIR))
    
    from akshare_service.skills.financial_summary import get_financial_summary
    from akshare_service.skills.cashflow import get_cashflow_data
    from akshare_service.skills.valuation import get_valuation_data
    
    # 尝试获取数据
    try:
        fin = get_financial_summary(company, years=5, use_cache=True)
        cf = get_cashflow_data(company, years=5, use_cache=True)
        val = get_valuation_data(company)
        
        return {
            "financial": fin,
            "cashflow": cf,
            "valuation": val,
            "success": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def run_deerflow_analysis(company: str) -> dict:
    """通过 DeerFlow API 运行分析"""
    import requests
    
    # DeerFlow API 端点
    DEERFLOW_URL = "http://localhost:2024/api/chat"
    
    prompt = f"""
请使用 company-deep-analysis skill 对 {company} 进行 V4.2 辩证分析。

分析要求：
1. 严格按照 SKILL.md 中的六轮辩证推导框架
2. 所有数据必须标注来源
3. 禁止使用 model_hallucination 级别的数据
4. 输出完整的投资决策报告
"""
    
    try:
        response = requests.post(
            DEERFLOW_URL,
            json={"message": prompt},
            timeout=300
        )
        return {
            "success": True,
            "result": response.json()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="Company Deep Analysis V4.2")
    parser.add_argument("--company", required=True, help="公司名称或股票代码")
    parser.add_argument("--mode", choices=["deerflow", "direct"], default="direct", 
                        help="运行模式：deerflow（通过API）或 direct（直接执行）")
    parser.add_argument("--output", choices=["json", "markdown", "gist"], default="markdown",
                        help="输出格式")
    args = parser.parse_args()
    
    print(f"=== Company Deep Analysis V4.2 ===")
    print(f"目标公司: {args.company}")
    print(f"运行模式: {args.mode}")
    print()
    
    if args.mode == "deerflow":
        # 通过 DeerFlow API 运行
        result = run_deerflow_analysis(args.company)
    else:
        # 直接获取数据
        print("正在获取财务数据...")
        result = get_financial_data(args.company)
        
        if result["success"]:
            print("✓ 财务数据获取成功")
            print()
            print("=== 数据预览 ===")
            if result["financial"]["annual_data"]:
                latest = result["financial"]["annual_data"][0]
                print(f"最新年度: {latest['year']}")
                print(f"营收: {latest['revenue']['value']} {latest['revenue']['unit']}")
                print(f"净利润: {latest['net_profit']['value']} {latest['net_profit']['unit']}")
                print(f"ROE: {latest['roe']['value']}%")
                print(f"毛利率: {latest['gross_margin']['value']}%")
            
            if args.output == "json":
                print()
                print("=== 完整数据 (JSON) ===")
                print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"✗ 数据获取失败: {result['error']}")
            print()
            print("提示：请确保股票代码正确，或尝试使用中文名称")
    
    return result

if __name__ == "__main__":
    main()