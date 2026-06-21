"""
level.py — загрузка и логика уровня.

Уровень читается из обычного текстового файла (levels/level_XX.txt), где
каждый символ — это тайл (см. легенду в settings.py). Такой подход —
огромный плюс для расширения: чтобы сделать новый уровень, нужно просто
нарисовать его в текстовом редакторе. Никакого кода.
"""
import pygame
import settings as S


class Level:
    def __init__(self, text):
        # разбиваем на строки, убираем пустые хвосты
        self.rows = [line.rstrip("\n") for line in text.splitlines() if line.strip("\n") != "" or True]
        # удаляем полностью пустые строки в конце
        while self.rows and self.rows[-1].strip() == "":
            self.rows.pop()

        self.h = len(self.rows)
        self.w = max((len(r) for r in self.rows), default=0)
        # дополняем строки пробелами до одинаковой ширины
        self.rows = [r.ljust(self.w, ".") for r in self.rows]

        self.pixel_w = self.w * S.TILE
        self.pixel_h = self.h * S.TILE

        # объекты, которые собираем из символов
        self.start = (S.TILE * 2, S.TILE * 2)
        self.exit_rect = None
        self.crystals = []   # список pygame.Rect
        self.spikes = []     # список pygame.Rect (для проверки смерти)

        self._parse()

    def _parse(self):
        for ty, row in enumerate(self.rows):
            for tx, ch in enumerate(row):
                px, py = tx * S.TILE, ty * S.TILE
                if ch == "@":
                    self.start = (px + S.TILE // 2, py + S.TILE)
                elif ch == "E":
                    self.exit_rect = pygame.Rect(px, py, S.TILE, S.TILE)
                elif ch == "*":
                    self.crystals.append(pygame.Rect(px + 3, py + 3, S.TILE - 6, S.TILE - 6))
                elif ch == "^":
                    # хитбокс шипов чуть меньше тайла — так честнее (совет из отзывов к Polarity Cube)
                    self.spikes.append(pygame.Rect(px + 2, py + S.TILE // 2, S.TILE - 4, S.TILE // 2))

    # --- работа с тайлами ---

    def tile_at(self, tx, ty):
        if 0 <= ty < self.h and 0 <= tx < self.w:
            return self.rows[ty][tx]
        return "."

    @staticmethod
    def is_solid(ch, polarity):
        """Твёрд ли тайл для текущей полярности игрока?
        # — всегда твёрдый.
        B — твёрдый только когда игрок 'blue'.
        O — твёрдый только когда игрок 'orange'."""
        if ch == "#":
            return True
        if ch == "B":
            return polarity == "blue"
        if ch == "O":
            return polarity == "orange"
        return False

    def solid_rects_around(self, rect, polarity):
        """Возвращает прямоугольники твёрдых тайлов рядом с rect.
        Берём только окрестность игрока — это быстро даже на больших картах."""
        result = []
        tx0 = max(0, rect.left // S.TILE - 1)
        tx1 = min(self.w, rect.right // S.TILE + 2)
        ty0 = max(0, rect.top // S.TILE - 1)
        ty1 = min(self.h, rect.bottom // S.TILE + 2)
        for ty in range(ty0, ty1):
            for tx in range(tx0, tx1):
                ch = self.rows[ty][tx]
                if self.is_solid(ch, polarity):
                    result.append(pygame.Rect(tx * S.TILE, ty * S.TILE, S.TILE, S.TILE))
        return result

    def overlaps_solid(self, rect, polarity):
        """Пересекается ли rect хоть с одним твёрдым тайлом?
        Используется при смене полярности: нельзя застрять внутри блока."""
        for r in self.solid_rects_around(rect, polarity):
            if rect.colliderect(r):
                return True
        return False

    # --- отрисовка ---

    def draw(self, surf, assets, cam_x, cam_y, anim_t):
        # рисуем только видимые тайлы (оптимизация)
        tx0 = max(0, int(cam_x // S.TILE))
        tx1 = min(self.w, int((cam_x + S.INTERNAL_W) // S.TILE) + 1)
        ty0 = max(0, int(cam_y // S.TILE))
        ty1 = min(self.h, int((cam_y + S.INTERNAL_H) // S.TILE) + 1)

        for ty in range(ty0, ty1):
            for tx in range(tx0, tx1):
                ch = self.rows[ty][tx]
                if ch == ".":
                    continue
                x = tx * S.TILE - cam_x
                y = ty * S.TILE - cam_y
                if ch == "#":
                    surf.blit(assets.wall, (x, y))
                elif ch == "B":
                    surf.blit(assets.block["blue"], (x, y))
                elif ch == "O":
                    surf.blit(assets.block["orange"], (x, y))
                elif ch == "^":
                    surf.blit(assets.spike, (x, y))

        # кристаллы (с лёгким "дыханием" по вертикали)
        import math
        bob = math.sin(anim_t * 0.1) * 2
        for c in self.crystals:
            surf.blit(assets.crystal, (c.x - 3 - cam_x, c.y - 3 + bob - cam_y))

        # выход (пульсирует)
        if self.exit_rect:
            surf.blit(assets.exit, (self.exit_rect.x - cam_x, self.exit_rect.y - cam_y))
