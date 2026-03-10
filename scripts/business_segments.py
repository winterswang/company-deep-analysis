"""
业务结构数据获取工具
从年报或其他数据源提取业务分部数据

注意：当前 AkShare 不提供业务结构数据，需要从以下来源获取：
1. 年报 PDF 解析（推荐）
2. TuShare pro.fina_indicator 部分字段
3. 东方财富 Choice API
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


# 业务结构模板（需手动填充或从年报解析）
BUSINESS_SEGMENT_TEMPLATE = {
    "code": "",
    "year": 2024,
    "source": "年报解析",
    "source_detail": "年报第XX页",
    "segments": [
        {
            "name": "业务名称",
            "revenue": {"value": 0, "unit": "亿元", "yoy_growth": None},
            "cost": {"value": 0, "unit": "亿元"},
            "gross_profit": {"value": 0, "unit": "亿元"},
            "gross_margin": None,
            "revenue_share": None,
            "notes": ""
        }
    ],
    "total_revenue": {"value": 0, "unit": "亿元"},
    "reconciliation_note": "各分部收入之和等于合并营收"
}


# 已知的业务结构数据（手动维护）
KNOWN_BUSINESS_SEGMENTS = {
    "300760": {  # 迈瑞医疗
        "company_name": "迈瑞医疗",
        "segments_2024": [
            {
                "name": "体外诊断",
                "revenue_value": 137.65,
                "yoy_growth": 10.2,
                "gross_margin": 65.5,
                "revenue_share": 37.5
            },
            {
                "name": "生命信息与支持",
                "revenue_value": 135.57,
                "yoy_growth": 5.3,
                "gross_margin": 62.0,
                "revenue_share": 36.9
            },
            {
                "name": "医学影像",
                "revenue_value": 74.84,
                "yoy_growth": -2.0,
                "gross_margin": 60.0,
                "revenue_share": 20.4
            },
            {
                "name": "其他",
                "revenue_value": 19.20,
                "yoy_growth": None,
                "gross_margin": None,
                "revenue_share": 5.2
            }
        ],
        "source": "2024年年报第18页"
    },
    "600519": {  # 贵州茅台
        "company_name": "贵州茅台",
        "segments_2024": [
            {
                "name": "茅台酒",
                "revenue_value": 1459.0,
                "yoy_growth": 15.0,
                "gross_margin": 94.0,
                "revenue_share": 85.0
            },
            {
                "name": "系列酒",
                "revenue_value": 200.0,
                "yoy_growth": 20.0,
                "gross_margin": 80.0,
                "revenue_share": 12.0
            }
        ],
        "source": "2024年年报第XX页"
    }
}


def get_business_segments(code: str, year: int = 2024) -> Dict[str, Any]:
    """
    获取业务结构数据
    
    Args:
        code: 股票代码
        year: 年份
    
    Returns:
        业务结构数据
    """
    # 检查是否有已知数据
    if code in KNOWN_BUSINESS_SEGMENTS:
        known = KNOWN_BUSINESS_SEGMENTS[code]
        segments = []
        
        for seg in known.get(f"segments_{year}", known.get("segments_2024", [])):
            segments.append({
                "name": seg["name"],
                "revenue": {
                    "value": seg["revenue_value"],
                    "unit": "亿元",
                    "yoy_growth": seg.get("yoy_growth")
                },
                "gross_margin": seg.get("gross_margin"),
                "revenue_share": seg.get("revenue_share"),
                "notes": seg.get("notes", "")
            })
        
        return {
            "code": code,
            "company_name": known.get("company_name", ""),
            "year": year,
            "source": known.get("source", "手动维护"),
            "segments": segments,
            "fetched_at": datetime.now().isoformat(),
            "data_quality": "高" if known.get("source") else "待验证"
        }
    
    # 没有已知数据，返回模板
    return {
        "code": code,
        "year": year,
        "source": "待获取",
        "segments": [],
        "fetched_at": datetime.now().isoformat(),
        "data_quality": "无数据",
        "instructions": [
            "1. 从公司年报「管理层讨论与分析」章节获取",
            "2. 查找「主营业务分析」或「收入成本分析」表格",
            "3. 提取各业务线的收入、成本、毛利率",
            "4. 计算各业务线收入占比"
        ]
    }


def calculate_segment_metrics(segments: List[Dict]) -> Dict[str, Any]:
    """
    计算业务结构指标
    
    Args:
        segments: 业务分部列表
    
    Returns:
        计算结果
    """
    total_revenue = sum(s.get("revenue", {}).get("value", 0) for s in segments)
    
    results = []
    for seg in segments:
        revenue = seg.get("revenue", {}).get("value", 0)
        share = (revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        results.append({
            "name": seg["name"],
            "revenue": seg.get("revenue"),
            "gross_margin": seg.get("gross_margin"),
            "revenue_share": round(share, 1),
            "yoy_growth": seg.get("revenue", {}).get("yoy_growth")
        })
    
    return {
        "segments": results,
        "total_revenue": round(total_revenue, 2),
        "segment_count": len(segments),
        "top_segment": results[0]["name"] if results else None,
        "concentration_hhi": _calculate_hhi(results)  # 赫芬达尔指数
    }


def _calculate_hhi(segments: List[Dict]) -> float:
    """
    计算赫芬达尔指数（市场集中度）
    
    HHI = Σ(市场份额)²
    
    HHI > 2500: 高度集中
    1500 < HHI < 2500: 中度集中
    HHI < 1500: 低度集中
    """
    hhi = sum((s.get("revenue_share", 0) ** 2) for s in segments)
    return round(hhi, 0)


def generate_segment_table(data: Dict[str, Any]) -> str:
    """生成业务结构 Markdown 表格"""
    if not data.get("segments"):
        return f"""
