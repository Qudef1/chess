import pygame
import sys
from constants import *

pygame.init()

screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption('Chess')
font = pygame.font.SysFont('Arial',32)
game_state = 'MENU'

clock = pygame.time.Clock()

def draw_board(selected_square:int):
    for i in range(64):
        row = i // 8
        col = i % 8
        x = col * SQUARE_SIZE
        y = row * SQUARE_SIZE
        
        # Цвет клетки (шахматный порядок)
        color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
        
        # Подсветка выбранной
        if selected_square is not None and i == selected_square:
            color = HIGHLIGHT
            
        pygame.draw.rect(screen, color, (x+ BOARD_OFFSET, y+ BOARD_OFFSET, SQUARE_SIZE, SQUARE_SIZE))
        
        # Здесь потом будешь рисовать фигуры:
        # if board_array[i] is not None:
        #     screen.blit(piece_images[board_array[i]], (x, y))

def draw_menu():
    screen.fill('#65BA9C')
    mouse_pos = pygame.mouse.get_pos()
    button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 50, 200, 100)
    
    # Проверка наведения мыши
    color = BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, button_rect)
    
    text = font.render("Играть", True, TEXT_COLOR)
    text_rect = text.get_rect(center=button_rect.center)
    screen.blit(text, text_rect)

    return button_rect

def get_square_from_mouse(pos):
    x,y = pos
    
    if BOARD_OFFSET <= x < BOARD_OFFSET + BOARD_SIZE and BOARD_OFFSET <= y <BOARD_OFFSET+BOARD_SIZE:
        col = (x-BOARD_OFFSET) // SQUARE_SIZE
        row = (y-BOARD_OFFSET) // SQUARE_SIZE
        return row * 8 + col
    return None

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if game_state == "MENU":
                btn_rect = draw_menu()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "MENU":
                btn_rect = draw_menu()
                if pygame.mouse.get_pressed()[0] and btn_rect.collidepoint(pygame.mouse.get_pos()):
                    game_state = "GAME"
            elif game_state == "GAME":
                # Логика клика по доске
                idx = get_square_from_mouse(event.pos)
                if idx is not None:
                    # Тут логика выбора фигуры или хода
                    selected_piece_index = idx
                    print(f"Клик по клетке: {idx}")
                    draw_board(selected_square = selected_piece_index)

    pygame.display.flip()
    clock.tick(120)

pygame.quit()
sys.exit()
