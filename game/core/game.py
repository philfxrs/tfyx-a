from __future__ import annotations

import pygame
from typing import Dict, Tuple, Optional, Callable

from game.ai.tower_ai import TowerBrain
from game.core.combat import DamageCalculator
from game.core.config_loader import DataManager
from game.core.director import GameDirector
from game.core.map import GridMap
from game.core.ui import HUD
from game.ecs.entities import EntityManager
from game.ecs import components as comp
from game.ecs.systems import MovementSystem, TowerSystem, CleanupSystem


class Game:
    """塔防原型的核心游戏类。"""

    def __init__(self, screen: pygame.Surface, data_path: str = "data") -> None:
        self.screen = screen
        self.data = DataManager(data_path)
        self.entities = EntityManager()
        self.tower_brain: Optional[TowerBrain] = None
        self.tower_system: Optional[TowerSystem] = None
        self.movement_system: Optional[MovementSystem] = None
        self.cleanup_system: Optional[CleanupSystem] = None
        self.director: Optional[GameDirector] = None
        self.hud = HUD()
        self.tower_table: Dict[str, Dict] = {}
        self.grid_map: Optional[GridMap] = None
        self.level_data: Dict = {}
        self.gold: int = 0
        self.life: int = 0
        self.initial_life: int = 0
        self.selected_tower: str = "physical"
        self.grid_surface: Optional[pygame.Surface] = None
        self.last_reload_time: float = 0.0
        self.web_hooks: Dict[str, Callable] = {}

    def setup(self, level_name: str = "level1") -> None:
        """初始化资源、读取关卡与数据表。"""
        self.tower_table = self.data.load_table("towers")
        self.level_data = self.data.load_level(level_name)
        self.gold = self.level_data.get("initial_gold", 100)
        self.life = self.level_data.get("initial_life", 10)
        self.initial_life = max(1, self.life)
        grid = self.level_data["grid"]
        start = tuple(self.level_data["start"])
        goal = tuple(self.level_data["goal"])
        tile_size = 64
        self.grid_map = GridMap(grid=grid, start=start, goal=goal, tile_size=tile_size)
        self.grid_surface = self._build_grid_surface()
        self.tower_brain = TowerBrain(tile_size)
        self.movement_system = MovementSystem(tile_size)
        damage_calc = DamageCalculator()
        self.tower_system = TowerSystem(self.tower_brain, damage_calc, tile_size)
        self.cleanup_system = CleanupSystem(goal, tile_size, self._on_enemy_escape)
        self.director = GameDirector(self.data, self.entities, self.grid_map, self.level_data)
        # 自动开启第一波
        self.director.start_next_wave(self.get_player_life_ratio())

    def _build_grid_surface(self) -> pygame.Surface:
        assert self.grid_map is not None
        width = len(self.grid_map.grid[0]) * self.grid_map.tile_size
        height = len(self.grid_map.grid) * self.grid_map.tile_size
        surface = pygame.Surface((width, height))
        for y, row in enumerate(self.grid_map.grid):
            for x, tile in enumerate(row):
                rect = pygame.Rect(x * self.grid_map.tile_size, y * self.grid_map.tile_size, self.grid_map.tile_size, self.grid_map.tile_size)
                color = (40, 40, 40)
                if tile == 2:
                    color = (90, 90, 90)
                elif tile == 0:
                    color = (60, 60, 60)
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (20, 20, 20), rect, 1)
        return surface

    def update(self, dt: float, current_time: float) -> None:
        """主更新循环，驱动所有系统。"""
        if not self.director or not self.grid_map:
            return
        if self.life <= 0:
            return
        self.data.hot_reload()
        # 热加载后刷新表数据
        self.tower_table = self.data.load_table("towers")
        self.director.enemy_table = self.data.load_table("enemies")
        if self.tower_system:
            self.tower_system.update(dt, self.entities, self._on_enemy_killed)
        if self.movement_system:
            self.movement_system.update(dt, self.entities)
        if self.cleanup_system:
            self.cleanup_system.update(self.entities)
        self.director.update(dt, self.get_player_life_ratio)

    def render(self) -> None:
        if not self.grid_surface:
            return
        self.screen.blit(self.grid_surface, (0, 0))
        for entity_id, position in self.entities.positions.items():
            renderable = self.entities.renderables.get(entity_id)
            if not renderable:
                continue
            pygame.draw.circle(self.screen, renderable.color, (int(position.x), int(position.y)), renderable.radius)
        total_waves = len(self.level_data.get("waves", [])) if self.level_data else 0
        current_wave = max(1, self.director.current_wave_index + 1 if self.director else 1)
        self.hud.draw(self.screen, self.gold, self.life, current_wave, total_waves)
        self._draw_selection_hint()
        if self.life <= 0:
            self._draw_game_over()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_build(event.pos)
        if event.type == pygame.KEYDOWN:
            self._handle_key(event.key)

    def _handle_key(self, key: int) -> None:
        mapping = {
            pygame.K_1: "physical",
            pygame.K_2: "magic",
            pygame.K_3: "aoe",
            pygame.K_4: "slow",
            pygame.K_SPACE: "next_wave",
        }
        if key not in mapping:
            return
        command = mapping[key]
        if command == "next_wave" and self.director:
            self.director.start_next_wave(self.get_player_life_ratio())
        elif command in self.tower_table:
            self.selected_tower = command

    def _handle_build(self, mouse_pos: Tuple[int, int]) -> None:
        if not self.grid_map:
            return
        tower_data = self.tower_table.get(self.selected_tower)
        if not tower_data:
            return
        if self.gold < tower_data["cost"]:
            return
        tile_x = mouse_pos[0] // self.grid_map.tile_size
        tile_y = mouse_pos[1] // self.grid_map.tile_size
        tile = (tile_x, tile_y)
        if not self.grid_map.try_place_tower(tile):
            return
        self.gold -= tower_data["cost"]
        entity_id = self.entities.create()
        px = tile_x * self.grid_map.tile_size + self.grid_map.tile_size / 2
        py = tile_y * self.grid_map.tile_size + self.grid_map.tile_size / 2
        tower_component = comp.Tower(
            tower_type=self.selected_tower,
            range=tower_data["range"],
            damage=tower_data["damage"],
            attack_speed=tower_data["attack_speed"],
            element=tower_data["element"],
            effects=tower_data.get("effects", []),
        )
        color_map = {
            "physical": (120, 120, 200),
            "magic": (150, 80, 200),
            "aoe": (200, 140, 60),
            "slow": (80, 160, 220),
        }
        render = comp.Renderable(color=color_map.get(self.selected_tower, (200, 200, 200)), radius=20)
        self.entities.add_component(entity_id, comp.Position(px, py))
        self.entities.add_component(entity_id, tower_component)
        self.entities.add_component(entity_id, render)
        self.entities.add_component(entity_id, comp.Target())

    def _on_enemy_killed(self, enemy_id: int, enemy: comp.Enemy) -> None:
        self.gold += enemy.bounty

    def _on_enemy_escape(self, enemy: comp.Enemy) -> None:
        self.life -= 1
        if self.life <= 0:
            self.life = 0

    def get_player_life_ratio(self) -> float:
        return self.life / max(1, self.initial_life)

    def _draw_selection_hint(self) -> None:
        if not self.grid_map:
            return
        font = pygame.font.SysFont("simhei", 18)
        info = f"当前选择: {self.tower_table.get(self.selected_tower, {}).get('name', self.selected_tower)}"
        label = font.render(info, True, (200, 200, 50))
        self.screen.blit(label, (16, 48))

    def _draw_game_over(self) -> None:
        font = pygame.font.SysFont("simhei", 48)
        label = font.render("防线崩溃", True, (255, 80, 80))
        rect = label.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(label, rect)

    # --- 预留 Web/Three.js 接口 ---
    def register_web_hook(self, name: str, callback) -> None:
        """允许未来接入 Web 前端时复用同构逻辑。"""
        self.web_hooks[name] = callback

    def export_state(self) -> Dict:
        """导出游戏状态，供 Web 或调试界面使用。"""
        return {
            "gold": self.gold,
            "life": self.life,
            "wave": self.director.current_wave_index if self.director else 0,
            "towers": [
                {
                    "id": entity_id,
                    "type": tower.tower_type,
                    "pos": (self.entities.positions[entity_id].x, self.entities.positions[entity_id].y),
                }
                for entity_id, tower in self.entities.towers.items()
            ],
        }
