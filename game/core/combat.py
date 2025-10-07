from __future__ import annotations

from typing import Dict, Tuple, Optional

from game.ecs import components as comp


class DamageCalculator:
    """战斗计算器，统一处理伤害、护甲、元素克制等逻辑。"""

    def __init__(self) -> None:
        # 元素克制矩阵，可在数据层扩展，这里提供基础示例
        self.element_matrix: Dict[Tuple[str, str], float] = {
            ("physical", "earth"): 0.9,
            ("physical", "air"): 1.0,
            ("arcane", "earth"): 1.1,
            ("arcane", "air"): 1.2,
            ("fire", "earth"): 1.2,
            ("fire", "air"): 0.8,
            ("frost", "earth"): 1.0,
            ("frost", "air"): 1.1,
        }

    def calculate(self, tower: comp.Tower, target: comp.CombatStats) -> Tuple[float, Optional[comp.SlowStatus]]:
        """返回造成的伤害与可能的减速效果。"""
        element_key = (tower.element, target.element)
        element_multiplier = self.element_matrix.get(element_key, 1.0)
        base_damage = tower.damage * element_multiplier
        # 护甲与魔抗同时考虑，假定物理塔受护甲影响，魔法塔受魔抗影响
        armor_effect = target.armor if tower.element in {"physical"} else 0.0
        resist_effect = target.resistance if tower.element in {"arcane", "fire", "frost"} else 0.0
        reduction = armor_effect * 0.4 + resist_effect * 0.3
        damage = max(1.0, base_damage - reduction)
        slow_status = None
        if "slow" in tower.effects:
            slow_status = comp.SlowStatus(ratio=0.6, duration=2.0)
        return damage, slow_status
