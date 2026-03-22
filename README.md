# Company Deep Analysis V8.0

上市公司深度价值投资分析技能 - 多轮深度思考框架

---

## 🚀 最新版本

**V8.0** - 单Agent深度思考循环架构

[![GitHub](https://img.shields.io/badge/GitHub-winterswang/company--deep--analysis-blue)](https://github.com/winterswang/company-deep-analysis)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ✨ 核心特性

### 1. 单Agent深度思考循环 ⭐

```
输入: base_report_generator 输出
      ↓
第N轮: 反思 → 行动(工具) → 推理 → 评分
      ↓
结束条件: 10轮上限 或 连续2轮无新发现
      ↓
输出: 各维度分析结果 + 思维链
```

### 2. 四维分析框架

| 维度 | 描述 |
|------|------|
| **财务异常分析** | 识别财务指标异常，验证假设 |
| **经营洞察分析** | 深入理解商业模式和竞争力 |
| **护城河识别** | 分析企业竞争优势和可持续性 |
| **可持续性评估** | 评估长期投资价值 |

### 3. 完整数据源集成

| 数据源 | 质量 | 内容 |
|--------|------|------|
| **AkShare** | P0 | 财务数据、行情数据 |
| **雪球爬虫** | P0-P2 | 讨论、资讯、公告、专栏 |
| **Tavily** | P2 | 实时搜索 |
| **Exa** | P2 | 深度搜索 |

---

## 📁 目录结构

```
company-deep-analysis/
├── SKILL.md                      # 主Skill文档
├── README.md                     # 本文件
│
├── skills/                        # 技能模块 (V8.0)
│   └── company-deep-analysis/
│       ├── data_collector/        # 数据收集服务
│       │   ├── tools.py            # 数据获取API
│       │   └── schemas.py          # 数据格式定义
│       │
│       ├── base_report_generator/  # 基础报告生成
│       │   ├── generator.py        # 报告生成器
│       │   └── schemas.py          # 报告结构
│       │
│       ├── analysis_loop/          # 分析引擎 (V8.0核心)
│       │   ├── engine.py           # 深度思考循环引擎
│       │   ├── prompts.py          # 思考提示词
│       │   └── schemas.py          # 分析维度定义
│       │
│       └── final_report_generator/ # 最终报告 (待开发)
│
└── docs/                          # 需求文档
    └── requirements/
        └── company-deep-analysis/
            ├── 01-data-collector.md
            ├── 02-base-report-generator.md
            ├── 03-analysis-engine.md
            └── 04-report-generator.md
```

---

## 🔄 版本历史

| 版本 | 日期 | 核心改进 |
|------|------|----------|
| **V8.0** | 2026-03-22 | 单Agent深度思考循环架构 |
| V6.3.2 | 2026-03-12 | 本地数据支持（PDF/Excel） |
| V6.3.1 | 2026-03-11 | 辩证式分析框架落地 |
| V4.4 | 2026-03-14 | 早期版本 |

---

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/winterswang/company-deep-analysis.git

# 安装依赖
pip install akshare pandas playwright httpx

# 安装浏览器
playwright install chromium
```

---

## 🚀 使用方法

### 命令行

```bash
python3 -m skills.company-deep-analysis.base_report_generator \
    --company "贵州茅台" \
    --stock 600519 \
    --market A
```

### 代码调用

```python
from skills.company_deep_analysis import CompanyDeepAnalysis

analyzer = CompanyDeepAnalysis({
    "max_rounds": 10,
    "new_findings_threshold": 2,
    "dimensions": [
        "financial_anomaly",
        "business_insight",
        "moat识别",
        "sustainability"
    ]
})

result = analyzer.analyze("贵州茅台", "600519", "A")
```

---

## 🔧 依赖

| 组件 | 用途 |
|------|------|
| akshare | 财务数据API |
| pandas | 数据处理 |
| playwright | 网页爬取 |
| 百炼 GLM-5 | LLM分析 |
| Tavily | 实时搜索 |
| Exa | 深度搜索 |

---

## 📄 License

MIT

---

## 👤 Author

**winterswang**

- GitHub: [@winterswang](https://github.com/winterswang)

---

## 🙏 致谢

- [AkShare](https://github.com/akfamily/akshare) - 财务数据API
- [雪球](https://xueqiu.com) - 专业投资者社区
- [DeerFlow](https://github.com/winterswang/deer-flow-analysis) - AI Agent 框架

---

*版本: V8.0 | 更新: 2026-03-22*