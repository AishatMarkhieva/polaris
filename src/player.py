"""
player.py — игрок: физика и механика полярности.

Игрок получает контроллер (см. input_manager.py) и сам не знает,
клавиатура это или геймпад. Это и есть ключ к будущему кооперативу.

Физика — классический тайловый платформер:
  1) применяем ввод и гравитацию к скорости;
  2) двигаемся по X, разрешаем столкновения;
  3) двигаемся по Y, разрешаем столкновения.
Раздельное разрешение по осям — самый надёжный способ без "залипаний".

Координаты храним как float (fx, fy) для плавности, а для столкновений
используем обычный pygame.Rect (целочисленный). Так код работает и на
classic pygame, и на pygame-ce.

Дополнительно: coyote time и jump buffer — мелочи, которые делают
управление "честным" и приятным.
"""
import pygame
import settings as S


class Player:
    def __init__(self, x, y, controller, polarity="blue"):
        self.rect = pygame.Rect(0, 0, S.PLAYER_W, S.PLAYER_H)
        # float-позиция верхнего левого угла
        self.fx = x - S.PLAYER_W / 2
        self.fy = y - S.PLAYER_H
        self._sync_rect()

        self.vx = 0.0
        self.vy = 0.0
        self.controller = controller
        self.polarity = polarity
        self.on_ground = False
        self.facing = 1

        self._coyote = 0
        self._jump_buffer = 0
        self.alive = True

    # --- синхронизация float-позиции и целочисленного Rect ---
    def _sync_rect(self):
        self.rect.x = round(self.fx)
        self.rect.y = round(self.fy)

    def respawn(self, x, y):
        self.fx = x - S.PLAYER_W / 2
        self.fy = y - S.PLAYER_H
        self._sync_rect()
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.alive = True

    def try_switch(self, level, particles):
        """Сменить полярность, если в новой полярности игрок не окажется
        внутри твёрдого блока (защита от застревания + пазл-механика)."""
        new_pol = "orange" if self.polarity == "blue" else "blue"
        if level.overlaps_solid(self.rect, new_pol):
            return False
        self.polarity = new_pol
        bright, _ = S.POLARITY_COLORS[new_pol]
        particles.burst(self.rect.centerx, self.rect.centery, bright, count=18, speed=3)
        return True

    def update(self, level, particles):
        st = self.controller.poll()

        if st.switch_pressed:
            self.try_switch(level, particles)

        # горизонтальное движение
        if st.move_x != 0:
            self.vx += st.move_x * S.MOVE_ACCEL
            self.vx = max(-S.MOVE_MAX, min(S.MOVE_MAX, self.vx))
            self.facing = 1 if st.move_x > 0 else -1
        else:
            self.vx *= S.FRICTION
            if abs(self.vx) < 0.05:
                self.vx = 0.0

        # прыжок: буфер + coyote
        if st.jump_pressed:
            self._jump_buffer = S.JUMP_BUFFER
        if self._jump_buffer > 0:
            self._jump_buffer -= 1
        if self._coyote > 0:
            self._coyote -= 1

        if self._jump_buffer > 0 and self._coyote > 0:
            self.vy = S.JUMP_VELOCITY
            self._jump_buffer = 0
            self._coyote = 0
            self.on_ground = False

        # короткий прыжок: отпустил кнопку — гасим подъём
        if not st.jump_held and self.vy < 0:
            self.vy *= 0.55

        # гравитация
        self.vy += S.GRAVITY
        self.vy = min(self.vy, S.FALL_MAX)

        # движение и коллизии
        self._move_x(level)
        self._move_y(level)

        if self.on_ground:
            self._coyote = S.COYOTE_TIME

    def _move_x(self, level):
        self.fx += self.vx
        self._sync_rect()
        for solid in level.solid_rects_around(self.rect, self.polarity):
            if self.rect.colliderect(solid):
                if self.vx > 0:
                    self.rect.right = solid.left
                elif self.vx < 0:
                    self.rect.left = solid.right
                self.fx = self.rect.x
                self.vx = 0.0

    def _move_y(self, level):
        self.fy += self.vy
        self._sync_rect()
        self.on_ground = False
        for solid in level.solid_rects_around(self.rect, self.polarity):
            if self.rect.colliderect(solid):
                if self.vy > 0:
                    self.rect.bottom = solid.top
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = solid.bottom
                self.fy = self.rect.y
                self.vy = 0.0

    def draw(self, surf, assets, cam_x, cam_y):
        img = assets.player[self.polarity]
        if self.facing < 0:
            img = pygame.transform.flip(img, True, False)
        surf.blit(img, (round(self.fx - cam_x), round(self.fy - cam_y)))
