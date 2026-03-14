"""
V6.3.2 分析师角色 - 重构版

核心改进：
1. 投资故事线设计（业务→财务→估值→决策的逻辑闭环）
2. 分章节生成（避免截断）
3. 强制逻辑串联
4. 真正的辩证式输出
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


class AnalystV632:
    """分析师角色 V6.3.2 - 投资故事线设计"""
    
    # 投资故事线框架
    STORY_FRAMEWORK = """
# 投资分析故事线

## 核心逻辑链

```
公司是什么？（业务理解）
    ↓
如何赚钱？（商业模式）
    ↓
赚多少钱？（财务表现）
    ↓
能持续吗？（护城河）
    ↓
值多少钱？（估值）
    ↓
买不买？（投资决策）
```

## 逻辑串联要求

每个章节必须回答上一章引出的问题，并为下一章铺垫：

| 章节 | 回答的问题 | 引出的问题 |
|------|-----------|-----------|
| 业务分析 | 公司做什么？ | 如何赚钱？ |
| 商业模式 | 如何创造价值？ | 赚多少钱？ |
| 财务分析 | 实际赚了多少？ | 能持续吗？ |
| 护城河 | 竞争优势是什么？ | 风险是什么？ |
| 风险评估 | 什么可能出错？ | 值多少钱？ |
| 估值分析 | 合理价格是多少？ | 买不买？ |
| 投资决策 | 最终结论？ | - |

## 辩证式结构

每个核心结论必须包含：

```
【观点】{核心结论}
【证据】{支撑数据}
【反驳】{可能的反对意见}
【回应】{对反驳的回应}
【结论】{最终判断}
```
"""
    
    # 系统提示词
    SYSTEM_PROMPT = """你是资深投资分析师，专注于深度价值投资分析。

# 你的分析风格

1. **逻辑严谨**：每个结论都有清晰的推导过程
2. **证据驱动**：每个判断都有数据支撑
3. **辩证思维**：主动考虑反对意见并回应
4. **投资导向**：所有分析最终服务于投资决策

# 投资故事线

你的报告必须遵循"业务→财务→估值→决策"的逻辑闭环：

```
业务分析：公司是什么？如何赚钱？
    ↓ 铺垫
财务分析：赚了多少？质量如何？
    ↓ 铺垫
护城河：能持续吗？优势是什么？
    ↓ 铺垫
估值：值多少钱？安全边际？
    ↓ 铺垫
决策：买不买？为什么？
```

# 辩证式输出

每个核心观点必须包含：
- 【观点】：明确的主张
- 【证据】：支撑的数据
- 【反驳】：可能的反对意见
- 【回应】：对反驳的回应
- 【结论】：最终判断

# 数据引用格式

使用标准化格式引用数据：
- 财务数据：[10-Q p.F-12]
- 行业数据：[IDC Report 2025, p.23]
- 第三方研究：[Bloomberg Terminal]

# 禁止事项

❌ 罗列数据不做分析
❌ 抽象表述缺乏具体数字
❌ 孤立章节缺乏逻辑串联
❌ 只有结论没有推导过程
"""
    
    # 分章节生成提示词
    CHAPTER_PROMPTS = {
        "executive_summary": """# 生成执行摘要

## 公司信息
- 公司名称：{company}
- 股票代码：{ticker}
- 当前股价：{current_price}

## 已收集数据
{data_summary}

## 输出要求

生成执行摘要（500字以内），必须包含：

### 1. 投资结论（100字）
- 估值判断：高估/合理/低估
- 投资建议：强烈买入/买入/持有/卖出
- 目标价区间

### 2. 核心逻辑（200字）
用3个要点说明投资逻辑：
- 要点1：业务层面的核心发现
- 要点2：财务层面的关键洞察
- 要点3：估值层面的主要判断

### 3. 关键风险（100字）
列出2-3个最重要的风险因素

### 4. 投资故事线（100字）
一句话概括投资故事："{company}是一家____的公司，因为____，所以值得投资/观望/回避。"
""",

        "business_analysis": """# 生成业务分析

## 公司信息
- 公司名称：{company}

## 已收集数据
{data}

## 输出要求

生成业务分析章节（800-1000字），必须包含：

### 1. 公司定位（150字）
- 公司是什么？（一句话定义）
- 主营业务是什么？
- 目标客户是谁？

