from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional


class DataManager:
    """数据驱动中心，负责加载与热更新 JSON 表。

    过去的实现假设当前工作目录永远位于项目根目录下，
    在 Windows 直接通过绝对路径执行 ``python path/to/main.py`` 时，
    相对路径 ``data`` 会解析到调用者的工作目录，导致找不到资源。
    因此这里将数据目录改为默认使用模块所在位置推导出来的绝对路径，
    并对外提供自定义路径的能力。"""

    def __init__(self, base_path: Optional[str] = None) -> None:
        # 计算项目根目录（game/core/ -> game -> 项目根）
        module_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(module_dir, "..", ".."))

        resolved_path: str
        if base_path is None:
            resolved_path = os.path.join(project_root, "data")
        else:
            # 允许传入绝对路径，或项目内的相对路径
            if not os.path.isabs(base_path):
                candidate = os.path.join(project_root, base_path)
                resolved_path = os.path.abspath(candidate if os.path.isdir(candidate) else base_path)
            else:
                resolved_path = base_path

        self.base_path = resolved_path
        if not os.path.isdir(self.base_path):
            raise FileNotFoundError(f"数据目录不存在: {self.base_path}")

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
        if not os.path.exists(full):
            raise FileNotFoundError(f"配置文件不存在: {full}")
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
