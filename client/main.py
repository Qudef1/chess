"""Основной цикл игры в шахматы."""
import os
import sys
import pygame
import random
from queue import Queue

# Добавляем корень проекта в путь импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import WIDTH, HEIGHT, BLACK, BOARD_OFFSET, BOARD_SIZE, UI_PANEL_WIDTH, BUTTON_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT
from client.renderer import (
    PieceRenderer,
    draw_board,
    draw_pieces,
    draw_legal_moves,
    draw_game_over,
    draw_side_panel,
    get_screen_coords,
    get_square_from_mouse,
)
from client.ui import Button, InputField
from client.network import NetworkClient
from client.game import ChessGame
from stockfish.stockfish_engine import StockfishEngine
from engine.move import Move, EN_PASSANT
from engine.figures import WHITE as FIG_WHITE, BLACK as FIG_BLACK

pygame.init()
pygame.mixer.init()
# Load and play music
music_file = os.path.join(os.path.dirname(__file__), '..', 'music', 'Skrillex - Bangarang.mp3')
if os.path.exists(music_file):
    pygame.mixer.music.load(music_file)
    pygame.mixer.music.play(-1)  # Loop indefinitely
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Chess')
font = pygame.font.SysFont('Arial', 24)
title_font = pygame.font.SysFont('Arial', 36, bold=True)
clock = pygame.time.Clock()

# Инициализация
game = ChessGame()
renderer = PieceRenderer()
renderer.load_pieces()
stockfish_engine = StockfishEngine(depth=10)

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

animation_active = False
animation_move = None
animation_start = 0
animation_duration = 250
animation_piece = 0
animation_from = 0
animation_to = 0
animation_capture_sq = -1
animation_is_remote = False
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


def start_move_animation(move: Move, is_remote: bool = False, on_complete=None):
    global animation_active, animation_move, animation_start, animation_piece
    global animation_from, animation_to, animation_capture_sq, animation_is_remote, animation_on_complete

    if animation_active:
        return

    animation_active = True
    animation_move = move
    animation_start = pygame.time.get_ticks()
    animation_piece = game.board.get_piece(move.from_square)
    animation_from = move.from_square
    animation_to = move.to_square
    animation_is_remote = is_remote
    animation_on_complete = on_complete

    if move.flag == EN_PASSANT:
        if get_square_from_mouse:  # only for logic, not actually used
            pass
        # capture square depends on mover color
        animation_capture_sq = move.to_square - 8 if animation_piece > 0 else move.to_square + 8
    else:
        animation_capture_sq = move.to_square


def complete_move_animation():
    global animation_active, animation_move, animation_capture_sq, animation_is_remote, animation_on_complete, my_turn

    if not animation_active or animation_move is None:
        return

    game.make_move(animation_move)

    # For local mode, flip board after move
    if mode == 'local':
        game.white_perspective = not game.white_perspective

    if animation_is_remote:
        my_turn = True
    else:
        if mode == 'stockfish' and not game.game_over:
            apply_stockfish_move()

    if animation_on_complete:
        try:
            animation_on_complete()
        except Exception:
            pass

    animation_active = False
    animation_move = None
    animation_capture_sq = -1
    animation_is_remote = False
    animation_on_complete = None


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
    labels = ['Локальная игра', 'Против Stockfish', 'Онлайн', 'Настройки', 'Выход']
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


def set_status(text: str):
    global online_status
    online_status = text


def reset_game(new_mode: str):
    global mode, player_color, my_turn, draw_offer_pending
    mode = new_mode
    game.reset()
    draw_offer_pending = False
    player_color = FIG_WHITE
    game.white_perspective = True  # Always show from white's perspective
    if mode == 'stockfish':
        my_turn = True
        set_status('Игра против Stockfish. Вы белые.')
    elif mode == 'online':
        my_turn = False
        set_status('Онлайн: ожидайте подключения.')
    else:
        my_turn = True
        set_status('Локальная игра')


def apply_stockfish_move():
    if stockfish_engine.is_available():
        best_move = stockfish_engine.get_best_move(game.board)
    else:
        legal = game.move_generator.generate_legal_moves(game.board)
        best_move = random.choice(legal) if legal else None
    if best_move is not None:
        start_move_animation(best_move, on_complete=lambda: set_status('Ход компьютера выполнен.'))


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
    # Reset local game state when disconnecting from online
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
            # Ensure a fresh board for the new online game
            reset_game('online')
            color = message.get('payload', {}).get('color', 'white')
            player_color = FIG_WHITE if color == 'white' else FIG_BLACK
            # Keep white perspective (white at bottom)
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
            game.game_result = 'stalemate'
            set_status('Соперник сдался. Вы победили.')
        elif event_type == 'draw_offer':
            draw_offer_pending = True
            set_status('Соперник предлагает ничью. Нажмите ещё раз, чтобы принять.')
        elif event_type == 'draw_accepted':
            game.game_over = True
            game.game_result = 'stalemate'
            draw_offer_pending = False
            set_status('Ничья согласована.')
        elif event_type == 'draw_rejected':
            draw_offer_pending = False
            set_status('Соперник отклонил ничью.')
        elif event_type == 'opponent_left':
            game.game_over = True
            set_status('Соперник отключился.')
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
    
    # Block all board interactions during opponent's turn in online mode
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
            start_move_animation(move_to_make, on_complete=lambda: set_status('Ход выполнен.'))
            if mode == 'stockfish':
                # ход компьютера будет выполнен после окончания анимации
                pass
        draw_offer_pending = False
        return
    game.select_square(idx)


