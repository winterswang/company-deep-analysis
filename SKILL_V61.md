---
name: company-deep-analysis
description: 上市公司深度价值投资分析。采用辩证式分析框架（分析师+挑战者），迭代改进直至高质量投资报告输出。
version: 6.1.0
triggers:
  - pattern: "DeerFlow 深度分析 {company}"
    command: "python3 /root/.openclaw/workspace/deer-flow-analysis/skills/custom/company-deep-analysis/scripts/run_v61_analysis.py --company {company}"
  - pattern: "DeerFlow 分析 {company}"
    command: "python3 /root/.openclaw/workspace/deer-flow-analysis/skills/custom/company-deep-analysis/scripts/run_v61_analysis.py --company {company}"
---

# 公司深度分析技能 V6.1

## 📋 版本说明

| 版本 | 更新日期 | 核心改进 |
|------|----------|----------|
| **V6.1** | 2026-03-11 | **辩证式分析框架**：分析师+挑战者协作，迭代改进 |
| V5.1 | 2026-03-11 | 质疑者边界约束，融合雪球8主题框架 |
| V5.0 | 2026-03-10 | 双LLM辩证分析框架 |
| V4.4 | 2026-03-10 | 三层辩证分析框架 |

---

## 🎯 核心方法论

### 辩证式分析框架（否定之否定）

```
┌─────────────────────────────────────────────────────────────┐
│                    V6.1 双角色协作架构                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   【主链路】分析师（Analyst）                                 │
│   - 生成投资分析报告                                         │
│   - 响应挑战者的建议                                         │
│   - 执行改进ToDo                                             │
│   - 输出最终报告                                             │
│                                                             │
│                     ↕ 辩证对话                               │
│                                                             │
│   【副链路】挑战者（Challenger）                              │
│   - 阅读分析报告                                             │
│   - 提出改进建议                                             │
│   - 给出具体ToDo                                             │
│   - 评估改进效果（评分）                                      │
│                                                             │
│   终止条件：评分 >= 85分                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 辩证过程

```
正题（分析师V1报告）
  ↓ 否定
反题（挑战者发现不足，提出改进建议+ToDo）
  ↓ 否定之否定
合题（分析师V2报告，更高层次）
  ↓ 继续...
最终合题（高质量投资报告）
```

---

## 📊 分析流程

```
阶段1: 数据收集
  ├─ 雪球爬虫（专业观点）
  ├─ AkShare（财务数据）
  └─ Tavily/Exa（行业分析）
      ↓
阶段2: 初始化评估
  └─ 雪球8主题评分（总分200）
      ↓
阶段3: 辩证分析（核心）⭐
  ├─ 分析师生成报告
  ├─ 挑战者评估+给ToDo
  ├─ 分析师改进报告
  └─ 循环直至评分>=85
      ↓
阶段4: 最终报告
  └─ 结构化投资分析报告
```

---

## 🚀 快速开始

### 触发词

```
DeerFlow 深度分析 FISV
DeerFlow 分析 迈瑞医疗
```

### 命令行调用

```bash
python3 scripts/run_v61_analysis.py --company FISV --max-iterations 5
```

### 代码调用

```python
from core.analyzer_v61 import DialecticalAnalyzerV61

analyzer = DialecticalAnalyzerV61({
    'max_iterations': 5,
    'score_threshold': 85
})

report = analyzer.analyze('FISV', initial_data)
```

---

## 📈 输出格式

### 结构化投资分析报告

```
# {公司名} 投资价值分析报告

## 一、执行摘要
- 估值判断（低估/合理/高估）
- 投资建议（强烈买入/买入/观望/避免）
- 核心投资逻辑（3条，带引用）
- 关键风险

## 二、业务分析
- 商业模式（做什么、怎么赚钱）
- 护城河分析（类型、本质、强度、变化）

## 三、财务质量分析
- 盈利能力（ROIC/ROE趋势表格）
- 增长质量
- 现金流
- 资产负债表

## 四、竞争格局
- 行业地位
- 竞争优势
- 竞争威胁

