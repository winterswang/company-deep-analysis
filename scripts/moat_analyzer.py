"""
护城河趋势分析工具
通过财务数据变化透视竞争优势变化，判断护城河状态
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime


def analyze_roe_trend(annual_data: List[Dict]) -> Dict[str, Any]:
    """
    分析 ROE 趋势，诊断竞争优势变化
    
    Args:
        annual_data: 年度财务数据列表
    
    Returns:
        ROE 趋势分析结果
    """
    if len(annual_data) < 2:
        return {"error": "数据不足"}
    
    # 提取 ROE 数据
    roe_values = []
    for d in annual_data:
        roe = d.get("roe", {}).get("value")
        if roe:
            roe_values.append({"year": d["year"], "roe": roe})
    
    if len(roe_values) < 2:
        return {"error": "ROE 数据不足"}
    
    # 计算变化
    latest = roe_values[0]
    prev = roe_values[1]
    change = latest["roe"] - prev["roe"]
    
    # 判断趋势
    if change > 2:
        trend = "上升"
        moat_signal = "护城河可能强化"
    elif change < -2:
        trend = "下降"
        moat_signal = "⚠️ 护城河可能被侵蚀"
    else:
        trend = "稳定"
        moat_signal = "护城河稳定"
    
    # 需要进一步分析的原因
    questions = []
    if change < -2:
        questions.extend([
            "净利率是否下降？→ 定价权或成本优势",
            "资产周转率是否下降？→ 运营效率或资产质量",
            "杠杆是否变化？→ 财务策略调整"
        ])
    
    return {
        "latest_roe": latest["roe"],
        "prev_roe": prev["roe"],
        "change": round(change, 2),
        "trend": trend,
        "moat_signal": moat_signal,
        "questions": questions
    }


def analyze_margin_trend(annual_data: List[Dict]) -> Dict[str, Any]:
    """
    分析毛利率趋势，诊断定价权和成本优势
    """
    if len(annual_data) < 2:
        return {"error": "数据不足"}
    
    # 提取毛利率数据
    margin_values = []
    for d in annual_data:
        gm = d.get("gross_margin", {}).get("value")
        nm = d.get("net_margin", {}).get("value")
        if gm:
            margin_values.append({
                "year": d["year"], 
                "gross_margin": gm,
                "net_margin": nm
            })
    
    if len(margin_values) < 2:
        return {"error": "毛利率数据不足"}
    
    # 计算变化
    latest = margin_values[0]
    prev = margin_values[1]
    gm_change = latest["gross_margin"] - prev["gross_margin"]
    
    # 判断趋势
    if gm_change > 1:
        trend = "上升"
        moat_signal = "定价权增强或成本优势强化"
    elif gm_change < -1:
        trend = "下降"
        moat_signal = "⚠️ 定价权削弱或成本上升"
    else:
        trend = "稳定"
        moat_signal = "毛利率稳定"
    
    # 分析原因
    possible_reasons = []
    if gm_change < -1:
        possible_reasons = [
            "集采降价 → 定价权被削弱",
            "竞争加剧/价格战 → 定价权被削弱",
            "原材料成本上升 → 成本转嫁能力弱",
            "产品结构变化 → 低毛利产品占比提升"
        ]
    
    return {
        "latest_gross_margin": latest["gross_margin"],
        "prev_gross_margin": prev["gross_margin"],
        "change": round(gm_change, 2),
        "trend": trend,
        "moat_signal": moat_signal,
        "possible_reasons": possible_reasons
    }


def analyze_growth_trend(annual_data: List[Dict]) -> Dict[str, Any]:
    """
    分析增速趋势，诊断竞争地位变化
    """
    if len(annual_data) < 2:
        return {"error": "数据不足"}
    
    # 提取增速数据
    growth_values = []
    for d in annual_data:
        yoy = d.get("revenue", {}).get("yoy_growth")
        if yoy is not None:
            growth_values.append({"year": d["year"], "yoy_growth": yoy})
    
    if len(growth_values) < 1:
        return {"error": "增速数据不足"}
    
    latest = growth_values[0]
    
    # 判断增速水平
    if latest["yoy_growth"] > 15:
        level = "高增长"
        moat_signal = "竞争优势强"
    elif latest["yoy_growth"] > 5:
        level = "中速增长"
        moat_signal = "竞争优势稳定"
    elif latest["yoy_growth"] > 0:
        level = "低速增长"
        moat_signal = "⚠️ 竞争优势可能弱化"
    else:
        level = "负增长"
        moat_signal = "⚠️ 竞争优势被侵蚀"
    
    return {
        "latest_yoy_growth": latest["yoy_growth"],
        "level": level,
        "moat_signal": moat_signal
    }


def analyze_fcf_quality(cashflow_data: List[Dict], financial_data: List[Dict]) -> Dict[str, Any]:
    """
    分析 FCF 质量，判断盈利质量
    """
    if not cashflow_data or not financial_data:
        return {"error": "数据不足"}
    
    # 提取 FCF/净利润
    fcf_ratios = []
    for cf in cashflow_data:
        year = cf["year"]
        fcf = cf.get("free_cashflow", {}).get("value", 0)
        
        # 找对应年份的净利润
        for fin in financial_data:
            if fin["year"] == year:
                net_profit = fin.get("net_profit", {}).get("value", 0)
                if net_profit > 0:
                    ratio = (fcf / net_profit) * 100
                    fcf_ratios.append({"year": year, "ratio": round(ratio, 2)})
    
    if not fcf_ratios:
        return {"error": "FCF/净利润数据不足"}
    
    latest = fcf_ratios[0]
    
    # 判断质量
    if latest["ratio"] > 80:
        quality = "优秀"
        moat_signal = "盈利质量高，护城河稳固"
    elif latest["ratio"] > 50:
        quality = "良好"
        moat_signal = "盈利质量中等"
    else:
        quality = "警惕"
        moat_signal = "⚠️ 盈利质量差"
    
    return {
        "latest_fcf_ratio": latest["ratio"],
        "quality": quality,
        "moat_signal": moat_signal
    }


def overall_moat_assessment(
    roe_analysis: Dict,
    margin_analysis: Dict,
    growth_analysis: Dict,
    fcf_analysis: Dict
) -> Dict[str, Any]:
    """
    综合护城河评估
    """
    # 计算信号数量
    warning_count = 0
    positive_count = 0
    
    for analysis in [roe_analysis, margin_analysis, growth_analysis, fcf_analysis]:
        signal = analysis.get("moat_signal", "")
        if "⚠️" in signal:
            warning_count += 1
        elif "强化" in signal or "稳固" in signal or "强" in signal:
            positive_count += 1
    
    # 综合判断
    if warning_count >= 2:
        status = "被侵蚀"
        confidence = "高" if warning_count >= 3 else "中"
        action = "建议减仓或退出"
    elif warning_count == 1:
        status = "边际弱化"
        confidence = "中"
        action = "密切监控，控制仓位"
    else:
        status = "稳固"
        confidence = "高" if positive_count >= 3 else "中"
        action = "可持有或加仓"
    
    return {
        "status": status,
        "confidence": confidence,
        "warning_count": warning_count,
        "positive_count": positive_count,
        "action": action,
        "analyzed_at": datetime.now().isoformat()
    }


def generate_moat_report(
    financial_data: List[Dict],
    cashflow_data: List[Dict]
) -> str:
    """
    生成护城河分析报告
    """
    # 执行各项分析
    roe_analysis = analyze_roe_trend(financial_data)
    margin_analysis = analyze_margin_trend(financial_data)
    growth_analysis = analyze_growth_trend(financial_data)
    fcf_analysis = analyze_fcf_quality(cashflow_data, financial_data)
    
    # 综合评估
    overall = overall_moat_assessment(
        roe_analysis, margin_analysis, growth_analysis, fcf_analysis
    )
    
    # 生成报告
    report = f"""
