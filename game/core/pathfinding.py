from __future__ import annotations

import heapq
from typing import Dict, List, Tuple, Optional

GridPosition = Tuple[int, int]


def heuristic(a: GridPosition, b: GridPosition) -> float:
    """A* 曼哈顿启发式。"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid: List[List[int]], start: GridPosition, goal: GridPosition) -> Optional[List[GridPosition]]:
    """标准 A*，返回路径网格坐标列表。"""
    open_set: List[Tuple[float, GridPosition]] = []
    heapq.heappush(open_set, (0.0, start))
    came_from: Dict[GridPosition, GridPosition] = {}
    g_score: Dict[GridPosition, float] = {start: 0.0}

    width = len(grid[0])
    height = len(grid)

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        x, y = current
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue
            if grid[ny][nx] == 1:
                continue
            tentative = g_score[current] + 1
            neighbor = (nx, ny)
            if tentative < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                f_score = tentative + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))
    return None
