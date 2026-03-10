"""
国际对比估值工具
与全球同行业龙头对比估值，判断当前估值是否合理
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


# 国际龙头公司配置（按行业分类）
INDUSTRY_LEADERS = {
    "医疗器械": {
        "domestic_example": "迈瑞医疗",
        "leaders": [
            {"name": "美敦力", "code": "MDT", "market": "US", "notes": "全球最大医疗器械公司"},
            {"name": "雅培", "code": "ABT", "market": "US", "notes": "诊断与医疗器械"},
            {"name": "西门子医疗", "code": "SIX.DE", "market": "DE", "notes": "影像设备"},
            {"name": "飞利浦", "code": "PHG", "market": "US", "notes": "医疗设备"},
        ]
    },
    "白酒": {
        "domestic_example": "贵州茅台",
        "leaders": [
            {"name": "帝亚吉欧", "code": "DEO", "market": "US", "notes": "全球最大烈酒公司"},
            {"name": "保乐力加", "code": "RI.PA", "market": "FR", "notes": "法国烈酒集团"},
            {"name": "百富门", "code": "BF-B", "market": "US", "notes": "美国烈酒公司"},
        ]
    },
    "银行": {
        "domestic_example": "招商银行",
        "leaders": [
            {"name": "摩根大通", "code": "JPM", "market": "US", "notes": "美国最大银行"},
            {"name": "美国银行", "code": "BAC", "market": "US", "notes": "美国第二大银行"},
            {"name": "汇丰控股", "code": "HSBC", "market": "HK", "notes": "国际银行"},
        ]
    },
    "新能源": {
        "domestic_example": "宁德时代",
        "leaders": [
            {"name": "特斯拉", "code": "TSLA", "market": "US", "notes": "电动汽车"},
            {"name": "LG新能源", "code": "373220.KS", "market": "KR", "notes": "电池"},
        ]
    },
    "半导体": {
        "domestic_example": "中芯国际",
        "leaders": [
            {"name": "台积电", "code": "TSM", "market": "US", "notes": "全球最大代工厂"},
            {"name": "英伟达", "code": "NVDA", "market": "US", "notes": "GPU龙头"},
            {"name": "英特尔", "code": "INTC", "market": "US", "notes": "CPU龙头"},
        ]
    },
    "互联网": {
        "domestic_example": "腾讯",
        "leaders": [
            {"name": "Meta", "code": "META", "market": "US", "notes": "社交媒体"},
            {"name": "Alphabet", "code": "GOOGL", "market": "US", "notes": "搜索与广告"},
            {"name": "亚马逊", "code": "AMZN", "market": "US", "notes": "电商与云"},
        ]
    }
}


def get_industry_leaders(industry: str) -> Optional[Dict[str, Any]]:
    """
    获取行业国际龙头公司列表
    
    Args:
        industry: 行业名称
    
    Returns:
        行业龙头配置
    """
    return INDUSTRY_LEADERS.get(industry)


def calculate_valuation_comparison(
    company_data: Dict[str, Any],
    peers_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    计算估值对比分析
    
    Args:
        company_data: 本公司数据
        peers_data: 对比公司数据列表
    
    Returns:
        对比分析结果
    """
    results = []
    
    company_pe = company_data.get("pe_ttm", 0)
    company_pb = company_data.get("pb", 0)
    company_roe = company_data.get("roe", 0)
    
    total_pe = 0
    total_pb = 0
    total_roe = 0
    valid_count = 0
    
    for peer in peers_data:
        if peer.get("pe_ttm") and peer["pe_ttm"] > 0:
            total_pe += peer["pe_ttm"]
            total_pb += peer.get("pb", 0)
            total_roe += peer.get("roe", 0)
            valid_count += 1
            
            # 计算折溢价
            pe_premium = (company_pe / peer["pe_ttm"] - 1) * 100 if company_pe > 0 else 0
            
            results.append({
                "name": peer.get("name"),
                "code": peer.get("code"),
                "market": peer.get("market"),
                "pe_ttm": peer.get("pe_ttm"),
                "pb": peer.get("pb"),
                "roe": peer.get("roe"),
                "pe_premium_vs_company": round(pe_premium, 1)
            })
    
    # 计算行业中位数
    median_pe = total_pe / valid_count if valid_count > 0 else 0
    median_pb = total_pb / valid_count if valid_count > 0 else 0
    median_roe = total_roe / valid_count if valid_count > 0 else 0
    
    # 计算相对估值
    relative_valuation = {}
    if median_pe > 0:
        relative_valuation["pe_vs_median"] = round((company_pe / median_pe - 1) * 100, 1)
        relative_valuation["pe_median"] = round(median_pe, 1)
    if median_pb > 0:
        relative_valuation["pb_vs_median"] = round((company_pb / median_pb - 1) * 100, 1)
        relative_valuation["pb_median"] = round(median_pb, 1)
    
    # 估值判断
    valuation_verdict = _get_valuation_verdict(relative_valuation, company_roe, median_roe)
    
    return {
        "company": {
            "name": company_data.get("name"),
            "pe_ttm": company_pe,
            "pb": company_pb,
            "roe": company_roe
        },
        "peers": results,
        "median": {
            "pe_ttm": round(median_pe, 1) if median_pe else None,
            "pb": round(median_pb, 1) if median_pb else None,
            "roe": round(median_roe, 1) if median_roe else None
        },
        "relative_valuation": relative_valuation,
        "verdict": valuation_verdict,
        "analyzed_at": datetime.now().isoformat()
    }


