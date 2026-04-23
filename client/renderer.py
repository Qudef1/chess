"""Рендерер фигур и отрисовка доски."""

import pygame
from engine.board import Board
from engine.figures import (
    WHITE_PAWN, WHITE_KNIGHT, WHITE_BISHOP, WHITE_ROOK, WHITE_QUEEN, WHITE_KING,
    BLACK_PAWN, BLACK_KNIGHT, BLACK_BISHOP, BLACK_ROOK, BLACK_QUEEN, BLACK_KING,
)
from client.constants import (
    SQUARE_SIZE,
    BOARD_OFFSET,
    LIGHT_SQUARE,
    DARK_SQUARE,
    HIGHLIGHT,
    HINT,
    PANEL_BG,
    TEXT_COLOR,
    STATUS_COLOR,
    BOARD_SIZE,
    UI_PANEL_WIDTH,
    BUTTON_COLOR,
)


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
    rank = square_index // 8
    file = square_index % 8

    if white_perspective:
        row = 7 - rank
        col = file
    else:
        row = rank
        col = 7 - file

    x = BOARD_OFFSET + col * SQUARE_SIZE
    y = BOARD_OFFSET + row * SQUARE_SIZE
    return x, y


def get_square_from_mouse(pos: tuple[int, int], white_perspective: bool) -> int | None:
    x, y = pos
    if BOARD_OFFSET <= x < BOARD_OFFSET + BOARD_SIZE and BOARD_OFFSET <= y < BOARD_OFFSET + BOARD_SIZE:
        col = (x - BOARD_OFFSET) // SQUARE_SIZE
        row = (y - BOARD_OFFSET) // SQUARE_SIZE
        if white_perspective:
            rank = 7 - row
            file = col
        else:
            rank = row
            file = 7 - col
        return rank * 8 + file
    return None


def draw_board(screen: pygame.Surface, board: Board, selected_square: int | None = None, white_perspective: bool = True,
              light_square=None, dark_square=None, highlight=None):
    if light_square is None:
        light_square = LIGHT_SQUARE
    if dark_square is None:
        dark_square = DARK_SQUARE
    if highlight is None:
        highlight = HIGHLIGHT
    for i in range(64):
        x, y = get_screen_coords(i, white_perspective)
        rank = i // 8
        file = i % 8
        if white_perspective:
            row = 7 - rank
            col = file
        else:
            row = rank
            col = 7 - file
        color = light_square if (row + col) % 2 == 0 else dark_square
        if selected_square is not None and i == selected_square:
            color = highlight
        pygame.draw.rect(screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))


def draw_pieces(screen: pygame.Surface, board: Board, renderer: PieceRenderer, white_perspective: bool = True, skip_squares: set[int] | None = None):
    for square_index, piece_code in enumerate(board.squares):
        if skip_squares and square_index in skip_squares:
            continue
        if piece_code != 0 and piece_code in renderer.piece_images:
            x, y = get_screen_coords(square_index, white_perspective)
            screen.blit(renderer.piece_images[piece_code], (x, y))


def draw_legal_moves(screen: pygame.Surface, legal_moves: list, white_perspective: bool = True, hint_color=None):
    if hint_color is None:
        hint_color = HINT
    for move in legal_moves:
        x, y = get_screen_coords(move.to_square, white_perspective)
        hint_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        hint_surface.fill((*hint_color, 100))
        screen.blit(hint_surface, (x, y))


def draw_game_over(screen: pygame.Surface, game_result: str | None, font: pygame.font.Font):
    if game_result == 'mate':
        text = font.render('Мат!', True, (255, 255, 255))
    elif game_result == 'stalemate':
        text = font.render('Пат! Ничья', True, (255, 255, 255))
    else:
        return
    text_rect = text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    screen.blit(text, text_rect)


def draw_side_panel(screen: pygame.Surface, font: pygame.font.Font, title: str, status_lines: list[str],
                    panel_x: int, button_rects: list[pygame.Rect],
                    panel_bg=None, text_color=None, status_color=None):
    if panel_bg is None:
        panel_bg = PANEL_BG
    if text_color is None:
        text_color = TEXT_COLOR
    if status_color is None:
        status_color = STATUS_COLOR
    panel_width = UI_PANEL_WIDTH - 40
    panel_rect = pygame.Rect(panel_x, BOARD_OFFSET, panel_width, screen.get_height() - BOARD_OFFSET * 2)
    pygame.draw.rect(screen, panel_bg, panel_rect, border_radius=12)
    title_surface = font.render(title, True, text_color)
    screen.blit(title_surface, (panel_x + 20, BOARD_OFFSET + 20))

    y = BOARD_OFFSET + 500  # Below buttons
    for line in status_lines:
        status_surface = font.render(line, True, status_color)
        screen.blit(status_surface, (panel_x + 20, y))
        y += 34

    for rect in button_rects:
        pygame.draw.rect(screen, BUTTON_COLOR, rect, border_radius=10)


def draw_text_box(screen: pygame.Surface, font: pygame.font.Font, header: str, body: str, rect: pygame.Rect):
    pygame.draw.rect(screen, PANEL_BG, rect, border_radius=8)
    header_surface = font.render(header, True, TEXT_COLOR)
    body_surface = font.render(body, True, STATUS_COLOR)
    screen.blit(header_surface, (rect.x + 12, rect.y + 12))
    screen.blit(body_surface, (rect.x + 12, rect.y + 46))

