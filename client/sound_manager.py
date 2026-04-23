"""Менеджер звуков игры."""
import os
import pygame


class SoundManager:
    def __init__(self, sounds_dir: str = None):
        if sounds_dir is None:
            sounds_dir = os.path.join(os.path.dirname(__file__), '..', 'sounds')
        self.sounds_dir = sounds_dir
        self.sounds = {}
        self.enabled = True
        self._load_sounds()

    def _load_sounds(self):
        """Загрузить все звуковые файлы."""
        sound_files = {
            'move': 'move.mp3',
            'check': 'check.mp3',
            'game_over': 'game_over.mp3',
            'win': 'win.mp3',
            'lose': 'lose.mp3',
            'game': 'game.mp3',
        }
        for key, filename in sound_files.items():
            path = os.path.join(self.sounds_dir, filename)
            if os.path.exists(path):
                try:
                    self.sounds[key] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"Warning: could not load sound {filename}: {e}")
            else:
                print(f"Warning: sound file not found: {path}")

    def play(self, sound_name: str):
        """Воспроизвести звук по имени."""
        if not self.enabled or sound_name not in self.sounds:
            return
        try:
            self.sounds[sound_name].play()
        except Exception as e:
            print(f"Error playing sound {sound_name}: {e}")

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def is_enabled(self) -> bool:
        return self.enabled

    def set_volume(self, volume: float):
        """Установить громкость звуков (0.0 - 1.0)."""
        volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(volume)
