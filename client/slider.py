"""Слайдер для регулировки громкости."""
import pygame
from client.constants import BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR


class Slider:
    def __init__(self, rect: pygame.Rect, min_val: float = 0.0, max_val: float = 1.0, initial_val: float = 0.5):
        self.rect = rect
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.dragging = False
        self.handle_radius = 10

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            handle_x = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
            handle_y = self.rect.centery
            dist = ((mouse_x - handle_x) ** 2 + (mouse_y - handle_y) ** 2) ** 0.5
            if dist <= self.handle_radius + 5:
                self.dragging = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x = event.pos[0]
            relative_x = max(0, min(self.rect.width, mouse_x - self.rect.x))
            self.value = self.min_val + (relative_x / self.rect.width) * (self.max_val - self.min_val)
            return True
        return False

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]):
        pygame.draw.rect(surface, (80, 80, 80), self.rect, border_radius=4)

        filled_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        if filled_width > 0:
            filled_rect = pygame.Rect(self.rect.x, self.rect.y, filled_width, self.rect.height)
            pygame.draw.rect(surface, BUTTON_COLOR, filled_rect, border_radius=4)

        handle_x = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        handle_y = self.rect.centery

        dist = ((mouse_pos[0] - handle_x) ** 2 + (mouse_pos[1] - handle_y) ** 2) ** 0.5
        handle_color = BUTTON_HOVER if dist <= self.handle_radius + 5 or self.dragging else (200, 200, 200)

        pygame.draw.circle(surface, handle_color, (handle_x, handle_y), self.handle_radius)
        pygame.draw.circle(surface, (50, 50, 50), (handle_x, handle_y), self.handle_radius, 2)