## 护城河趋势分析报告

### 综合评估

**护城河状态**: {overall['status']}
**置信度**: {overall['confidence']}
**建议行动**: {overall['action']}

---

### 详细分析

#### 1. ROE 趋势分析

| 指标 | 数值 |
|------|------|
| 最新 ROE | {roe_analysis.get('latest_roe', 'N/A')}% |
| 前期 ROE | {roe_analysis.get('prev_roe', 'N/A')}% |
| 变化 | {roe_analysis.get('change', 'N/A')}个百分点 |
| 趋势 | {roe_analysis.get('trend', 'N/A')} |
| **信号** | {roe_analysis.get('moat_signal', 'N/A')} |

#### 2. 毛利率趋势分析

| 指标 | 数值 |
|------|------|
| 最新毛利率 | {margin_analysis.get('latest_gross_margin', 'N/A')}% |
| 前期毛利率 | {margin_analysis.get('prev_gross_margin', 'N/A')}% |
| 变化 | {margin_analysis.get('change', 'N/A')}个百分点 |
| 趋势 | {margin_analysis.get('trend', 'N/A')} |
| **信号** | {margin_analysis.get('moat_signal', 'N/A')} |

#### 3. 增速趋势分析

| 指标 | 数值 |
|------|------|
| 最新营收增速 | {growth_analysis.get('latest_yoy_growth', 'N/A')}% |
| 增速水平 | {growth_analysis.get('level', 'N/A')} |
| **信号** | {growth_analysis.get('moat_signal', 'N/A')} |

#### 4. 现金流质量分析

| 指标 | 数值 |
|------|------|
| FCF/净利润 | {fcf_analysis.get('latest_fcf_ratio', 'N/A')}% |
| 质量 | {fcf_analysis.get('quality', 'N/A')} |
| **信号** | {fcf_analysis.get('moat_signal', 'N/A')} |

---

*分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    return report


# 测试
if __name__ == '__main__':
    # 测试数据（迈瑞医疗）
    financial_data = [
        {"year": 2024, "roe": {"value": 28.63}, "gross_margin": {"value": 63.11}, "net_margin": {"value": 31.77}, "revenue": {"yoy_growth": 5.14}, "net_profit": {"value": 116.68}},
        {"year": 2023, "roe": {"value": 34.73}, "gross_margin": {"value": 64.18}, "net_margin": {"value": 33.16}, "revenue": {"yoy_growth": 15.04}, "net_profit": {"value": 115.82}},
    ]
    
    cashflow_data = [
        {"year": 2024, "free_cashflow": {"value": 104.73}},
        {"year": 2023, "free_cashflow": {"value": 83.73}},
    ]
    
    print(generate_moat_report(financial_data, cashflow_data))