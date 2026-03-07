import pygame
import sys
import os

# Добавляем корень проекта в путь импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import *
from engine.figures import *
from engine.board import Board
from engine.move_generator import MoveGenerator

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Chess')
font = pygame.font.SysFont('Arial', 32)
game_state = 'MENU'

clock = pygame.time.Clock()


class PieceRenderer:
    def __init__(self):
        self.piece_images = {}

    def load_pieces(self):
        piece_mapping = {
            WHITE_PAWN: 'pawnW',
            WHITE_KNIGHT: 'knightW',
            WHITE_BISHOP: 'bishopW',
            WHITE_ROOK: 'rookW',
            WHITE_QUEEN: 'queenW',
            WHITE_KING: 'kingW',
            BLACK_PAWN: 'pawnB2',
            BLACK_KNIGHT: 'knightB2',
            BLACK_BISHOP: 'bishopB2',
            BLACK_ROOK: 'rookB2',
            BLACK_QUEEN: 'queenB2',
            BLACK_KING: 'kingB2',
        }
        for piece_code, piece_name in piece_mapping.items():
            try:
                img = pygame.image.load(f"images/pieces/{piece_name}.png").convert_alpha()
                img = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
                self.piece_images[piece_code] = img
            except FileNotFoundError:
                print(f"Warning: not found file for {piece_name}")

    def draw_piece(self, screen, piece_code, square_index):
        if piece_code == 0:
            return
        row = square_index // 8
        col = square_index % 8
        x = BOARD_OFFSET + col * SQUARE_SIZE
        y = BOARD_OFFSET + row * SQUARE_SIZE

        if piece_code in self.piece_images:
            screen.blit(self.piece_images[piece_code], (x, y))


def draw_board(screen, board: Board, selected_square=None, white_perspective=True):
    for i in range(64):
        # Переворачиваем отображение клетки в зависимости от перспективы
        if white_perspective:
            row = 7 - (i // 8)  # Инвертируем для pygame (y=0 сверху)
            col = i % 8
        else:
            row = i // 8
            col = 7 - (i % 8)
        
        x = col * SQUARE_SIZE + BOARD_OFFSET
        y = row * SQUARE_SIZE + BOARD_OFFSET

        # Цвет клетки (шахматный порядок)
        color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE

        # Подсветка выбранной
        if selected_square is not None and i == selected_square:
            color = HIGHLIGHT

        pygame.draw.rect(screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))


def draw_board_with_pieces(screen, board: Board, renderer: PieceRenderer, selected_square=None, white_perspective=True):
    draw_board(screen, board, selected_square, white_perspective)
    for square_index, piece_code in enumerate(board.squares):
        # Переворачиваем позицию отрисовки фигуры
        if white_perspective:
            row = 7 - (square_index // 8)  # Инвертируем для pygame (y=0 сверху)
            col = square_index % 8
        else:
            row = square_index // 8
            col = 7 - (square_index % 8)
        
        x = BOARD_OFFSET + col * SQUARE_SIZE
        y = BOARD_OFFSET + row * SQUARE_SIZE

        if piece_code in renderer.piece_images:
            screen.blit(renderer.piece_images[piece_code], (x, y))


def draw_legal_moves(screen, legal_moves: list, white_perspective=True):
    """Отрисовка подсветки доступных ходов."""
    for move in legal_moves:
        if white_perspective:
            row = 7 - (move.to_square // 8)  # Инвертируем для pygame (y=0 сверху)
            col = move.to_square % 8
        else:
            row = move.to_square // 8
            col = 7 - (move.to_square % 8)
        
        x = BOARD_OFFSET + col * SQUARE_SIZE
        y = BOARD_OFFSET + row * SQUARE_SIZE

        # Рисуем полупрозрачный круг или квадрат на клетке назначения
        hint_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        hint_surface.fill((*HINT, 100))  # Добавляем альфа-канал
        screen.blit(hint_surface, (x, y))


def draw_game_over(screen, game_result):
    """Отрисовка сообщения о конце игры."""
    if game_result == 'mate':
        text = font.render("Мат!", True, (255, 255, 255))
    elif game_result == 'stalemate':
        text = font.render("Пат! Ничья", True, (255, 255, 255))
    else:
        return
    
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    
    # Полупрозрачный фон
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    
    screen.blit(text, text_rect)


def draw_menu(screen):
    screen.fill((255, 255, 255))
    mouse_pos = pygame.mouse.get_pos()
    button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 100)

    # Проверка наведения мыши
    color = BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, button_rect)

    text = font.render("Играть", True, TEXT_COLOR)
    text_rect = text.get_rect(center=button_rect.center)
    screen.blit(text, text_rect)

    return button_rect


