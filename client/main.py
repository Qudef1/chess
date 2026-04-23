"""Основной цикл игры в шахматы."""
import os
import sys
import pygame
import random
from queue import Queue

# Добавляем корень проекта в путь импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import WIDTH, HEIGHT, BOARD_OFFSET, BOARD_SIZE, UI_PANEL_WIDTH, BUTTON_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT, LIGHT_SQUARE, DARK_SQUARE,  HIGHLIGHT, HINT
from client.renderer import (
    PieceRenderer,
    draw_board,
    draw_pieces,
    draw_legal_moves,
    get_screen_coords,
    get_square_from_mouse,
)
from client.ui import Button, InputField, NumericInputField
from client.network import NetworkClient
from client.game import ChessGame
from client.sound_manager import SoundManager
from stockfish.stockfish_engine import StockfishEngine
from engine.move import Move
from engine.figures import WHITE as FIG_WHITE, BLACK as FIG_BLACK

pygame.init()
pygame.mixer.init()

# Load and play menu music
music_file = os.path.join(os.path.dirname(__file__), '..', 'music', 'Skrillex - Bangarang.mp3')
if os.path.exists(music_file):
    pygame.mixer.music.load(music_file)
    pygame.mixer.music.play(-1)  # Loop indefinitely

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Chess')
font = pygame.font.SysFont('Arial', 24)
title_font = pygame.font.SysFont('Arial', 36, bold=True)
big_title_font = pygame.font.SysFont('Arial', 72, bold=True)
clock = pygame.time.Clock()

# Инициализация
game = ChessGame()
renderer = PieceRenderer()
renderer.load_pieces()
stockfish_engine = StockfishEngine(depth=1)
sound_manager = SoundManager()

network_events = Queue()
network_client = None

server_input = InputField(pygame.Rect(BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING, 180, BUTTON_WIDTH, BUTTON_HEIGHT), 'ws://127.0.0.1:8000/ws')

mode = 'local'
player_color = FIG_WHITE
my_turn = True
online_status = 'Готов к игре'
draw_offer_pending = False
sound_enabled = True
music_enabled = True
sound_volume = 0.2
music_volume = 0.2

# Settings input fields (created once and reused)
sound_input_field = NumericInputField(pygame.Rect(BOARD_OFFSET + 220, 170, 100, 40), str(int(sound_volume * 100)))
music_input_field = NumericInputField(pygame.Rect(BOARD_OFFSET + 220, 230, 100, 40), str(int(music_volume * 100)))

# Темы оформления
THEMES = {
    'classic': {
        'name': 'Классическая',
        'panel_bg': (32, 32, 32),
        'text_color': (255, 255, 255),
        'status_color': (220, 220, 220),
    }
}

current_theme = 'classic'

def get_theme_color(key: str):
    return THEMES[current_theme][key]


animation_active = False
animation_move = None
animation_start = 0
animation_duration = 250
animation_piece = 0
animation_from = 0
animation_to = 0
animation_capture_sq = -1
animation_is_remote = False
animation_is_stockfish = False
animation_on_complete = None


def move_to_dict(move: Move) -> dict:
    return {
        'from_square': move.from_square,
        'to_square': move.to_square,
        'flag': move.flag,
        'promotion': move.promotion,
    }


def move_from_dict(data: dict) -> Move:
    return Move(int(data['from_square']), int(data['to_square']), int(data.get('flag', 0)), int(data.get('promotion', 0)))


def start_move_animation(move: Move, is_remote: bool = False, is_stockfish: bool = False, on_complete=None):
    global animation_active, animation_move, animation_start, animation_piece
    global animation_from, animation_to, animation_capture_sq, animation_is_remote, animation_is_stockfish, animation_on_complete

    if animation_active:
        return

    animation_active = True
    animation_move = move
    animation_start = pygame.time.get_ticks()
    animation_piece = game.board.get_piece(move.from_square)
    animation_from = move.from_square
    animation_to = move.to_square
    animation_is_remote = is_remote
    animation_is_stockfish = is_stockfish
    animation_on_complete = on_complete



