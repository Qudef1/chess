"""Рендерер фигур и отрисовка доски."""
import pygame
from engine.board import Board
from engine.figures import (
    WHITE_PAWN, WHITE_KNIGHT, WHITE_BISHOP, WHITE_ROOK, WHITE_QUEEN, WHITE_KING,
    BLACK_PAWN, BLACK_KNIGHT, BLACK_BISHOP, BLACK_ROOK, BLACK_QUEEN, BLACK_KING,
)
from constants import SQUARE_SIZE, BOARD_OFFSET, LIGHT_SQUARE, DARK_SQUARE, HIGHLIGHT, HINT


class PieceRenderer:
    """Класс для отрисовки шахматных фигур."""
    
    def __init__(self):
        self.piece_images = {}

    def load_pieces(self):
        """Загрузить изображения фигур."""
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


def get_screen_coords(square_index: int, white_perspective: bool) -> tuple[int, int]:
    """
    Преобразовать индекс клетки (0-63) в экранные координаты.
    
    Args:
        square_index: Индекс клетки (0 = a1, 63 = h8)
        white_perspective: True если белые снизу, False если чёрные снизу
    
    Returns:
        Кортеж (x, y) экранных координат
    """
    rank = square_index // 8
    file = square_index % 8
    
    if white_perspective:
        # Белые снизу: a1 (0) → нижний левый угол
        row = 7 - rank  # Инвертируем для pygame (y=0 сверху)
        col = file
    else:
        # Чёрные снизу: a8 (56) → нижний левый угол
        row = rank  # Не инвертируем
        col = 7 - file  # Зеркалим по горизонтали
    
    x = BOARD_OFFSET + col * SQUARE_SIZE
    y = BOARD_OFFSET + row * SQUARE_SIZE
    return x, y


def get_square_from_mouse(pos: tuple[int, int], white_perspective: bool) -> int | None:
    """
    Преобразовать координаты мыши в индекс клетки.
    
    Args:
        pos: Кортеж (x, y) координат мыши
        white_perspective: True если белые снизу, False если чёрные снизу
    
    Returns:
        Индекс клетки (0-63) или None если клик вне доски
    """
    x, y = pos

    if BOARD_OFFSET <= x < BOARD_OFFSET + SQUARE_SIZE * 8 and BOARD_OFFSET <= y < BOARD_OFFSET + SQUARE_SIZE * 8:
        col = (x - BOARD_OFFSET) // SQUARE_SIZE
        row = (y - BOARD_OFFSET) // SQUARE_SIZE

        if white_perspective:
            # row=0 (верх экрана) → rank 7, row=7 (низ экрана) → rank 0
            rank = 7 - row
            file = col
        else:
            # row=0 (верх экрана) → rank 0, row=7 (низ экрана) → rank 7
            rank = row
            file = 7 - col

        return rank * 8 + file
    return None


def draw_board(screen: pygame.Surface, board: Board, selected_square: int | None = None, white_perspective: bool = True):
    """
    Отрисовать шахматную доску.
    
    Args:
        screen: Pygame поверхность для отрисовки
        board: Объект доски
        selected_square: Индекс выбранной клетки или None
        white_perspective: True если белые снизу, False если чёрные снизу
    """
    for i in range(64):
        x, y = get_screen_coords(i, white_perspective)
        
        # Цвет клетки (шахматный порядок)
        rank = i // 8
        file = i % 8
        if white_perspective:
            row = 7 - rank
            col = file
        else:
            row = rank
            col = 7 - file
        
        color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE

        # Подсветка выбранной
        if selected_square is not None and i == selected_square:
            color = HIGHLIGHT

        pygame.draw.rect(screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))


def draw_pieces(screen: pygame.Surface, board: Board, renderer: PieceRenderer, white_perspective: bool = True):
    """
    Отрисовать фигуры на доске.
    
    Args:
        screen: Pygame поверхность для отрисовки
        board: Объект доски
        renderer: Объект рендерера фигур
        white_perspective: True если белые снизу, False если чёрные снизу
    """
    for square_index, piece_code in enumerate(board.squares):
        if piece_code != 0 and piece_code in renderer.piece_images:
            x, y = get_screen_coords(square_index, white_perspective)
            screen.blit(renderer.piece_images[piece_code], (x, y))


def draw_legal_moves(screen: pygame.Surface, legal_moves: list, white_perspective: bool = True):
    """
    Отрисовать подсветку доступных ходов.
    
    Args:
        screen: Pygame поверхность для отрисовки
        legal_moves: Список доступных ходов
        white_perspective: True если белые снизу, False если чёрные снизу
    """
    for move in legal_moves:
        x, y = get_screen_coords(move.to_square, white_perspective)

        # Рисуем полупрозрачный квадрат на клетке назначения
        hint_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        hint_surface.fill((*HINT, 100))  # Добавляем альфа-канал
        screen.blit(hint_surface, (x, y))


def draw_game_over(screen: pygame.Surface, game_result: str | None, font: pygame.font.Font):
    """
    Отрисовать сообщение о конце игры.
    
    Args:
        screen: Pygame поверхность для отрисовки
        game_result: 'mate', 'stalemate' или None
        font: Шрифт для отрисовки текста
    """
    if game_result == 'mate':
        text = font.render("Мат!", True, (255, 255, 255))
    elif game_result == 'stalemate':
        text = font.render("Пат! Ничья", True, (255, 255, 255))
    else:
        return

    text_rect = text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))

    # Полупрозрачный фон
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))

    screen.blit(text, text_rect)


def draw_menu(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    """
    Отрисовать главное меню.
    
    Args:
        screen: Pygame поверхность для отрисовки
        font: Шрифт для отрисовки текста
    
    Returns:
        Rect кнопки "Играть"
    """
    from constants import (
        WIDTH, HEIGHT, BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR
    )
    
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
