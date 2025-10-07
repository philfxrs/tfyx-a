from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, Optional

from game.ecs import components as comp
from game.ecs.entities import EntityManager


class TowerBrain:
    """塔 AI：负责自动选靶，并提供基于经验的权重学习。"""

    def __init__(self, grid_size: int) -> None:
        self.grid_size = grid_size
        self.preferences: Dict[int, Dict[str, float]] = defaultdict(lambda: defaultdict(lambda: 1.0))

    def select_target(
        self,
        tower_id: int,
        tower: comp.Tower,
        position: comp.Position,
        entities: EntityManager,
    ) -> Optional[int]:
        best_id: Optional[int] = None
        best_score = -1.0
        for enemy_id, enemy in entities.enemies.items():
            target_pos = entities.positions.get(enemy_id)
            target_stats = entities.combats.get(enemy_id)
            if not target_pos or not target_stats:
                continue
            distance = math.dist((position.x, position.y), (target_pos.x, target_pos.y))
            if distance > tower.range * self.grid_size:
                continue
            preference = self.preferences[tower_id][target_stats.element]
            health_factor = target_stats.health / max(1.0, target_stats.max_health)
            distance_factor = 1.0 - min(1.0, distance / (tower.range * self.grid_size + 1e-5))
            score = preference * (1.2 - health_factor) + distance_factor
            if score > best_score:
                best_score = score
                best_id = enemy_id
        return best_id

    def learn(self, tower_id: int, enemy_element: str, damage: float) -> None:
        """简单学习：根据造成的伤害调整元素偏好。"""
        prefs = self.preferences[tower_id]
        for element in list(prefs.keys()):
            prefs[element] *= 0.98
        prefs[enemy_element] += damage * 0.01
