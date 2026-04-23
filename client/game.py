"""Логика игры и управление состоянием."""
from engine.board import Board
from engine.move_generator import MoveGenerator
from engine.figures import BLACK, WHITE, get_piece_color, EMPTY


class ChessGame:
    """Класс для управления состоянием шахматной игры."""
    
    def __init__(self):
        self.board = Board()
        self.move_generator = MoveGenerator()
        self.selected_square = None
        self.legal_moves = []
        self.white_perspective = True  # Белые снизу
        self.game_over = False
        self.game_result = None  # 'mate', 'stalemate'
        self.result = None       # 'win', 'lose', 'stalemate' — для игрока

    def reset(self):
        """Сбросить игру к начальной позиции."""
        self.board = Board()
        self.selected_square = None
        self.legal_moves = []
        self.white_perspective = True
        self.game_over = False
        self.game_result = None
        self.result = None

    def select_square(self, square_index: int):
        """
        Выбрать клетку и сгенерировать ходы для фигуры на ней.
        
        Args:
            square_index: Индекс выбранной клетки
        """
        piece = self.board.get_piece(square_index)
        
        # Если кликнули на свою фигуру - выбираем её
        if piece != EMPTY and get_piece_color(piece) == self.board.side_to_move:
            self.selected_square = square_index
            # Генерируем все легальные ходы и фильтруем по выбранной клетке
            all_legal_moves = self.move_generator.generate_legal_moves(self.board)
            self.legal_moves = [m for m in all_legal_moves if m.from_square == square_index]
            print(f"Клик по клетке: {square_index}, доступно ходов: {len(self.legal_moves)}")
        else:
            # Если кликнули на пустую клетку или фигуру противника
            self.selected_square = None
            self.legal_moves = []

    def make_move(self, move):
        """
        Сделать ход.
        
        Args:
            move: Объект хода для выполнения
        """
        old_en_passant = self.board.en_passant_square
        moved_piece = self.board.get_piece(move.from_square)
        result = self.board.make_move(move)

        # captured содержится в result[0]
        captured = result[0]

        # Для рокировки нужно передать old_castling в unmake_move
        old_castling = result[3] if len(result) > 3 else 0

        # Сбрасываем выделение
        self.selected_square = None
        self.legal_moves = []

        # Проверяем на мат/пат
        self.check_game_over()
        
        return captured, old_en_passant, moved_piece, old_castling

    def check_game_over(self):
        """Проверка на мат или пат."""
        all_legal_moves = self.move_generator.generate_legal_moves(self.board)
        if len(all_legal_moves) == 0:
            self.game_over = True
            # Проверяем, под шахом ли король
            king_sq = self.board.find_king(self.board.side_to_move)
            enemy_color = BLACK if self.board.side_to_move == WHITE else WHITE
            if self.board.is_square_attacked(king_sq, enemy_color):
                self.game_result = 'mate'
                # Победил тот, чей ход сейчас (сделал последний ход — поставил мат)
                self.result = None  # Определяется на уровне main.py с учётом режима
                print(f"Мат! Победили {'белые' if self.board.side_to_move == BLACK else 'чёрные'}")
            else:
                self.game_result = 'stalemate'
                self.result = 'stalemate'
                print("Пат! Ничья")
        else:
            self.game_over = False
            self.game_result = None
            self.result = None

    def get_move_for_square(self, square_index: int):
        """
        Получить ход для клетки, если он есть в списке легальных.
        
        Args:
            square_index: Индекс клетки назначения
        
        Returns:
            Объект хода или None
        """
        return next((m for m in self.legal_moves if m.to_square == square_index), None)
