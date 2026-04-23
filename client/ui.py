from dataclasses import dataclass
import pygame
from client.constants import BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR, PANEL_BG, INPUT_BG, INPUT_ACTIVE_BG


@dataclass
class Button:
    text: str
    rect: pygame.Rect

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, mouse_pos: tuple[int, int]):
        hovered = self.rect.collidepoint(mouse_pos)
        color = BUTTON_HOVER if hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        text_surface = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def contains(self, position: tuple[int, int]) -> bool:
        return self.rect.collidepoint(position)


@dataclass
class InputField:
    rect: pygame.Rect
    text: str = ''
    active: bool = False

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
                try:
                    clipboard = pygame.scrap.get_text() if pygame.scrap.get_init() else None
                    if clipboard:
                        self.text += clipboard
                except Exception:
                    pass
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif len(event.unicode) > 0:
                self.text += event.unicode

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, mouse_pos: tuple[int, int]):
        color = INPUT_ACTIVE_BG if self.active else INPUT_BG
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BUTTON_COLOR, self.rect, 2, border_radius=8)
        text_surface = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 12, self.rect.centery))
        surface.blit(text_surface, text_rect)


@dataclass
class NumericInputField:
    """Input field that only accepts numeric values."""
    rect: pygame.Rect
    text: str = ''
    active: bool = False
    min_val: int = 0
    max_val: int = 100

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
                try:
                    clipboard = pygame.scrap.get_text() if pygame.scrap.get_init() else None
                    if clipboard:
                        for char in clipboard:
                            if char.isdigit():
                                self.text += char
                except Exception:
                    pass
            elif event.key == pygame.K_RETURN:
                self.active = False
                self._validate_and_clamp()
            elif event.unicode.isdigit():
                self.text += event.unicode

    def _validate_and_clamp(self):
        """Validate and clamp the value to min/max."""
        if self.text:
            try:
                val = int(self.text)
                val = max(self.min_val, min(self.max_val, val))
                self.text = str(val)
            except ValueError:
                self.text = str(self.min_val)

    def get_value(self) -> int:
        """Get the numeric value, or min_val if invalid."""
        try:
            return int(self.text) if self.text else self.min_val
        except ValueError:
            return self.min_val

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, mouse_pos: tuple[int, int]):
        color = INPUT_ACTIVE_BG if self.active else INPUT_BG
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BUTTON_COLOR, self.rect, 2, border_radius=8)
        text_surface = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 12, self.rect.centery))
        surface.blit(text_surface, text_rect)
