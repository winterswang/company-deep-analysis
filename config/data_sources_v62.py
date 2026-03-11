"""
V6.2 数据源配置

数据源质量等级：
- AkShare: P0（财务数据）
- 雪球爬虫: P0（专业分析）
- 本地数据（link collection）: P0
- Tavily: P2（搜索引擎）
- Exa: P2（搜索引擎）
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class DataSourceType(Enum):
    """数据源类型"""
    AKSHARE = "akshare"
    XUEQIU = "xueqiu"
    LOCAL = "local"  # 本地数据（link collection）
    TAVILY = "tavily"
    EXA = "exa"


@dataclass
class DataSourceConfig:
    """数据源配置"""
    name: str
    source_type: DataSourceType
    quality: str  # P0-P4
    description: str
    best_for: List[str]  # 最佳使用场景
    

# 数据源质量映射
DATA_SOURCE_QUALITY = {
    DataSourceType.AKSHARE: "P0",      # 财务数据，高质量
    DataSourceType.XUEQIU: "P0",       # 专业分析，高质量
    DataSourceType.LOCAL: "P0",        # 本地数据，用户收藏，高质量
    DataSourceType.TAVILY: "P2",       # 搜索引擎，需验证
    DataSourceType.EXA: "P2",          # 搜索引擎，需验证
}


# 数据源配置
DATA_SOURCES = {
    DataSourceType.AKSHARE: DataSourceConfig(
        name="AkShare",
        source_type=DataSourceType.AKSHARE,
        quality="P0",
        description="开源财经数据接口，提供A股、美股、港股等财务数据",
        best_for=["财务指标", "行情数据", "财务报表"]
    ),
    
    DataSourceType.XUEQIU: DataSourceConfig(
        name="雪球爬虫",
        source_type=DataSourceType.XUEQIU,
        quality="P0",
        description="雪球专业投资者分析文章和分析",
        best_for=["专业分析", "行业观点", "管理层讨论"]
    ),
    
    DataSourceType.LOCAL: DataSourceConfig(
        name="本地数据",
        source_type=DataSourceType.LOCAL,
        quality="P0",
        description="用户收藏的链接和文章（link collection）",
        best_for=["用户关注的内容", "已验证的高质量分析"]
    ),
    
    DataSourceType.TAVILY: DataSourceConfig(
        name="Tavily",
        source_type=DataSourceType.TAVILY,
        quality="P2",
        description="AI优化的搜索引擎",
        best_for=["实时新闻", "行业动态", "补充信息"]
    ),
    
    DataSourceType.EXA: DataSourceConfig(
        name="Exa",
        source_type=DataSourceType.EXA,
        quality="P2",
        description="语义搜索引擎",
        best_for=["深度研究", "相似内容", "补充验证"]
    ),
}


def get_data_quality(source_type: DataSourceType) -> str:
    """获取数据源质量等级"""
    return DATA_SOURCE_QUALITY.get(source_type, "P4")


def get_best_source_for(data_type: str) -> List[DataSourceType]:
    """根据数据类型推荐最佳数据源"""
    recommendations = {
        "财务指标": [DataSourceType.AKSHARE, DataSourceType.XUEQIU],
        "行情数据": [DataSourceType.AKSHARE],
        "专业分析": [DataSourceType.XUEQIU, DataSourceType.LOCAL],
        "行业动态": [DataSourceType.TAVILY, DataSourceType.EXA],
        "管理层讨论": [DataSourceType.XUEQIU, DataSourceType.LOCAL],
        "竞争分析": [DataSourceType.XUEQIU, DataSourceType.TAVILY],
        "估值数据": [DataSourceType.AKSHARE, DataSourceType.XUEQIU],
    }
    return recommendations.get(data_type, [DataSourceType.TAVILY, DataSourceType.EXA])


# 数据获取优先级
DATA_FETCH_PRIORITY = [
    DataSourceType.AKSHARE,    # 首选：财务数据
    DataSourceType.XUEQIU,     # 次选：专业分析
    DataSourceType.LOCAL,      # 本地数据
    DataSourceType.TAVILY,     # 补充：搜索引擎
    DataSourceType.EXA,        # 补充：深度搜索
]


if __name__ == "__main__":
    print("=== 数据源配置 ===")
    for source_type, config in DATA_SOURCES.items():
        print(f"\n{config.name} [{config.quality}]")
        print(f"  描述: {config.description}")
        print(f"  最佳用途: {', '.join(config.best_for)}")