def complete_move_animation():
    global animation_active, animation_move, animation_capture_sq, animation_is_remote, animation_is_stockfish, animation_on_complete, my_turn

    if not animation_active or animation_move is None:
        return

    game.make_move(animation_move)
    game.check_game_over()

    if game.game_result == 'mate' and game.result is None:
        if mode == 'online' and animation_is_remote:
            game.result = 'lose'
        else:
            game.result = 'win'
    elif game.game_result == 'stalemate':
        game.result = 'stalemate'

    if sound_enabled:
        sound_manager.play('move')

    if mode == 'local':
        game.white_perspective = not game.white_perspective

    saved_on_complete = animation_on_complete
    was_remote = animation_is_remote
    was_stockfish = animation_is_stockfish

    animation_active = False
    animation_move = None
    animation_capture_sq = -1
    animation_is_remote = False
    animation_is_stockfish = False
    animation_on_complete = None

    if saved_on_complete:
        try:
            saved_on_complete()
        except Exception:
            pass

    if was_remote:
        my_turn = True
    elif was_stockfish:
        my_turn = True

    if mode == 'stockfish' and not game.game_over and not was_stockfish:
        apply_stockfish_move()


def draw_moving_piece():
    if not animation_active or animation_move is None:
        return

    now = pygame.time.get_ticks()
    progress = min((now - animation_start) / animation_duration, 1.0)
    start_x, start_y = get_screen_coords(animation_from, game.white_perspective)
    end_x, end_y = get_screen_coords(animation_to, game.white_perspective)
    x = start_x + (end_x - start_x) * progress
    y = start_y + (end_y - start_y) * progress

    if animation_piece in renderer.piece_images:
        screen.blit(renderer.piece_images[animation_piece], (x, y))

    if progress >= 1.0:
        complete_move_animation()


def update_menu_buttons() -> list[Button]:
    x = BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING
    y = 140
    labels = ['Локальная игра', 'Против Stockfish', 'Онлайн', 'Справка', 'Настройки', 'Выход']
    return [Button(text, pygame.Rect(x, y + i * (BUTTON_HEIGHT + BUTTON_SPACING), BUTTON_WIDTH, BUTTON_HEIGHT)) for i, text in enumerate(labels)]


def update_game_buttons() -> list[Button]:
    x = BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING
    y = 140
    labels = ['Сдаться', 'Предложить ничью', 'Перезапустить', 'В меню']
    return [Button(text, pygame.Rect(x, y + i * (BUTTON_HEIGHT + BUTTON_SPACING), BUTTON_WIDTH, BUTTON_HEIGHT)) for i, text in enumerate(labels)]


def get_active_game_buttons() -> list[Button]:
    """Get game buttons appropriate for current mode."""
    x = BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING
    y = 140
    if mode == 'online':
        labels = ['Сдаться', 'Предложить ничью', 'В меню']
    else:
        labels = ['Сдаться', 'Предложить ничью', 'Перезапустить', 'В меню']
    return [Button(text, pygame.Rect(x, y + i * (BUTTON_HEIGHT + BUTTON_SPACING), BUTTON_WIDTH, BUTTON_HEIGHT)) for i, text in enumerate(labels)]


menu_buttons = update_menu_buttons()
game_buttons = update_game_buttons()


def get_online_connect_buttons():
    connect_btn = Button('Подключиться', pygame.Rect(BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING, 260, BUTTON_WIDTH, BUTTON_HEIGHT))
    back_btn = Button('Назад', pygame.Rect(BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING, 340, BUTTON_WIDTH, BUTTON_HEIGHT))
    return connect_btn, back_btn


def get_settings_buttons():
    """Return all settings screen buttons and input fields."""
    sound_btn = Button(f"Звук: {'Вкл' if sound_enabled else 'Выкл'}", pygame.Rect(BOARD_OFFSET, 160, 200, 50))
    music_btn = Button(f"Музыка: {'Вкл' if music_enabled else 'Выкл'}", pygame.Rect(BOARD_OFFSET, 220, 200, 50))
    back_btn = Button('Назад', pygame.Rect(BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING, 400, BUTTON_WIDTH, BUTTON_HEIGHT))
    return sound_btn, music_btn, sound_input_field, music_input_field, back_btn


def set_status(text: str):
    global online_status
    online_status = text


