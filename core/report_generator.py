"""
V7.0 完整报告生成器

严格按照需求文档 §9.3 的报告结构实现：
1. 核心结论（一句话）
2. 财务数据质量报告
3. 五层追问分析
4. 投资决策（估值、风险、建议）
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))


class V70ReportGenerator:
    """
    V7.0 完整报告生成器
    
    严格按需求文档 §9.3 实现
    """
    
    def __init__(self):
        self.company = ""
        self.ticker = ""
        self.market = ""
    
    def generate_complete_report(
        self,
        company: str,
        ticker: str,
        market: str,
        financial_data: Dict,
        quality_assessments: Dict,
        questioning_results: List,
        context: Dict = None
    ) -> str:
        """
        生成完整投资分析报告
        
        按需求文档 §9.3 的结构
        """
        
        self.company = company
        self.ticker = ticker
        self.market = market
        context = context or {}
        
        # 提取关键信息
        moat_type = self._extract_moat_type(questioning_results)
        core_insight = self._generate_core_insight(questioning_results)
        
        report = f"""# {company} 投资分析报告 V7.0

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析框架**: V7.0 深度投资分析
**股票代码**: {ticker}
**市场**: {market}

---

## 一、核心结论（一句话）

{company}的本质是"{core_insight['essence']}"，护城河来自"{moat_type}"，这个组合因{core_insight['reason']}而难以复制。

---

## 二、财务数据质量报告

### 数据质量统计

"""
        
        # 添加财务数据质量详情
        report += self._generate_quality_section(quality_assessments, financial_data)
        
        report += """
---

## 三、五层追问分析

"""
        
        # 添加五层追问详情
        report += self._generate_questioning_section(questioning_results)
        
        report += """
---

## 四、投资决策

"""
        
        # 添加投资决策（估值、风险、建议）
        report += self._generate_decision_section(questioning_results, financial_data, context)
        
        report += """
---

**分析完成**

*本报告由 Company Deep Analysis V7.0 生成*
*分析框架: 财务数据质量验证 + 五层追问 + 奖励函数驱动*
"""
        
        return report
    
    def _extract_moat_type(self, questioning_results: List) -> str:
        """提取护城河类型"""
        for result in questioning_results:
            if hasattr(result, 'moat_type') and result.moat_type:
                return result.moat_type.value
        return "未识别"
    
    def _generate_core_insight(self, questioning_results: List) -> Dict:
        """生成核心洞察 - 基于五层追问结果"""
        
        if not questioning_results:
            return {
                "essence": "待深入分析",
                "reason": "需要更多分析"
            }
        
        # 收集所有层的观察
        all_observations = []
        moat_types = []
        
        for result in questioning_results:
            if hasattr(result, 'observation') and result.observation:
                all_observations.append(result.observation)
            if hasattr(result, 'moat_type') and result.moat_type:
                moat_types.append(result.moat_type.value)
        
        # 使用 LLM 提炼核心洞察
        if all_observations:
            combined_text = "\n".join(all_observations[-5:])  # 取最近5条观察
            
            prompt = f"""请基于以下分析观察，用一句话概括这家公司的企业本质。

分析观察:
{combined_text[:1500]}

要求：
1. 用一个短语概括公司本质（如"广告驱动型平台"、"供应链重构者"）
2. 说明护城河来源
3. 说明不可复制的原因