### 2. 商业模式分析（300字）

必须回答以下问题：
- **如何获客？** 获客渠道、获客成本
- **如何赚钱？** 收入来源、定价模式
- **成本结构是什么？** 主要成本项、成本优势

使用表格展示：
| 收入来源 | 占比 | 毛利率 | 增长趋势 |
|----------|------|--------|----------|

### 3. 业务增长驱动（200字）

分析增长来源：
- 国内业务：增长驱动因素
- 海外业务：Temu的增长逻辑

### 4. 与下一章的逻辑衔接（50字）

"基于以上业务分析，我们接下来分析财务表现，验证业务逻辑是否转化为财务成果。"

### 数据引用要求

每个关键数据必须标注来源：
- 格式：[来源, 页码]
- 示例：[PDD 2025 Q3 10-Q, p.F-8]
""",

        "financial_analysis": """# 生成财务质量分析

## 公司信息
- 公司名称：{company}

## 已收集数据
{data}

## 上一章业务分析核心结论
{previous_conclusion}

## 输出要求

生成财务分析章节（1000-1200字），必须包含：

### 1. 财务表现概览（200字）

用表格展示核心指标：
| 指标 | 2023 | 2024 | 2025Q3 | 趋势 |
|------|------|------|--------|------|
| 营收 | - | - | - | ↗️ |
| 净利润 | - | - | - | ↗️ |
| ROIC | - | - | - | ↗️ |
| ROE | - | - | - | ↗️ |

### 2. 盈利能力分析（300字）

**观点：盈利能力的核心判断**
【证据】从已收集数据中提取具体数据
【反驳】可能的质疑
【回应】对质疑的回应
【结论】最终判断

必须分析：
- ROIC的构成（NOPAT和Invested Capital的拆解）
- ROIC趋势及驱动因素
- 毛利率、净利率的变化

### 3. 现金流分析（200字）

- 经营现金流/净利润比率
- 自由现金流状况
- 现金流质量评价

### 4. 资产负债分析（200字）

- 现金及等价物
- 债务水平
- 净现金状况

### 5. 与上一章的逻辑验证（100字）

"财务表现验证了/未验证业务分析的预期：..."

### 6. 与下一章的逻辑铺垫（100字）

"基于财务分析，我们接下来分析护城河，探讨这种盈利能力能否持续。"
""",

        "moat_analysis": """# 生成护城河分析

## 公司信息
- 公司名称：{company}

## 已收集数据
{data}

## 上一章财务分析核心结论
{previous_conclusion}

## 输出要求

生成护城河分析章节（1000-1200字），必须包含：

### 1. 护城河类型识别（200字）

判断公司护城河类型：
- 转换成本
- 网络效应
- 成本优势
- 品牌溢价
- 有效规模

**观点：核心护城河是什么？**
【证据】从已收集数据中提取具体数据
【反驳】可能的质疑
【回应】对质疑的回应
【结论】最终判断

### 2. 护城河深度分析（400字）

使用表格展示成本优势：
| 成本环节 | 行业均值 | 公司水平 | 优势幅度 | 来源 |
|----------|----------|----------|----------|------|
| 获客成本 | - | - | -% | - |
| 履约成本 | - | - | -% | - |
| ... | ... | ... | ... | ... |

分析要点：
- 护城河的本质是什么？
- 护城河是否可持续？
- 竞争对手能否复制？

### 3. 竞争格局分析（200字）

- 主要竞争对手
- 市场份额对比
- 竞争优势对比

### 4. 护城河变化趋势（100字）

- 护城河在变宽还是变窄？
- 关键影响因素是什么？

### 5. 与上一章的逻辑验证（100字）

"护城河分析解释了财务表现的可持续性：..."

### 6. 与下一章的逻辑铺垫（100字）

"基于护城河分析，我们接下来分析风险因素，评估护城河可能面临的威胁。"
""",

        "risk_analysis": """# 生成风险分析

## 公司信息
- 公司名称：{company}

## 已收集数据
{data}

## 上一章护城河分析核心结论
{previous_conclusion}

## 输出要求

生成风险分析章节（800-1000字），必须包含：

### 1. 风险清单（300字）

