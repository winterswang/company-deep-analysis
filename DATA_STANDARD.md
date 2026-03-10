# 数据标准规范 V2.0

## 目的

确保分析报告中的数据：
1. 来源可靠、可追溯
2. 质量达标、可验证
3. 避免 AI 模型幻觉
4. **数据不足时自动升级检索**

---

## 第一部分：数据源分级

### 1.1 数据源优先级

| 级别 | 来源类型 | 示例 | 可靠性 | 使用规则 |
|------|----------|------|--------|----------|
| **P0** | 官方 | 年报、IR、公告 | ⭐⭐⭐⭐⭐ | 直接使用 |
| **P1** | 专业数据商 | TuShare、AkShare、Bloomberg | ⭐⭐⭐⭐⭐ | 直接使用 |
| **P2** | 权威媒体/专业平台 | 财新、雪球、研报 | ⭐⭐⭐⭐ | 交叉验证后使用 |
| **P3** | 专业自媒体 | 雪球大V、公众号 | ⭐⭐⭐ | 标注偏见风险 |
| **P4** | 普通来源 | 博客、论坛 | ⭐⭐ | 仅作参考 |

### 1.2 数据类型与数据源匹配

| 数据类型 | 允许的数据源级别 | 最低质量要求 | 数据源示例 |
|----------|------------------|--------------|-----------|
| **财务数据** | P0、P1 | A级 | 年报、TuShare、AkShare |
| **行情数据** | P0、P1 | A级 | AkShare、TuShare |
| **行业数据** | P1、P2 | B级 | SNE Research、研报、雪球 |
| **市占率** | P1、P2、P3 | B级 | 研报、雪球专业文章 |
| **管理层信息** | P0、P2 | B级 | 年报、雪球 |
| **观点/分析** | P2、P3、P4 | C级 | 雪球、研报、公众号 |

### 1.3 雪球数据定位

**雪球数据属于 P2-P3 级别**：

| 数据类型 | 级别 | 可靠性评估 | 使用建议 |
|----------|------|-----------|----------|
| **专业大V分析** | P2 | ⭐⭐⭐⭐ | 交叉验证后使用 |
| **公司讨论区** | P3 | ⭐⭐⭐ | 了解市场情绪 |
| **公司新闻/公告** | P2 | ⭐⭐⭐⭐ | 补充信息源 |
| **财务数据** | P2 | ⭐⭐⭐⭐ | 与官方数据对比验证 |

---

## 第二部分：技术接口定义

### 2.1 财务数据接口（AkShare）

**主要财务指标**：
```python
get_financial_summary(code, years=5)
# 返回：营收、净利润、ROE、毛利率、增速
```

**现金流数据**：
```python
get_cashflow_data(code, years=5)
# 返回：经营现金流、资本开支、FCF
```

**估值数据**：
```python
get_valuation_data(code)
# 返回：PE、PB、市值
```

### 2.2 雪球数据接口

**雪球分析爬虫**：
```python
# 位置：/root/.openclaw/workspace/xueqiu-analyzer-skill/
python3 scripts/smart_crawler_v2.py {code}
# 返回：专业分析文章、讨论、新闻
```

**Link Collector**：
```python
# 位置：/root/.openclaw/workspace/link-collector/
python3 collector.py {url}
# 收藏归档文章，提取关键信息
```

### 2.3 数据格式标准

**财务数据**：
```json
{
  "year": 2024,
  "revenue": {"value": 367.26, "unit": "亿元", "source": "AkShare"},
  "net_profit": {"value": 116.68, "unit": "亿元", "source": "AkShare"}
}
```

**雪球分析数据**：
```json
{
  "source": "雪球@用户名",
  "level": "P2",
  "content": "文章摘要...",
  "quality_score": 82,
  "verified": true
}
```

---

## 第三部分：数据质量评估

### 3.1 质量评分维度

| 维度 | 权重 | 评分方法 |
|------|------|----------|
| **准确性** | 30% | 与官方数据一致性 |
| **及时性** | 20% | <1月=100, <3月=80, >3月=50 |
| **完整性** | 20% | 完整=100, 缺失>10%=70 |
| **可追溯性** | 15% | 官方=100, 媒体=80, 估算=50 |
| **偏见性** | 15% | 无偏见=100, 有偏见=50 |

### 3.2 质量评分等级