请按以下格式输出：
本质: [短语]
护城河: [类型]
原因: [一句话说明]
"""
            
            try:
                from core.llm_client import LLMClient
                llm = LLMClient()
                response = llm.chat([{"role": "user", "content": prompt}])
                
                # 解析 LLM 返回
                essence = "企业"
                moat = "未识别"
                reason = "需要进一步分析"
                
                for line in response.split("\n"):
                    line = line.strip()
                    if line.startswith("本质:"):
                        essence = line.replace("本质:", "").strip()
                    elif line.startswith("护城河:"):
                        moat = line.replace("护城河:", "").strip()
                    elif line.startswith("原因:"):
                        reason = line.replace("原因:", "").strip()
                
                return {
                    "essence": essence,
                    "moat": moat,
                    "reason": reason
                }
                
            except Exception as e:
                print(f"LLM提炼失败: {e}")
        
        # Fallback：使用硬编码
        return {
            "essence": "企业",
            "reason": "需要更多分析"
        }
    
    def _generate_quality_section(
        self, 
        quality_assessments: Dict,
        financial_data: Dict
    ) -> str:
        """生成数据质量部分"""
        
        if not quality_assessments:
            return "数据质量验证待完成"
        
        # 统计
        trusted = sum(1 for a in quality_assessments.values() if hasattr(a, 'quality_label') and a.quality_label.value == "可信")
        pending = sum(1 for a in quality_assessments.values() if hasattr(a, 'quality_label') and a.quality_label.value == "待验证")
        unavailable = sum(1 for a in quality_assessments.values() if hasattr(a, 'quality_label') and a.quality_label.value == "不可用")
        
        avg_score = sum(
            a.quality_score for a in quality_assessments.values() 
            if hasattr(a, 'quality_score')
        ) / len(quality_assessments) if quality_assessments else 0
        
        report = f"""| 指标 | 数量 |
|------|------|
| 可信数据 | {trusted} 条 |
| 待验证数据 | {pending} 条 |
| 不可用数据 | {unavailable} 条 |
| 平均质量评分 | {avg_score:.1f}/10 |

### 数据质量详情

| 数据项 | 数值 | 来源 | 质量评分 | 验证状态 |
|--------|------|------|----------|----------|
"""
        
        for name, assessment in quality_assessments.items():
            if hasattr(assessment, 'quality_score'):
                value = assessment.value if hasattr(assessment, 'value') else financial_data.get(name, 'N/A')
                source = assessment.source if hasattr(assessment, 'source') else '未知'
                score = assessment.quality_score
                label = assessment.quality_label.value if hasattr(assessment, 'quality_label') else '未知'
                report += f"| {name} | {value} | {source} | {score:.1f}/10 | {label} |\n"
        
        return report
    
    def _generate_questioning_section(self, questioning_results: List) -> str:
        """生成五层追问部分"""
        
        if not questioning_results:
            return "五层追问待完成"
        
        report = ""
        
        for i, result in enumerate(questioning_results, 1):
            if hasattr(result, 'layer'):
                report += f"### 异常 {i}: {getattr(result, 'question', '未知异常')[:50]}...\n\n"
                report += f"- **到达层级**: 第{result.layer}层\n"
                report += f"- **有效证据**: {len(result.evidence) if hasattr(result, 'evidence') else 0}条\n"
                
                if hasattr(result, 'moat_type') and result.moat_type:
                    report += f"- **护城河类型**: {result.moat_type.value}\n"
                
                if hasattr(result, 'reward'):
                    report += f"- **奖励函数值**: {result.reward}\n"
                
                if hasattr(result, 'observation'):
                    report += f"\n**观察**: {result.observation[:300]}...\n"
                
                report += "\n---\n\n"
        
        return report
    
    def _generate_decision_section(
        self,
        questioning_results: List,
        financial_data: Dict,
        context: Dict
    ) -> str:
        """
        生成投资决策部分
        
        按需求文档要求：估值、风险、建议
        """
        
        moat_type = self._extract_moat_type(questioning_results)
        
        # 1. 估值分析
        report = """### 1. 估值分析

"""
        
        # 获取估值相关数据
        pe_ratio = financial_data.get("PE", financial_data.get("市盈率", "N/A"))
        pb_ratio = financial_data.get("PB", financial_data.get("市净率", "N/A"))
        market_cap = financial_data.get("市值", "N/A")
        
        report += f"""| 估值指标 | 数值 |
|----------|------|
| 市盈率 (P/E) | {pe_ratio} |
| 市净率 (P/B) | {pb_ratio} |
| 市值 | {market_cap} |

**估值判断**: 基于{moat_type}护城河，估值合理性待进一步分析。

"""
        
        # 2. 风险分析
        report += """### 2. 风险分析

