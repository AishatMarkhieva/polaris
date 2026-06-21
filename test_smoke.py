"""
test_smoke.py — автоматическая проверка без графического окна.
Запускает игру с "ботом", прогоняет много кадров и проверяет, что
ничего не падает, физика стабильна (нет NaN), уровни загружаются.
Не часть игры — нужен только для разработки.
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import math
import pygame
import settings as S
from src.game import Game, STATE_PLAYING
from src.input_manager import InputState


class ScriptedController:
    """Бот: бежит вправо, иногда прыгает, переключает цвет каждые ~50 кадров."""
    def __init__(self):
        self.t = 0
    def poll(self):
        self.t += 1
        st = InputState()
        st.move_x = 1.0
        st.jump_pressed = (self.t % 22 == 0)
        st.jump_held = (self.t % 22 < 8)
        st.switch_pressed = (self.t % 55 == 0)
        return st


def run():
    g = Game()
    g.controllers = [ScriptedController()]
    g.start_game()

    frames = 0
    levels_seen = set()
    for _ in range(6000):
        g.update()
        g.draw()
        frames += 1

        # проверка стабильности физики
        for p in g.players:
            assert not math.isnan(p.rect.x) and not math.isnan(p.rect.y), "NaN в координатах!"
            assert -10000 < p.rect.x < 100000, "координата X улетела"

        levels_seen.add(g.level_index)

        # если бот застрял и не проходит — насильно двигаем дальше, чтобы
        # проверить загрузку всех уровней и переходы состояний
        if g.state != STATE_PLAYING:
            if g.level_index >= len(__import__("src.game", fromlist=["LEVEL_FILES"]).LEVEL_FILES) - 1 \
               and g.state == "game_complete":
                break
            g.advance_level()

        # каждые 800 кадров принудительно следующий уровень (чтобы пройти все)
        if frames % 800 == 0 and g.state == STATE_PLAYING:
            g.advance_level()

    pygame.quit()
    print(f"OK: прогнали {frames} кадров, состояний без падений.")
    print(f"Загружены уровни (индексы): {sorted(levels_seen)}")


if __name__ == "__main__":
    run()