```
质量得分 = 准确性×30% + 及时性×20% + 完整性×20% + 可追溯性×15% + (1-偏见性)×15%

等级划分：
- A级 (90-100): 高质量，直接使用
- B级 (70-89): 较高质量，谨慎使用
- C级 (50-69): 中等质量，需交叉验证
- D级 (<50): 低质量，禁止使用
```

### 3.3 数据源白名单

```yaml
financial_data:
  whitelist:
    - name: "公司年报"
      level: P0
      reliability: 0.95
      priority: 1
      
    - name: "TuShare Pro"
      level: P1
      reliability: 0.90
      priority: 2
      
    - name: "AkShare"
      level: P1
      reliability: 0.85
      priority: 3

industry_data:
  whitelist:
    - name: "SNE Research"
      level: P1
      reliability: 0.90
      
    - name: "雪球专业文章"
      level: P2
      reliability: 0.75
      criteria: ["作者粉丝>1万", "历史准确率>70%"]
      
    - name: "券商研报"
      level: P2
      reliability: 0.80

opinion_sources:
  whitelist:
    - name: "雪球大V"
      level: P3
      reliability: 0.70
      criteria: ["粉丝>1万", "认证用户优先"]
```

---

## 第四部分：数据质量升级机制 ⭐ V2.0 新增

### 4.1 自动升级触发条件

| 条件 | 触发动作 |
|------|----------|
| 数据质量评分 < B级 | 自动启动升级检索 |
| 关键数据缺失 | 多源补充检索 |
| 数据来源单一 | 添加交叉验证源 |
| 数据时效过期 | 重新获取最新数据 |

### 4.2 升级检索策略

```
数据质量升级流程：

Step 1: 检查当前数据质量
  ├─ 如果 ≥ B级 → 通过
  └─ 如果 < B级 → 进入升级流程

Step 2: 升级检索（按优先级）
  ├─ P0: 公司年报/IR → 获取官方数据
  ├─ P1: TuShare/AkShare → 专业数据API
  ├─ P2: 雪球分析爬虫 → 专业观点和分析
  ├─ P2: Link Collector → 收藏文章提取
  └─ P3: Web搜索 → 补充信息

Step 3: 多源交叉验证
  ├─ 对比不同来源数据
  ├─ 计算数据一致性
  └─ 生成验证报告

Step 4: 质量评估
  ├─ 重新计算质量评分
  └─ 如果仍 < B级 → 标注数据不确定性
```

### 4.3 雪球数据利用策略

**场景1：财务数据补充验证**

```python
def validate_with_xueqiu(code: str, financial_data: dict) -> dict:
    """
    用雪球数据验证财务数据
    
    流程：
    1. 爬取雪球公司分析文章
    2. 提取文章中的财务数据
    3. 与 API 数据对比
    4. 计算一致性得分
    """
    # 爬取雪球分析
    xueqiu_data = crawl_xueqiu_analysis(code)
    
    # 提取财务数据
    extracted_data = extract_financial_from_articles(xueqiu_data)
    
    # 对比验证
    consistency = compare_data(financial_data, extracted_data)
    
    return {
        "consistency_score": consistency,
        "xueqiu_sources": extracted_data["sources"],
        "verified": consistency > 0.9
    }
```

**场景2：行业/市占率数据获取**

```python
def get_industry_data_from_xueqiu(company: str, industry: str) -> dict:
    """
    从雪球获取行业数据
    
    适用：
    - 市占率数据
    - 行业增速
    - 竞争格局分析
    """
    # 搜索雪球相关文章
    articles = search_xueqiu_articles(f"{company} {industry} 市占率")
    
    # 提取关键数据
    data = extract_industry_metrics(articles)
    
    # 评估质量
    quality = assess_data_quality(data)
    
    return {
        "data": data,
        "quality": quality,
        "sources": articles
    }
```

**场景3：管理层/战略信息**

```python
def get_management_info_from_xueqiu(company: str) -> dict:
    """
    从雪球获取管理层信息
    
    适用：
    - 管理层背景
    - 战略方向
    - 市场评价
    """
    # 爬取公司讨论和分析
    discussions = crawl_xueqiu_discussions(company)
    
    # 提取管理层相关信息
    mgmt_info = extract_management_info(discussions)
    
    return mgmt_info
```

### 4.4 升级检索次数限制

| 数据类型 | 最大检索次数 | 超时时间 |
|----------|--------------|----------|
| 财务数据 | 3次 | 60秒 |
| 行业数据 | 5次 | 120秒 |
| 市占率 | 5次 | 120秒 |
| 管理层信息 | 3次 | 60秒 |