使用表格展示风险因素：
| 风险类型 | 风险描述 | 发生概率 | 影响程度 | 应对措施 |
|----------|----------|----------|----------|----------|
| 竞争风险 | - | 高/中/低 | 高/中/低 | - |
| 监管风险 | - | 高/中/低 | 高/中/低 | - |
| 运营风险 | - | 高/中/低 | 高/中/低 | - |

### 2. 关键风险深度分析（300字）

选择2个最重要的风险进行深度分析：

**风险1**（从数据中识别最重要风险）
- 风险本质：
- 可能影响：
- 应对策略：
- 实际冲击：

**风险2**（从数据中识别第二重要风险）
- 风险本质：
- 可能影响：
- 应对策略：
- 实际冲击：

### 3. 风险量化（100字）

- 风险对估值的影响（量化）
- 风险溢价要求

### 4. 与上一章的逻辑关联（100字）

"风险分析补充了护城河分析的不足：..."

### 5. 与下一章的逻辑铺垫（100字）

"基于风险分析，我们进行估值分析时需要考虑这些风险因素。"
""",

        "valuation_analysis": """# 生成估值分析

## 公司信息
- 公司名称：{company}
- 股票代码：{ticker}
- 当前股价：{current_price}

## 已收集数据
{data}

## 上一章风险分析核心结论
{previous_conclusion}

## 输出要求

生成估值分析章节（1000-1200字），必须包含：

### 1. 估值方法选择（150字）

说明使用的估值方法及理由：
- DCF估值（适用于稳定现金流公司）
- 相对估值（适用于可比公司明确的公司）
- 分部估值（适用于多业务线公司）

### 2. 核心假设（200字）

使用表格展示核心假设：
| 假设项 | 假设值 | 假设依据 |
|--------|--------|----------|
| 营收增速 | -% | - |
| 毛利率 | -% | - |
| 折现率（WACC） | -% | - |
| 永续增长率 | -% | - |

### 3. 估值计算（300字）

**观点：公司合理估值**
【证据】从已收集数据中提取计算过程
【反驳】可能的质疑
【回应】对质疑的回应
【结论】最终判断

估值结果：
- 保守估值：$X（假设悲观情况）
- 基准估值：$Y（基准假设）
- 乐观估值：$Z（假设乐观情况）

### 4. 敏感性分析（150字）

使用表格展示敏感性分析：
| 情景 | 营收增速 | 毛利率 | 目标价 | 较现价空间 |
|------|----------|--------|--------|------------|
| 悲观 | -% | -% | $- | -% |
| 基准 | -% | -% | $- | -% |
| 乐观 | -% | -% | $- | -% |

### 5. 安全边际（100字）

- 当前股价：$-
- 基准估值：$-
- 安全边际：-%
- 判断：安全边际充足/不足

### 6. 与上一章的逻辑关联（100字）

"估值分析考虑了风险分析中的关键风险：..."
""",

        "investment_decision": """# 生成投资决策

## 公司信息
- 公司名称：{company}
- 股票代码：{ticker}
- 当前股价：{current_price}

## 前几章核心结论
- 业务分析：{business_conclusion}
- 财务分析：{financial_conclusion}
- 护城河：{moat_conclusion}
- 风险分析：{risk_conclusion}
- 估值分析：{valuation_conclusion}

## 输出要求

生成投资决策章节（500-600字），必须包含：

### 1. 投资结论（100字）

- 投资建议：强烈买入/买入/持有/卖出
- 目标价：$X - $Y
- 投资期限：短期/中期/长期

### 2. 决策依据（200字）

基于完整分析链得出结论：

| 维度 | 核心发现 | 对决策的影响 |
|------|----------|--------------|
| 业务 | - | - |
| 财务 | - | - |
| 护城河 | - | - |
| 风险 | - | - |
| 估值 | - | - |

### 3. 入场条件（100字）

什么情况下适合买入？
- 价格条件：股价低于$X
- 时间条件：...
- 事件条件：...

### 4. 跟踪指标（50字）

需要持续跟踪的关键指标：
- 财务指标：...
- 业务指标：...

### 5. 退出条件（50字）

