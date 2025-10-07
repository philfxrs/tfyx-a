from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Callable, Optional

from game.ai.enemy_ai import EnemyAdaptiveAI, EnemyModifier
from game.ecs import components as comp
from game.ecs.entities import EntityManager
from .map import GridMap
from .config_loader import DataManager


@dataclass
class WaveEnemy:
    enemy_type: str
    count: int
    interval: float
    timer: float = 0.0


class GameDirector:
    """导演系统：协调波次、敌人 AI 与生成逻辑。"""

    def __init__(
        self,
        data: DataManager,
        entity_manager: EntityManager,
        grid_map: GridMap,
        level_data: Dict,
    ) -> None:
        self.data = data
        self.entities = entity_manager
        self.map = grid_map
        self.level_data = level_data
        self.enemy_table = data.load_table("enemies")
        self.waves: List[Dict] = level_data["waves"]
        self.current_wave_index = -1
        self.wave_state: List[WaveEnemy] = []
        self.enemy_ai = EnemyAdaptiveAI()
        self.current_modifier = EnemyModifier()
        self.active = False

    def start_next_wave(self, player_life_ratio: float) -> bool:
        """开启下一波次，返回是否成功。"""
        if self.active and self.entities.enemies:
            return False
        if self.current_wave_index + 1 >= len(self.waves):
            return False
        self.current_wave_index += 1
        wave = self.waves[self.current_wave_index]
        self.wave_state = [
            WaveEnemy(enemy_type=item["type"], count=item["count"], interval=item["interval"] / 1000.0)
            for item in wave["enemies"]
        ]
        self.current_modifier = self.enemy_ai.update(self.current_wave_index, player_life_ratio)
        self.active = True
        return True

    def update(self, dt: float, get_player_life_ratio: Callable[[], float]) -> None:
        if not self.active:
            return
        finished_groups = 0
        for group in self.wave_state:
            if group.count <= 0:
                finished_groups += 1
                continue
            group.timer -= dt
            if group.timer <= 0:
                self.spawn_enemy(group.enemy_type)
                group.count -= 1
                group.timer = group.interval
        if finished_groups == len(self.wave_state):
            # 若场上无敌人则自动进入下一波
            if not self.entities.enemies:
                self.active = False
                self.start_next_wave(get_player_life_ratio())

    def spawn_enemy(self, enemy_type: str) -> None:
        template = self.enemy_table[enemy_type]
        path = self.map.find_path()
        if not path:
            return
        entity_id = self.entities.create()
        position = comp.Position(
            x=path[0][0] * self.map.tile_size + self.map.tile_size / 2,
            y=path[0][1] * self.map.tile_size + self.map.tile_size / 2,
        )
        stats = comp.CombatStats(
            max_health=template["health"] * self.current_modifier.health_multiplier,
            health=template["health"] * self.current_modifier.health_multiplier,
            armor=template["armor"],
            resistance=template["resistance"],
            element=template["element"],
        )
        enemy = comp.Enemy(
            path=path,
            speed=template["speed"] * self.current_modifier.speed_multiplier,
            bounty=template["bounty"],
        )
        render = comp.Renderable(color=(200, 80, 80), radius=16)
        self.entities.add_component(entity_id, position)
        self.entities.add_component(entity_id, stats)
        self.entities.add_component(entity_id, enemy)
        self.entities.add_component(entity_id, render)
        self.entities.add_component(entity_id, comp.Effects())
