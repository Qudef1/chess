from engine.figures import *
from engine.move import Move, EN_PASSANT, NORMAL, CAPTURE, PROMOTION, DOUBLE_PAWN_PUSH, CASTLING

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

    def to_fen(self) -> str:
        """Сформировать FEN-представление текущей позиции."""
        piece_map = {
            WHITE_PAWN: 'P', WHITE_KNIGHT: 'N', WHITE_BISHOP: 'B', WHITE_ROOK: 'R', WHITE_QUEEN: 'Q', WHITE_KING: 'K',
            BLACK_PAWN: 'p', BLACK_KNIGHT: 'n', BLACK_BISHOP: 'b', BLACK_ROOK: 'r', BLACK_QUEEN: 'q', BLACK_KING: 'k',
        }
        ranks = []
        for rank in range(7, -1, -1):
            empty_count = 0
            row = ''
            for file in range(8):
                sq = rank * 8 + file
                piece = self.get_piece(sq)
                if piece == EMPTY:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row += str(empty_count)
                        empty_count = 0
                    row += piece_map.get(piece, '?')
            if empty_count > 0:
                row += str(empty_count)
            ranks.append(row)

        castling = ''
        if self.castling_rights & WHITE_KINGSIDE:
            castling += 'K'
        if self.castling_rights & WHITE_QUEENSIDE:
            castling += 'Q'
        if self.castling_rights & BLACK_KINGSIDE:
            castling += 'k'
        if self.castling_rights & BLACK_QUEENSIDE:
            castling += 'q'
        if castling == '':
            castling = '-'

        en_passant = '-' if self.en_passant_square == -1 else square_name(self.en_passant_square)
        active_color = 'w' if self.side_to_move == WHITE else 'b'
        return f"{'/'.join(ranks)} {active_color} {castling} {en_passant} {self.halfmove_clock} {self.fullmove_number}"
    
    def make_move(self,move:Move):
        piece = self.get_piece(move.from_square)
        old_castling = self.castling_rights
        old_en_passant = self.en_passant_square

        self.en_passant_square = -1
        
        # Для en passant captured_piece берётся не с to_square
        if move.flag == EN_PASSANT:
            captured_pawn_sq = move.to_square - 8 if get_piece_color(piece) == WHITE else move.to_square + 8
            captured_piece = self.get_piece(captured_pawn_sq)
        else:
            captured_piece = self.get_piece(move.to_square)
        
        # Обновление прав на рокировку при ходе короля или ладьи
        if piece == WHITE_KING:
            self.castling_rights &= ~(WHITE_KINGSIDE | WHITE_QUEENSIDE)
        elif piece == BLACK_KING:
            self.castling_rights &= ~(BLACK_KINGSIDE | BLACK_QUEENSIDE)
        elif piece == WHITE_ROOK:
            if move.from_square == A1:
                self.castling_rights &= ~WHITE_QUEENSIDE
            elif move.from_square == H1:
                self.castling_rights &= ~WHITE_KINGSIDE
        elif piece == BLACK_ROOK:
            if move.from_square == A8:
                self.castling_rights &= ~BLACK_QUEENSIDE
            elif move.from_square == H8:
                self.castling_rights &= ~BLACK_KINGSIDE
        
        if move.flag == EN_PASSANT:
            # При en passant сбитая пешка находится на клетке, которую она перепрыгнула
            # Белые бьют на to_square, сбитая пешка на to_square - 8
            # Чёрные бьют на to_square, сбитая пешка на to_square + 8
            captured_pawn_sq = move.to_square - 8 if get_piece_color(piece) == WHITE else move.to_square + 8
            self.set_piece(captured_pawn_sq, EMPTY)
            self.set_piece(move.to_square, piece)
            self.set_piece(move.from_square, EMPTY)

        elif move.flag == DOUBLE_PAWN_PUSH:
            self.en_passant_square = (move.from_square + move.to_square) // 2
            self.set_piece(move.to_square, piece)
            self.set_piece(move.from_square, EMPTY)

        elif move.flag == PROMOTION:
            self.set_piece(move.to_square, move.promotion)
            self.set_piece(move.from_square, EMPTY)
            
        elif move.flag == CASTLING:
            # Рокировка: перемещаем короля и ладью
            self.set_piece(move.to_square, piece)
            self.set_piece(move.from_square, EMPTY)
            
            # Определяем тип рокировки по направлению
            if move.to_square > move.from_square:  # Королевский фланг (вправо)
                # Ладья с h-линии на f-линию
                rook_from = H1 if piece == WHITE_KING else H8
                rook_to = F1 if piece == WHITE_KING else F8
            else:  # Ферзевый фланг (влево)
                # Ладья с a-линии на d-линию
                rook_from = A1 if piece == WHITE_KING else A8
                rook_to = D1 if piece == WHITE_KING else D8
            
            rook = self.get_piece(rook_from)
            self.set_piece(rook_to, rook)
            self.set_piece(rook_from, EMPTY)

        # Обычный ход
        else:
            self.set_piece(move.to_square, piece)
            self.set_piece(move.from_square, EMPTY)

        # Обновить side_to_move
        self.side_to_move = BLACK if self.side_to_move == WHITE else WHITE

        # Вернуть информацию о ходе для unmake
        return (captured_piece, old_en_passant, piece, old_castling)

    def unmake_move(self, move: Move, captured_piece: int, old_en_passant: int, moved_piece: int, old_castling: int) -> None:
        """Отменить ход."""
        # Для promotion восстанавливаем пешку, а не фигуру
        if move.flag == PROMOTION:
            # moved_piece уже содержит пешку (мы сохранили её перед make_move)
            self.set_piece(move.from_square, moved_piece)
            self.set_piece(move.to_square, captured_piece)
        elif move.flag == CASTLING:
            # Восстанавливаем короля и ладью
            self.set_piece(move.from_square, moved_piece)
            self.set_piece(move.to_square, EMPTY)

            # Определяем тип рокировки по направлению
            if move.to_square > move.from_square:  # Королевский фланг
                rook_from = H1 if moved_piece == WHITE_KING else H8
                rook_to = F1 if moved_piece == WHITE_KING else F8
            else:  # Ферзевый фланг
                rook_from = A1 if moved_piece == WHITE_KING else A8
                rook_to = D1 if moved_piece == WHITE_KING else D8

            rook = self.get_piece(rook_to)
            self.set_piece(rook_from, rook)
            self.set_piece(rook_to, EMPTY)
        elif move.flag == EN_PASSANT:
            # Восстанавливаем пешку на from_square
            self.set_piece(move.from_square, moved_piece)
            # Восстанавливаем сбитую пешку
            captured_pawn_sq = move.to_square - 8 if get_piece_color(moved_piece) == WHITE else move.to_square + 8
            self.set_piece(captured_pawn_sq, captured_piece)
            # Очищаем to_square
            self.set_piece(move.to_square, EMPTY)
        else:
            self.set_piece(move.from_square, moved_piece)
            self.set_piece(move.to_square, captured_piece)

        # Вернуть en passant
        self.en_passant_square = old_en_passant
        
        # Вернуть права на рокировку
        self.castling_rights = old_castling

        # Вернуть пешку при en passant
        if move.flag == EN_PASSANT:
            # При en passant сбитая пешка находится на клетке, которую она перепрыгнула
            # Белые бьют на to_square, сбитая пешка на to_square - 8
            # Чёрные бьют на to_square, сбитая пешка на to_square + 8
            captured_pawn_sq = move.to_square - 8 if get_piece_color(moved_piece) == WHITE else move.to_square + 8
            self.set_piece(captured_pawn_sq, captured_piece)

        # Вернуть ход
        self.side_to_move = BLACK if self.side_to_move == WHITE else WHITE

    def is_square_attacked(self,sq:int,by_color:int) -> bool:
        # Пешки атакуют по диагонали вперёд
        # Белые пешки атакуют +7 (влево-вверх) и +9 (вправо-вверх)
        # Чёрные пешки атакуют -7 (влево-вниз) и -9 (вправо-вниз)
        # Чтобы найти пешку, которая атакует короля, нужно искать в обратном направлении:
        # Для белых: ищем на -7 (вправо-вниз) и -9 (влево-вниз) от короля
        # Для чёрных: ищем на +7 (вправо-вверх) и +9 (влево-вверх) от короля
        pawn_attacks = [-7, -9] if by_color == WHITE else [7, 9]
        
        for offset in pawn_attacks:
            attacker = sq + offset
            if 0 <= attacker < 64:
                piece = self.get_piece(attacker)
                if piece == (WHITE_PAWN if by_color == WHITE else BLACK_PAWN):
                    if abs(file_of(sq) - file_of(attacker)) == 1:
                        return True
                
        knight = WHITE_KNIGHT if by_color == WHITE else BLACK_KNIGHT
        knight_offsets = [-17, -15, -10, -6, 6, 10, 15, 17]
        
        for offset in knight_offsets:
            attacker = sq + offset
            if 0 <= attacker < 64:
                piece = self.get_piece(attacker)
                if piece == knight:
                    if abs(file_of(sq) - file_of(attacker)) <= 2:
                        return True
        
        # === Проверка атак королём ===
        king = WHITE_KING if by_color == WHITE else BLACK_KING
        king_offsets = [-9, -8, -7, -1, 1, 7, 8, 9]
        
        for offset in king_offsets:
            attacker = sq + offset
            if 0 <= attacker < 64:
                piece = self.get_piece(attacker)
                if piece == king:
                    if abs(file_of(sq) - file_of(attacker)) <= 1:
                        return True
        
        # === Проверка атак слоном/ферзём (диагонали) ===
        bishop = WHITE_BISHOP if by_color == WHITE else BLACK_BISHOP
        queen = WHITE_QUEEN if by_color == WHITE else BLACK_QUEEN

        for direction in [-9, -7, 7, 9]:
            attacker = sq + direction
            prev = sq
            while 0 <= attacker < 64:
                # Проверка, что шаг валиден (не пересекает край доски)
                from_file = file_of(prev)
                to_file = file_of(attacker)
                # +7 = влево-вверх (file -1), -7 = вправо-вниз (file +1)
                # +9 = вправо-вверх (file +1), -9 = влево-вниз (file -1)
                if direction == 7 and to_file != from_file - 1:
                    break
                if direction == -7 and to_file != from_file + 1:
                    break
                if direction == 9 and to_file != from_file + 1:
                    break
                if direction == -9 and to_file != from_file - 1:
                    break
                
                piece = self.get_piece(attacker)
                if piece != EMPTY:
                    if piece == bishop or piece == queen:
                        return True
                    break  # Фигура блокирует
                prev = attacker
                attacker += direction
        
        # === Проверка атак ладьёй/ферзём (вертикали/горизонтали) ===
        rook = WHITE_ROOK if by_color == WHITE else BLACK_ROOK

        for direction in [-8, -1, 1, 8]:
            attacker = sq + direction
            prev = sq
            while 0 <= attacker < 64:
                # Проверка для горизонталей (file должен меняться на 1)
                if direction in [-1, 1]:
                    from_file = file_of(prev)
                    to_file = file_of(attacker)
                    if direction == 1 and to_file != from_file + 1:
                        break
                    if direction == -1 and to_file != from_file - 1:
                        break

                piece = self.get_piece(attacker)
                if piece != EMPTY:
                    if piece == rook or piece == queen:
                        return True
                    break  # Фигура блокирует
                prev = attacker
                attacker += direction
        
        return False
    

    
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