# Company Deep Analysis Skill

上市公司深度价值投资分析技能 - 辩证式分析框架 + 本地数据支持

---

## 🚀 最新版本

**V6.3.2** - 本地数据支持（PDF/Excel）+ 辩证式分析框架

[![GitHub](https://img.shields.io/badge/GitHub-winterswang/company--deep--analysis-blue)](https://github.com/winterswang/company-deep-analysis)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ✨ 核心特性

### 1. 辩证式分析框架 ⭐

```
分析师（Analyst）←→ 挑战者（Challenger）
     ↓                    ↓
  生成报告            评估质量（打分）
     ↓                    ↓
  改进报告    ←    提出挑战点 + ToDo
     ↓                    ↓
  直到评分 >= 85分
```

### 2. 本地数据支持 ⭐

| 类型 | 格式 | 提取方式 |
|------|------|----------|
| **PDF** | .pdf | pdfplumber |
| **Excel** | .xlsx, .xls | pandas |
| **文本** | .md, .txt | 直接读取 |

### 3. 完整数据源集成

| 数据源 | 质量 | 内容 |
|--------|------|------|
| **本地文件** | P0 | PDF财报、Excel估值模型 |
| **雪球爬虫** | P0-P2 | 讨论、资讯、公告、专栏 |
| **AkShare** | P0 | 财务数据、行情数据 |
| **Tavily** | P2 | 实时搜索 |
| **Exa** | P2 | 深度搜索 |

### 4. 雪球数据质量评估

| 数据类型 | 判断标准 | 质量等级 |
|----------|----------|----------|
| 专栏文章 | 内容≥300字符 | P0 |
| 公告 | 固定 | P1 |
| 讨论 | >300字符 | P1 |
| 讨论 | 150-300字符 | P2 |
| 讨论 | <150字符 | P4（丢弃）|

---

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/winterswang/company-deep-analysis.git

# 安装依赖
pip install pdfplumber PyPDF2 pandas openpyxl playwright

# 安装浏览器
playwright install chromium
```

---

## 🚀 使用方法

### 命令行

```bash
python3 core/analyzer_v631.py --company Nintendo --ticker NTDOY --market us
```

### 代码调用

```python
from core.analyzer_v631 import DialecticalAnalyzerV631

analyzer = DialecticalAnalyzerV631({
    "max_iterations": 5,
    "score_threshold": 85,
    "min_valid_data": 8
})

report, success = analyzer.analyze_with_data_collection(
    company="Nintendo",
    ticker="NTDOY",
    market="us"
)
```

### 本地文件处理

```python
# 将文件放到 data/local/ 目录
# PDF财报
data/local/nintendo_q3_report.pdf

# Excel估值模型
data/local/nintendo_valuation_model.xlsx

# 自动加载并提取数据
```

---

## 📁 目录结构

```
company-deep-analysis/
├── SKILL.md                      # 主Skill文档
├── README.md                     # 本文件
│
├── docs/                         # 文档
│   ├── REQUIREMENTS_V63.md       # V6.3需求文档
│   ├── STRUCTURE_V632.md         # V6.3.2结构详情
│   ├── CHANGELOG.md              # 变更日志
│   └── METHODOLOGY.md            # 方法论
│
├── core/                         # 核心模块
│   ├── analyzer_v631.py          # V6.3.1主分析器
│   ├── analyst.py                # 分析师角色
│   ├── challenger.py             # 挑战者角色
│   └── llm_client.py             # LLM客户端
│
├── scripts/                      # 脚本
│   ├── data_collector_v63_fixed.py # 数据收集器
│   ├── local_data_loader.py      # 本地数据加载器
│   └── xueqiu_quality_evaluator.py # 雪球质量评估
│
├── config/                       # 配置
│   └── data_sources_v62.py       # 数据源配置
│
├── data/local/                   # 本地数据
│   ├── *.pdf                     # PDF财报
│   └── *.xlsx                    # Excel估值模型
│
└── reports/                      # 分析报告
    ├── v631/                     # V6.3.1报告
    └── archived/                 # 历史报告
```

---

## 📊 分析流程

```
【阶段1: 数据收集】
    ├─ 本地数据加载（PDF/Excel）⭐
    ├─ 雪球爬虫（讨论/资讯/公告/专栏）
    ├─ AkShare（财务数据）
    ├─ Tavily（实时搜索）
    └─ Exa（深度搜索）
        ↓
【阶段2: 数据质量检查】
    ├─ P2及以上 → 保留
    └─ P3及以下 → 丢弃
        ↓
【阶段3: 辩证式分析】⭐
    │
    │  第1轮：分析师生成初始报告
    │  第2轮：挑战者评估 → 执行ToDo → 分析师改进
    │  第3轮：挑战者评估 → 执行ToDo → 分析师改进
    │  ...
    │  直到评分>=85分
    ↓
【阶段4: 输出报告】
    └─ 每个章节：初始→挑战→解答→最终
```

---

## 📈 输出格式

### 投资分析报告

```markdown
# {公司名} 投资价值分析报告

## 📊 辩证过程统计
| 轮次 | 评分 | 挑战点数 | ToDo数 |

## 一、执行摘要
### 【初始版本】
### 【挑战点】
### 【解答】
### 【最终版本】

... (七个章节)

## 📎 附录：数据引用报告
```

### 数据引用报告

```markdown
# 数据引用清单报告

## 一、数据收集统计
## 二、本地数据详情
## 三、雪球数据详情
## 四、数据质量评估
```

---

## 📋 分析报告

| 公司 | 版本 | 评分 | 日期 | 链接 |
|------|------|------|------|------|
| 任天堂 | V6.3.2 | **94分** | 2026-03-11 | [Gist](https://gist.github.com/winterswang/56041b2de66cd94fdac50da1334f5baf) |
| 任天堂 | V6.3.1 | 97分 | 2026-03-11 | [Gist](https://gist.github.com/winterswang/e3a12788ca3c2db8dddc7a9f3005a959) |
| 任天堂 | V6.3 | - | 2026-03-11 | [Gist](https://gist.github.com/winterswang/84ed2f703bcdd0e2781a863d46f5f169) |

---

## 🔄 版本历史

| 版本 | 日期 | 核心改进 |
|------|------|----------|
| **V6.3.2** | 2026-03-12 | 本地数据支持（PDF/Excel） |
| V6.3.1 | 2026-03-11 | 辩证式分析框架落地 |
| V6.3 | 2026-03-11 | 完整数据源集成 |
| V6.2 | 2026-03-11 | 数据质量控制 |
| V6.1 | 2026-03-11 | 辩证式分析框架设计 |
| V5.0 | 2026-03-11 | 迭代式分析 |
| V4.3 | 2026-03-11 | 数据质量管理机制 |

---

## 🔧 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| max_iterations | 5 | 最大辩证轮数 |
| score_threshold | 85 | 终止阈值 |
| min_valid_data | 8 | 最少有效数据数 |

---

## 📦 依赖

| 组件 | 用途 |
|------|------|
| pdfplumber | PDF提取 |
| PyPDF2 | PDF备选 |
| pandas | Excel处理 |
| openpyxl | Excel备选 |
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
- Project: [company-deep-analysis](https://github.com/winterswang/company-deep-analysis)

---

## 🙏 致谢

- [DeerFlow](https://github.com/winterswang/deer-flow-analysis) - AI Agent 框架
- [AkShare](https://github.com/akfamily/akshare) - 财务数据API
- [雪球](https://xueqiu.com) - 专业投资者社区

---

*版本: V6.3.2 | 更新: 2026-03-12*