def reset_game(new_mode: str, selected_color: int = FIG_WHITE):
    global mode, player_color, my_turn, draw_offer_pending
    mode = new_mode
    game.reset()
    if hasattr(game, '_check_sound_played'):
        game._check_sound_played = False
    if hasattr(game, '_game_over_sound_played'):
        game._game_over_sound_played = False
    game.result = None
    draw_offer_pending = False
    player_color = selected_color
    game.white_perspective = (player_color == FIG_WHITE)
    if mode == 'stockfish':
        if player_color == FIG_WHITE:
            my_turn = True
            set_status('Игра против Stockfish. Вы белые.')
        else:
            my_turn = False
            set_status('Игра против Stockfish. Вы чёрные.')
            apply_stockfish_move()
    elif mode == 'online':
        my_turn = False
        set_status('Онлайн: ожидайте подключения.')
    else:
        my_turn = True
        set_status('Локальная игра')


def apply_stockfish_move():
    global my_turn
    if stockfish_engine.is_available():
        best_move = stockfish_engine.get_best_move(game.board)
    else:
        legal = game.move_generator.generate_legal_moves(game.board)
        best_move = random.choice(legal) if legal else None
    if best_move is not None:
        my_turn = False
        start_move_animation(best_move, is_stockfish=True, on_complete=lambda: set_status('Ход компьютера выполнен.'))


def on_network_message(message: dict):
    network_events.put(message)


def connect_online():
    global network_client
    if network_client is not None:
        return
    set_status('Попытка соединения...')
    network_client = NetworkClient(server_input.text, on_network_message)
    network_client.connect()


def disconnect_online():
    global network_client, my_turn
    if network_client is not None:
        network_client.disconnect()
        network_client = None
    set_status('Отключено от сервера.')
    my_turn = False
    reset_game('local')


def handle_network_events():
    global game_state, my_turn, player_color, draw_offer_pending, network_client, mode
    while not network_events.empty():
        message = network_events.get()
        event_type = message.get('type')
        if event_type == 'connected':
            set_status('Соединение установлено. Отправка данных...')
            if network_client:
                network_client.send_join('Player')
        elif event_type == 'waiting':
            set_status(message.get('message', 'Ожидание соперника...'))
        elif event_type == 'game_start':
            mode = 'online'
            reset_game('online')
            color = message.get('payload', {}).get('color', 'white')
            player_color = FIG_WHITE if color == 'white' else FIG_BLACK
            game.white_perspective = (player_color == FIG_WHITE)
            my_turn = player_color == FIG_WHITE
            game_state = 'GAME'
            set_status(f'Игра началась. Вы {"белые" if player_color == FIG_WHITE else "чёрные"}.')
        elif event_type == 'opponent_move':
            move_data = message.get('payload', {})
            remote_move = move_from_dict(move_data)
            start_move_animation(remote_move, is_remote=True, on_complete=lambda: set_status('Ход соперника принят. Ваш ход.'))
            my_turn = True
        elif event_type == 'opponent_resigned':
            game.game_over = True
            game.game_result = 'mate'
            game.result = 'win'
            if not getattr(game, '_game_over_sound_played', False):
                sound_manager.play('win')
                game._game_over_sound_played = True
            set_status('Соперник сдался. Вы победили!')
        elif event_type == 'draw_offer':
            draw_offer_pending = True
            set_status('Соперник предлагает ничью. Нажмите ещё раз, чтобы принять.')
        elif event_type == 'draw_accepted':
            game.game_over = True
            game.game_result = 'stalemate'
            game.result = 'stalemate'
            draw_offer_pending = False
            if not getattr(game, '_game_over_sound_played', False):
                sound_manager.play('game_over')
                game._game_over_sound_played = True
            set_status('Ничья согласована.')
        elif event_type == 'draw_rejected':
            draw_offer_pending = False
            set_status('Соперник отклонил ничью.')
        elif event_type == 'opponent_left':
            game.game_over = True
            game.game_result = 'stalemate'
            game.result = 'win'
            if not getattr(game, '_game_over_sound_played', False):
                sound_manager.play('win')
                game._game_over_sound_played = True
            set_status('Соперник отключился. Вы победили!')
        elif event_type == 'disconnected':
            set_status('Сервер отключён. Возврат в меню.')
            network_client = None
            game_state = 'MENU'
        elif event_type == 'error':
            set_status(f"Ошибка сети: {message.get('message', '')}")