def _get_valuation_verdict(relative: Dict, company_roe: float, median_roe: float) -> Dict[str, Any]:
    """判断估值是否合理"""
    pe_vs_median = relative.get("pe_vs_median", 0)
    pb_vs_median = relative.get("pb_vs_median", 0)
    
    # ROE 支撑判断
    roe_support = company_roe > median_roe * 1.2 if median_roe > 0 else False
    
    verdict = {
        "status": "合理",
        "reason": "",
        "risk_level": "低"
    }
    
    # PE 折价
    if pe_vs_median < -30:
        verdict["status"] = "可能低估"
        verdict["reason"] = f"PE 较行业中位数折价 {abs(pe_vs_median):.1f}%"
        verdict["risk_level"] = "低"
    # PE 溢价
    elif pe_vs_median > 30:
        if roe_support:
            verdict["status"] = "溢价合理"
            verdict["reason"] = f"PE 溢价 {pe_vs_median:.1f}%，但 ROE 高于行业，估值有支撑"
            verdict["risk_level"] = "中"
        else:
            verdict["status"] = "可能高估"
            verdict["reason"] = f"PE 较行业中位数溢价 {pe_vs_median:.1f}%，且 ROE 无明显优势"
            verdict["risk_level"] = "高"
    else:
        verdict["reason"] = f"PE 与行业相当（偏差 {pe_vs_median:.1f}%），估值合理"
    
    return verdict


def generate_comparison_table(comparison: Dict[str, Any]) -> str:
    """生成 Markdown 对比表格"""
    md = """
### 国际对比估值

| 对比项 | 本公司 | """
    
    # 添加对比公司列
    peers = comparison.get("peers", [])
    for peer in peers[:3]:
        md += f"{peer['name']} | "
    md += "行业中位数 |\n"
    
    md += "|--------|--------|"
    for _ in peers[:3]:
        md += "--------|"
    md += "--------|\n"
    
    # PE 行
    company = comparison.get("company", {})
    median = comparison.get("median", {})
    md += f"| PE(TTM) | {company.get('pe_ttm', 'N/A')} | "
    for peer in peers[:3]:
        md += f"{peer.get('pe_ttm', 'N/A')} | "
    md += f"{median.get('pe_ttm', 'N/A')} |\n"
    
    # PB 行
    md += f"| PB | {company.get('pb', 'N/A')} | "
    for peer in peers[:3]:
        md += f"{peer.get('pb', 'N/A')} | "
    md += f"{median.get('pb', 'N/A')} |\n"
    
    # ROE 行
    md += f"| ROE(%) | {company.get('roe', 'N/A')} | "
    for peer in peers[:3]:
        md += f"{peer.get('roe', 'N/A')} | "
    md += f"{median.get('roe', 'N/A')} |\n"
    
    # 结论
    verdict = comparison.get("verdict", {})
    md += f"""
**估值判断**：{verdict.get('status', 'N/A')}

**原因**：{verdict.get('reason', 'N/A')}

**风险等级**：{verdict.get('risk_level', 'N/A')}
"""
    
    return md


# 测试
if __name__ == '__main__':
    # 测试迈瑞医疗对比
    company_data = {
        "name": "迈瑞医疗",
        "pe_ttm": 24,
        "pb": 5.5,
        "roe": 28
    }
    
    peers_data = [
        {"name": "美敦力", "code": "MDT", "market": "US", "pe_ttm": 25, "pb": 3.2, "roe": 12},
        {"name": "雅培", "code": "ABT", "market": "US", "pe_ttm": 28, "pb": 4.5, "roe": 15},
        {"name": "西门子医疗", "code": "SIX.DE", "market": "DE", "pe_ttm": 22, "pb": 3.8, "roe": 18},
    ]
    
    result = calculate_valuation_comparison(company_data, peers_data)
    print(generate_comparison_table(result))