def get_square_from_mouse(pos, white_perspective=True):
    x, y = pos

    if BOARD_OFFSET <= x < BOARD_OFFSET + BOARD_SIZE and BOARD_OFFSET <= y < BOARD_OFFSET + BOARD_SIZE:
        col = (x - BOARD_OFFSET) // SQUARE_SIZE
        row = (y - BOARD_OFFSET) // SQUARE_SIZE
        
        # Переворачиваем координаты в зависимости от перспективы
        # В pygame y=0 сверху, поэтому инвертируем row для white_perspective
        if white_perspective:
            # row=0 (верх экрана) → rank 7, row=7 (низ экрана) → rank 0
            return (7 - row) * 8 + col
        else:
            # row=0 (верх экрана) → rank 0, row=7 (низ экрана) → rank 7
            return row * 8 + (7 - col)
    return None


# Инициализация
board = Board()
renderer = PieceRenderer()
renderer.load_pieces()
move_generator = MoveGenerator()
selected_square = None
legal_moves = []
white_perspective = True  # Белые снизу (стандартная перспектива)
game_over = False
game_result = None  # 'mate', 'stalemate', None

def check_game_over():
    """Проверка на мат или пат."""
    global game_over, game_result
    all_legal_moves = move_generator.generate_legal_moves(board)
    if len(all_legal_moves) == 0:
        game_over = True
        # Проверяем, под шахом ли король
        king_sq = board.find_king(board.side_to_move)
        enemy_color = BLACK if board.side_to_move == WHITE else WHITE
        if board.is_square_attacked(king_sq, enemy_color):
            game_result = 'mate'
            winner = 'Белые' if board.side_to_move == BLACK else 'Чёрные'
            print(f"Мат! Победили {winner}")
        else:
            game_result = 'stalemate'
            print("Пат! Ничья")
    else:
        game_over = False
        game_result = None
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "MENU":
                btn_rect = draw_menu(screen)
                if btn_rect.collidepoint(pygame.mouse.get_pos()):
                    game_state = "GAME"
            elif game_state == "GAME":
                # Если игра окончена, игнорируем клики
                if game_over:
                    continue
                    
                idx = get_square_from_mouse(event.pos, white_perspective)
                if idx is not None:
                    piece = board.get_piece(idx)

                    # Проверяем, есть ли ход на эту клетку в списке легальных
                    move_to_make = next((m for m in legal_moves if m.to_square == idx), None)

                    if move_to_make:
                        # Делаем ход
                        captured = board.get_piece(move_to_make.to_square)
                        old_en_passant = board.en_passant_square
                        moved_piece = board.get_piece(move_to_make.from_square)
                        board.make_move(move_to_make)

                        # Переворачиваем доску после хода
                        white_perspective = not white_perspective

                        # Сбрасываем выделение
                        selected_square = None
                        legal_moves = []
                        print(f"Ход сделан: {move_to_make.from_square} -> {move_to_make.to_square}")
                        
                        # Проверяем на мат/пат
                        check_game_over()

                    # Если кликнули на свою фигуру - выбираем её
                    elif piece != EMPTY and get_piece_color(piece) == board.side_to_move:
                        selected_square = idx
                        # Генерируем все легальные ходы и фильтруем по выбранной клетке
                        all_legal_moves = move_generator.generate_legal_moves(board)
                        legal_moves = [m for m in all_legal_moves if m.from_square == idx]
                        print(f"Клик по клетке: {idx}, доступно ходов: {len(legal_moves)}")
                    else:
                        # Если кликнули на пустую клетку или фигуру противника
                        selected_square = None
                        legal_moves = []

    # Отрисовка
    if game_state == "MENU":
        draw_menu(screen)
    elif game_state == "GAME":
        screen.fill(BLACK)
        draw_board_with_pieces(screen, board, renderer, selected_square, white_perspective)
        
        # Если игра не закончена, рисуем подсветку ходов
        if not game_over:
            draw_legal_moves(screen, legal_moves, white_perspective)
        
        # Отрисовка сообщения о конце игры
        if game_over:
            draw_game_over(screen, game_result)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