### 4.5 升级失败处理

```markdown
如果数据质量仍不达标：

1. **明确标注数据不确定性**
   - 在报告中标注"数据质量：C级"
   - 说明数据来源和局限性

2. **降低决策权重**
   - C级数据不作为核心决策依据
   - 仅作为参考信息

3. **建议用户手动验证**
   - 提供验证建议
   - 推荐可靠数据源
```

---

## 第五部分：验证规则与流程

### 5.1 数据验证流程

```
┌─────────────────────────────────────────────┐
│           数据验证流程                        │
├─────────────────────────────────────────────┤
│                                             │
│  1. 数据源检查                               │
│     └─ 是否在白名单？                        │
│                                             │
│  2. 数据级别检查                             │
│     └─ 是否符合数据类型要求？                 │
│                                             │
│  3. 数据质量评分                             │
│     ├─ 如果 ≥ B级 → 通过                     │
│     └─ 如果 < B级 → 触发升级检索             │
│                                             │
│  4. 交叉验证                                 │
│     ├─ 多源数据对比                          │
│     └─ 雪球数据验证                          │
│                                             │
│  5. 时效性检查                               │
│     └─ 财务数据不超过3个月                    │
│                                             │
│  6. 偏见识别                                 │
│     └─ 观点类数据标注风险                     │
│                                             │
└─────────────────────────────────────────────┘
```

### 5.2 验证检查清单

**财务数据必查**：
- [ ] 数据来源是否为 P0/P1？
- [ ] 是否标注来源 API 接口？
- [ ] 是否标注获取时间？
- [ ] 数据是否在3个月内？
- [ ] 质量评分是否 ≥ B级？
- [ ] 是否需要雪球数据交叉验证？

**行业数据必查**：
- [ ] 数据来源是否在白名单？
- [ ] 是否需要交叉验证？
- [ ] 是否触发升级检索？
- [ ] 雪球专业文章是否已检索？

---

## 第六部分：置信度与标注

### 6.1 置信度分类

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| **verified** | 已验证，来自 P0/P1 | 财务数据、官方数据 |
| **cross_validated** | 交叉验证通过 | 多源验证后的数据 |
| **estimated** | 估算，需标注依据 | 无法直接获取的数据 |
| **model_hallucination** | 模型幻觉 | **禁止使用** |

### 6.2 数据来源标注格式

**报告末尾必含**：

```markdown
## 📊 数据来源与质量

| 数据项 | 数值 | 来源 | 级别 | 质量 | 验证状态 | 获取时间 |
|--------|------|------|------|------|----------|----------|
| 财务数据 | 2020-2024 | TuShare | P1 | A | ✅ 已验证 | 2026-03-10 |
| 市占率 | 5.5% | 雪球@XX | P2 | B | ✅ 交叉验证 | 2024-12-15 |
| 行业增速 | 3% | 估算 | P4 | C | ⚠️ 待验证 | - |

## ⚠️ 数据质量提示

- ✅ 已通过升级检索获取高质量数据：财务数据、市占率
- ⚠️ C级数据：行业增速为估算，建议手动验证
```

---

## 第七部分：禁止事项

```
❌ 财务数据使用 P2-P4 来源（除非已交叉验证）
❌ 使用 model_hallucination 数据
❌ 使用"可能"、"大概"等模糊表述
❌ 在没有数据时编造数值
❌ 单源数据直接用于关键决策（需交叉验证）
❌ 使用超过3个月的财务数据
❌ 升级检索超时后继续尝试
❌ 使用未验证的雪球数据作为唯一来源
```

---

## 附录：工具支持

### A. 数据验证工具

```bash
# 运行数据质量检查
python3 scripts/data_validator.py --code 300760

# 触发升级检索
python3 scripts/data_validator.py --code 300760 --upgrade
```

### B. 雪球数据获取

```bash
# 爬取雪球分析
python3 /root/.openclaw/workspace/xueqiu-analyzer-skill/scripts/smart_crawler_v2.py 300760

# 收藏归档文章
python3 /root/.openclaw/workspace/link-collector/collector.py {url}
```

### C. 质量报告生成

```python
# 生成数据质量报告
from scripts.data_validator import generate_quality_report

report = generate_quality_report(company_code)
print(report)
```

---

*版本: V2.0*
*更新时间: 2026-03-10*
*核心改进: 数据质量升级机制 + 雪球数据利用*