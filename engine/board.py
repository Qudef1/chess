from figures import *

class Board:
    def __init__(self):
        self.squares: list[int] = [0] * 64
        self.side_to_move: int = WHITE
        self.castling_rights: int = ALL_CASTLING_RIGHTS
        self.en_passant_square: int = -1
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1
        self.set_start_position()

    def set_start_position(self):
        for i in range(64):
            self.squares[i] = EMPTY
        
        # Белые фигуры (1-я горизонталь)
        self.squares[A1] = WHITE_ROOK
        self.squares[B1] = WHITE_KNIGHT
        self.squares[C1] = WHITE_BISHOP
        self.squares[D1] = WHITE_QUEEN
        self.squares[E1] = WHITE_KING
        self.squares[F1] = WHITE_BISHOP
        self.squares[G1] = WHITE_KNIGHT
        self.squares[H1] = WHITE_ROOK
        
        # Белые пешки (2-я горизонталь)
        for file in range(8):
            self.squares[square(file, 1)] = WHITE_PAWN
        
        # Чёрные пешки (7-я горизонталь)
        for file in range(8):
            self.squares[square(file, 6)] = BLACK_PAWN
        
        # Чёрные фигуры (8-я горизонталь)
        self.squares[A8] = BLACK_ROOK
        self.squares[B8] = BLACK_KNIGHT
        self.squares[C8] = BLACK_BISHOP
        self.squares[D8] = BLACK_QUEEN
        self.squares[E8] = BLACK_KING
        self.squares[F8] = BLACK_BISHOP
        self.squares[G8] = BLACK_KNIGHT
        self.squares[H8] = BLACK_ROOK
        
        # Сброс состояния
        self.side_to_move = WHITE
        self.castling_rights = ALL_CASTLING_RIGHTS
        self.en_passant_square = -1
        self.halfmove_clock = 0
        self.fullmove_number = 1

    def set_piece(self,sq,piece):
        self.squares[sq] = piece

    def get_piece(self,sq) -> int:
        return self.squares[sq]
        

    def is_empty(self,sq) -> bool:
        return self.squares[sq] == EMPTY

    def is_enemy(self,sq,color) -> bool:
        piece = self.squares[sq]
        if piece == EMPTY:
            return False
        return get_piece_color(piece) != color

    def is_friend(self,sq:int,color:int) -> bool:
        piece = self.squares[sq]
        if piece == EMPTY:
            return False
        return get_piece_color(piece) == color
    
    def find_king(self,color:int) -> int:
        king = WHITE_KING if color == WHITE else BLACK_KING
        for sq in range(64):
            if self.squares[sq] ==king:
                return sq
        return -1
    
    def copy(self) -> 'Board':
        new_board = Board.__new__(Board)
        new_board.squares = self.squares.copy()
        new_board.side_to_move = self.side_to_move
        new_board.castling_rights = self.castling_rights
        new_board.en_passant_square = self.en_passant_square
        new_board.halfmove_clock = self.halfmove_clock
        new_board.fullmove_number = self.fullmove_number
        return new_board

    def __repr__(self) -> str:
        """Визуальное представление доски для отладки."""
        piece_symbols = {
            EMPTY: '.',
            WHITE_PAWN: 'P', WHITE_KNIGHT: 'N', WHITE_BISHOP: 'B',
            WHITE_ROOK: 'R', WHITE_QUEEN: 'Q', WHITE_KING: 'K',
            BLACK_PAWN: 'p', BLACK_KNIGHT: 'n', BLACK_BISHOP: 'b',
            BLACK_ROOK: 'r', BLACK_QUEEN: 'q', BLACK_KING: 'k'
        }
        
        lines = []
        lines.append("  a b c d e f g h")
        
        for rank in range(7, -1, -1):
            line = f"{rank + 1} "
            for file in range(8):
                sq = square(file, rank)
                piece = self.squares[sq]
                line += piece_symbols[piece] + " "
            line += f"{rank + 1}"
            lines.append(line)
        
        lines.append("  a b c d e f g h")
        lines.append(f"Side: {'White' if self.side_to_move == WHITE else 'Black'}")
        lines.append(f"Castling: {self._castling_to_str()}")
        lines.append(f"En passant: {square_name(self.en_passant_square) if self.en_passant_square != -1 else '-'}")
        
        return "\n".join(lines)
    
    def _castling_to_str(self) -> str:
        """Вернуть строку доступных рокировок (например, 'KQkq')."""
        result = ""
        if self.castling_rights & WHITE_KINGSIDE:
            result += "K"
        if self.castling_rights & WHITE_QUEENSIDE:
            result += "Q"
        if self.castling_rights & BLACK_KINGSIDE:
            result += "k"
        if self.castling_rights & BLACK_QUEENSIDE:
            result += "q"
        return result if result else "-"
    
    def __eq__(self, other: object) -> bool:
        """Проверка равенства досок (для тестов)."""
        if not isinstance(other, Board):
            return False
        return (
            self.squares == other.squares and
            self.side_to_move == other.side_to_move and
            self.castling_rights == other.castling_rights and
            self.en_passant_square == other.en_passant_square and
            self.halfmove_clock == other.halfmove_clock and
            self.fullmove_number == other.fullmove_number
        )
    

if __name__ == "__main__":
    board = Board()
    print(board)