"""
        
        # 基于分析结果生成公司特定风险
        risks = self._generate_risk_analysis(questioning_results, financial_data, moat_type)
        
        report += "| 风险类型 | 风险描述 | 严重程度 |\n"
        report += "|----------|----------|----------|\n"
        
        for risk in risks:
            report += f"| {risk['type']} | {risk['description']} | {risk['severity']} |\n"
        
        report += "\n"
        
        # 3. 投资建议
        report += """### 3. 投资建议

"""
        
        # 基于分析结果生成投资建议
        recommendation = self._generate_investment_recommendation(
            moat_type, financial_data, questioning_results
        )
        
        report += f"**建议**: {recommendation['action']}\n\n"
        report += "**理由**:\n"
        for reason in recommendation['reasons']:
            report += f"- {reason}\n"
        
        report += "\n**关注点**:\n"
        for point in recommendation['watch_points']:
            report += f"- {point}\n"
        
        return report
    
    def _get_quality_summary(self, questioning_results: List) -> str:
        """获取数据质量总结"""
        if questioning_results:
            for r in questioning_results:
                if hasattr(r, 'evidence'):
                    count = len(r.evidence)
                    if count >= 10:
                        return "较高"
                    elif count >= 5:
                        return "中等"
        return "待验证"
    
    def _generate_risk_analysis(
        self,
        questioning_results: List,
        financial_data: Dict,
        moat_type: str
    ) -> List[Dict]:
        """
        生成风险分析 - 基于分析结果
        
        不再使用固定模板，而是基于：
        1. 护城河类型的弱点
        2. 财务数据异常
        3. 行业特定风险
        """
        
        risks = []
        
        # 1. 基于护城河类型的风险
        moat_risks = {
            "网络效应": {"type": "用户流失风险", "severity": "高"},
            "转换成本": {"type": "技术替代风险", "severity": "中"},
            "成本优势": {"type": "成本优势减弱", "severity": "中"},
            "无形资产": {"type": "品牌/专利风险", "severity": "中"},
            "有效规模": {"type": "市场扩张风险", "severity": "中"},
            "未识别": {"type": "护城河不确定性", "severity": "高"}
        }
        
        moat_risk = moat_risks.get(moat_type, {"type": "竞争风险", "severity": "中"})
        risks.append({
            "type": moat_risk["type"],
            "description": f"{moat_type}护城河可能受到挑战",
            "severity": moat_risk["severity"]
        })
        
        # 2. 基于财务数据的风险
        if "ROIC" in financial_data:
            roic = financial_data["ROIC"]
            if isinstance(roic, dict):
                values = list(roic.values())
                if len(values) >= 2 and values[-1] < values[-2]:
                    risks.append({
                        "type": "盈利能力下降",
                        "description": f"ROIC从{values[-2]:.1f}%下降至{values[-1]:.1f}%",
                        "severity": "高"
                    })
        
        # 3. 行业通用风险
        risks.append({
            "type": "行业竞争",
            "description": "行业竞争格局变化可能影响市场地位",
            "severity": "中"
        })
        
        risks.append({
            "type": "宏观风险",
            "description": "宏观经济波动可能影响消费需求",
            "severity": "低"
        })
        
        return risks
    
    def _generate_investment_recommendation(
        self,
        moat_type: str,
        financial_data: Dict,
        questioning_results: List
    ) -> Dict:
        """
        生成投资建议 - 基于分析结果
        
        考虑因素：
        1. 护城河强度
        2. 财务数据质量
        3. 增长趋势
        """
        
        # 计算综合评分
        moat_score = {
            "网络效应": 3,
            "转换成本": 2.5,
            "成本优势": 2,
            "无形资产": 2.5,
            "有效规模": 2,
            "未识别": 0.5
        }.get(moat_type, 1)
        
        # 检查财务数据质量
        evidence_count = 0
        if questioning_results:
            for r in questioning_results:
                if hasattr(r, 'evidence'):
                    evidence_count += len(r.evidence)
        
        quality_score = min(evidence_count / 10, 3)  # 0-3分
        
        # 检查增长趋势
        growth_score = 1
        if "营收" in financial_data:
            revenue = financial_data["营收"]
            if isinstance(revenue, dict):
                values = list(revenue.values())
                if len(values) >= 2 and values[-1] > values[-2] * 1.1:
                    growth_score = 2  # 增长超过10%
        
        # 综合评分
        total_score = moat_score + quality_score + growth_score
        
        # 生成建议
        if total_score >= 6:
            action = "买入"
            reasons = [
                f"{moat_type}护城河强劲",
                f"财务数据质量较高（{evidence_count}条证据）",
                "增长趋势良好"
            ]
            watch_points = [
                "护城河强度的持续性",
                "竞争格局变化",
                "季度财务数据"
            ]
        elif total_score >= 4:
            action = "持有"
            reasons = [
                f"{moat_type}护城河存在，但强度待观察",
                f"财务数据质量中等（{evidence_count}条证据）"
            ]
            watch_points = [
                "护城河强化或减弱的信号",
                "行业竞争态势",
                "管理层战略调整"
            ]
        else:
            action = "观望"
            reasons = [
                "护城河不明确或较弱",
                "财务数据质量不足",
                "需要更多信息支撑决策"
            ]
            watch_points = [
                "公司基本面变化",
                "行业趋势变化",
                "新的财务数据披露"
            ]
        
        return {
            "action": action,
            "reasons": reasons,
            "watch_points": watch_points
        }
    
    def generate_data_references_report(
        self,
        company: str,
        financial_data: Dict,
        quality_assessments: Dict,
        questioning_results: List
    ) -> str:
        """
        生成数据引用报告
        
        按需求文档 §9.2 要求
        """
        
        report = f"""# {company} 数据引用报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析框架**: V7.0

