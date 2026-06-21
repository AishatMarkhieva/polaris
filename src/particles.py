"""
particles.py — лёгкая система частиц.

Частицы добавляют игре "сочности": вспышка при смене полярности,
искры при сборе кристалла, разлёт при смерти. Это не влияет на геймплей,
но сильно улучшает ощущение от игры.
"""
import random
import math
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, vx, vy, life, color, size):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.08          # лёгкая гравитация на частицы
        self.vx *= 0.96
        self.life -= 1
        return self.life > 0

    def draw(self, surf, cam_x, cam_y):
        # затухание через уменьшение размера
        t = self.life / self.max_life
        s = max(1, int(self.size * t))
        pygame.draw.rect(
            surf, self.color,
            (int(self.x - cam_x), int(self.y - cam_y), s, s)
        )


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def burst(self, x, y, color, count=14, speed=2.5, size=3):
        for _ in range(count):
            ang = random.uniform(0, 6.283)
            spd = random.uniform(0.5, speed)
            self.particles.append(Particle(
                x, y,
                spd * math.cos(ang),
                spd * math.sin(ang),
                random.randint(18, 34), color, size
            ))

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, surf, cam_x, cam_y):
        for p in self.particles:
            p.draw(surf, cam_x, cam_y)
