# Online Chess Project — Full Development Plan

## Цель проекта

Создать онлайн-шахматы:

* собственный шахматный движок (rules + move generation)
* клиент на Pygame
* сервер для онлайн игры
* режим против Stockfish

---

# Этап 0 — Подготовка проекта

## 0.1 Создать структуру репозитория

```
chess/
    engine/
    server/
    client/
    stockfish/
    tests/
```

## 0.2 Настроить окружение

Установить:

```
python >= 3.10
pygame
fastapi
uvicorn
websockets
```

## 0.3 Базовые файлы

```
engine/
    board.py
    move.py
    move_generator.py
    attacks.py
    fen.py

server/
    server.py
    room.py

client/
    main.py
    ui.py
    network.py
```

---

# Этап 1 — Основа шахматного движка

(самая важная часть проекта)

## 1.1 Представление доски

Реализовать:

```
64 клетки
индексация 0..63
```

Формула:

```
square = rank * 8 + file
```

Создать:

Board class

```
class Board:
    squares[64]
    side_to_move
    castling_rights
    en_passant
    halfmove_clock
    fullmove_number
```

## 1.2 Кодирование фигур

```
EMPTY = 0

WHITE:
PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

BLACK:
-1..-6
```

---

# Этап 2 — Структура ходов

Создать класс Move

```
class Move:
    from_square
    to_square
    promotion
    flag
```

Флаги:

```
NORMAL
CAPTURE
CASTLING
EN_PASSANT
PROMOTION
DOUBLE_PAWN_PUSH
```

---

# Этап 3 — Генерация псевдо-ходов

Файл:

```
move_generator.py
```

Нужно реализовать:

генерацию для:

* pawn
* knight
* bishop
* rook
* queen
* king

---

## 3.1 Пешки

Реализовать:

* движение вперед
* двойной ход
* взятия
* promotion
* en passant

---

## 3.2 Конь

Offsets:

```
[-17, -15, -10, -6, 6, 10, 15, 17]
```

---

## 3.3 Скользящие фигуры

Направления:

bishop

```
NE
NW
SE
SW
```

rook

```
N
S
E
W
```

queen

```
все направления
```

---

# Этап 4 — Проверка шаха

Создать:

```
is_square_attacked(square)
```

Проверять атаки:

* pawn
* knight
* bishop
* rook
* queen
* king

---

# Этап 5 — Легальные ходы

Алгоритм:

```
generate pseudo moves
for move in moves:
    make_move
    if king not in check:
        legal move
    unmake_move
```

---

# Этап 6 — Make / Unmake Move

Реализовать:

```
make_move(move)
unmake_move(move)
```

Это должно поддерживать:

* capture
* promotion
* en passant
* castling

---

# Этап 7 — FEN

Создать:

```
load_fen()
generate_fen()
```

Нужно для:

* сохранения партии
* отправки позиции
* Stockfish

---

# Этап 8 — Perft тест

Создать:

```
perft(depth)
```

Проверочные значения:

```
depth 1 = 20
depth 2 = 400
depth 3 = 8902
depth 4 = 197281
```

Если не совпадает — баг в генерации ходов.

---

# Этап 9 — UI (Pygame)

Создать:

```
доска
фигуры
клики мышью
подсветка ходов
```

Функции:

```
draw_board()
draw_pieces()
handle_click()
```

---

# Этап 10 — Связь клиент ↔ сервер

Использовать WebSocket.

Сообщения:

JOIN
MOVE
STATE
START
END

MOVE

```
{
  from: int,
  to: int,
  promotion: int
}
```

---

# Этап 11 — Сервер

GameRoom:

```
players
board
move_history
game_state
```

Логика:

```
получили ход
проверили
применили
отправили игрокам
```

---

# Этап 12 — Matchmaking

Реализовать:

```
queue игроков
создание комнаты
назначение цвета
```

---

# Этап 13 — Игра против бота

Когда режим:

```
player_vs_bot
```

Алгоритм:

```
игрок сделал ход
обновить board
отправить позицию stockfish
получить лучший ход
применить
отправить клиенту
```

---

# Этап 14 — Таймер

Добавить:

```
blitz
rapid
classical
```

Хранить:

```
remaining_time
increment
```

---

# Этап 15 — Стабильность

Добавить:

reconnect

```
player reconnect
send state
restore game
```

---

# Этап 16 — Улучшения

После MVP:

* spectator mode
* рейтинг игроков
* PGN сохранение
* анализ партии
* move history UI
* arrows как в lichess

---

# Этап 17 — Тестирование

Обязательно протестировать:

* en passant
* pinned pieces
* double check
* stalemate
* repetition
* 50 move rule

---

# Этап 18 — Финальная структура проекта

```
chess/
    engine/
        board.py
        move.py
        move_generator.py
        attacks.py
        fen.py

    server/
        server.py
        room.py
        matchmaking.py

    client/
        main.py
        ui.py
        network.py

    stockfish/
        engine.py

    tests/
        perft_tests.py
```

---

# Реалистичная оценка сложности

Engine:
~3000–5000 строк

Server:
~1000 строк

Client:
~2000 строк

Итого:
~6000–9000 строк

---

# Рекомендуемый порядок разработки

1 Engine core
2 Perft tests
3 UI
4 Server
5 Online games
6 Stockfish
7 Features
