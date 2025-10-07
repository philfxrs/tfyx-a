from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional


class DataManager:
    """数据驱动中心，负责加载与热更新 JSON 表。"""

    def __init__(self, base_path: str = "data") -> None:
        self.base_path = base_path
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.mtimes: Dict[str, float] = {}

    def _load_json(self, path: str) -> Any:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)

    def _full_path(self, relative: str) -> str:
        return os.path.join(self.base_path, relative)

    def load_table(self, name: str) -> Dict[str, Any]:
        relative = os.path.join("tables", f"{name}.json")
        return self._load_with_cache(relative)

    def load_level(self, name: str) -> Dict[str, Any]:
        relative = os.path.join("levels", f"{name}.json")
        return self._load_with_cache(relative)

    def _load_with_cache(self, relative: str) -> Dict[str, Any]:
        full = self._full_path(relative)
        mtime = os.path.getmtime(full)
        if relative not in self.cache or self.mtimes.get(relative) != mtime:
            self.cache[relative] = self._load_json(full)
            self.mtimes[relative] = mtime
        return self.cache[relative]

    def hot_reload(self) -> None:
        """定期调用以实现热加载，检测文件是否更新。"""
        for relative in list(self.cache.keys()):
            full = self._full_path(relative)
            try:
                mtime = os.path.getmtime(full)
            except FileNotFoundError:
                continue
            if mtime != self.mtimes.get(relative):
                self.cache[relative] = self._load_json(full)
                self.mtimes[relative] = mtime
