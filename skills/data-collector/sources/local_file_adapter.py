"""Local file adapter for cached data."""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.base import DataSourceResult


class LocalFileAdapter:
    """Adapter for reading cached data from local files."""
    
    def __init__(self):
        self.source_name = "本地文件"
        self.source_type = "local"
        # Default cache directories
        self.cache_dirs = [
            "/root/.openclaw/workspace/deer-flow-analysis/skills/custom/company-deep-analysis/data",
            "/tmp/data_collector_cache",
        ]
    
    def set_cache_dir(self, cache_dir: str):
        """Set a custom cache directory."""
        if cache_dir not in self.cache_dirs:
            self.cache_dirs.insert(0, cache_dir)
    
    async def fetch(self, query: dict) -> DataSourceResult:
        """Fetch cached data from local files."""
        try:
            ticker = query.get("ticker", "")
            company = query.get("company", "")
            data_type = query.get("data_type", "financial")  # financial, news, announcements
            
            if not ticker and not company:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="No ticker or company provided"
                )
            
            search_key = ticker.upper() if ticker else company
            
            # Try to find cached files in each cache directory
            for cache_dir in self.cache_dirs:
                cache_path = Path(cache_dir)
                if not cache_path.exists():
                    continue
                
                # Look for files matching the company/ticker
                files = list(cache_path.glob(f"*{search_key}*"))
                
                data = []
                for f in files:
                    if f.suffix == ".json":
                        try:
                            with open(f, "r", encoding="utf-8") as fp:
                                content = json.load(fp)
                                data.append({
                                    "type": "local_cache",
                                    "source": "本地文件",
                                    "filename": f.name,
                                    "path": str(f),
                                    "content": content,
                                    "cached_at": f.stat().st_mtime
                                })
                        except Exception:
                            pass
                
                if data:
                    return DataSourceResult(
                        source_name=self.source_name,
                        source_type=self.source_type,
                        data=data,
                        success=True
                    )
            
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=f"No cached data found for {search_key}"
            )
            
        except Exception as e:
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=str(e)
            )