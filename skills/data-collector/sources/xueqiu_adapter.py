"""Xueqiu (雪球) adapter for financial data and discussions."""

import sys
import os
# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sources.base import DataSourceResult


class XueqiuAdapter:
    """Adapter for Xueqiu (雪球) data.
    
    Uses xueqiu-analyzer-skill to crawl:
    - Stock discussions (评论)
    - News (资讯)
    - Notices (公告)
    - Articles (文章)
    """
    
    def __init__(self):
        self.source_name = "雪球"
        self.source_type = "crawler"
        self.xueqiu_project = os.path.join(project_root, "..", "..", "..", "xueqiu-analyzer-skill")
    
    async def fetch(self, query: dict) -> DataSourceResult:
        """Fetch data from Xueqiu."""
        try:
            company = query.get("company", "")
            ticker = query.get("ticker", "")
            
            if not company and not ticker:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="No company or ticker provided"
                )
            
            # Use ticker as symbol (e.g., "PDD" for 拼多多)
            symbol = ticker if ticker else company
            
            # Check if xueqiu-analyzer-skill project exists
            if not os.path.exists(self.xueqiu_project):
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error=f"Xueqiu analyzer project not found at {self.xueqiu_project}"
                )
            
            # Add xueqiu-analyzer-skill to path
            sys.path.insert(0, os.path.join(self.xueqiu_project, "scripts"))
            
            try:
                # Import the crawler from xueqiu-analyzer-skill
                from stock_crawler_v2 import XueqiuStockCrawlerV2
                
                # Create crawler instance (headless mode)
                crawler = XueqiuStockCrawlerV2(headless=True)
                
                # Crawl the stock
                stock_info = crawler.crawl(
                    symbol=symbol,
                    max_discussions=20,
                    max_news=20,
                    max_notices=10
                )
                
                if stock_info is None:
                    return DataSourceResult(
                        source_name=self.source_name,
                        source_type=self.source_type,
                        data=[],
                        success=False,
                        error=f"Failed to crawl {symbol} from Xueqiu"
                    )
                
                # Convert to our data format
                data = []
                
                # Add discussions
                for d in stock_info.discussions[:10]:
                    data.append({
                        "type": "discussion",
                        "source": "雪球",
                        "title": d.content[:100] if d.content else "",
                        "content": d.content,
                        "author": d.author,
                        "created_at": str(d.created_at) if d.created_at else "",
                        "likes": d.likes,
                        "comments": d.comments,
                        "symbol": symbol
                    })
                
                # Add news
                for n in stock_info.news[:10]:
                    data.append({
                        "type": "news",
                        "source": "雪球",
                        "title": n.title,
                        "content": n.content,
                        "published_at": str(n.published_at) if n.published_at else "",
                        "symbol": symbol
                    })
                
                # Add notices
                for nt in stock_info.notices[:5]:
                    data.append({
                        "type": "notice",
                        "source": "雪球",
                        "title": nt.title,
                        "content": nt.content,
                        "published_at": str(nt.published_at) if nt.published_at else "",
                        "symbol": symbol
                    })
                
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=data,
                    success=True
                )
                
            except ImportError as e:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error=f"Cannot import Xueqiu crawler: {e}"
                )
            except Exception as e:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error=f"Error crawling Xueqiu: {e}"
                )
            
        except Exception as e:
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=str(e)
            )
