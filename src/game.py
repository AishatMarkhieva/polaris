"""
game.py — главный класс, связывающий всё вместе.

Это простая машина состояний (state machine):
  TITLE          — заставка
  PLAYING        — играем уровень
  LEVEL_COMPLETE — уровень пройден
  GAME_COMPLETE  — все уровни пройдены

Такая структура легко расширяется: добавить меню паузы, выбор уровня
или экран настроек = просто новое состояние.
"""
import os
import pygame
import settings as S
from src.assets import Assets
from src.level import Level
from src.player import Player
from src.camera import Camera
from src.particles import ParticleSystem
from src.ui import UI
from src.input_manager import KeyboardController, GamepadController, detect_gamepads
from src.generator import generate_level

LEVELS_DIR = os.path.join(os.path.dirname(__file__), "..", "levels")

# Порядок уровней. Добавил файл в levels/ — допиши имя сюда.
LEVEL_FILES = [
    "level_01.txt",
    "level_02.txt",
    "level_03.txt",
    "level_04.txt",
]

STATE_TITLE = "title"
STATE_PLAYING = "playing"
STATE_LEVEL_COMPLETE = "level_complete"
STATE_GAME_COMPLETE = "game_complete"


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(S.TITLE)
        self.window = pygame.display.set_mode((S.WINDOW_W, S.WINDOW_H))
        # внутренняя поверхность низкого разрешения -> потом увеличим (пиксель-арт)
        self.screen = pygame.Surface((S.INTERNAL_W, S.INTERNAL_H))
        self.clock = pygame.time.Clock()

        self.assets = Assets()
        self.ui = UI()
        self.particles = ParticleSystem()

        # --- управление ---
        # Один игрок на WASD. Чтобы сделать кооп — см. setup_players().
        self.gamepads = detect_gamepads()
        self.controllers = self._setup_controllers()

        self.state = STATE_TITLE
        self.level_index = 0
        self.endless = False          # True = бесконечный режим (случайные уровни)
        self.level = None
        self.players = []
        self.anim_t = 0
        self.fade = 0.0           # 0..1 для плавных переходов
        self.fade_dir = 0         # -1 светлеем, +1 темнеем
        self.pending_action = None
        self.running = True

    def _setup_controllers(self):
        """Возвращает список контроллеров для игроков.

        СЕЙЧАС: один игрок (WASD), либо геймпад, если он подключён.

        ЧТОБЫ ВКЛЮЧИТЬ ЛОКАЛЬНЫЙ КООПЕРАТИВ (2 игрока на одном ПК):
        раскомментируй второй контроллер ниже. Игрок 1 — WASD,
        игрок 2 — стрелки (или второй геймпад). Остальной код уже готов
        к нескольким игрокам.
        """
        controllers = []
        if self.gamepads:
            controllers.append(GamepadController(self.gamepads[0]))
        else:
            controllers.append(KeyboardController("wasd"))

        # --- КООПЕРАТИВ (раскомментируй для 2 игроков) ---
        # if len(self.gamepads) >= 2:
        #     controllers.append(GamepadController(self.gamepads[1]))
        # else:
        #     controllers.append(KeyboardController("arrows"))

        return controllers

    # ------------------------------------------------------------------
    # ЗАГРУЗКА УРОВНЯ
    # ------------------------------------------------------------------
    def load_level(self, index):
        """Загружает уровень из файла levels/*.txt."""
        path = os.path.join(LEVELS_DIR, LEVEL_FILES[index])
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        self._apply_level(text, index)

    def load_generated(self, index):
        """Создаёт случайный уровень (бесконечный режим)."""
        # длина уровня плавно растёт — дальше = чуть длиннее
        text = generate_level(length=64 + index * 4)
        self._apply_level(text, index)

    def _apply_level(self, text, index):
        """Общая часть: построить уровень, камеру, игроков, выбрать фон."""
        self.level = Level(text)
        self.camera = Camera(self.level.pixel_w, self.level.pixel_h)
        self.ui.set_level_background(index)   # <-- свой фон на каждый уровень

        # создаём игроков на точке старта
        sx, sy = self.level.start
        self.players = []
        for i, ctrl in enumerate(self.controllers):
            pol = "blue" if i == 0 else "orange"
            self.players.append(Player(sx + i * 10, sy, ctrl, polarity=pol))

        self.crystals_got = 0
        self.crystals_total = len(self.level.crystals)
        self.particles = ParticleSystem()

    def start_game(self):
        self.endless = False
        self.level_index = 0
        self.load_level(0)
        self.state = STATE_PLAYING

    def start_endless(self):
        self.endless = True
        self.level_index = 0
        self.load_generated(0)
        self.state = STATE_PLAYING

    # ------------------------------------------------------------------
    # ОБРАБОТКА СОБЫТИЙ
    # ------------------------------------------------------------------
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.running = False
                if self.state == STATE_TITLE and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.start_game()
                elif self.state == STATE_TITLE and e.key == pygame.K_g:
                    self.start_endless()
                elif self.state == STATE_LEVEL_COMPLETE and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.advance_level()
                elif self.state == STATE_GAME_COMPLETE and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state = STATE_TITLE
                if self.state == STATE_PLAYING and e.key == pygame.K_r:
                    self.respawn_all()
            elif e.type == pygame.JOYBUTTONDOWN:
                # кнопка Start (обычно 7) на геймсе тоже подтверждает экраны
                if self.state == STATE_TITLE:
                    self.start_game()
                elif self.state == STATE_LEVEL_COMPLETE:
                    self.advance_level()

    def advance_level(self):
        self.level_index += 1
        if self.endless:
            # бесконечный режим: всегда генерируем следующий случайный уровень
            self.load_generated(self.level_index)
            self.state = STATE_PLAYING
        elif self.level_index >= len(LEVEL_FILES):
            self.state = STATE_GAME_COMPLETE
        else:
            self.load_level(self.level_index)
            self.state = STATE_PLAYING

    def respawn_all(self):
        sx, sy = self.level.start
        for i, p in enumerate(self.players):
            p.respawn(sx + i * 10, sy)

    # ------------------------------------------------------------------
    # ОБНОВЛЕНИЕ ЛОГИКИ
    # ------------------------------------------------------------------
    def update(self):
        self.anim_t += 1
        self.particles.update()

        if self.state != STATE_PLAYING:
            return

        for p in self.players:
            p.update(self.level, self.particles)

            # падение в пропасть = смерть
            if p.rect.top > self.level.pixel_h + 40:
                self.kill_player(p)
                continue

            # шипы
            for s in self.level.spikes:
                if p.rect.colliderect(s):
                    self.kill_player(p)
                    break

            # кристаллы
            for c in self.level.crystals[:]:
                if p.rect.colliderect(c):
                    self.level.crystals.remove(c)
                    self.crystals_got += 1
                    self.particles.burst(c.centerx, c.centery, S.C_CRYSTAL, count=12, speed=2)

        # выход: достаточно, чтобы любой игрок дошёл до двери
        if self.level.exit_rect:
            for p in self.players:
                if p.rect.colliderect(self.level.exit_rect):
                    self.state = STATE_LEVEL_COMPLETE
                    self.particles.burst(self.level.exit_rect.centerx,
                                         self.level.exit_rect.centery,
                                         S.C_EXIT, count=24, speed=3)
                    break

        # камера следит за первым игроком
        target = self.players[0]
        self.camera.update(target.rect.centerx, target.rect.centery)

    def kill_player(self, p):
        self.camera.add_shake(8)
        bright, _ = S.POLARITY_COLORS[p.polarity]
        self.particles.burst(p.rect.centerx, p.rect.centery, bright, count=22, speed=4)
        self.particles.burst(p.rect.centerx, p.rect.centery, S.C_SPIKE, count=14, speed=3)
        sx, sy = self.level.start
        idx = self.players.index(p)
        p.respawn(sx + idx * 10, sy)

    # ------------------------------------------------------------------
    # ОТРИСОВКА
    # ------------------------------------------------------------------
    def draw(self):
        cam_x, cam_y = (self.camera.offset if self.state == STATE_PLAYING else (0, 0))

        self.ui.draw_background(self.screen, cam_x, cam_y)

        if self.state in (STATE_PLAYING, STATE_LEVEL_COMPLETE):
            self.level.draw(self.screen, self.assets, cam_x, cam_y, self.anim_t)
            for p in self.players:
                p.draw(self.screen, self.assets, cam_x, cam_y)
            self.particles.draw(self.screen, cam_x, cam_y)
            level_label = (f"Endless {self.level_index + 1}" if self.endless
                           else f"Level {self.level_index + 1}")
            self.ui.draw_hud(self.screen, level_label,
                             self.crystals_got, self.crystals_total,
                             self.players[0].polarity)

        if self.state == STATE_TITLE:
            self.ui.draw_center_text(
                self.screen,
                ["POLARIS", "Меняй полярность — меняй мир"],
                subtitle="ENTER — кампания    G — бесконечный режим    ESC — выход",
            )

        elif self.state == STATE_LEVEL_COMPLETE:
            self.ui.draw_center_text(
                self.screen,
                ["Уровень пройден!",
                 f"Кристаллы: {self.crystals_got}/{self.crystals_total}"],
                subtitle="ENTER — дальше",
            )

        elif self.state == STATE_GAME_COMPLETE:
            self.ui.draw_center_text(
                self.screen,
                ["Поздравляем!", "Ты прошёл все уровни"],
                subtitle="ENTER — в меню",
            )

        # увеличиваем внутреннюю картинку до размера окна (чёткий пиксель-арт)
        scaled = pygame.transform.scale(self.screen, (S.WINDOW_W, S.WINDOW_H))
        self.window.blit(scaled, (0, 0))
        pygame.display.flip()

    # ------------------------------------------------------------------
    # ГЛАВНЫЙ ЦИКЛ
    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(S.FPS)
        pygame.quit()
