"""
input_manager.py — абстракция управления.

ЗАЧЕМ ЭТО ВАЖНО (особенно для будущего кооператива):
Игрок (player.py) НЕ читает клавиатуру напрямую. Вместо этого он получает
объект-"контроллер", у которого спрашивает: "влево? вправо? прыжок? смена цвета?".

Благодаря этому добавить второго игрока = просто создать второй контроллер
(например, на стрелках или на геймпаде) и второго Player. Логика игрока не меняется.

Есть три вида контроллеров:
  * KeyboardController(scheme="wasd")  — WASD + Space + Shift/E
  * KeyboardController(scheme="arrows")— стрелки + Enter + RShift
  * GamepadController(joystick)        — геймпад (стики/крестовина + кнопки)
"""
import pygame


class InputState:
    """Снимок состояния управления в текущем кадре."""
    def __init__(self):
        self.move_x = 0.0          # -1 влево, +1 вправо, 0 стоп
        self.jump_pressed = False  # прыжок только что нажат (одиночное срабатывание)
        self.jump_held = False     # прыжок удерживается
        self.switch_pressed = False  # смена полярности только что нажата


class KeyboardController:
    """Управление с клавиатуры по выбранной раскладке."""

    SCHEMES = {
        "wasd": {
            "left": pygame.K_a, "right": pygame.K_d,
            "jump": pygame.K_SPACE, "switch": pygame.K_LSHIFT,
        },
        "arrows": {
            "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
            "jump": pygame.K_UP, "switch": pygame.K_RSHIFT,
        },
    }

    def __init__(self, scheme="wasd"):
        self.keys = self.SCHEMES[scheme]
        self._prev_jump = False
        self._prev_switch = False

    def poll(self):
        pressed = pygame.key.get_pressed()
        st = InputState()
        if pressed[self.keys["left"]]:
            st.move_x -= 1.0
        if pressed[self.keys["right"]]:
            st.move_x += 1.0

        jump = pressed[self.keys["jump"]]
        st.jump_held = jump
        st.jump_pressed = jump and not self._prev_jump   # фронт нажатия
        self._prev_jump = jump

        switch = pressed[self.keys["switch"]]
        st.switch_pressed = switch and not self._prev_switch
        self._prev_switch = switch
        return st


class GamepadController:
    """Управление геймпадом. Левый стик / крестовина — движение,
    A (низ) — прыжок, X (лево) — смена полярности."""

    def __init__(self, joystick, deadzone=0.35):
        self.js = joystick
        self.deadzone = deadzone
        self._prev_jump = False
        self._prev_switch = False

    def poll(self):
        st = InputState()
        # горизонтальная ось левого стика
        axis = self.js.get_axis(0)
        if abs(axis) > self.deadzone:
            st.move_x += 1.0 if axis > 0 else -1.0
        # крестовина (hat), если есть
        if self.js.get_numhats() > 0:
            hx, _ = self.js.get_hat(0)
            if hx != 0:
                st.move_x = float(hx)

        # кнопки: 0 обычно A (прыжок), 2 обычно X (смена цвета).
        # На разных геймпадах нумерация отличается — при необходимости поправь.
        jump = self.js.get_button(0)
        st.jump_held = bool(jump)
        st.jump_pressed = bool(jump) and not self._prev_jump
        self._prev_jump = bool(jump)

        switch = self.js.get_button(2)
        st.switch_pressed = bool(switch) and not self._prev_switch
        self._prev_switch = bool(switch)
        return st


def detect_gamepads():
    """Инициализирует и возвращает список подключённых геймпадов."""
    pygame.joystick.init()
    pads = []
    for i in range(pygame.joystick.get_count()):
        js = pygame.joystick.Joystick(i)
        js.init()
        pads.append(js)
    return pads
