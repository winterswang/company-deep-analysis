---
name: data-collector
description: 统一数据收集服务。根据自然语言需求，智能调用多种数据源获取数据，并进行质量评估。输出标准化 JSON，可被其他模块复用。
version: 1.0
---

# Data Collector Skill

## 概述

统一的数据收集服务，能够根据自然语言需求智能收集各类数据。

## 功能

### 1. 多数据源支持

| 数据源 | 类型 | 质量等级 |
|--------|------|----------|
| AkShare | API | P0 |
| Tavily | 搜索 | P2 |

### 2. 质量评估

- **Layer 1**: 来源评级 (P0-P4)
- **Layer 2**: 交叉验证
- **Layer 3**: LLM 深度评估

### 3. 输出格式

```json
{
  "skill": "data-collector",
  "version": "1.0",
  "query": "PDD 2024 财务数据",
  "collected_at": "2026-03-14T20:00:00Z",
  "company": "PDD",
  "ticker": "PDD",
  "market": "us",
  "data": [...],
  "sources_used": [...],
  "quality_assessment": {...}
}
```

## 使用方法

### 命令行

```bash
python -m skills.data_collector.collector "分析 PDD Holdings"
```

### 代码调用

```python
from skills.data_collector import DataCollector

collector = DataCollector()
result = await collector.collect("PDD 2024 财务数据")
```

## 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| query | 自然语言查询 | "PDD 财务数据" |
| company | 公司名称 | "PDD Holdings" |
| ticker | 股票代码 | "PDD" |
| market | 市场 | "us" 或 "cn" |

## 质量评分

综合评分 = 来源可靠性 × 0.4 + 交叉验证 × 0.3 + LLM评估 × 0.3

---

*Version: 1.0 | Updated: 2026-03-14*