def handle_board_click(position: tuple[int, int]):
    global my_turn, draw_offer_pending
    if game.game_over:
        return

    # Блокируем ввод во время анимации (ход Stockfish или удалённый ход)
    if animation_active:
        return

    if mode == 'online' and not my_turn:
        return

    idx = get_square_from_mouse(position, game.white_perspective)
    if idx is None:
        return
    move_to_make = game.get_move_for_square(idx)
    if move_to_make:
        if mode == 'online' and network_client:
            network_client.send_move(move_to_dict(move_to_make))
            my_turn = False
            set_status('Ход отправлен. Ждём соперника.')
            start_move_animation(move_to_make, is_remote=False)
        else:
            on_complete = None if mode == 'stockfish' else lambda: set_status('Ход выполнен.')
            start_move_animation(move_to_make, on_complete=on_complete)
        draw_offer_pending = False
        return
    game.select_square(idx)


def action_button_clicked(label: str):
    global draw_offer_pending, game_state
    if label == 'Сдаться':
        game.game_over = True
        game.game_result = 'mate'
        game.result = 'lose'
        if not getattr(game, '_game_over_sound_played', False):
            sound_manager.play('lose')
            game._game_over_sound_played = True
        if mode == 'online' and network_client:
            network_client.send_resign()
            set_status('Вы сдались.')
        else:
            set_status('Вы сдались. Игра окончена.')
    elif label == 'Предложить ничью':
        if mode == 'online' and network_client:
            if draw_offer_pending:
                network_client.send_accept_draw()
                draw_offer_pending = False
                set_status('Ничья согласована.')
            else:
                network_client.send_offer_draw()
                set_status('Предложение ничьи отправлено.')
        else:
            if draw_offer_pending:
                game.game_over = True
                game.game_result = 'stalemate'
                game.result = 'stalemate'
                draw_offer_pending = False
                set_status('Ничья принята.')
            else:
                draw_offer_pending = True
                set_status('Ничья предложена. Нажмите ещё раз, чтобы принять.')
    elif label == 'Перезапустить':
        if mode != 'online':
            reset_game(mode)
    elif label == 'В меню':
        disconnect_online()
        game_state = 'MENU'


def play_game_music():
    """Остановить менюшную музыку и включить игровую."""
    game_music = os.path.join(os.path.dirname(__file__), '..', 'music', 'game.mp3')
    if os.path.exists(game_music):
        pygame.mixer.music.load(game_music)
        pygame.mixer.music.play(-1)
    elif os.path.exists(music_file):
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1)


def play_menu_music():
    """Вернуть менюшную музыку."""
    if os.path.exists(music_file):
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1)


def is_king_in_check() -> bool:
    """Проверяет, находится ли король текущего игрока под шахом."""
    king_sq = game.board.find_king(game.board.side_to_move)
    if king_sq == -1:
        return False
    enemy_color = FIG_BLACK if game.board.side_to_move == FIG_WHITE else FIG_WHITE
    return game.board.is_square_attacked(king_sq, enemy_color)


def draw_game_over_beautiful(screen: pygame.Surface, game_result: str, font: pygame.font.Font, big_font: pygame.font.Font):
    """Красивое сообщение о завершении игры с overlay только на области доски."""
    panel_x = BOARD_OFFSET - 10
    panel_y = BOARD_OFFSET - 10
    panel_w = BOARD_SIZE + 20
    panel_h = BOARD_SIZE + 20

    overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (panel_x, panel_y))

    # Определяем текст и цвет в зависимости от результата
    if game_result == 'win':
        title_text = 'ПОБЕДА!'
        sub_text = 'Поздравляем! Вы выиграли партию.'
        title_color = (255, 215, 0)
        sub_color = (220, 220, 220)
    elif game_result == 'lose':
        title_text = 'ПОРАЖЕНИЕ'
        sub_text = 'К сожалению, вы проиграли.'
        title_color = (200, 60, 60)
        sub_color = (200, 200, 200)
    elif game_result == 'stalemate':
        title_text = 'ПАТ!'
        sub_text = 'Ничья. Ни один из игроков не может сделать ход.'
        title_color = (180, 180, 255)
        sub_color = (200, 200, 200)
    else:
        return

    title_surface = big_font.render(title_text, True, title_color)
    sub_surface = font.render(sub_text, True, sub_color)

    center_x = panel_x + panel_w // 2
    center_y = panel_y + panel_h // 2

    title_rect = title_surface.get_rect(center=(center_x, center_y - 20))
    sub_rect = sub_surface.get_rect(center=(center_x, center_y + 30))

    screen.blit(title_surface, title_rect)
    screen.blit(sub_surface, sub_rect)


