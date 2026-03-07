"""Основной цикл игры в шахматы."""
import pygame
import sys
import os

# Добавляем корень проекта в путь импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import WIDTH, HEIGHT, BLACK
from engine.board import Board
from engine.move_generator import MoveGenerator
from client.renderer import (
    PieceRenderer,
    draw_board,
    draw_pieces,
    draw_legal_moves,
    draw_game_over,
    draw_menu,
    get_square_from_mouse,
)
from client.game import ChessGame

# Инициализация pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Chess')
font = pygame.font.SysFont('Arial', 32)
clock = pygame.time.Clock()

# Инициализация игры
game = ChessGame()
renderer = PieceRenderer()
renderer.load_pieces()

# Состояние игры
game_state = 'MENU'
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "MENU":
                btn_rect = draw_menu(screen, font)
                if btn_rect.collidepoint(pygame.mouse.get_pos()):
                    game_state = "GAME"
                    
            elif game_state == "GAME":
                # Если игра окончена, игнорируем клики
                if game.game_over:
                    continue

                idx = get_square_from_mouse(event.pos, game.white_perspective)
                if idx is not None:
                    # Проверяем, есть ли ход на эту клетку в списке легальных
                    move_to_make = game.get_move_for_square(idx)

                    if move_to_make:
                        # Делаем ход
                        game.make_move(move_to_make)
                    else:
                        # Выбираем фигуру или сбрасываем выделение
                        game.select_square(idx)

    # Отрисовка
    if game_state == "MENU":
        draw_menu(screen, font)
    elif game_state == "GAME":
        screen.fill(BLACK)
        draw_board(screen, game.board, game.selected_square, game.white_perspective)
        draw_pieces(screen, game.board, renderer, game.white_perspective)

        # Если игра не закончена, рисуем подсветку ходов
        if not game.game_over:
            draw_legal_moves(screen, game.legal_moves, game.white_perspective)

        # Отрисовка сообщения о конце игры
        if game.game_over:
            draw_game_over(screen, game.game_result, font)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
