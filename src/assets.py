"""
assets.py — загрузка и генерация спрайтов.

Главная идея для тебя как для художника:
  * Игра умеет работать БЕЗ картинок — все спрайты рисуются кодом (плейсхолдеры).
  * Как только ты положишь свой PNG в assets/sprites/ с нужным именем —
    игра автоматически возьмёт ТВОЙ спрайт вместо плейсхолдера.

Имена файлов, которые игра ищет (всё опционально):
  assets/sprites/player_blue.png    — игрок в синей полярности
  assets/sprites/player_orange.png  — игрок в оранжевой полярности
  assets/sprites/wall.png           — стена
  assets/sprites/block_blue.png     — синий блок
  assets/sprites/block_orange.png   — оранжевый блок
  assets/sprites/spike.png          — шипы
  assets/sprites/crystal.png        — кристалл
  assets/sprites/exit.png           — выход

Размер спрайтов: тайлы — TILE x TILE (16x16), игрок — PLAYER_W x PLAYER_H.
Любой PNG автоматически масштабируется под нужный размер.
"""
import os
import pygame
import settings as S

SPRITES_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites")


def _load_or_none(name, size):
    """Пробуем загрузить PNG. Если файла нет — вернём None (нарисуем плейсхолдер)."""
    path = os.path.join(SPRITES_DIR, name)
    if os.path.isfile(path):
        img = pygame.image.load(path).convert_alpha()
        if img.get_size() != size:
            img = pygame.transform.scale(img, size)
        return img
    return None


# ----- ниже: процедурная отрисовка плейсхолдеров (если своих PNG нет) -----

def _make_player(bright, dark, size):
    """Маленький кубик-герой с простым 'лицом'."""
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    pygame.draw.rect(surf, dark, (0, 0, w, h), border_radius=3)
    pygame.draw.rect(surf, bright, (1, 1, w - 2, h - 3), border_radius=3)
    # глаза
    eye = (20, 20, 30)
    pygame.draw.rect(surf, eye, (w // 2 - 4, h // 2 - 2, 2, 3))
    pygame.draw.rect(surf, eye, (w // 2 + 2, h // 2 - 2, 2, 3))
    return surf


def _make_wall(size):
    w, h = size
    surf = pygame.Surface(size)
    surf.fill(S.C_WALL)
    pygame.draw.rect(surf, S.C_WALL_EDGE, (0, 0, w, h), 1)
    pygame.draw.line(surf, S.C_WALL_EDGE, (0, 0), (w, 0), 2)  # подсветка сверху
    return surf


def _make_block(bright, dark, size):
    """Полярный блок: рамка ярким цветом, внутри полупрозрачная заливка."""
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surf, (*dark, 110), (0, 0, w, h), border_radius=2)
    pygame.draw.rect(surf, (*bright, 255), (0, 0, w, h), width=2, border_radius=2)
    # точка-сердцевина
    pygame.draw.circle(surf, (*bright, 200), (w // 2, h // 2), 2)
    return surf


def _make_spike(size):
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)
    n = 3
    bw = w / n
    for i in range(n):
        x0 = i * bw
        pygame.draw.polygon(
            surf, S.C_SPIKE,
            [(x0, h), (x0 + bw / 2, h * 0.25), (x0 + bw, h)]
        )
    return surf


def _make_crystal(size):
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)
    cx, cy = w / 2, h / 2
    pts = [(cx, 2), (w - 3, cy), (cx, h - 2), (3, cy)]
    pygame.draw.polygon(surf, S.C_CRYSTAL, pts)
    pygame.draw.polygon(surf, S.C_WHITE, pts, 1)
    return surf


def _make_exit(size):
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surf, S.C_EXIT, (2, 1, w - 4, h - 2), border_radius=4)
    pygame.draw.rect(surf, S.C_WHITE, (2, 1, w - 4, h - 2), 1, border_radius=4)
    pygame.draw.circle(surf, (30, 30, 40), (w // 2, h // 2), 3)
    return surf


class Assets:
    """Единое хранилище всех спрайтов. Создаётся один раз при старте."""

    def __init__(self):
        tile = (S.TILE, S.TILE)
        psize = (S.PLAYER_W, S.PLAYER_H)

        self.player = {
            "blue":   _load_or_none("player_blue.png", psize)
                      or _make_player(S.C_BLUE, S.C_BLUE_DARK, psize),
            "orange": _load_or_none("player_orange.png", psize)
                      or _make_player(S.C_ORANGE, S.C_ORANGE_DARK, psize),
        }
        self.wall    = _load_or_none("wall.png", tile)        or _make_wall(tile)
        self.block = {
            "blue":   _load_or_none("block_blue.png", tile)
                      or _make_block(S.C_BLUE, S.C_BLUE_DARK, tile),
            "orange": _load_or_none("block_orange.png", tile)
                      or _make_block(S.C_ORANGE, S.C_ORANGE_DARK, tile),
        }
        self.spike   = _load_or_none("spike.png", tile)   or _make_spike(tile)
        self.crystal = _load_or_none("crystal.png", tile) or _make_crystal(tile)
        self.exit    = _load_or_none("exit.png", tile)    or _make_exit(tile)
