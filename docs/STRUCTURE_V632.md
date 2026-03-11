# Company Deep Analysis Skill V6.3.2 结构详情

## 一、版本历史

| 版本 | 日期 | 核心改进 |
|------|------|----------|
| **V6.3.2** | 2026-03-11 | 本地数据支持（PDF/Excel） |
| V6.3.1 | 2026-03-11 | 辩证式分析框架落地 |
| V6.3 | 2026-03-11 | 完整数据源集成 |
| V6.2 | 2026-03-11 | 数据质量控制 |
| V6.1 | 2026-03-11 | 辩证式分析框架设计 |

---

## 二、目录结构

```
company-deep-analysis/
├── SKILL.md                      # 主Skill文档 ⭐
├── README.md                     # 项目说明
│
├── docs/                         # 文档
│   ├── REQUIREMENTS_V63.md       # V6.3需求文档 ⭐
│   ├── CHANGELOG.md              # 变更日志
│   ├── METHODOLOGY.md            # 方法论
│   └── REFERENCES.md             # 参考文献
│
├── core/                         # 核心模块
│   ├── analyzer_v631.py          # V6.3.1主分析器 ⭐
│   ├── analyst.py                # 分析师角色 ⭐
│   ├── challenger.py             # 挑战者角色 ⭐
│   ├── llm_client.py             # LLM客户端
│   └── models.py                 # 数据模型
│
├── scripts/                      # 脚本
│   ├── data_collector_v63_fixed.py # V6.3.2数据收集器 ⭐
│   ├── local_data_loader.py      # 本地数据加载器 ⭐
│   ├── xueqiu_quality_evaluator.py # 雪球质量评估器
│   └── run_v63_full_analysis.py  # 分析入口
│
├── config/                       # 配置
│   └── data_sources_v62.py       # 数据源配置
│
├── data/                         # 数据
│   └── local/                    # 本地数据
│       ├── nintendo_q3_report.pdf
│       └── nintendo_valuation_model.xlsx
│
└── reports/                      # 报告
    └── v631/                     # V6.3.1报告
        ├── Nintendo_v631_report_*.md
        └── Nintendo_v631_数据引用报告_*.md
```

---

## 三、核心组件

### 3.1 分析器 (core/analyzer_v631.py)

```python
class DialecticalAnalyzerV631:
    """V6.3.1 辩证式分析器"""
    
    def __init__(self, config):
        self.max_iterations = config.get("max_iterations", 5)
        self.score_threshold = config.get("score_threshold", 85)
        
        self.analyst = Analyst()
        self.challenger = Challenger()
        self.collector = IntegratedDataCollectorV63()
    
    def analyze_with_data_collection(self, company, ticker, market):
        # 阶段1: 数据收集
        data_points = self.collector.collect_all(company, ticker, market)
        
        # 阶段2: 数据质量检查
        
        # 阶段3: 辩证式分析
        report = self._run_dialectic_analysis(company, evidence)
        
        # 阶段4: 保存报告
        return report, success
```

### 3.2 分析师角色 (core/analyst.py)

```python
class Analyst:
    """分析师角色 - 主链路"""
    
    def generate_initial_report(self, company, data):
        """生成初始报告"""
        
    def improve_report(self, report, challenges, todos, new_evidence):
        """改进报告"""
```

### 3.3 挑战者角色 (core/challenger.py)

```python
class Challenger:
    """挑战者角色 - 副链路"""
    
    def evaluate(self, report, round_number):
        """评估报告，返回Evaluation对象"""
        return Evaluation(
            score=0-100,
            scores_by_dimension={...},
            challenges=[...],
            todos=[...],
            should_continue=True/False
        )
```

### 3.4 数据收集器 (scripts/data_collector_v63_fixed.py)

```python
class IntegratedDataCollectorV63:
    """V6.3.2 完整数据收集器"""
    
    def collect_all(self, company, ticker, market):
        # 0. 本地数据 (P0)
        local_data = LocalDataLoader().load_all()
        
        # 1. 雪球爬虫 (P0)
        xueqiu_data = XueqiuStockPageCrawler().crawl()
        
        # 2. AkShare (P0)
        akshare_data = AkShareFinancialProvider().get_data()
        
        # 3. Tavily (P2)
        tavily_data = self._tavily_search()
        
        # 4. Exa (P2)
        exa_data = self._exa_search()
        
        return all_data
```

### 3.5 本地数据加载器 (scripts/local_data_loader.py)

```python
class LocalDataLoader:
    """本地数据加载器"""
    
    def load_all(self, company):
        """加载所有本地数据"""
        for file in data_dir:
            if suffix == '.pdf':
                data.extend(self._load_pdf(file))
            elif suffix in ['.xlsx', '.xls']:
                data.extend(self._load_excel(file))
```

---

## 四、数据源配置

| 数据源 | 质量 | 内容 | 提取方式 |
|--------|------|------|----------|
| **本地PDF** | P0 | 官方财报 | pdfplumber |
| **本地Excel** | P0 | 估值模型 | pandas |
| **雪球爬虫** | P0-P2 | 讨论/资讯/公告/专栏 | Playwright |
| **AkShare** | P0 | 财务数据 | API |
| **Tavily** | P2 | 实时搜索 | API |
| **Exa** | P2 | 深度搜索 | API |

---

## 五、分析流程

```
【阶段1: 数据收集】
    ├─ 本地数据加载（PDF/Excel）⭐ 新增
    ├─ 雪球爬虫
    ├─ AkShare
    ├─ Tavily
    └─ Exa
        ↓
【阶段2: 数据质量检查】
    ├─ P2及以上 → 保留
    └─ P3及以下 → 丢弃
        ↓
【阶段3: 辩证式分析】⭐
    │
    │  第1轮：分析师生成初始报告
    │  第2轮：挑战者评估 → 执行ToDo → 分析师改进
    │  ...
    │  直到评分>=85分
    ↓
【阶段4: 输出报告】
    └─ 每个章节：初始→挑战→解答→最终
```

---

## 六、输出格式

### 6.1 报告结构

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

### 6.2 数据引用报告

```markdown
# 数据引用清单报告

## 一、数据收集统计
## 二、本地数据详情
## 三、雪球数据详情
## 四、搜索引擎数据
## 五、数据质量评估
```

---

## 七、使用方法

### 命令行

```bash
python3 core/analyzer_v631.py --company Nintendo --ticker NTDOY --market us
```

### 代码调用

```python
from core.analyzer_v631 import DialecticalAnalyzerV631

analyzer = DialecticalAnalyzerV631({"max_iterations": 5})
report, success = analyzer.analyze_with_data_collection(
    company="Nintendo",
    ticker="NTDOY",
    market="us"
)
```

---

## 八、依赖

| 组件 | 依赖 |
|------|------|
| PDF处理 | pdfplumber, PyPDF2 |
| Excel处理 | pandas, openpyxl |
| 网页爬取 | playwright |
| LLM | 百炼 GLM-5 |
| 搜索 | Tavily, Exa |

---

## 九、版本对比

| 功能 | V6.3 | V6.3.1 | V6.3.2 |
|------|------|--------|--------|
| 数据源 | 雪球+AkShare+搜索 | 同左 | **+本地文件** |
| 辩证过程 | 设计 | **实现** | 优化 |
| 分析师/挑战者 | 无 | **实现** | 优化 |
| 本地PDF支持 | ❌ | ❌ | ✅ |
| 本地Excel支持 | ❌ | ❌ | ✅ |

---

**文档版本**: V6.3.2
**更新时间**: 2026-03-12