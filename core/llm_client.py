"""
LLM 客户端
用于调用阿里云百炼 API
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LLMConfig:
    """LLM配置"""
    api_key: str
    base_url: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    model: str = "qwen-plus"  # 阿里云百炼模型
    max_tokens: int = 8192  # 增加到8192，支持长篇报告
    temperature: float = 0.7


class LLMClient:
    """LLM客户端"""

    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            # 从环境变量读取，支持多种环境变量名
            api_key = os.environ.get("DASHSCOPE_API_KEY", "") or \
                      os.environ.get("ALIBABA_API_KEY", "")

            # 如果环境变量为空，尝试从多个.env文件加载
            if not api_key:
                env_paths = [
                    Path(__file__).parent.parent.parent.parent / ".env",  # deer-flow-analysis/.env
                    Path(__file__).parent.parent.parent / ".env",  # company-deep-analysis/.env
                    Path("/root/.openclaw/workspace/deer-flow-analysis/.env"),  # 绝对路径
                ]
                for env_path in env_paths:
                    if env_path.exists():
                        with open(env_path) as f:
                            for line in f:
                                line = line.strip()
                                if line.startswith("DASHSCOPE_API_KEY="):
                                    api_key = line.split("=", 1)[1]
                                    break
                        if api_key:
                            break

            self.config = LLMConfig(api_key=api_key)
        else:
            self.config = config

        if not self.config.api_key:
            raise ValueError("DASHSCOPE_API_KEY not found in environment variables or .env files")

    def chat(self, messages: list, temperature: Optional[float] = None) -> str:
        """发送聊天请求"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        # 阿里云百炼API格式
        payload = {
            "model": self.config.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "max_tokens": self.config.max_tokens,
                "temperature": temperature if temperature is not None else self.config.temperature,
            }
        }

        try:
            response = requests.post(
                self.config.base_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()

            result = response.json()
            return result["output"]["text"]  # 阿里云百炼返回格式

        except requests.exceptions.Timeout:
            raise TimeoutError("LLM request timed out")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM request failed: {e}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Invalid LLM response: {e}")

    def chat_with_system(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> str:
        """带系统提示的聊天"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat(messages, temperature)


class SkepticLLM:
    """质疑者LLM"""
    
    SYSTEM_PROMPT = """你是 **陈光明**，一位资深价值投资分析师，以批判性思维和敏锐的洞察力著称。

你的特点：
- 30年投资经验，经历过多次牛熊周期
- 擅长发现问题，从不轻易接受表面结论
- 对"常识"保持警惕，总是追问"为什么"

# 核心原则：聚焦投资决策

你的质疑必须聚焦于**投资决策相关**的问题，而非元数据问题。

## ✅ 有效质疑域（你应该质疑的）

### 1. 财务数据矛盾
- 利润增速与营收增速不一致？
- 现金流与净利润差异？
- ROIC/ROE趋势异常？
- 毛利率/净利率波动原因？

### 2. 护城河真实性
- 转换成本是否被高估？
- 竞争对手是否在侵蚀市场份额？
- 技术护城河是否可持续？
- 品牌溢价是否真实？

### 3. 管理层执行力
- 战略与执行是否一致？
- 资本配置是否合理（回购 vs 分红 vs 投资）？
- 激励机制是否有效？
- 过往承诺是否兑现？

### 4. 估值合理性
- PE是否匹配增长率（PEG）？
- DCF假设是否过于乐观？
- 风险溢价是否充分？
- 与同行对比是否合理？

### 5. 风险评估
- 已知风险是否充分反映在估值中？
- 是否存在黑天鹅隐患？
- 尾部风险是否被忽视？
- 行业监管变化影响？

## ❌ 无效质疑域（你不应该质疑）

**这些是元数据问题，不影响投资决策**：

- ❌ CIK编号是否正确（假设基本信息可信）
- ❌ EDGAR文件格式（不影响投资决策）
- ❌ 符号标签语义（过度哲学化）
- ❌ 数据源基础设施（超出投资分析范畴）
- ❌ 监管文件编号格式（与投资价值无关）

# 评分标准

你的评分应该反映"投资决策支撑度"，评分范围0-100：

| 维度 | 满分 | 评估重点 |
|------|------|----------|
| 财务质量 | 25 | 数据一致性、趋势健康度 |
| 护城河 | 25 | 真实性、可持续性 |
| 管理层 | 15 | 执行力、激励机制 |
| 估值 | 15 | 合理性、安全边际 |
| 风险 | 10 | 风险识别充分度 |
| 竞争格局 | 10 | 竞争分析深度 |

# 注意事项
- 不要为了质疑而质疑，每个质疑都应该与投资决策相关
- 如果你认为分析已经足够好，就直接说"分析充分"
- 你的目标是帮助发现投资决策中的盲点"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def identify_doubts(self, hypothesis: str, evidences: list, resolved_doubts: list) -> str:
        """识别疑点"""
        user_prompt = f"""# 质疑者任务

## 当前分析假设
{hypothesis}

## 已收集的证据
{self._format_evidences(evidences)}

## 已解决的疑点
{self._format_resolved_doubts(resolved_doubts)}

## 你的任务

### 1. 识别投资相关的疑点

请聚焦于以下类型的投资问题：

| 类型 | 示例问题 |
|------|----------|
| 财务矛盾 | 利润增速11% vs 营收增速3.6%，是否可持续？ |
| 护城河质疑 | 转换成本高，但客户流失率如何？ |
| 管理层质疑 | 回购资金来源？是否举债回购？ |
| 估值质疑 | P/E 35x是否匹配增长预期？ |
| 风险质疑 | 高债务($28B)是否可控？ |

输出格式：
```
## 发现的疑点

| ID | 类型 | 疑点描述 | 投资影响 | 优先级 |
|----|------|----------|----------|--------|
| D001 | 财务矛盾 | 利润增速远高于营收增速 | 高 | P0 |
| D002 | 护城河质疑 | 转换成本高但新客户获取困难 | 中 | P1 |
```

### 2. 投资决策评分

基于投资决策支撑度评分（0-100）：

| 维度 | 得分 | 扣分原因 |
|------|------|----------|
| 财务质量 | X/25 | ... |
| 护城河 | X/25 | ... |
| 管理层 | X/15 | ... |
| 估值 | X/15 | ... |
| 风险 | X/10 | ... |
| 竞争格局 | X/10 | ... |
| **总分** | **X/100** | |

### 3. 核心投资疑虑

列出2-3个最关键的投资疑虑

### 4. 分析充分性

- 如果评分>=85分且无P0疑点：说明"分析充分"
- 否则：说明"需要继续分析"
"""
        return self.llm.chat_with_system(self.SYSTEM_PROMPT, user_prompt, temperature=0.5)

    def _format_evidences(self, evidences: list) -> str:
        if not evidences:
            return "暂无证据"
        lines = []
        for i, e in enumerate(evidences, 1):
            source = e.get("source", "未知来源") if isinstance(e, dict) else str(e)
            content = e.get("content", "")[:200] if isinstance(e, dict) else str(e)[:200]
            lines.append(f"{i}. [{source}] {content}...")
        return "\n".join(lines)

    def _format_resolved_doubts(self, doubts: list) -> str:
        if not doubts:
            return "暂无已解决疑点"
        lines = []
        for d in doubts:
            desc = d.get("description", "") if isinstance(d, dict) else str(d)
            resolution = d.get("resolution", "已解决") if isinstance(d, dict) else "已解决"
            lines.append(f"- {desc}: {resolution}")
        return "\n".join(lines)


class ResolverLLM:
    """解决者LLM"""

    SYSTEM_PROMPT = """你是 **张磊**，一位资深研究分析师，擅长寻找证据和构建逻辑链条。

你的特点：
- 20年研究经验，覆盖多个行业
- 擅长从海量信息中找到关键证据
- 能够将碎片信息拼成完整的逻辑图
- 你的名言是："每个质疑都是一个深入理解的机会"

你的工作方式：
- 面对质疑，首先思考"这个问题可以如何验证？"
- 设计针对性的数据收集方案
- 评估证据的质量和相关性
- 构建有力的反驳或承认不足并修正假设

你不会：
- 回避质疑
- 用模糊的语言敷衍
- 忽视证据的局限性
- 过度自信

你的输出必须是结构化的，严格按照要求的格式输出。"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def design_search_plan(self, doubts: list, current_hypothesis: str) -> str:
        """设计检索方案"""
        user_prompt = f"""# 解决者任务：设计检索方案

## 待验证的疑点
{self._format_doubts(doubts)}

## 当前假设
{current_hypothesis}

## 可用数据源
| 数据源 | 用途 | 最佳场景 |
|--------|------|----------|
| AkShare | 财务数据 | ROIC、现金流、利润率等 |
| 雪球 | 中文分析 | 中国投资者观点、深度文章 |
| Tavily | 实时搜索 | 新闻、公告、最新动态 |
| Exa | 深度研究 | 语义搜索、行业报告 |

## 你的任务

为每个疑点设计检索方案：

```
## 检索方案

### 疑点 D001: [疑点描述]

**验证思路**：[如何验证这个疑点]

**检索目标**：
| 数据源 | 搜索查询 | 期望找到什么 |
|--------|----------|--------------|
| AkShare | [具体指标] | [期望数据] |
| Tavily | [搜索词] | [期望信息] |

### 疑点 D002: ...
```

注意：
1. 每个疑点至少设计1-2个检索目标
2. 根据疑点类型选择最合适的数据源
3. 搜索查询要具体，避免过于宽泛
"""
        return self.llm.chat_with_system(self.SYSTEM_PROMPT, user_prompt, temperature=0.7)

    def evaluate_evidence(self, doubt: dict, evidences: list) -> str:
        """评估证据"""
        user_prompt = f"""# 解决者任务：评估证据

## 待验证的疑点
- 类型: {doubt.get('type', '未知')}
- 描述: {doubt.get('description', '未知')}
- 为什么是问题: {doubt.get('reason', '未知')}

## 收集到的证据
{self._format_collected_evidences(evidences)}

## 你的任务

评估证据是否足以回答疑点：

```
## 证据评估

### 证据质量
| ID | 来源 | 可信度 | 相关性 | 局限性 |
|----|------|--------|--------|--------|
| E001 | ... | P0-P4 | 高/中/低 | ... |

### 证据一致性
[不同证据之间是否一致？是否有矛盾？]

### 验证结果
- **状态**: 已解决 / 需要更多证据 / 无法验证
- **结论**: [基于证据得出的结论]
- **置信度**: 0-100%
- **对假设的影响**: [这个结论如何影响当前假设]

### 是否产生新疑点
[是/否，如果是，描述新疑点]
```
"""
        return self.llm.chat_with_system(self.SYSTEM_PROMPT, user_prompt, temperature=0.7)

    def update_hypothesis(self, current_hypothesis: str, validation_results: list) -> str:
        """修正假设"""
        user_prompt = f"""# 解决者任务：修正假设

## 当前假设
{current_hypothesis}

## 验证结果
{self._format_validation_results(validation_results)}

## 你的任务

根据验证结果，修正假设：

```
## 假设更新

### 验证发现总结
1. [疑点D001]: [结论]
2. [疑点D002]: [结论]

### 假设修正
[修正后的假设，要更加精确]

### 修正理由
[解释为什么这样修正]

### 新的疑点
[修正后是否产生新的疑点]
```

修正原则：
1. 假设应该更加精确，而非更加模糊
2. 每个修正都应该有证据支撑
3. 承认不确定性，不要强行下结论
"""
        return self.llm.chat_with_system(self.SYSTEM_PROMPT, user_prompt, temperature=0.7)

    def _format_doubts(self, doubts: list) -> str:
        if not doubts:
            return "暂无疑点"
        lines = []
        for d in doubts:
            did = d.get("id", "?")
            dtype = d.get("type", "未知")
            desc = d.get("description", "")
            priority = d.get("priority", "P2")
            lines.append(f"- [{did}] [{priority}] {dtype}: {desc}")
        return "\n".join(lines)

    def _format_collected_evidences(self, evidences: list) -> str:
        if not evidences:
            return "暂无证据"
        lines = []
        for e in evidences:
            eid = e.get("id", "?")
            source = e.get("source", "未知")
            cred = e.get("credibility", "P4")
            content = e.get("content", "")[:300]
            lines.append(f"### {eid} [{cred}] 来源: {source}\n{content}...")
        return "\n\n".join(lines)

    def _format_validation_results(self, results: list) -> str:
        if not results:
            return "暂无验证结果"
        lines = []
        for r in results:
            did = r.get("doubt_id", "?")
            status = r.get("status", "未知")
            conclusion = r.get("conclusion", "")
            lines.append(f"- [{did}] {status}: {conclusion}")
        return "\n".join(lines)