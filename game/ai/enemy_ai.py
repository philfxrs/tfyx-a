from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class EnemyModifier:
    """敌人属性修正值，用于导演系统调度。"""

    health_multiplier: float = 1.0
    speed_multiplier: float = 1.0


class EnemyAdaptiveAI:
    """根据战局表现调整敌人强度。"""

    def __init__(self) -> None:
        self.difficulty_score = 1.0

    def update(self, wave_index: int, player_life_ratio: float) -> EnemyModifier:
        """根据当前波次与玩家生命比例调整难度。"""
        # 玩家生命越高说明压力不足，略微提高难度；反之降低
        if player_life_ratio > 0.8:
            self.difficulty_score *= 1.05
        elif player_life_ratio < 0.4:
            self.difficulty_score *= 0.95
        # 难度随波次线性增长
        base = 1.0 + wave_index * 0.05
        score = base * self.difficulty_score
        return EnemyModifier(
            health_multiplier=min(2.5, score),
            speed_multiplier=min(1.8, 0.9 + score * 0.1),
        )
