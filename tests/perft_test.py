import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine'))

from board import Board
from move_generator import MoveGenerator

def perft(board: Board, depth: int, gen: MoveGenerator) -> int:
    """Perft тест - подсчёт количества позиций на заданной глубине."""
    if depth == 0:
        return 1
    
    moves = gen.generate_legal_moves(board)
    if depth == 1:
        return len(moves)
    
    total = 0
    for move in moves:
        captured = board.get_piece(move.to_square)
        old_en_passant = board.en_passant_square
        moved_piece = board.get_piece(move.from_square)
        
        board.make_move(move)
        nodes = perft(board, depth - 1, gen)
        board.unmake_move(move, captured, old_en_passant, moved_piece)
        
        total += nodes
    
    return total

def perft_debug(board: Board, depth: int, gen: MoveGenerator) -> int:
    """Perft с отладочным выводом для depth=1."""
    moves = gen.generate_legal_moves(board)
    total = 0
    
    for move in moves:
        captured = board.get_piece(move.to_square)
        old_en_passant = board.en_passant_square
        moved_piece = board.get_piece(move.from_square)
        
        board.make_move(move)
        nodes = perft(board, depth - 1, gen)
        board.unmake_move(move, captured, old_en_passant, moved_piece)
        
        print(f"  {move}: {nodes}")
        total += nodes
    
    return total

if __name__ == "__main__":
    print("=" * 50)
    print("PERFT ТЕСТ")
    print("=" * 50)
    
    board = Board()
    gen = MoveGenerator()
    
    # Проверочные значения для начальной позиции
    expected = {
        1: 20,
        2: 400,
        3: 8902,
        4: 197281
    }
    
    for depth in range(1, 5):
        print(f"\nPerft({depth}):")
        result = perft(board, depth, gen)
        exp = expected[depth]
        status = "✓" if result == exp else "✗"
        print(f"  Результат: {result} (ожидалось: {exp}) {status}")
        
        if result != exp:
            print("  ОШИБКА! Не совпадает с ожидаемым значением!")
            if depth == 1:
                print("  Ходы:")
                perft_debug(board, 1, gen)
            break
    
    print("\n" + "=" * 50)
