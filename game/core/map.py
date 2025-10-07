from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .pathfinding import astar, GridPosition


@dataclass
class GridMap:
    """网格地图，支持塔防核心操作。"""

    grid: List[List[int]]
    start: GridPosition
    goal: GridPosition
    tile_size: int = 64

    def in_bounds(self, pos: GridPosition) -> bool:
        x, y = pos
        return 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0])

    def is_walkable(self, pos: GridPosition) -> bool:
        """1 表示障碍，其他值可通行。"""
        if not self.in_bounds(pos):
            return False
        x, y = pos
        return self.grid[y][x] != 1

    def is_buildable(self, pos: GridPosition) -> bool:
        """0 表示可建造，路径与障碍不可建塔。"""
        if not self.in_bounds(pos):
            return False
        x, y = pos
        return self.grid[y][x] == 0

    def find_path(self) -> Optional[List[GridPosition]]:
        return astar(self.grid, self.start, self.goal)

    def try_place_tower(self, pos: GridPosition) -> bool:
        """尝试放置塔，确保不阻断路径。"""
        if not self.is_buildable(pos):
            return False
        x, y = pos
        self.grid[y][x] = 1
        path = self.find_path()
        if path is None:
            self.grid[y][x] = 0
            return False
        return True

    def remove_tower(self, pos: GridPosition) -> None:
        x, y = pos
        if self.in_bounds(pos) and self.grid[y][x] == 1:
            self.grid[y][x] = 0
