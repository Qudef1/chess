# Chess Project

Шахматное приложение с поддержкой локальной игры, игры против Stockfish и онлайн-игры.

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Архитектура проекта](#архитектура-проекта)
- [Структура каталогов](#структура-каталогов)
- [Описание модулей и классов](#описание-модулей-классов)
- [Режимы игры](#режимы-игры)
- [Звуки и музыка](#звуки-и-музыка)
- [Настройки](#настройки)

---

## Быстрый старт

### Запуск игры

```bash
cd chess
python -m client.main
```

Требуется Python 3.10+ и pygame.

### Запуск сервера (для онлайн-игры)

```bash
cd chess
python -m server.main
```

Сервер стартует на `http://0.0.0.0:8000`. Подключение из клиента: `ws://127.0.0.1:8000/ws`.

---

## Архитектура проекта

Проект построен по модульной архитектуре. Код разделён на три основных слоя:

```
┌─────────────────────────────────────────┐
│           client/  (UI, pygame)          │
│  main.py, renderer.py, ui.py, game.py    │
│  network.py, sound_manager.py, constants │
├─────────────────────────────────────────┤
│           engine/  (логика шахмат)        │
│  board.py, figures.py, move.py           │
│  move_generator.py                       │
├─────────────────────────────────────────┤
│  server/  (онлайн-режим, FastAPI)       │
│  main.py, manager.py, room.py, models.py │
├─────────────────────────────────────────┤
│  stockfish/  (движок анализа)           │
│  stockfish_engine.py                    │
└─────────────────────────────────────────┘
```

Клиент импортирует модули движка напрямую и не зависит от сервера. Сервер полностью автономен и не содержит логики игры — он только маршрутизирует сообщения между клиентами.

### Поток данных при ходе игрока

```
Игрок кликает мышью
    → handle_board_click (main.py)
        → game.select_square / game.get_move_for_square (game.py)
            → move_generator.generate_legal_moves (move_generator.py)
        → start_move_animation
            → animate → complete_move_animation
                → game.make_move (board.py)
                → sound_manager.play('move')
                → apply_stockfish_move (если режим stockfish)
                    → stockfish_engine.get_best_move
                → check_game_over → draw_game_over_beautiful
```

---

## Структура каталогов

```
chess/
├── client/              # Клиентская часть (pygame UI)
│   ├── main.py         # Главный цикл, состояния, обработка событий
│   ├── renderer.py     # Отрисовка доски, фигур, подсказок
│   ├── ui.py           # Классы Button, InputField
│   ├── game.py         # ChessGame — состояние игры
│   ├── network.py      # NetworkClient — WebSocket-клиент
│   ├── sound_manager.py # SoundManager — воспроизведение звуков
│   └── constants.py   # Константы: размеры, цвета, размеры UI
├── engine/             # Движок шахматной логики
│   ├── board.py        # Board — доска и все операции с ней
│   ├── figures.py      # Константы фигур, цветов, клеток, утилиты
│   ├── move.py         # Move — класс хода с флагами
│   └── move_generator.py # MoveGenerator — генерация ходов
├── server/             # Онлайн-сервер (FastAPI + WebSocket)
│   ├── main.py         # FastAPI-приложение, endpoint /ws
│   ├── manager.py      # RoomManager — управление комнатами
│   ├── room.py         # Room — комната двух игроков
│   └── models.py       # Pydantic-модели сообщений
├── stockfish/          # Интеграция со Stockfish
│   ├── stockfish_engine.py # StockfishEngine — обёртка над UCI
│   └── stockfish_guide.md  # Руководство по установке
├── images/pieces/      # PNG-файлы фигур
├── music/              # MP3-файлы фоновой музыки
├── sounds/             # MP3-файлы звуковых эффектов
└── tests/              # Тесты: perft и генерация ходов
```

---

## Описание модулей и классов

### client/constants.py

Набор глобальных констант: размеры окна (`WIDTH`, `HEIGHT`), смещения, цвета по умолчанию, размеры кнопок. Все физические размеры вынесены сюда, чтобы их можно было менять в одном месте.

### client/ui.py

**Button** — дата-класс кнопки с текстом и прямоугольником. Метод `draw` отрисовывает кнопку с учётом наведения мыши. Метод `contains` проверяет попадание точки внутрь.

**InputField** — поле ввода для адреса сервера. Поддерживает ввод текста, backspace, paste через Ctrl+V.

**NumericInputField** — специализированное поле ввода для числовых значений (0-100). Принимает только цифры, автоматически зажимает значение в диапазоне при нажатии Enter. Используется для регулировки громкости звуков и музыки в меню настроек.

### client/sound_manager.py

**SoundManager** — загружает звуковые файлы из папки `sounds/` при инициализации. Метод `play(sound_name)` воспроизводит звук по ключу. Метод `set_enabled` включает/выключает звуки.

Имена звуков: `move`, `check`, `game_over`, `win`, `lose`, `game`.

### client/renderer.py

**PieceRenderer** — загружает PNG-файлы фигур из `images/pieces/` при вызове `load_pieces()`. Хранит словарь `piece_images`, где ключ — числовой код фигуры из `figures.py`, значение — поверхность `pygame.Surface`.

Функции отрисовки:

- `get_screen_coords(square_index, white_perspective)` — преобразует индекс клетки 0–63 в экранные координаты. При `white_perspective=True` белые находятся внизу (классический вид), иначе доска перевёрнута.
- `get_square_from_mouse(pos, white_perspective)` — обратное преобразование: координаты мыши → индекс клетки.
- `draw_board(screen, board, selected_square, white_perspective, light_square, dark_square, highlight)` — отрисовывает 64 клетки доски с учётом темы.
- `draw_pieces(screen, board, renderer, white_perspective, skip_squares)` — отрисовывает все фигуры на доске. `skip_squares` нужен во время анимации, чтобы на исходной и целевой клетках не было дублирования.
- `draw_legal_moves(screen, legal_moves, white_perspective, hint_color)` — рисует полупрозрачные зелёные круги на клетках, куда может пойти выбранная фигура.
- `draw_side_panel(screen, font, title, status_lines, panel_x, button_rects, ...)` — боковая панель с заголовком, статусом и кнопками.

### client/game.py

**ChessGame** — класс управления состоянием шахматной партии. Содержит:

- `board` — объект `Board` (позиция, очередь хода, рокировки, en passant).
- `selected_square` — индекс выбранной клетки (или `None`).
- `legal_moves` — список легальных ходов выбранной фигуры.
- `white_perspective` — ориентация доски.
- `game_over`, `game_result` — флаг окончания и тип (`mate`, `stalemate`).

Методы:

- `select_square(idx)` — выбор фигуры, генерация и фильтрация ходов.
- `make_move(move)` — применение хода к доске, возврат информации для `unmake`.
- `check_game_over()` — проверка на мат/пат после хода.
- `get_move_for_square(idx)` — поиск хода по целевой клетке.

### engine/figures.py

Константы и утилиты. Фигуры кодируются числами: белые — положительные (1–6), чёрные — отрицательные (−1 до −6). EMPTY = 0. Цвета: `WHITE = 1`, `BLACK = −1`.

Битовое поле для рокировок: `WHITE_KINGSIDE=1`, `WHITE_QUEENSIDE=2`, `BLACK_KINGSIDE=4`, `BLACK_QUEENSIDE=8`.

Константы клеток: от `A1=0` до `H8=63`. Функции `square(file, rank)`, `file_of(sq)`, `rank_of(sq)`, `square_name(sq)` — преобразования между координатами.

`get_piece_color(piece)` возвращает цвет фигуры. `get_piece_type(piece)` возвращает тип (1–6).

### engine/board.py

**Board** — класс доски. Хранит:

- `squares: list[int]` — 64 элемента, коды фигур.
- `side_to_move` — чей ход (`WHITE` или `BLACK`).
- `castling_rights` — битовое поле доступных рокировок.
- `en_passant_square` — индекс клетки, доступной для en passant, или −1.
- `halfmove_clock`, `fullmove_number` — счётчики для правила 50 ходов.

Методы:

- `set_start_position()` — расставляет фигуры в начальную позицию.
- `get_piece(sq)`, `set_piece(sq, piece)` — доступ к клетке.
- `is_empty(sq)`, `is_enemy(sq, color)`, `is_friend(sq, color)` — проверки.
- `find_king(color)` — поиск короля на доске.
- `make_move(move)` — делает ход, обновляет рокировки и en passant. Возвращает кортеж `(captured_piece, old_en_passant, moved_piece, old_castling)` для отмены.
- `unmake_move(...)` — отменяет ход.
- `is_square_attacked(sq, by_color)` — проверяет, атакована ли клетка фигурами указанного цвета.
- `to_fen()` — генерирует FEN-строку позиции.
- `copy()` — копия доски для тестов.

### engine/move.py

**Move** — дата-класс хода. Поля: `from_square`, `to_square`, `flag`, `promotion`.

Флаги ходов:

| Флаг | Значение | Описание |
|------|----------|----------|
| `NORMAL` | 0 | Обычный ход |
| `CAPTURE` | 1 | Взятие |
| `CASTLING` | 2 | Рокировка |
| `EN_PASSANT` | 3 | Взятие на проходе |
| `PROMOTION` | 4 | Превращение пешки |
| `DOUBLE_PAWN_PUSH` | 5 | Двойной ход пешки |

`__repr__` возвращает нотацию вида `e2e4(N)`.

### engine/move_generator.py

**MoveGenerator** — генератор ходов. Не хранит состояния, только методы.

- `generate_moves(board)` — все псевдо-легальные ходы (без проверки на шах).
- `generate_legal_moves(board)` — фильтрует псевдо-легальные ходы, отбрасывая те, что оставляют своего короля под шахом.

Приватные методы: `_generate_pawn_moves`, `_generate_knight_moves`, `_generate_bishop_moves`, `_generate_rook_moves`, `_generate_queen_moves`, `_generate_king_moves`, `_generate_castling_moves`, `_generate_en_passant`.

`_is_valid_step` и `_is_valid_square` — валидация границ доски (не дают ладье/королю пересекать края).

### client/network.py

**NetworkClient** — асинхронный WebSocket-клиент в отдельном потоке. Использует `websockets` и `asyncio`.

- `connect()` — запускает поток с event loop.
- `send(message)` — отправляет сообщение в очередь.
- `send_join`, `send_move`, `send_resign`, `send_offer_draw`, `send_accept_draw` — типизированные методы отправки.

Входящие сообщения обрабатываются через колбэк `on_message`, который кладёт их в `queue.Queue` для синхронной обработки в главном потоке.

### server/models.py

**MovePayload** — Pydantic-модель хода (from_square, to_square, flag, promotion).

**ClientMessage** — входящее сообщение от клиента (type, nickname, move, message).

**ServerMessage** — исходящее сообщение сервера (type, payload, message).

### server/room.py

**Room** — комната двух игроков. Хранит два `WebSocket` соединения и словарь соответствия `id(websocket) → color`. Методы:

- `get_opponent(websocket)` — возвращает WebSocket второго игрока.
- `get_color(websocket)` — возвращает цвет игрока (`white`/`black`).
- `broadcast(message, exclude)` — отправляет сообщение обоим игрокам, опционально исключая одного.
- `contains(websocket)` — проверяет, состоит ли игрок в комнате.

### server/manager.py

**RoomManager** — синглтон управления комнатами.

- `connect(websocket)` — первый клиент становится в очередь ожидания (`waiting`), второй — создаёт комнату и получает цвет.
- `disconnect(websocket)` — удаляет клиента; если у opponent есть комната, ему отправляется `opponent_left`.
- `handle_message(websocket, text)` — парсит `ClientMessage`, маршрутизирует ходы, resign, draw-офферы между игроками.

### stockfish/stockfish_engine.py

**StockfishEngine** — обёртка над UCI-интерфейсом Stockfish.

- `is_available()` — проверяет наличие бинарника.
- `get_best_move(board)` — формирует FEN, запускает процесс Stockfish, отправляет UCI-команды, читает `bestmove`, декодирует ответ в объект `Move`. Таймаут — 5 секунд.
- `_fallback_move(board)` — если Stockfish недоступен, возвращает случайный легальный ход (fallback).
- `_decode_uci(uci_move, board)` — преобразует строку UCI (например, `e2e4q`) в объект `Move`.
- `_board_to_fen(board)` — преобразует позицию в FEN.

---

## Режимы игры

### Локальная игра (`local`)

Два игрока за одним компьютером. После каждого хода доска переворачивается (`white_perspective = not white_perspective`), чтобы каждый игрок видел позицию со своей стороны.

### Против Stockfish (`stockfish`)

Игрок выбирает цвет (белые или чёрные). После каждого хода игрока вызывается `apply_stockfish_move()`, которая:

1. Запрашивает лучший ход у Stockfish
2. Устанавливает флаг `is_stockfish=True` для отслеживания хода компьютера
3. Анимирует ход с установкой `my_turn = False`

После завершения анимации хода компьютера:
- Проверяется флаг `was_stockfish` в `complete_move_animation()`
- Устанавливается `my_turn = True` для передачи инициативы игроку
- Функция `apply_stockfish_move()` вызывается только после ходов игрока, не компьютера

Это предотвращает бесконечный цикл ходов Stockfish. Если `StockfishEngine.is_available()` возвращает `False`, используется случайный ход.

### Онлайн (`online`)

Клиент подключается по WebSocket к серверу. При подключении первого игрока он ждёт (`waiting`). Второй игрок спаривается с первым. Сервер пересылает ходы, сигналы о сдаче и предложения ничьи. Логика игры полностью на клиенте — сервер не хранит позицию.

### Сдача и ничья

- **Сдача**: устанавливает `game.game_over = True`, `game.game_result = 'mate'`, воспроизводит звук `lose`.
- **Принятие ничьи** (в локальном/Stockfish режиме — двойное нажатие кнопки, в онлайне — accept от opponent): `game_over = True`, `game_result = 'stalemate'`.

---

## Звуки и музыка

### Звуковые эффекты (SoundManager, папка `sounds/`)

| Ключ | Файл | Когда воспроизводится |
|------|------|----------------------|
| `move` | `move.mp3` | После завершения анимации любого хода |
| `check` | `check.mp3` | Король под шахом (один раз на состояние) |
| `game_over` | `game_over.mp3` | Игра окончена, ничья |
| `win` | `win.mp3` | Игра окончена, победа игрока |
| `lose` | `lose.mp3` | Игра окончена, поражение игрока |
| `game` | `game.mp3` | Переключение меню → игра (музыка) |

### Фоновая музыка

- `music/Skrillex - Bangarang.mp3` — играет в меню и используется как fallback.
- `music/game.mp3` — включается при входе в режим игры (`play_game_music()`).
- `pygame.mixer.music` управляет фоновой музыкой, `SoundManager` — короткими эффектами.

---

## Настройки

В режиме **SETTINGS** доступны:

- **Звук** — кнопка для включения/выключения `SoundManager` (звуки ходов, шаха, окончания).
- **Громкость звуков** — числовое поле ввода (0-100) для регулировки громкости звуковых эффектов.
- **Музыка** — кнопка для включения/выключения `pygame.mixer.music` (фоновая музыка).
- **Громкость музыки** — числовое поле ввода (0-100) для регулировки громкости фоновой музыки.
- **Тема** — выбор цветового оформления из пяти вариантов. Каждая тема определяет цвета: `light_square`, `dark_square`, `highlight`, `hint`, `panel_bg`, `text_color`, `status_color`.

Поля ввода громкости:
- Принимают только цифры (0-100)
- Автоматически зажимают значение при нажатии Enter или выходе из меню
- Изменения применяются при нажатии кнопки "Назад"

Доступные темы: **Классическая** (бежево-коричневая), **Зелёная** (классическая зелёная шахматная), **Синяя** (холодная синяя), **Коричневая** (тёплая красно-коричневая), **Фиолетовая** (тёмно-фиолетовая).

Выбор темы применяется мгновенно: цвета передаются параметрами в функции `draw_board`, `draw_legal_moves`, `draw_side_panel`.

---

## Экран справки

Кнопка **Справка** в главном меню открывает полноэкранную справку с правилами шахмат и описанием интерфейса программы. Реализована в функции `draw_help_screen` внутри `main.py`.

---

## Тесты

```
tests/perft_test.py   — тест скорости и корректности генератора ходов (perft)
tests/test_moves.py   — тесты валидации отдельных ходов и позиций
```

Запуск:

```bash
python tests/perft_test.py
python tests/test_moves.py
```
