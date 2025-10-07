from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Type, TypeVar, Generic, Optional

from . import components as comp

T = TypeVar("T")


class EntityManager:
    """简单的实体管理器，负责组件的增删改查。"""

    def __init__(self) -> None:
        self._next_id = 1
        self.positions: Dict[int, comp.Position] = {}
        self.renderables: Dict[int, comp.Renderable] = {}
        self.combats: Dict[int, comp.CombatStats] = {}
        self.towers: Dict[int, comp.Tower] = {}
        self.enemies: Dict[int, comp.Enemy] = {}
        self.effects: Dict[int, comp.Effects] = {}
        self.targets: Dict[int, comp.Target] = {}

    def create(self) -> int:
        entity_id = self._next_id
        self._next_id += 1
        return entity_id

    def remove(self, entity_id: int) -> None:
        for storage in [
            self.positions,
            self.renderables,
            self.combats,
            self.towers,
            self.enemies,
            self.effects,
            self.targets,
        ]:
            storage.pop(entity_id, None)

    def add_component(self, entity_id: int, component: object) -> None:
        """根据组件类型分类存储。"""
        if isinstance(component, comp.Position):
            self.positions[entity_id] = component
        elif isinstance(component, comp.Renderable):
            self.renderables[entity_id] = component
        elif isinstance(component, comp.CombatStats):
            self.combats[entity_id] = component
        elif isinstance(component, comp.Tower):
            self.towers[entity_id] = component
        elif isinstance(component, comp.Enemy):
            self.enemies[entity_id] = component
        elif isinstance(component, comp.Effects):
            self.effects[entity_id] = component
        elif isinstance(component, comp.Target):
            self.targets[entity_id] = component
        elif isinstance(component, comp.SlowStatus):
            # 减速状态需要依附在 Effects 上，若不存在则创建
            effects = self.effects.setdefault(entity_id, comp.Effects())
            effects.slows.append(component)
        else:
            raise TypeError(f"未知组件类型: {type(component)!r}")

    def get_components(self, entity_id: int) -> Dict[str, object]:
        """调试辅助，便于日志输出。"""
        return {
            "position": self.positions.get(entity_id),
            "renderable": self.renderables.get(entity_id),
            "combat": self.combats.get(entity_id),
            "tower": self.towers.get(entity_id),
            "enemy": self.enemies.get(entity_id),
            "effects": self.effects.get(entity_id),
            "target": self.targets.get(entity_id),
        }
