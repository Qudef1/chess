import sys
import os

# Добавляем корень проекта в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine'))

from board import Board
from move_generator import MoveGenerator
from move import Move, NORMAL, DOUBLE_PAWN_PUSH, EN_PASSANT, CAPTURE, PROMOTION
from figures import WHITE, BLACK, WHITE_PAWN, WHITE_KNIGHT, EMPTY

def test_initial_position():
    """Тест начальной позиции - должно быть 20 ходов."""
    board = Board()
    gen = MoveGenerator()
    
    # Отладка: проверим фигуры
    print(f"e2 = {board.get_piece(28)} (ожидалось {WHITE_PAWN})")
    print(f"b1 = {board.get_piece(1)} (ожидалось {WHITE_KNIGHT})")
    print(f"side_to_move = {board.side_to_move} (ожидалось {WHITE})")
    
    moves = gen.generate_legal_moves(board)
    print(f"Количество ходов из начальной позиции: {len(moves)}")
    print(f"Ожидалось: 20")
    
    if len(moves) == 20:
        print("✓ Тест пройден!")
    else:
        print("✗ Тест НЕ пройден!")
        print("Ходы:")
        for move in moves:
            print(f"  {move}")
    
    return len(moves) == 20

def test_pawn_moves():
    """Тест ходов пешками."""
    board = Board()
    gen = MoveGenerator()
    
    moves = gen.generate_legal_moves(board)
    
    # Пешки могут ходить на 1 или 2 клетки вперёд
    pawn_moves = [m for m in moves if m.from_square >= 8 and m.from_square <= 15]
    print(f"\nХоды пешками: {len(pawn_moves)}")
    print(f"Ожидалось: 16 (8 пешек × 2 хода)")
    
    for move in pawn_moves:
        print(f"  {move}")
    
    return len(pawn_moves) == 16

def test_knight_moves():
    """Тест ходов конями."""
    board = Board()
    gen = MoveGenerator()
    
    moves = gen.generate_legal_moves(board)
    
    # Кони могут ходить на b1-a3, b1-c3, g1-f3, g1-h3
    knight_moves = [m for m in moves if m.from_square in [1, 6]]
    print(f"\nХоды конями: {len(knight_moves)}")
    print(f"Ожидалось: 4")
    
    for move in knight_moves:
        print(f"  {move}")
    
    return len(knight_moves) == 4

def test_make_move():
    """Тест применения хода."""
    board = Board()
    print("\nДо хода:")
    print(board)
    
    # e2-e4
    move = Move(28, 44, DOUBLE_PAWN_PUSH)
    board.make_move(move)
    
    print("\nПосле e2-e4:")
    print(board)
    
    # Проверка en passant
    expected_ep = 36  # e3
    if board.en_passant_square == expected_ep:
        print(f"✓ En passant установлен верно: {board.en_passant_square}")
    else:
        print(f"✗ En passant неверен: {board.en_passant_square} (ожидалось {expected_ep})")
    
    return True

def test_black_moves():
    """Тест ходов чёрных после e2-e4."""
    board = Board()
    gen = MoveGenerator()
    
    # e2-e4
    move = Move(28, 44, DOUBLE_PAWN_PUSH)
    board.make_move(move)
    
    moves = gen.generate_legal_moves(board)
    print(f"\nХоды чёрных после e2-e4: {len(moves)}")
    
    return len(moves) > 0

if __name__ == "__main__":
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ ШАХМАТНОГО ДВИЖКА")
    print("=" * 50)
    
    results = []
    
    results.append(("Начальная позиция (20 ходов)", test_initial_position()))
    results.append(("Ходы пешками (16)", test_pawn_moves()))
    results.append(("Ходы конями (4)", test_knight_moves()))
    results.append(("make_move()", test_make_move()))
    results.append(("Ходы чёрных", test_black_moves()))
    
    print("\n" + "=" * 50)
    print("ИТОГИ:")
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(r[1] for r in results)
    print("=" * 50)
    if all_passed:
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ✓")
    else:
        print("ЕСТЬ ПРОВАЛЫ! ✗")
