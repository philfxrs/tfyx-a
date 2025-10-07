from __future__ import annotations

import pygame

from game.core.config_loader import DataManager
from game.core.game import Game


def main() -> None:
    pygame.init()
    data = DataManager()
    level = data.load_level("level1")
    tile_size = 64
    width = len(level["grid"][0]) * tile_size
    height = len(level["grid"]) * tile_size
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("AI 塔防原型")

    game = Game(screen)
    game.setup("level1")

    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        current_time = pygame.time.get_ticks() / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)
        game.update(dt, current_time)
        screen.fill((10, 10, 10))
        game.render()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
