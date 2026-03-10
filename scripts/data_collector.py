#!/usr/bin/env python3
"""
公司深度分析 - 数据收集器 V2.0
整合 AkShare 标准化接口，支持多数据源路由

使用方法：
    python data_collector.py --code 300760 --output /tmp/data.json
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# 添加 AkShare 标准化接口路径（优先级最高）
AKSHARE_DOCS_PATH = Path("/root/.openclaw/workspace/akshare_docs")
if AKSHARE_DOCS_PATH.exists():
    sys.path.insert(0, str(AKSHARE_DOCS_PATH))
    print(f"[DEBUG] 添加路径: {AKSHARE_DOCS_PATH}")

# 本地 akshare_service（容器内）
SCRIPT_DIR = Path(__file__).parent.parent
LOCAL_AKSHARE = SCRIPT_DIR / "akshare_service"
if LOCAL_AKSHARE.exists():
    sys.path.insert(0, str(SCRIPT_DIR))
    print(f"[DEBUG] 添加路径: {SCRIPT_DIR}")

# 调试输出
print(f"[DEBUG] sys.path 前3项: {sys.path[:3]}")

# 尝试导入标准化接口
try:
    from akshare_service.skills.financial_summary import get_financial_summary
    from akshare_service.skills.cashflow import get_cashflow_data
    from akshare_service.skills.finance import calculate_roic
    from akshare_service.skills.market import get_current_price
    STANDARDIZED_API_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] AkShare 标准化接口不可用: {e}")
    STANDARDIZED_API_AVAILABLE = False


def collect_company_data(code: str, years: int = 5, use_cache: bool = True) -> Dict[str, Any]:
    """收集公司完整数据（标准化输出）"""
    result = {
        "code": code,
        "timestamp": datetime.now().isoformat(),
        "financials": None,
        "cashflow": None,
        "roic": None,
        "valuation": None,
        "dividend_ratio": None,
        "errors": []
    }
    
    if not STANDARDIZED_API_AVAILABLE:
        result["errors"].append("AkShare 标准化接口不可用")
        return result
    
    # 1. 获取财务指标
    print(f"[INFO] 获取财务指标 ({years}年)...")
    try:
        financials = get_financial_summary(code, years=years, use_cache=use_cache)
        if financials.get('annual_data'):
            result["financials"] = financials
            print(f"[OK] 来源: {financials.get('source')}, {len(financials['annual_data'])}年")
    except Exception as e:
        result["errors"].append(f"财务指标异常: {e}")
    
    # 2. 获取现金流
    print(f"[INFO] 获取现金流...")
    try:
        cashflow = get_cashflow_data(code, years=years, use_cache=use_cache)
        if cashflow.get('annual_data'):
            result["cashflow"] = cashflow
            print(f"[OK] 来源: {cashflow.get('source')}")
    except Exception as e:
        result["errors"].append(f"现金流异常: {e}")
    
    # 3. ROIC
    print(f"[INFO] 获取 ROIC...")
    try:
        import pandas as pd
        roic_df = calculate_roic("A股", code, years=years)
        if roic_df is not None and not roic_df.empty:
            result["roic"] = {
                "source": "AkShare.calculate_roic",
                "data": roic_df.to_dict('records') if hasattr(roic_df, 'to_dict') else []
            }
            print(f"[OK] ROIC: {len(roic_df)}年")
    except Exception as e:
        result["errors"].append(f"ROIC异常: {e}")
    
    # 4. 估值
    print(f"[INFO] 获取估值...")
    try:
        valuation = get_current_price("A股", code)
        if valuation and not valuation.get('error'):
            result["valuation"] = {
                "source": "AkShare.get_current_price",
                "data": valuation
            }
            print(f"[OK] PE={valuation.get('pe', 'N/A')}")
    except Exception as e:
        result["errors"].append(f"估值异常: {e}")
    
    return result


def print_summary(data: Dict[str, Any]):
    """打印数据摘要"""
    print("\n" + "="*50)
    print(f"📊 {data['code']} 数据摘要")
    print("="*50)
    
    if data.get("financials") and data["financials"].get("annual_data"):
        print(f"\n📈 财务指标 ({data['financials'].get('source')})")
        for d in data["financials"]["annual_data"][-3:]:
            print(f"   {d['year']}: 营收{d['revenue']['value']}亿, 净利{d['net_profit']['value']}亿")
    
    if data.get("cashflow") and data["cashflow"].get("annual_data"):
        print(f"\n💵 现金流 ({data['cashflow'].get('source')})")
        for d in data["cashflow"]["annual_data"][-2:]:
            print(f"   {d['year']}: FCF {d['free_cashflow']['value']}亿")
    
    if data.get("errors"):
        print(f"\n⚠️ 错误: {len(data['errors'])}个")
        for e in data["errors"][:2]:
            print(f"   - {e}")
    
    print("\n" + "="*50)


def generate_data_sources_table(data: Dict[str, Any]) -> str:
    """生成数据来源表格"""
    sources = []
    if data.get("financials"):
        sources.append(("财务指标", data["financials"].get("source", "N/A")))
    if data.get("cashflow"):
        sources.append(("现金流", data["cashflow"].get("source", "N/A")))
    if data.get("roic"):
        sources.append(("ROIC", data["roic"].get("source", "N/A")))
    
    table = "\n## 数据来源\n\n| 数据项 | 来源 |\n|--------|------|\n"
    for item, source in sources:
        table += f"| {item} | {source} |\n"
    return table


def main():
    parser = argparse.ArgumentParser(description="公司数据收集器 V2.0")
    parser.add_argument("--code", "-c", required=True, help="股票代码")
    parser.add_argument("--years", "-y", type=int, default=5)
    parser.add_argument("--output", "-o", help="输出文件")
    parser.add_argument("--no-cache", action="store_true")
    
    args = parser.parse_args()
    
    data = collect_company_data(args.code, years=args.years, use_cache=not args.no_cache)
    print_summary(data)
    print(generate_data_sources_table(data))
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n[OK] 保存到: {args.output}")
    
    print("\n--- JSON ---")
    print(json.dumps(data, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()