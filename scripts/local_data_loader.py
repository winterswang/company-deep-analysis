"""
V6.3.2 本地数据加载器

支持从本地文件加载数据：
- PDF文件
- Excel文件
- 文本文件
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analyzer_v62 import DataPoint


class LocalDataLoader:
    """本地数据加载器"""
    
    def __init__(self, data_dir: str = "data/local"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_all(self, company: str = None) -> List[DataPoint]:
        """加载所有本地数据
        
        Args:
            company: 公司名称（用于过滤相关文件）
        """
        
        data_points = []
        company_lower = company.lower() if company else ""
        
        # 遍历所有文件
        for file_path in self.data_dir.iterdir():
            if file_path.is_file():
                # 检查文件是否与目标公司相关
                file_name_lower = file_path.name.lower()
                if company_lower and company_lower not in file_name_lower:
                    # 如果指定了公司名，跳过不相关的文件
                    continue
                
                suffix = file_path.suffix.lower()
                
                if suffix == '.pdf':
                    data_points.extend(self._load_pdf(file_path, company))
                elif suffix in ['.xlsx', '.xls']:
                    data_points.extend(self._load_excel(file_path, company))
                elif suffix in ['.md', '.txt']:
                    data_points.extend(self._load_text(file_path, company))
        
        return data_points
    
    def _load_pdf(self, file_path: Path, company: str = None) -> List[DataPoint]:
        """加载PDF文件"""
        
        data_points = []
        
        try:
            import pdfplumber
            
            with pdfplumber.open(file_path) as pdf:
                # 提取文本
                text_content = []
                for i, page in enumerate(pdf.pages[:20]):
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                
                full_text = '\n\n'.join(text_content)
                
                # 创建数据点
                data_points.append(DataPoint(
                    name=f"PDF内容: {file_path.stem}",
                    value=full_text[:10000],
                    source=f"本地PDF: {file_path.name}",
                    quality="P0",
                    validity=datetime.now().strftime("%Y-%m-%d"),
                    notes=f"文件: {file_path.name}, 页数: {len(pdf.pages)}"
                ))
                
                # 尝试提取关键财务数据
                data_points.extend(self._extract_financial_data(full_text, file_path.name, company))
                
        except Exception as e:
            print(f"PDF加载失败: {e}")
        
        return data_points
    
    def _load_excel(self, file_path: Path, company: str = None) -> List[DataPoint]:
        """加载Excel文件"""
        
        data_points = []
        
        try:
            import pandas as pd
            
            excel_file = pd.ExcelFile(file_path)
            
            # 创建概览数据点
            data_points.append(DataPoint(
                name=f"Excel概览: {file_path.stem}",
                value=f"工作表数: {len(excel_file.sheet_names)}",
                source="本地Excel",
                quality="P0",
                validity=datetime.now().strftime("%Y-%m-%d"),
                notes=f"工作表: {', '.join(excel_file.sheet_names[:10])}..."
            ))
            
            # 提取关键工作表数据
            key_sheets = ['Valuation', 'Model', 'Actuals', '5 yr DCF', 'SOTP', 'Cash']
            
            for sheet_name in excel_file.sheet_names:
                if sheet_name in key_sheets:
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                        
                        # 转换为文本摘要
                        summary = f"工作表: {sheet_name}\n"
                        summary += f"行数: {len(df)}, 列数: {len(df.columns)}\n"
                        summary += f"列名: {', '.join(df.columns.astype(str)[:10])}\n"
                        summary += f"\n数据预览:\n{df.head(10).to_string()}"
                        
                        data_points.append(DataPoint(
                            name=f"Excel: {sheet_name}",
                            value=summary[:5000],
                            source="本地Excel",
                            quality="P0",
                            validity=datetime.now().strftime("%Y-%m-%d"),
                            notes=f"文件: {file_path.name}"
                        ))
                    except Exception as e:
                        print(f"工作表 {sheet_name} 加载失败: {e}")
            
        except Exception as e:
            print(f"Excel加载失败: {e}")
        
        return data_points
    
    def _load_text(self, file_path: Path) -> List[DataPoint]:
        """加载文本文件"""
        
        data_points = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            data_points.append(DataPoint(
                name=f"文本内容: {file_path.stem}",
                value=content[:10000],
                source="本地文本",
                quality="P1",
                validity=datetime.now().strftime("%Y-%m-%d"),
                notes=f"文件: {file_path.name}"
            ))
            
        except Exception as e:
            print(f"文本加载失败: {e}")
        
        return data_points
    
    def _extract_financial_data(self, text: str, source: str, company: str = None) -> List[DataPoint]:
        """从文本中提取财务数据"""
        
        import re
        
        data_points = []
        
        # 通用财务指标提取模式（支持多种货币和单位）
        patterns = {
            '营收': [
                r'(?:营收|营业收入|Revenue|Net Sales)[：:\s]*([\d,\.]+)\s*(?:亿元|十亿元|亿|B|billion)',
                r'(?:营收|营业收入|Revenue)[：:\s]*\$?([\d,\.]+)\s*(?:亿美元|USD)?',
            ],
            '净利润': [
                r'(?:净利润|归母净利润|Net Income|Net Profit)[：:\s]*([\d,\.]+)\s*(?:亿元|十亿元|亿|B|billion)',
                r'(?:净利润|Net Income)[：:\s]*\$?([\d,\.]+)\s*(?:亿美元|USD)?',
            ],
            '毛利率': [
                r'(?:毛利率|Gross Margin|Gross Profit Margin)[：:\s]*([\d\.]+)\s*%',
            ],
            'ROE': [
                r'(?:ROE|净资产收益率|Return on Equity)[：:\s]*([\d\.]+)\s*%',
            ],
            'ROIC': [
                r'(?:ROIC|投入资本回报率|Return on Invested Capital)[：:\s]*([\d\.]+)\s*%',
            ],
            '营业利润': [
                r'(?:营业利润|Operating Income|Operating Profit)[：:\s]*([\d,\.]+)\s*(?:亿元|十亿元|亿|B|billion)',
            ],
        }
        
        for name, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    value = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    data_points.append(DataPoint(
                        name=name,
                        value=value,
                        source=f"本地PDF提取: {source}",
                        quality="P0",
                        validity=datetime.now().strftime("%Y-%m-%d"),
                        notes="从PDF自动提取"
                    ))
                    break  # 找到匹配就跳出
        
        return data_points


# 测试
if __name__ == "__main__":
    loader = LocalDataLoader("/root/.openclaw/workspace/deer-flow-analysis/skills/custom/company-deep-analysis/data/local")
    data_points = loader.load_all()
    
    print(f"加载了 {len(data_points)} 条本地数据")
    for dp in data_points[:5]:
        print(f"  - {dp.name}: {dp.value[:50]}... [{dp.quality}]")