### 业务结构分析

**数据来源**：{data.get('source', '待获取')}

⚠️ 暂无业务结构数据，请从年报获取：

{chr(10).join(data.get('instructions', []))}
"""
    
    segments = data["segments"]
    metrics = calculate_segment_metrics(segments)
    
    md = f"""
### 业务结构分析

**数据来源**：{data.get('source', 'N/A')}

| 业务名称 | 收入(亿元) | 同比增长 | 毛利率 | 收入占比 |
|----------|-----------|----------|--------|----------|
"""
    
    for seg in metrics["segments"]:
        revenue = seg.get("revenue", {})
        yoy = revenue.get('yoy_growth')
        yoy_str = f"{yoy}%" if yoy is not None else "N/A"
        gm = seg.get('gross_margin')
        gm_str = f"{gm}%" if gm is not None else "N/A"
        md += f"| {seg['name']} | {revenue.get('value', 'N/A')} | {yoy_str} | {gm_str} | {seg['revenue_share']}% |\n"
    
    md += f"""
**业务集中度**：赫芬达尔指数 {metrics['concentration_hhi']} ({'高度集中' if metrics['concentration_hhi'] > 2500 else '中度集中' if metrics['concentration_hhi'] > 1500 else '低度集中'})

**最大业务线**：{metrics['top_segment']}（占比 {metrics['segments'][0]['revenue_share']}%）
"""
    
    return md


def add_business_segment_data(
    code: str,
    year: int,
    segments: List[Dict],
    source: str
) -> Dict[str, Any]:
    """
    添加业务结构数据（手动维护用）
    
    Args:
        code: 股票代码
        year: 年份
        segments: 业务分部数据
        source: 数据来源
    
    Returns:
        添加结果
    """
    global KNOWN_BUSINESS_SEGMENTS
    
    if code not in KNOWN_BUSINESS_SEGMENTS:
        KNOWN_BUSINESS_SEGMENTS[code] = {}
    
    KNOWN_BUSINESS_SEGMENTS[code][f"segments_{year}"] = segments
    KNOWN_BUSINESS_SEGMENTS[code]["source"] = source
    
    return {
        "success": True,
        "code": code,
        "year": year,
        "segments_added": len(segments),
        "message": f"已添加 {code} {year}年业务结构数据"
    }


# 测试
if __name__ == '__main__':
    # 测试迈瑞医疗
    data = get_business_segments("300760", year=2024)
    print(generate_segment_table(data))
    
    # 测试未知公司
    print("\n" + "="*50)
    data2 = get_business_segments("000001", year=2024)
    print(generate_segment_table(data2))