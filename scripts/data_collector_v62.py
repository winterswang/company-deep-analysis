"""
V6.2 数据收集器

整合数据源：
1. AkShare (P0) - 财务数据
2. 雪球爬虫 (P0) - 专业分析
3. 本地数据 (P0) - link collection
4. Tavily (P2) - 搜索引擎
5. Exa (P2) - 深度搜索
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.data_sources_v62 import DataSourceType, get_data_quality
from core.analyzer_v62 import DataPoint


class DataCollectorV62:
    """V6.2 数据收集器"""
    
    def __init__(self):
        self.collected_data: List[DataPoint] = []
        self.local_data_path = Path("/root/.openclaw/workspace/ideas-and-notes/inbox")
    
    def collect_all(self, company: str, ticker: str = None) -> List[DataPoint]:
        """收集所有数据"""
        print(f"\n【数据收集】目标: {company}")
        print("=" * 60)
        
        # 1. AkShare财务数据 (P0)
        self._collect_from_akshare(company, ticker)
        
        # 2. 雪球专业分析 (P0)
        self._collect_from_xueqiu(company)
        
        # 3. 本地数据 (P0)
        self._collect_from_local(company)
        
        # 4. Tavily搜索 (P2)
        self._collect_from_tavily(company)
        
        # 5. Exa深度搜索 (P2)
        self._collect_from_exa(company)
        
        return self.collected_data
    
    def _collect_from_akshare(self, company: str, ticker: str = None):
        """从AkShare获取财务数据"""
        print("\n[AkShare P0] 财务数据...")
        
        try:
            import akshare as ak
            
            # 美股数据
            if ticker:
                try:
                    # 获取美股财务数据
                    df = ak.stock_us_fundamental(symbol=ticker)
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            self.collected_data.append(DataPoint(
                                name=row.get('指标', '未知'),
                                value=str(row.get('值', '')),
                                source="AkShare",
                                quality="P0",
                                timestamp=datetime.now().isoformat(),
                                validity="最新",
                                notes="美股财务数据"
                            ))
                        print(f"  ✅ 获取 {len(df)} 条财务数据")
                except Exception as e:
                    print(f"  ⚠️ AkShare获取失败: {e}")
            
            # 如果没有ticker，尝试搜索
            if not ticker:
                print(f"  ⚠️ 未提供ticker，跳过AkShare")
                
        except ImportError:
            print("  ⚠️ AkShare未安装")
        except Exception as e:
            print(f"  ⚠️ AkShare错误: {e}")
    
    def _collect_from_xueqiu(self, company: str):
        """从雪球获取专业分析"""
        print("\n[雪球 P0] 专业分析...")
        
        try:
            # 检查是否有雪球分析报告
            xueqiu_report_path = Path(f"/root/.openclaw/workspace/xueqiu-analyzer-skill/data/reports")
            if xueqiu_report_path.exists():
                reports = list(xueqiu_report_path.glob(f"*{company}*.md"))
                if reports:
                    latest_report = max(reports, key=lambda x: x.stat().st_mtime)
                    self.collected_data.append(DataPoint(
                        name="雪球分析报告",
                        value=latest_report.name,
                        source="雪球爬虫",
                        quality="P0",
                        timestamp=datetime.now().isoformat(),
                        validity=latest_report.stat().st_mtime,
                        notes=f"报告路径: {latest_report}"
                    ))
                    print(f"  ✅ 找到雪球分析报告: {latest_report.name}")
                else:
                    print(f"  ⚠️ 未找到{company}的雪球分析报告")
            else:
                print("  ⚠️ 雪球报告目录不存在")
                
        except Exception as e:
            print(f"  ⚠️ 雪球数据获取失败: {e}")
    
    def _collect_from_local(self, company: str):
        """从本地数据获取"""
        print("\n[本地数据 P0] 用户收藏...")
        
        try:
            if self.local_data_path.exists():
                # 搜索最近几天文件夹中包含公司名的文件
                found_files = []
                for date_dir in sorted(self.local_data_path.iterdir(), reverse=True)[:7]:  # 最近7天
                    if date_dir.is_dir():
                        for md_file in date_dir.glob("*.md"):
                            if company.lower() in md_file.name.lower():
                                found_files.append(md_file)
                
                if found_files:
                    for f in found_files[:3]:  # 最多3个文件
                        self.collected_data.append(DataPoint(
                            name="本地收藏文章",
                            value=f.name,
                            source="本地数据",
                            quality="P0",
                            timestamp=datetime.now().isoformat(),
                            validity=str(f.stat().st_mtime),
                            notes=f"路径: {f}"
                        ))
                    print(f"  ✅ 找到 {len(found_files)} 个本地收藏文件")
                else:
                    print(f"  ⚠️ 未找到{company}相关的本地收藏")
            else:
                print("  ⚠️ 本地数据目录不存在")
                
        except Exception as e:
            print(f"  ⚠️ 本地数据获取失败: {e}")
    
    def _collect_from_tavily(self, company: str):
        """从Tavily搜索"""
        print("\n[Tavily P2] 搜索...")
        
        try:
            # 检查API key
            tavily_key = os.environ.get("TAVILY_API_KEY", "")
            if not tavily_key:
                # 尝试从.env加载
                env_path = Path("/root/.openclaw/workspace/deer-flow-analysis/.env")
                if env_path.exists():
                    with open(env_path) as f:
                        for line in f:
                            if line.startswith("TAVILY_API_KEY="):
                                tavily_key = line.strip().split("=", 1)[1]
                                break
            
            if tavily_key:
                # 这里可以实际调用Tavily API
                print(f"  ✅ Tavily API已配置，可搜索 {company} 相关信息")
                # 添加搜索任务到数据
                self.collected_data.append(DataPoint(
                    name="Tavily搜索",
                    value=f"可搜索{company}相关信息",
                    source="Tavily",
                    quality="P2",
                    timestamp=datetime.now().isoformat(),
                    validity="实时",
                    notes="需要时实际调用"
                ))
            else:
                print("  ⚠️ Tavily API未配置")
                
        except Exception as e:
            print(f"  ⚠️ Tavily配置失败: {e}")
    
    def _collect_from_exa(self, company: str):
        """从Exa搜索"""
        print("\n[Exa P2] 深度搜索...")
        
        try:
            # 检查API key
            exa_key = os.environ.get("EXA_API_KEY", "")
            if not exa_key:
                env_path = Path("/root/.openclaw/workspace/deer-flow-analysis/.env")
                if env_path.exists():
                    with open(env_path) as f:
                        for line in f:
                            if line.startswith("EXA_API_KEY="):
                                exa_key = line.strip().split("=", 1)[1]
                                break
            
            if exa_key:
                print(f"  ✅ Exa API已配置，可深度搜索 {company}")
                self.collected_data.append(DataPoint(
                    name="Exa搜索",
                    value=f"可深度搜索{company}相关研究",
                    source="Exa",
                    quality="P2",
                    timestamp=datetime.now().isoformat(),
                    validity="实时",
                    notes="需要时实际调用"
                ))
            else:
                print("  ⚠️ Exa API未配置")
                
        except Exception as e:
            print(f"  ⚠️ Exa配置失败: {e}")
    
    def get_summary(self) -> str:
        """获取数据收集摘要"""
        valid = [d for d in self.collected_data if d.is_valid()]
        invalid = [d for d in self.collected_data if not d.is_valid()]
        
        return f"""
数据收集摘要：
- 总数据: {len(self.collected_data)} 条
- 有效数据 (P2及以上): {len(valid)} 条
- 低质量数据 (P3及以下): {len(invalid)} 条

有效数据来源:
{chr(10).join([f'  [{d.quality}] {d.source}: {d.name}' for d in valid])}
"""


if __name__ == "__main__":
    collector = DataCollectorV62()
    data = collector.collect_all("Nintendo", "NTDOY")
    print(collector.get_summary())