---

## 一、财务数据来源

| 数据项 | 数值 | 来源 | 质量等级 | 质量评分 |
|--------|------|------|----------|----------|
"""
        
        for name, value in financial_data.items():
            assessment = quality_assessments.get(name)
            if assessment and hasattr(assessment, 'source'):
                source = assessment.source
                score = getattr(assessment, 'quality_score', 0)
                label = getattr(assessment, 'quality_label', '未知')
                if hasattr(label, 'value'):
                    label = label.value
                report += f"| {name} | {value} | {source} | {label} | {score:.1f}/10 |\n"
            else:
                report += f"| {name} | {value} | 未知 | 待验证 | - |\n"
        
        report += """
---

## 二、外部数据引用

"""
        
        # 提取外部搜索结果
        for i, result in enumerate(questioning_results, 1):
            if hasattr(result, 'evidence') and result.evidence:
                report += f"### 异常 {i} 的证据来源\n\n"
                for j, evidence in enumerate(result.evidence[:3], 1):
                    if hasattr(evidence, 'source'):
                        content = getattr(evidence, 'content', str(evidence))[:200]
                        source = getattr(evidence, 'source', '未知')
                        report += f"{j}. **来源**: {source}\n   **内容**: {content}...\n\n"
        
        report += """
---

## 三、数据验证记录

"""
        
        for name, assessment in quality_assessments.items():
            if hasattr(assessment, 'doubts') and assessment.doubts:
                report += f"### {name}\n\n"
                for doubt in assessment.doubts:
                    if hasattr(doubt, 'doubt_type'):
                        doubt_type = doubt.doubt_type
                        passed = "✅ 通过" if getattr(doubt, 'passed', False) else "❌ 未通过"
                        report += f"- {doubt_type}: {passed}\n"
                report += "\n"
        
        report += f"""
---

**报告生成时间**: {datetime.now().isoformat()}

*数据引用报告由 Company Deep Analysis V7.0 生成*
"""
        
        return report


# 测试
if __name__ == "__main__":
    generator = V70ReportGenerator()
    
    # 模拟数据
    financial_data = {
        "ROIC": 34.52,
        "ROE": 26.13,
        "毛利率": 60.92
    }
    
    quality_assessments = {}
    questioning_results = []
    
    report = generator.generate_complete_report(
        company="PDD Holdings",
        ticker="PDD",
        market="us",
        financial_data=financial_data,
        quality_assessments=quality_assessments,
        questioning_results=questioning_results
    )
    
    print(report[:2000])