def draw_help_screen(screen: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font, back_button: Button):
    """Отрисовка экрана справки с правилами шахмат."""
    screen.fill((20, 20, 20))

    title_surface = title_font.render('Справка: Правила шахмат', True, (255, 255, 255))
    screen.blit(title_surface, (BOARD_OFFSET, 40))

    rules = [
        ('Общие правила', [
            'Шахматы — игра для двух игроков на доске 8×8 клеток.',
            'Белые всегда ходят первыми. Игроки ходят по очереди.',
            'Цель игры — поставить мат королю противника.',
        ]),
        ('Фигуры и их ходы', [
            'Король: ходит на 1 клетку в любом направлении.',
            'Ферзь: ходит на любое количество клеток по вертикали, горизонтали или диагонали.',
            'Ладья: ходит на любое количество клеток по вертикали или горизонтали.',
            'Слон: ходит на любое количество клеток по диагонали.',
            'Конь: ходит буквой «Г» (на 2 клетки в одном направлении и 1 в перпендикулярном).',
            'Пешка: ходит вперёд на 1 клетку, бьёт по диагонали.',
        ]),
        ('Особые правила', [
            'Рокировка: король и ладья меняются местами, если между ними нет фигур.',
            'Взятие на проходе: пешка может взять пешку противника, прошедшую 2 клетки.',
            'Превращение пешки: пешка, дошедшая до последней горизонтали, превращается в любую фигуру.',
        ]),
        ('Окончание игры', [
            'Мат: король находится под шахом и не может от него спастись.',
            'Пат: король не под шахом, но нет доступных легальных ходов — ничья.',
            'Другие ничьи: трёхкратное повторение позиции или 50 ходов без взятия и пешечного хода.',
        ]),
        ('Интерфейс программы', [
            'Кликните на фигуру — появятся подсказки с возможными ходами.',
            'Кликните на подсвеченную клетку — фигура переместится.',
            'В режиме «Против Stockfish» компьютер играет за чёрных.',
            'В режиме «Онлайн» подключитесь к серверу для игры с другим игроком.',
        ]),
    ]

    y = 100
    for section_title, lines in rules:
        section_surface = font.render(section_title, True, (255, 215, 0))
        screen.blit(section_surface, (BOARD_OFFSET, y))
        y += 32

        for line in lines:
            line_surface = font.render(line, True, (200, 200, 200))
            screen.blit(line_surface, (BOARD_OFFSET + 20, y))
            y += 28
        y += 10

    back_button.draw(screen, font, pygame.mouse.get_pos())


