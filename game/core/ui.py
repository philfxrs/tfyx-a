from __future__ import annotations

import pygame


class HUD:
    """基础 HUD，用于展示资源、生命与波次信息。"""

    def __init__(self) -> None:
        self.font = pygame.font.SysFont("simhei", 20)

    def draw(self, surface: pygame.Surface, gold: int, life: int, wave: int, total_waves: int) -> None:
        text = f"金币: {gold}    生命: {life}    波次: {wave}/{total_waves}"
        label = self.font.render(text, True, (255, 255, 255))
        surface.blit(label, (16, 16))
