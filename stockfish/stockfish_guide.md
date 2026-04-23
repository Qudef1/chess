# Руководство по установке и настройке Stockfish

Stockfish — одна из самых сильных шахматных программ в мире с открытым исходным кодом. Она используется в данном проекте для игры против компьютера.

## Содержание

1. [Загрузка Stockfish](#1-загрузка-stockfish)
2. [Установка](#2-установка)
3. [Проверка работоспособности](#3-проверка-работоспособности)
4. [Настройка глубины анализа](#4-настройка-глубины-анализа)
5. [Устранение неполадок](#5-устранение-неполадок)

---

## 1. Загрузка Stockfish

### Способ 1: Официальный репозиторий (рекомендуется)

1. Перейдите на официальную страницу релизов Stockfish:
   **https://stockfishchess.org/download/**

2. Скачайте последнюю версию для вашей операционной системы:
   - **Windows**: файл `stockfish-windows-x86-64.exe` или `stockfish-windows-x86-64-avx2.exe` (более быстрая версия для современных процессоров)
   - **macOS**: файл `stockfish-macos-arm64` (Apple Silicon) или `stockfish-macos-x86-64` (Intel)
   - **Linux**: файл `stockfish-linux-x86-64` или `stockfish-linux-x86-64-avx2`

### Способ 2: GitHub Releases

1. Перейдите на страницу релизов:
   **https://github.com/official-stockfish/Stockfish/releases**

2. В разделе **Assets** последнего релиза найдите бинарный файл для вашей ОС.

---

## 2. Установка

### Windows

1. Скачайте `.exe` файл.
2. Поместите файл `stockfish.exe` (или переименнуйте скачанный файл) в папку проекта:
   ```
   chess/
   └── stockfish/
       ├── stockfish.exe      <-- сюда
       ├── stockfish_engine.py
       └── __init__.py
   ```
3. Убедитесь, что файл называется именно `stockfish.exe` (или измените путь в `stockfish_engine.py`).

### macOS

1. Скачайте бинарный файл для macOS.
2. Поместите его в папку `stockfish/` и сделайте исполняемым:
   ```bash
   chmod +x stockfish-macos-arm64
   ```
3. Переименнуйте или укажите путь в `stockfish_engine.py`.

### Linux

1. Скачайте бинарный файл для Linux.
2. Поместите его в папку `stockfish/`:
   ```bash
   chmod +x stockfish-linux-x86-64
   ```
3. Обновите путь в `stockfish_engine.py` при необходимости.

---

## 3. Проверка работоспособности

### Быстрая проверка в терминале

**Windows (PowerShell/CMD):**
```powershell
cd chess\stockfish
.\stockfish.exe
```

**macOS/Linux:**
```bash
cd chess/stockfish
./stockfish-macos-arm64
# или
./stockfish-linux-x86-64
```

После запуска вы увидите приглашение UCI. Введите команды:

```
uci
isready
position startpos
go depth 10
```

Вы должны увидеть результат анализа, завершающийся строкой вида:
```
bestmove e2e4
```

Для выхода введите:
```
quit
```

### Проверка в программе

1. Запустите игру: `python -m client.main` (из корня проекта).
2. В главном меню нажмите **Против Stockfish**.
3. Если в статусе написано `Игра против Stockfish. Вы белые.` — Stockfish успешно подключён.
4. Если написано `Игра против Stockfish. Stockfish недоступен, используется случайный ход.` — Stockfish не найден.

---

## 4. Настройка глубины анализа

Глубина анализа определяет, на сколько полуходов вперёд Stockfish просчитывает позицию. Чем больше глубина — тем сильнее играет Stockfish, но тем медленнее его ходы.

### Как изменить глубину

Откройте файл `client/main.py` и найдите строку инициализации движка:

```python
stockfish_engine = StockfishEngine(depth=10)
```

Измените значение `depth`:

| Значение | Сила игры | Примерное время хода |
|----------|-----------|---------------------|
| 5        | Начальный | < 1 сек              |
| 10       | Средняя   | 1–3 сек             |
| 15       | Сильная   | 3–10 сек            |
| 20       | Очень сильная | 10–60 сек        |
| 25+      | Экстремальная | > 1 мин          |

**Рекомендуемое значение для игры**: `depth=10` или `depth=12`.

### Также можно изменить в `stockfish_engine.py`

```python
class StockfishEngine:
    def __init__(self, binary_path: Optional[str] = None, depth: int = 10):
```

---

## 5. Устранение неполадок

### Ошибка: "Stockfish not found"

**Причина**: Файл `stockfish.exe` не найден.

**Решение**:
1. Убедитесь, что файл лежит в `chess/stockfish/stockfish.exe`.
2. Проверьте имя файла — он должен называться `stockfish.exe` (или путь должен быть обновлён).
3. Проверьте, что файл не заблокирован антивирусом.

### Ошибка: "Permission denied"

**Причина**: Бинарному файлу не присвоены права на выполнение (Linux/macOS).

**Решение**:
```bash
chmod +x stockfish-linux-x86-64
```

### Stockfish работает медленно

**Решение**:
1. Скачайте версию с `avx2` в названии — она использует расширенные инструкции процессора.
2. Уменьшите глубину анализа (`depth=5` или `depth=8`).
3. На Windows попробуйте версию `stockfish-windows-x86-64-avx2.exe`.

### Программа использует случайный ход вместо Stockfish

Это происходит потому, что `StockfishEngine.is_available()` возвращает `False`. Система автоматически переходит на fallback-режим (случайный ход из списка легальных). Проверьте:

1. Существует ли файл `stockfish.exe` в правильной директории.
2. Запускается ли Stockfish вручную в терминале.
3. Нет ли ошибок при запуске.

### Как добавить несколько версий Stockfish

Если вы хотите иметь несколько версий (например, слабую и сильную):

1. Положите разные бинарники в папку `stockfish/`:
   ```
   stockfish/
   ├── stockfish_easy.exe   (depth=3)
   ├── stockfish_medium.exe (depth=10)
   └── stockfish_hard.exe   (depth=20)
   ```

2. В `stockfish_engine.py` можно добавить параметр для выбора бинарника:
   ```python
   stockfish_engine = StockfishEngine(
       binary_path=os.path.join(os.path.dirname(__file__), 'stockfish_hard.exe'),
       depth=20
   )
   ```

---

## Дополнительные материалы

- **Официальный сайт**: https://stockfishchess.org/
- **GitHub репозиторий**: https://github.com/official-stockfish/Stockfish
- **Документация UCI**: https://www.shredderchess.com/download-divisions/uci-universal-chess-interface.html
