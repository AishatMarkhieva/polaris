"""
camera.py — камера, которая плавно следует за игроком.

Камера хранит смещение (offset). Всё рисуется со сдвигом на это смещение,
создавая эффект прокрутки уровня. Камера зажата в границах уровня,
чтобы не показывать пустоту за краем карты.
"""
import settings as S


class Camera:
    def __init__(self, level_pixel_w, level_pixel_h):
        self.x = 0.0
        self.y = 0.0
        self.level_w = level_pixel_w
        self.level_h = level_pixel_h
        self.shake = 0.0           # сила тряски (для эффекта удара/смерти)

    def add_shake(self, amount):
        self.shake = min(self.shake + amount, 12)

    def update(self, target_x, target_y):
        # хотим, чтобы цель была по центру экрана
        goal_x = target_x - S.INTERNAL_W / 2
        goal_y = target_y - S.INTERNAL_H / 2

        # плавное приближение (линейная интерполяция)
        self.x += (goal_x - self.x) * S.CAMERA_LERP
        self.y += (goal_y - self.y) * S.CAMERA_LERP

        # зажимаем в границах уровня
        self.x = max(0, min(self.x, self.level_w - S.INTERNAL_W))
        self.y = max(0, min(self.y, self.level_h - S.INTERNAL_H))

        # затухание тряски
        if self.shake > 0:
            self.shake *= 0.85
            if self.shake < 0.2:
                self.shake = 0.0

    @property
    def offset(self):
        import random
        sx = sy = 0
        if self.shake > 0:
            sx = random.uniform(-self.shake, self.shake)
            sy = random.uniform(-self.shake, self.shake)
        return self.x + sx, self.y + sy
