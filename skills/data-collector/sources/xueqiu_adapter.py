"""Xueqiu (雪球) adapter using xueqiu-analyzer-skill."""

import sys
import os
import json as json_lib
import subprocess

from sources.base import DataSourceResult


class XueqiuAdapter:
    """Adapter for Xueqiu using xueqiu-analyzer-skill."""
    
    def __init__(self):
        self.source_name = "雪球"
        self.source_type = "crawler"
        self.xueqiu_project = "/root/.openclaw/workspace/xueqiu-analyzer-skill"
        self.python = "/usr/bin/python3"
    
    async def fetch(self, query: dict) -> DataSourceResult:
        """Fetch data from Xueqiu."""
        try:
            ticker = query.get("ticker", "")
            company = query.get("company", "")
            
            if not company and not ticker:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="No company or ticker provided"
                )
            
            symbol = ticker if ticker else company
            
            if not os.path.exists(self.xueqiu_project):
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="Xueqiu project not found"
                )
            
            # Simple script - just like the demo!
            script = f'''
import sys
sys.path.insert(0, "{self.xueqiu_project}/scripts")

import json
import logging
logging.disable(100)

from stock_crawler_v2 import XueqiuStockCrawlerV2

crawler = XueqiuStockCrawlerV2()
result = crawler.crawl("{symbol}")

discussions = []
if result and result.discussions:
    for d in result.discussions[:10]:
        discussions.append({{
            "content": d.content[:500] if d.content else "",
            "author": d.author,
            "time": d.time
        }})

news = []
if result and result.news:
    for n in result.news[:10]:
        news.append({{
            "title": n.title[:200] if n.title else "",
            "content": n.content[:500] if n.content else "",
            "link": n.link
        }})

notices = []
if result and result.notices:
    for n in result.notices[:10]:
        notices.append({{
            "title": n.title[:200] if n.title else "",
            "link": n.link
        }})

data = {{
    "discussions": discussions,
    "news": news,
    "notices": notices
}}

print("XUEQIU_JSON_START")
print(json.dumps(data, ensure_ascii=False))
print("XUEQIU_JSON_END")
'''
            
            result = subprocess.run(
                [self.python, "-c", script],
                capture_output=True,
                text=True,
                timeout=1800,
                cwd=f"{self.xueqiu_project}/scripts"
            )
            
            if result.returncode != 0:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error=f"Crawler error: {result.stderr[:150]}"
                )
            
            # Parse JSON
            output = result.stdout
            if "XUEQIU_JSON_START" in output:
                try:
                    json_start = output.find("XUEQIU_JSON_START") + len("XUEQIU_JSON_START")
                    json_end = output.find("XUEQIU_JSON_END")
                    json_str = output[json_start:json_end].strip()
                    crawled_data = json_lib.loads(json_str)
                except Exception as e:
                    return DataSourceResult(
                        source_name=self.source_name,
                        source_type=self.source_type,
                        data=[],
                        success=False,
                        error=f"JSON error: {str(e)[:100]}"
                    )
            else:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="No JSON output"
                )
            
            # Convert
            data = []
            
            for d in crawled_data.get("discussions", []):
                data.append({
                    "type": "discussion",
                    "source": "雪球",
                    "content": d.get("content", ""),
                    "author": d.get("author", ""),
                    "time": d.get("time", ""),
                    "symbol": symbol
                })
            
            for n in crawled_data.get("news", []):
                data.append({
                    "type": "news",
                    "source": "雪球",
                    "title": n.get("title", ""),
                    "content": n.get("content", ""),
                    "link": n.get("link", ""),
                    "symbol": symbol
                })
            
            for nt in crawled_data.get("notices", []):
                data.append({
                    "type": "notice",
                    "source": "雪球",
                    "title": nt.get("title", ""),
                    "link": nt.get("link", ""),
                    "symbol": symbol
                })
            
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=data,
                success=True
            )
            
        except subprocess.TimeoutExpired:
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error="Crawler timeout"
            )
        except Exception as e:
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=str(e)[:200]
            )
