from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Dict


@dataclass
class Position:
    """空间位置组件，所有单位都需要。"""
    x: float
    y: float


@dataclass
class Renderable:
    """渲染信息组件，描述颜色与大小。"""
    color: Tuple[int, int, int]
    radius: int


@dataclass
class CombatStats:
    """战斗属性组件，包含生命、防御、元素等。"""
    max_health: float
    health: float
    armor: float
    resistance: float
    element: str


@dataclass
class Tower:
    """塔组件，记录攻击参数与技能效果。"""
    tower_type: str
    range: float
    damage: float
    attack_speed: float
    element: str
    effects: List[str]
    cooldown: float = 0.0
    experience: float = 0.0


@dataclass
class Enemy:
    """敌人组件，持有寻路路径与移动状态。"""
    path: List[Tuple[int, int]]
    speed: float
    path_index: int = 0
    progress: float = 0.0
    bounty: int = 0


@dataclass
class SlowStatus:
    """减速状态组件，持续记录剩余时间与比例。"""
    ratio: float
    duration: float


@dataclass
class Effects:
    """存放敌人身上的临时效果。"""
    slows: List[SlowStatus] = field(default_factory=list)


@dataclass
class Target:
    """塔的锁定目标，用于渲染与逻辑。"""
    enemy_id: int | None = None