## 五、管理层分析
- 管理层背景
- 战略执行
- 资本配置

## 六、估值分析
- 估值方法（三锚点交叉验证）
- 估值结论
- 安全边际

## 七、投资决策
- 建仓策略
- 跟踪指标
- 退出条件
```

---

## 🔍 挑战者评估维度

| 维度 | 满分 | 评估重点 |
|------|------|----------|
| 财务分析深度 | 20 | ROIC趋势分析是否充分？利润来源是否拆解？ |
| 护城河讨论 | 20 | 是否深入本质？有证据支撑吗？变化趋势分析了吗？ |
| 估值合理性 | 20 | PE与增长率匹配吗？DCF假设合理吗？ |
| 风险评估 | 20 | 债务风险、竞争风险、管理风险是否充分？ |
| 数据支撑 | 20 | 关键结论有原文引用吗？ |
| **总分** | **100** | >=85分达标 |

---

## ✅ 有效挑战领域

| 领域 | 具体内容 |
|------|----------|
| 财务分析深度 | ROIC趋势、利润来源、现金流质量 |
| 护城河讨论 | 本质分析、证据支撑、变化趋势 |
| 估值合理性 | PE与增长率匹配、DCF假设 |
| 风险评估 | 债务风险、竞争风险、管理风险 |
| 数据支撑 | 原文引用、数据可靠性 |

---

## ❌ 无效挑战领域

| 领域 | 说明 |
|------|------|
| 元数据 | CIK编号、EDGAR格式、数据源基础设施 |
| 已充分讨论 | 不重复质疑已深入分析的内容 |

---

## 🗂️ 目录结构

```
company-deep-analysis/
├── SKILL.md                      # 本文件（框架概览）
├── core/
│   ├── analyzer_v61.py           # V6.1 辩证式分析器
│   ├── llm_client.py             # LLM客户端
│   └── models.py                 # 数据模型
│
├── scripts/
│   ├── run_v61_analysis.py       # V6.1 运行脚本
│   └── run_analysis.py           # V4.x 运行脚本
│
├── docs/
│   ├── V6.1_design_proposal.md   # V6.1 设计方案
│   └── CHANGELOG.md              # 版本变更
│
├── reports/
│   ├── v61/                      # V6.1 分析报告
│   └── v5/                       # V5.x 分析报告
│
└── search/
    └── search_engine.py          # 搜索引擎
```

---

## 📊 V5.x vs V6.1 对比

| 维度 | V5.x | V6.1 |
|------|------|------|
| **输出质量** | 抽象疑点列表 | 结构化投资报告 |
| **质疑焦点** | 可能偏离到元数据 | **聚焦企业本身** |
| **迭代效率** | 10轮未达标 | **1-3轮达标** |
| **投资相关性** | 低 | **100%** |
| **挑战者角色** | 质疑者（质疑一切） | **提升质量** |
| **输出格式** | 疑点列表 | **改进建议+ToDo** |
| **终止机制** | 无评分 | **评分>=85终止** |

---

## 📦 依赖

- Python 3.8+
- 阿里云百炼 API（LLM）
- Tavily / Exa（搜索引擎）
- AkShare（财务数据）
- 雪球爬虫（专业观点）

---

## 📝 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| max_iterations | 5 | 最大迭代轮数 |
| score_threshold | 85 | 终止阈值 |
| min_to_do_per_round | 2 | 每轮至少2个ToDo |

---

## 🧪 测试

```bash
# 运行V6.1测试
cd company-deep-analysis
python3 -c "
from core.analyzer_v61 import DialecticalAnalyzerV61
analyzer = DialecticalAnalyzerV61({'max_iterations': 3})
report = analyzer.analyze('FISV', {})
print(report[:1000])
"
```

---

## 📚 相关文档

| 文档 | 链接 |
|------|------|
| V6.1设计方案 | docs/V6.1_design_proposal.md |
| 变更日志 | docs/CHANGELOG.md |

---

## 📄 License

MIT

---

*版本: V6.1 | 更新: 2026-03-11*