game_state = 'MENU'

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and game_state == 'ONLINE_CONNECT':
            server_input.handle_event(event)
        if event.type == pygame.KEYDOWN and game_state == 'SETTINGS':
            _, _, sound_input, music_input, _ = get_settings_buttons()
            sound_input.handle_event(event)
            music_input.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if game_state == 'MENU':
                for button in menu_buttons:
                    if button.contains(mouse_pos):
                        if button.text == 'Локальная игра':
                            reset_game('local')
                            game_state = 'GAME'
                            play_game_music()
                        elif button.text == 'Против Stockfish':
                            game_state = 'STOCKFISH_COLOR_SELECT'
                        elif button.text == 'Онлайн':
                            game_state = 'ONLINE_CONNECT'
                            set_status('Введите адрес сервера и нажмите Подключиться.')
                        elif button.text == 'Справка':
                            game_state = 'HELP'
                        elif button.text == 'Настройки':
                            game_state = 'SETTINGS'
                        elif button.text == 'Выход':
                            pygame.quit()
                            sys.exit()
                        break
            elif game_state == 'ONLINE_CONNECT':
                server_input.handle_event(event)
                connect_button, back_button = get_online_connect_buttons()
                if connect_button.contains(mouse_pos):
                    connect_online()
                elif back_button.contains(mouse_pos):
                    game_state = 'MENU'
            elif game_state == 'SETTINGS':
                sound_button, music_button, sound_input, music_input, back_button = get_settings_buttons()
                if sound_button.contains(mouse_pos):
                    sound_enabled = not sound_enabled
                    sound_manager.set_enabled(sound_enabled)
                elif music_button.contains(mouse_pos):
                    music_enabled = not music_enabled
                    if music_enabled and os.path.exists(music_file):
                        pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.stop()
                elif sound_input.rect.collidepoint(mouse_pos):
                    sound_input.active = True
                elif music_input.rect.collidepoint(mouse_pos):
                    music_input.active = True
                elif back_button.contains(mouse_pos):
                    game_state = 'MENU'
                    # Apply volume changes from input fields
                    sound_val = sound_input.get_value()
                    sound_volume = sound_val / 100.0
                    sound_manager.set_volume(sound_volume)
                    sound_input.text = str(int(sound_volume * 100))
                    
                    music_val = music_input.get_value()
                    music_volume = music_val / 100.0
                    pygame.mixer.music.set_volume(music_volume)
                    music_input.text = str(int(music_volume * 100))
                    
                    sound_input.active = False
                    music_input.active = False
            elif game_state == 'STOCKFISH_COLOR_SELECT':
                white_btn = Button('Играть белыми', pygame.Rect(BOARD_OFFSET + BOARD_SIZE // 2 - 120, 250, 240, 60))
                black_btn = Button('Играть чёрными', pygame.Rect(BOARD_OFFSET + BOARD_SIZE // 2 - 120, 330, 240, 60))
                back_btn = Button('Назад', pygame.Rect(BOARD_OFFSET + BOARD_SIZE // 2 - 120, 410, 240, 60))
                if white_btn.contains(mouse_pos):
                    reset_game('stockfish', FIG_WHITE)
                    game_state = 'GAME'
                    play_game_music()
                elif black_btn.contains(mouse_pos):
                    reset_game('stockfish', FIG_BLACK)
                    game_state = 'GAME'
                    play_game_music()
                elif back_btn.contains(mouse_pos):
                    game_state = 'MENU'
            elif game_state == 'HELP':
                back_button = Button('Назад', pygame.Rect(BOARD_OFFSET, HEIGHT - 80, 150, 50))
                if back_button.contains(mouse_pos):
                    game_state = 'MENU'
            elif game_state == 'GAME':
                clicked_button = False
                active_buttons = get_active_game_buttons()
                for button in active_buttons:
                    if button.contains(mouse_pos):
                        action_button_clicked(button.text)
                        clicked_button = True
                        break
                if not clicked_button:
                    handle_board_click(mouse_pos)

    handle_network_events()
    screen.fill((20, 20, 20))
    if game_state == 'MENU':
        title_surface = title_font.render('Chess Project', True, (255, 255, 255))
        screen.blit(title_surface, (BOARD_OFFSET, 80))
        for button in menu_buttons:
            button.draw(screen, font, pygame.mouse.get_pos())
        desc = font.render('Выберите режим игры', True, (200, 200, 200))
        screen.blit(desc, (BOARD_OFFSET, 140))
    elif game_state == 'ONLINE_CONNECT':
        title_surface = title_font.render('Онлайн-подключение', True, (255, 255, 255))
        screen.blit(title_surface, (BOARD_OFFSET, 80))
        server_input.draw(screen, font, pygame.mouse.get_pos())
        connect_button, back_button = get_online_connect_buttons()
        connect_button.draw(screen, font, pygame.mouse.get_pos())
        back_button.draw(screen, font, pygame.mouse.get_pos())
        info = font.render(online_status, True, (220, 220, 220))
        screen.blit(info, (BOARD_OFFSET, 360))
    elif game_state == 'SETTINGS':
        title_surface = title_font.render('Настройки', True, (255, 255, 255))
        screen.blit(title_surface, (BOARD_OFFSET, 80))
        sound_button, music_button, sound_input, music_input, back_button = get_settings_buttons()
        sound_button.draw(screen, font, pygame.mouse.get_pos())
        music_button.draw(screen, font, pygame.mouse.get_pos())

        volume_label = font.render('Громкость звуков (0-100):', True, (200, 200, 200))
        screen.blit(volume_label, (BOARD_OFFSET, 290))
        sound_input.draw(screen, font, pygame.mouse.get_pos())

        music_volume_label = font.render('Громкость музыки (0-100):', True, (200, 200, 200))
        screen.blit(music_volume_label, (BOARD_OFFSET, 350))
        music_input.draw(screen, font, pygame.mouse.get_pos())

        back_button.draw(screen, font, pygame.mouse.get_pos())
    elif game_state == 'STOCKFISH_COLOR_SELECT':
        title_surface = title_font.render('Выберите цвет фигур', True, (255, 255, 255))
        screen.blit(title_surface, (BOARD_OFFSET, 80))
        white_btn = Button('Играть белыми', pygame.Rect(BOARD_OFFSET + BOARD_SIZE // 2 - 120, 250, 240, 60))
        black_btn = Button('Играть чёрными', pygame.Rect(BOARD_OFFSET + BOARD_SIZE // 2 - 120, 330, 240, 60))
        back_btn = Button('Назад', pygame.Rect(BOARD_OFFSET + BOARD_SIZE // 2 - 120, 410, 240, 60))
        white_btn.draw(screen, font, pygame.mouse.get_pos())
        black_btn.draw(screen, font, pygame.mouse.get_pos())
        back_btn.draw(screen, font, pygame.mouse.get_pos())
    elif game_state == 'HELP':
        back_button = Button('Назад', pygame.Rect(BOARD_OFFSET, HEIGHT - 80, 150, 50))
        draw_help_screen(screen, font, title_font, back_button)
    elif game_state == 'GAME':
        LIGHT = LIGHT_SQUARE
        DARK = DARK_SQUARE
        HIGHLIGHT = HIGHLIGHT
        HINT_COLOR = HINT
        PANEL_BG = get_theme_color('panel_bg')
        TEXT_COLOR = get_theme_color('text_color')
        STATUS_COLOR = get_theme_color('status_color')

        draw_board(screen, game.board, game.selected_square, game.white_perspective,
                   light_square=LIGHT, dark_square=DARK, highlight=HIGHLIGHT)

        skip_squares = {animation_from, animation_capture_sq} if animation_active else None
        draw_pieces(screen, game.board, renderer, game.white_perspective, skip_squares=skip_squares)
        draw_moving_piece()
        if not game.game_over:
            draw_legal_moves(screen, game.legal_moves, game.white_perspective, hint_color=HINT_COLOR)

        # Check for check and play sound
        if not game.game_over and is_king_in_check():
            king_sq = game.board.find_king(game.board.side_to_move)
            x, y = get_screen_coords(king_sq, game.white_perspective)
            check_surface = pygame.Surface((90, 90), pygame.SRCALPHA)
            check_surface.fill((255, 0, 0, 120))
            screen.blit(check_surface, (x, y))
            # Play check sound once per check state
            if not getattr(game, '_check_sound_played', False):
                sound_manager.play('check')
                game._check_sound_played = True
        else:
            if hasattr(game, '_check_sound_played'):
                game._check_sound_played = False

        active_buttons = get_active_game_buttons()
        button_rects = [button.rect for button in active_buttons]

        # Draw side panel with theme colors
        panel_width = UI_PANEL_WIDTH - 40
        panel_x = BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING
        panel_rect = pygame.Rect(panel_x, BOARD_OFFSET, panel_width, HEIGHT - BOARD_OFFSET * 2)
        pygame.draw.rect(screen, PANEL_BG, panel_rect, border_radius=12)
        title_surface = font.render(f'Режим: {mode}', True, TEXT_COLOR)
        screen.blit(title_surface, (panel_x + 20, BOARD_OFFSET + 20))

        y = BOARD_OFFSET + 500
        for line in [
            f'Статус: {online_status}',
            f"Ваш цвет: {'белые' if player_color == FIG_WHITE else 'чёрные'}",
            f"Ваш ход: {'да' if (mode != 'online' or my_turn) else 'нет'}",
        ]:
            status_surface = font.render(line, True, STATUS_COLOR)
            screen.blit(status_surface, (panel_x + 20, y))
            y += 34

        for rect in button_rects:
            pygame.draw.rect(screen, (50, 50, 50), rect, border_radius=10)

        for button in active_buttons:
            button.draw(screen, font, pygame.mouse.get_pos())

        if game.game_over:
            result_for_player = game.result
            if result_for_player and not getattr(game, '_game_over_sound_played', False):
                sound_manager.play(result_for_player)
                game._game_over_sound_played = True

            draw_game_over_beautiful(screen, result_for_player, font, title_font)

    pygame.display.flip()
    clock.tick(60)
