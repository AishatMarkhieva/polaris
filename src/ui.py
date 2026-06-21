"""
ui.py — отрисовка интерфейса и фона.

Здесь собрано всё, что не относится к геймплею напрямую:
фон с градиентом, HUD (счёт/полярность), затемнение, текст по центру.
"""
import os
import pygame
import settings as S

# Папка для необязательных картинок-фонов: assets/backgrounds/level_01.png и т.д.
BG_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "backgrounds")


def make_gradient(w, h, top, bottom):
    """Готовим вертикальный градиент один раз — это дёшево для фона."""
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        col = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
        pygame.draw.line(surf, col, (0, y), (w, y))
    return surf


class UI:
    def __init__(self):
        # шрифт по умолчанию (без внешних файлов)
        self.font_big = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 22)
        self.font_small = pygame.font.Font(None, 16)
        # фон по умолчанию + текущий фон (меняется на каждом уровне)
        self.default_bg = make_gradient(S.INTERNAL_W, S.INTERNAL_H,
                                        S.C_BG_TOP, S.C_BG_BOTTOM)
        self.bg = self.default_bg
        self.bg_image = None        # если у уровня есть картинка-фон — лежит тут

    def set_level_background(self, index):
        """Выбирает фон для уровня с номером index (0,1,2...).

        Приоритет: 1) картинка assets/backgrounds/level_XX.png, если есть;
                   2) иначе цвета градиента из settings.LEVEL_BACKGROUNDS.
        """
        # 1) ищем картинку (нумерация в имени с 1: level_01.png для index=0)
        img_path = os.path.join(BG_DIR, f"level_{index + 1:02d}.png")
        if os.path.isfile(img_path):
            img = pygame.image.load(img_path).convert()
            self.bg_image = pygame.transform.scale(img, (S.INTERNAL_W, S.INTERNAL_H))
            return
        self.bg_image = None
        # 2) иначе — цветной градиент (по кругу, чтобы хватало на бесконечный режим)
        palette = S.LEVEL_BACKGROUNDS
        if palette:
            top, bottom = palette[index % len(palette)]
            self.bg = make_gradient(S.INTERNAL_W, S.INTERNAL_H, top, bottom)
        else:
            self.bg = self.default_bg

    def draw_background(self, surf, cam_x, cam_y):
        if self.bg_image is not None:
            surf.blit(self.bg_image, (0, 0))
        else:
            surf.blit(self.bg, (0, 0))
        # лёгкий параллакс: редкая сетка точек, медленно ползущая за камерой
        step = 48
        ox = int(-cam_x * 0.3) % step
        oy = int(-cam_y * 0.3) % step
        dot = (40, 38, 60)
        for x in range(ox - step, S.INTERNAL_W, step):
            for y in range(oy - step, S.INTERNAL_H, step):
                surf.set_at((x, y), dot)

    def draw_hud(self, surf, level_name, crystals_got, crystals_total, polarity):
        # имя уровня
        txt = self.font_small.render(level_name, True, S.C_TEXT_DIM)
        surf.blit(txt, (6, 5))
        # кристаллы
        ctxt = self.font_small.render(f"* {crystals_got}/{crystals_total}", True, S.C_CRYSTAL)
        surf.blit(ctxt, (6, 20))
        # индикатор полярности — кружок текущего цвета справа сверху
        bright, dark = S.POLARITY_COLORS[polarity]
        cx = S.INTERNAL_W - 16
        pygame.draw.circle(surf, dark, (cx, 14), 8)
        pygame.draw.circle(surf, bright, (cx, 14), 6)
        ptxt = self.font_small.render("SHIFT", True, S.C_TEXT_DIM)
        surf.blit(ptxt, (cx - 40, 8))

    def draw_center_text(self, surf, lines, subtitle=None):
        # затемнение
        veil = pygame.Surface((S.INTERNAL_W, S.INTERNAL_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        surf.blit(veil, (0, 0))

        y = S.INTERNAL_H // 2 - 30 * len(lines) // 2
        for i, line in enumerate(lines):
            font = self.font_big if i == 0 else self.font
            txt = font.render(line, True, S.C_TEXT)
            surf.blit(txt, (S.INTERNAL_W // 2 - txt.get_width() // 2, y))
            y += txt.get_height() + 6
        if subtitle:
            stxt = self.font_small.render(subtitle, True, S.C_TEXT_DIM)
            surf.blit(stxt, (S.INTERNAL_W // 2 - stxt.get_width() // 2, S.INTERNAL_H - 30))
