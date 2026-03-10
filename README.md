# Company Deep Analysis Skill

上市公司深度价值投资分析技能

## 版本

**V4.3** - 数据质量管理机制

## 核心功能

- 🔄 **辩证分析框架**：六轮推导（正题→反题→合题→再否定→估值→决策）
- 📊 **数据质量管理**：五级数据源分级、质量评分、自动升级检索
- 🎯 **护城河分析**：从财务数据透视竞争优势
- 💰 **多维度估值**：DDM、PE、国际对比

## 数据源分级

| 级别 | 来源 | 使用规则 |
|------|------|----------|
| P0 | 官方年报/IR | 直接使用 |
| P1 | TuShare/AkShare | 直接使用 |
| P2 | 雪球/研报 | 交叉验证后使用 |
| P3 | 专业自媒体 | 标注偏见风险 |
| P4 | 普通来源 | 仅作参考 |

## 目录结构

```
company-deep-analysis/
├── SKILL.md              # 分析框架定义
├── DATA_STANDARD.md      # 数据标准规范
├── README.md             # 本文件
├── scripts/
│   ├── data_validator.py # 数据质量验证
│   ├── moat_analyzer.py  # 护城河分析
│   └── run_analysis.py   # 触发词调用
├── config/
│   └── data_sources.yaml # 数据源配置
├── docs/
│   ├── CHANGELOG.md      # 版本变更
│   └── REFERENCES.md     # 参考文档
└── reports/              # 分析报告
```

## 使用方式

### 触发词

```
DeerFlow 深度分析 {公司名称}
DeerFlow 分析 {股票代码}
```

### 示例

```
DeerFlow 深度分析 迈瑞医疗
DeerFlow 分析 300760
```

## 分析报告

| 公司 | 版本 | 日期 | 链接 |
|------|------|------|------|
| 任天堂 | V4.3 | 2026-03-11 | [Gist](https://gist.github.com/winterswang/43a39ecbb997f) |
| 迈瑞医疗 | V4.2 | 2026-03-10 | [Gist](https://gist.github.com/winterswang/fa7c51f9be83bfc5028798d4f4f1fc2f) |

## 版本历史

| 版本 | 日期 | 核心改进 |
|------|------|----------|
| V4.3 | 2026-03-11 | 数据质量管理机制 + 自动升级检索 |
| V4.2 | 2026-03-10 | 强制数据来源标注 |
| V4.1 | 2026-03-10 | 辩证分析框架 |
| V4.0 | 2026-03-10 | 护城河核心分析 |

## 依赖

- DeerFlow 框架
- AkShare / TuShare (财务数据)
- Tavily / Exa (搜索引擎)
- 雪球爬虫 (专业观点)

## License

MIT

## Author

winterswang