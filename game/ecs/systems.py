from __future__ import annotations

import math
from typing import List, Tuple, Callable

from .entities import EntityManager
from . import components as comp
from game.ai.tower_ai import TowerBrain
from game.core.combat import DamageCalculator


class MovementSystem:
    """敌人寻路移动系统。"""

    def __init__(self, grid_size: int) -> None:
        self.grid_size = grid_size

    def update(self, dt: float, entities: EntityManager) -> None:
        for enemy_id, enemy in list(entities.enemies.items()):
            position = entities.positions.get(enemy_id)
            combat = entities.combats.get(enemy_id)
            if not position or not combat:
                continue
            speed_multiplier = 1.0
            effects = entities.effects.get(enemy_id)
            if effects:
                alive_slows: List[comp.SlowStatus] = []
                for slow in effects.slows:
                    slow.duration -= dt
                    if slow.duration > 0:
                        alive_slows.append(slow)
                        speed_multiplier *= slow.ratio
                effects.slows = alive_slows
            tile_speed = enemy.speed * speed_multiplier
            enemy.progress += tile_speed * dt
            while enemy.progress >= 1.0 and enemy.path_index < len(enemy.path) - 1:
                enemy.progress -= 1.0
                enemy.path_index += 1
            enemy.progress = min(enemy.progress, 0.999)
            tile_x, tile_y = enemy.path[enemy.path_index]
            position.x = tile_x * self.grid_size + self.grid_size / 2
            position.y = tile_y * self.grid_size + self.grid_size / 2


class TowerSystem:
    """塔攻击系统，调度塔 AI 完成选靶并执行伤害。"""

    def __init__(self, tower_ai: TowerBrain, damage_calc: DamageCalculator, grid_size: int) -> None:
        self.tower_ai = tower_ai
        self.damage_calc = damage_calc
        self.grid_size = grid_size

    def update(self, dt: float, entities: EntityManager, on_enemy_killed: Callable[[int, comp.Enemy], None]) -> None:
        for tower_id, tower in entities.towers.items():
            tower.cooldown = max(0.0, tower.cooldown - dt)
            position = entities.positions.get(tower_id)
            if not position:
                continue
            target_id = self.tower_ai.select_target(tower_id, tower, position, entities)
            if target_id is None:
                continue
            target_position = entities.positions.get(target_id)
            target_combat = entities.combats.get(target_id)
            if not target_position or not target_combat:
                continue
            distance = math.dist((position.x, position.y), (target_position.x, target_position.y))
            if distance > tower.range * self.grid_size:
                continue
            if tower.cooldown > 0:
                continue
            tower.cooldown = 1.0 / max(0.1, tower.attack_speed)
            damage, slow = self.damage_calc.calculate(tower, target_combat)
            target_combat.health -= damage
            if slow is not None:
                effects = entities.effects.setdefault(target_id, comp.Effects())
                effects.slows.append(slow)
            if target_combat.health <= 0:
                enemy = entities.enemies.get(target_id)
                if enemy:
                    on_enemy_killed(target_id, enemy)
                entities.remove(target_id)
            entities.targets.setdefault(tower_id, comp.Target()).enemy_id = target_id
            tower.experience += damage
            self.tower_ai.learn(tower_id, target_combat.element, damage)


class CleanupSystem:
    """敌人死亡或到达终点后的善后系统。"""

    def __init__(self, goal: Tuple[int, int], grid_size: int, on_enemy_escape: Callable[[comp.Enemy], None]) -> None:
        self.goal = goal
        self.grid_size = grid_size
        self.on_enemy_escape = on_enemy_escape

    def update(self, entities: EntityManager) -> None:
        goal_px = (self.goal[0] * self.grid_size + self.grid_size / 2, self.goal[1] * self.grid_size + self.grid_size / 2)
        for enemy_id, enemy in list(entities.enemies.items()):
            position = entities.positions.get(enemy_id)
            if not position:
                continue
            if abs(position.x - goal_px[0]) < self.grid_size / 2 and abs(position.y - goal_px[1]) < self.grid_size / 2:
                self.on_enemy_escape(enemy)
                entities.remove(enemy_id)