def action_button_clicked(label: str):
    global draw_offer_pending, game_state
    if label == 'Сдаться':
        if mode == 'online' and network_client:
            network_client.send_resign()
            game.game_over = True
            set_status('Вы сдались.')
        else:
            game.game_over = True
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
            # Local/Stockfish: require confirmation
            if draw_offer_pending:
                game.game_over = True
                game.game_result = 'stalemate'
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


game_state = 'MENU'

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and game_state == 'ONLINE_CONNECT':
            server_input.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if game_state == 'MENU':
                for button in menu_buttons:
                    if button.contains(mouse_pos):
                        if button.text == 'Локальная игра':
                            reset_game('local')
                            game_state = 'GAME'
                        elif button.text == 'Против Stockfish':
                            reset_game('stockfish')
                            game_state = 'GAME'
                        elif button.text == 'Онлайн':
                            game_state = 'ONLINE_CONNECT'
                            set_status('Введите адрес сервера и нажмите Подключиться.')
                        elif button.text == 'Настройки':
                            game_state = 'SETTINGS'
                        elif button.text == 'Выход':
                            pygame.quit()
                            sys.exit()
                        break
            elif game_state == 'ONLINE_CONNECT':
                server_input.handle_event(event)
                connect_button = Button('Подключиться', pygame.Rect(BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING, 260, BUTTON_WIDTH, BUTTON_HEIGHT))
                back_button = Button('Назад', pygame.Rect(BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING, 340, BUTTON_WIDTH, BUTTON_HEIGHT))
                if connect_button.contains(mouse_pos):
                    connect_online()
                elif back_button.contains(mouse_pos):
                    game_state = 'MENU'
            elif game_state == 'SETTINGS':
                sound_button = Button(f"Звук: {'Вкл' if sound_enabled else 'Выкл'}", pygame.Rect(BOARD_OFFSET, 160, 200, 50))
                music_button = Button(f"Музыка: {'Вкл' if music_enabled else 'Выкл'}", pygame.Rect(BOARD_OFFSET, 220, 200, 50))
                back_button = Button('Назад', pygame.Rect(BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING, 260, BUTTON_WIDTH, BUTTON_HEIGHT))
                if sound_button.contains(mouse_pos):
                    sound_enabled = not sound_enabled
                elif music_button.contains(mouse_pos):
                    music_enabled = not music_enabled
                    if music_enabled and os.path.exists(music_file):
                        pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.stop()
                elif back_button.contains(mouse_pos):
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
        connect_button = Button('Подключиться', pygame.Rect(BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING, 260, BUTTON_WIDTH, BUTTON_HEIGHT))
        back_button = Button('Назад', pygame.Rect(BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING, 340, BUTTON_WIDTH, BUTTON_HEIGHT))
        connect_button.draw(screen, font, pygame.mouse.get_pos())
        back_button.draw(screen, font, pygame.mouse.get_pos())
        info = font.render(online_status, True, (220, 220, 220))
        screen.blit(info, (BOARD_OFFSET, 360))
    elif game_state == 'SETTINGS':
        title_surface = title_font.render('Настройки', True, (255, 255, 255))
        screen.blit(title_surface, (BOARD_OFFSET, 80))
        sound_button = Button(f"Звук: {'Вкл' if sound_enabled else 'Выкл'}", pygame.Rect(BOARD_OFFSET, 160, 200, 50))
        music_button = Button(f"Музыка: {'Вкл' if music_enabled else 'Выкл'}", pygame.Rect(BOARD_OFFSET, 220, 200, 50))
        sound_button.draw(screen, font, pygame.mouse.get_pos())
        music_button.draw(screen, font, pygame.mouse.get_pos())
        back_button = Button('Назад', pygame.Rect(BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING, 260, BUTTON_WIDTH, BUTTON_HEIGHT))
        back_button.draw(screen, font, pygame.mouse.get_pos())
    elif game_state == 'GAME':
        draw_board(screen, game.board, game.selected_square, game.white_perspective)
        skip_squares = {animation_from, animation_capture_sq} if animation_active else None
        draw_pieces(screen, game.board, renderer, game.white_perspective, skip_squares=skip_squares)
        draw_moving_piece()
        if not game.game_over:
            draw_legal_moves(screen, game.legal_moves, game.white_perspective)
        active_buttons = get_active_game_buttons()
        button_rects = [button.rect for button in active_buttons]
        draw_side_panel(
            screen,
            font,
            f'Режим: {mode}',
            [
                f'Статус: {online_status}',
                f"Ваш цвет: {'белые' if player_color == FIG_WHITE else 'чёрные'}",
                f"Ваш ход: {'да' if (mode != 'online' or my_turn) else 'нет'}",
            ],
            BOARD_OFFSET + BOARD_SIZE + BUTTON_SPACING,
            button_rects,
        )
        for button in active_buttons:
            button.draw(screen, font, pygame.mouse.get_pos())
        if game.game_over:
            draw_game_over(screen, game.game_result, title_font)

    pygame.display.flip()
    clock.tick(60)