什么情况下应该卖出？
- 价格触发：股价高于$X
- 基本面恶化：...
"""
    }
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()
        self.chapters = {}  # 存储各章节内容
        self.conclusions = {}  # 存储各章节核心结论
    
    def generate_full_report(self, company: str, data: Dict[str, Any], ticker: str = None) -> str:
        """生成完整报告（分章节生成）"""
        
        print(f"\n{'='*60}")
        print(f"生成 {company} 投资分析报告")
        print(f"{'='*60}")
        
        # 1. 生成执行摘要
        print("\n[1/7] 生成执行摘要...")
        self.chapters["executive_summary"] = self._generate_chapter(
            "executive_summary", company, data, ticker=ticker
        )
        
        # 2. 生成业务分析
        print("[2/7] 生成业务分析...")
        self.chapters["business_analysis"] = self._generate_chapter(
            "business_analysis", company, data
        )
        self.conclusions["business"] = self._extract_conclusion(self.chapters["business_analysis"])
        
        # 3. 生成财务分析
        print("[3/7] 生成财务分析...")
        self.chapters["financial_analysis"] = self._generate_chapter(
            "financial_analysis", company, data,
            previous_conclusion=self.conclusions.get("business", "")
        )
        self.conclusions["financial"] = self._extract_conclusion(self.chapters["financial_analysis"])
        
        # 4. 生成护城河分析
        print("[4/7] 生成护城河分析...")
        self.chapters["moat_analysis"] = self._generate_chapter(
            "moat_analysis", company, data,
            previous_conclusion=self.conclusions.get("financial", "")
        )
        self.conclusions["moat"] = self._extract_conclusion(self.chapters["moat_analysis"])
        
        # 5. 生成风险分析
        print("[5/7] 生成风险分析...")
        self.chapters["risk_analysis"] = self._generate_chapter(
            "risk_analysis", company, data,
            previous_conclusion=self.conclusions.get("moat", "")
        )
        self.conclusions["risk"] = self._extract_conclusion(self.chapters["risk_analysis"])
        
        # 6. 生成估值分析
        print("[6/7] 生成估值分析...")
        self.chapters["valuation_analysis"] = self._generate_chapter(
            "valuation_analysis", company, data, ticker=ticker,
            previous_conclusion=self.conclusions.get("risk", "")
        )
        self.conclusions["valuation"] = self._extract_conclusion(self.chapters["valuation_analysis"])
        
        # 7. 生成投资决策
        print("[7/7] 生成投资决策...")
        self.chapters["investment_decision"] = self._generate_chapter(
            "investment_decision", company, data, ticker=ticker,
            conclusions=self.conclusions
        )
        
        # 8. 合并成完整报告
        print("\n合并报告...")
        full_report = self._merge_chapters(company)
        
        return full_report
    
    def _generate_chapter(
        self, 
        chapter_name: str, 
        company: str, 
        data: Dict[str, Any],
        ticker: str = None,
        previous_conclusion: str = "",
        conclusions: Dict[str, str] = None
    ) -> str:
        """生成单个章节"""
        
        prompt_template = self.CHAPTER_PROMPTS.get(chapter_name, "")
        if not prompt_template:
            return ""
        
        # 准备数据摘要
        data_summary = self._format_data_summary(data)
        data_full = self._format_data(data)
        
        # 格式化提示词
        prompt = prompt_template.format(
            company=company,
            ticker=ticker or "N/A",
            current_price=data.get("current_price", "N/A"),
            data_summary=data_summary,
            data=data_full,
            previous_conclusion=previous_conclusion,
            business_conclusion=conclusions.get("business", "") if conclusions else "",
            financial_conclusion=conclusions.get("financial", "") if conclusions else "",
            moat_conclusion=conclusions.get("moat", "") if conclusions else "",
            risk_conclusion=conclusions.get("risk", "") if conclusions else "",
            valuation_conclusion=conclusions.get("valuation", "") if conclusions else ""
        )
        
        # 调用LLM
        response = self.llm.chat_with_system(self.SYSTEM_PROMPT, prompt)
        
        return response
    
    def improve_chapter(
        self,
        chapter_name: str,
        current_content: str,
        challenges: List[Dict],
        new_evidence: Dict[str, Any] = None
    ) -> str:
        """根据挑战改进章节"""
        
        challenges_text = self._format_challenges(challenges)
        evidence_text = self._format_evidence(new_evidence) if new_evidence else "无新证据"
        
        prompt = f"""# 改进章节：{chapter_name}

## 当前内容

{current_content}

## 挑战者的挑战点

{challenges_text}

## 新获取的证据

{evidence_text}

## 改进要求

1. 针对每个挑战点给出具体回应
2. 引用新获取的证据
3. 保持辩证式结构（观点→证据→反驳→回应→结论）
4. 保持与前后章节的逻辑串联

请输出改进后的章节内容。"""
        
        return self.llm.chat_with_system(self.SYSTEM_PROMPT, prompt)
    
    def _format_data_summary(self, data: Dict[str, Any]) -> str:
        """格式化数据摘要"""
        if not data:
            return "暂无数据"
        
        summary = []
        by_source = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                source = value.get('source', 'unknown')
                if source not in by_source:
                    by_source[source] = 0
                by_source[source] += 1
        
        for source, count in by_source.items():
            summary.append(f"- {source}: {count}条数据")
        
        return "\n".join(summary)
    
    def _format_data(self, data: Dict[str, Any]) -> str:
        """格式化详细数据"""
        if not data:
            return "暂无数据"
        
        text = ""
        by_source = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                source = value.get('source', 'unknown')
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append((key, value))
        
        for source, items in by_source.items():
            text += f"\n### {source}\n"
            for key, value in items[:20]:  # 限制每个来源最多20条
                if isinstance(value, dict):
                    val = value.get('value', value.get('name', str(value)))
                    quality = value.get('quality', 'N/A')
                    text += f"- {key}: {val} [{quality}]\n"
        
        return text
    
    def _format_challenges(self, challenges: List[Dict]) -> str:
        """格式化挑战点"""
        text = "| # | 挑战内容 | 问题类型 | 严重程度 |\n|---|----------|----------|----------|\n"
        for i, c in enumerate(challenges, 1):
            content = c.get('content', c.get('challenge', ''))
            challenge_type = c.get('type', c.get('challenge_type', ''))
            severity = c.get('severity', '中')
            text += f"| {i} | {content} | {challenge_type} | {severity} |\n"
        return text
    
    def _format_evidence(self, evidence: Dict[str, Any]) -> str:
        """格式化证据"""
        if not evidence:
            return "无新证据"
        
        text = ""
        for key, value in evidence.items():
            text += f"\n### {key}\n"
            if isinstance(value, list):
                for item in value[:5]:
                    if isinstance(item, dict):
                        name = item.get('name', item.get('title', ''))
                        val = item.get('value', item.get('content', ''))
                        source = item.get('source', '')
                        quality = item.get('quality', 'P2')
                        text += f"- {name}: {val[:200]}... [{quality}] {source}\n"
            else:
                text += f"{value}\n"
        
        return text
    
    def _extract_conclusion(self, chapter_content: str) -> str:
        """提取章节核心结论"""
        # 简单实现：取最后一段作为结论
        paragraphs = chapter_content.split('\n\n')
        if paragraphs:
            return paragraphs[-1][:200] + "..."
        return ""
    
    def _merge_chapters(self, company: str) -> str:
        """合并所有章节成完整报告"""
        
        report = f"""# {company} 投资价值分析报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析框架**: V6.3.2 投资故事线 + 辩证式分析

---

"""
        
        # 添加目录
        report += "## 📑 目录\n\n"
        report += "1. [执行摘要](#1-执行摘要)\n"
        report += "2. [业务分析](#2-业务分析)\n"
        report += "3. [财务质量分析](#3-财务质量分析)\n"
        report += "4. [护城河分析](#4-护城河分析)\n"
        report += "5. [风险分析](#5-风险分析)\n"
        report += "6. [估值分析](#6-估值分析)\n"
        report += "7. [投资决策](#7-投资决策)\n\n---\n\n"
        
        # 添加各章节
        chapter_names = {
            "executive_summary": "执行摘要",
            "business_analysis": "业务分析",
            "financial_analysis": "财务质量分析",
            "moat_analysis": "护城河分析",
            "risk_analysis": "风险分析",
            "valuation_analysis": "估值分析",
            "investment_decision": "投资决策"
        }
        
        for i, (key, title) in enumerate(chapter_names.items(), 1):
            content = self.chapters.get(key, "")
            report += f"## {i}. {title}\n\n"
            report += content
            report += "\n\n---\n\n"
        
        return report


# 兼容旧版本
class Analyst(AnalystV632):
    """向后兼容"""
    pass