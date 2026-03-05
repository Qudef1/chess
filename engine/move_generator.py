from figures import *
from move import *
from board import Board

class MoveGenerator:
    # Смещения для коня
    KNIGHT_OFFSETS = [-17, -15, -10, -6, 6, 10, 15, 17]
    
    # Смещения для короля
    KING_OFFSETS = [-9, -8, -7, -1, 1, 7, 8, 9]
    
    # Направления для слона (диагонали)
    BISHOP_DIRECTIONS = [-9, -7, 7, 9]
    
    # Направления для ладьи (вертикали/горизонтали)
    ROOK_DIRECTIONS = [-8, -1, 1, 8]
    
    def __init__(self):
        pass

    def generate_moves(self, board: Board) -> list[Move]:
        """Сгенерировать все псевдо-легальные ходы."""
        moves = []
        color = board.side_to_move

        for sq in range(64):
            piece = board.get_piece(sq)
            if piece == EMPTY:
                continue
            if get_piece_color(piece) != color:
                continue

            # Генерация по типу фигуры
            piece_type = abs(piece)
            if piece_type == WHITE_PAWN:
                self._generate_pawn_moves(board, sq, color, moves)
            elif piece_type == WHITE_KNIGHT:
                self._generate_knight_moves(board, sq, color, moves)
            elif piece_type == WHITE_BISHOP:
                self._generate_bishop_moves(board, sq, color, moves)
            elif piece_type == WHITE_ROOK:
                self._generate_rook_moves(board, sq, color, moves)
            elif piece_type == WHITE_QUEEN:
                self._generate_queen_moves(board, sq, color, moves)
            elif piece_type == WHITE_KING:
                self._generate_king_moves(board, sq, color, moves)

        return moves

    def generate_legal_moves(self, board: Board) -> list[Move]:
        """Сгенерировать все легальные ходы."""
        pseudo_moves = self.generate_moves(board)
        legal_moves = []
        color = board.side_to_move  # Сохраняем цвет до хода
        enemy_color = BLACK if color == WHITE else WHITE

        for move in pseudo_moves:
            # Сохранить состояние
            captured = board.get_piece(move.to_square)
            old_en_passant = board.en_passant_square
            moved_piece = board.get_piece(move.from_square)  # Сохраняем фигуру, которой ходим

            # Применить ход
            result = board.make_move(move)

            # Проверить, не под шахом ли свой король
            # side_to_move уже переключился на врага, поэтому ищем короля нашего цвета
            king_sq = board.find_king(color)
            if not board.is_square_attacked(king_sq, enemy_color):
                legal_moves.append(move)

            # Отменить ход
            board.unmake_move(move, captured, old_en_passant, moved_piece)

        return legal_moves

    def _is_valid_move(self,from_sq:int,to_square:int,offset:int)->bool:
        if to_square < 0 or to_square>63:
            return False
        
        from_file = file_of(from_sq)
        to_file = file_of(to_square)
        file_diff = abs(from_file - to_file)

        if abs(offset) in [15,17]:
            return file_diff <= 2
        if abs(offset) in [6,10]:
            return file_diff <= 1
        
        if offset in [1,-1]:
            return file_diff == 1
        if offset in [-9,7]:
            return from_file == to_file + 1
        if offset in [-7,9]:
            return from_file == to_file - 1
        
        if offset == -8 or offset == 8:
            return True
        
        return False
    
    def _generate_knight_moves(self,board:Board,sq:int,color:int,moves:list):
        for offset in self.KNIGHT_OFFSETS:
            target = sq + offset
            if not self._is_valid_move(sq,target,offset):
                continue

            piece = board.get_piece(target)
            if piece == EMPTY or get_piece_color(piece) != color:
                flag = CAPTURE if piece != EMPTY else NORMAL
                moves.append(Move(sq,target,flag))

    def _generate_king_moves(self,board:Board,sq:int,color:int,moves:list):
        for offset in self.KING_OFFSETS:
            target = sq + offset
            if not self._is_valid_move(sq,target,offset):
                continue

            piece = board.get_piece(target)
            if piece == EMPTY or get_piece_color(piece) != color:
                flag = CAPTURE if piece != EMPTY else NORMAL
                moves.append(Move(sq,target,flag))

        self._generate_castling_moves(board,color,moves)

    def _generate_castling_moves(self, board: Board, color: int, moves: list):
        pass

    def _generate_bishop_moves(self,board:Board,sq:int,color:int,moves:list):
        for direction in self.BISHOP_DIRECTIONS:
            target = sq + direction
            while self._is_valid_move(sq,target,direction):
                piece = board.get_piece(target)
                if piece == EMPTY:
                    moves.append(Move(sq,target,NORMAL))
                else:
                    if get_piece_color(piece) != color:
                        moves.append(Move(sq,target,CAPTURE))
                    break
                target += direction

    def _generate_rook_moves(self,board:Board,sq:int,color:int,moves:list):
        for direction in self.ROOK_DIRECTIONS:
            target = sq + direction
            while self._is_valid_move(sq,target,direction):
                piece = board.get_piece(target)
                if piece == EMPTY:
                    moves.append(Move(sq,target,NORMAL))
                else:
                    if get_piece_color(piece) != color:
                        moves.append(Move(sq,target,CAPTURE))
                    break
                target += direction

    def _generate_queen_moves(self,board:Board,sq:int,color:int,moves:list):
        self._generate_bishop_moves(board,sq,color,moves)
        self._generate_rook_moves(board,sq,color,moves)

    def _generate_pawn_moves(self, board: Board, sq: int, color: int, moves: list):
        """Генерация ходов пешки."""
        rank = rank_of(sq)
        # Белые идут от rank 1 к rank 7 (+8), чёрные от rank 6 к rank 0 (-8)
        direction = 8 if color == WHITE else -8

        # === 1. Тихие ходы (вперёд) ===
        target = sq + direction
        if 0 <= target < 64 and board.get_piece(target) == EMPTY:
            # Проверка на promotion
            if (color == WHITE and rank_of(target) == 7) or (color == BLACK and rank_of(target) == 0):
                moves.append(Move(sq, target, PROMOTION, WHITE_QUEEN if color == WHITE else BLACK_QUEEN))
            else:
                moves.append(Move(sq, target, NORMAL))

                # Двойной ход
                if (color == WHITE and rank == 1) or (color == BLACK and rank == 6):
                    double_target = sq + direction * 2
                    if board.get_piece(double_target) == EMPTY:
                        moves.append(Move(sq, double_target, DOUBLE_PAWN_PUSH))

        # === 2. Взятия ===
        capture_offsets = [7, 9] if color == WHITE else [-9, -7]

        for offset in capture_offsets:
            target = sq + offset
            if not self._is_valid_move(sq, target, offset):
                continue

            piece = board.get_piece(target)
            if piece != EMPTY and get_piece_color(piece) != color:
                # Проверка на promotion
                if (color == WHITE and rank_of(target) == 7) or (color == BLACK and rank_of(target) == 0):
                    moves.append(Move(sq, target, PROMOTION, WHITE_QUEEN if color == WHITE else BLACK_QUEEN))
                else:
                    moves.append(Move(sq, target, CAPTURE))

        # === 3. En passant ===
        self._generate_en_passant(board, sq, color, moves)

    def _generate_en_passant(self, board: Board, sq: int, color: int, moves: list):
        """Генерация en passant."""
        if board.en_passant_square == -1:
            return
        
        # Белые бьют en passant с 5-й горизонтали (rank 3), чёрные с 4-й (rank 4)
        if (color == WHITE and rank_of(sq) != 3) or (color == BLACK and rank_of(sq) != 4):
            return
        
        # Белые: +7 (вправо-вверх), +9 (влево-вверх)
        # Чёрные: -7 (вправо-вниз), -9 (влево-вниз)
        capture_offsets = [7, 9] if color == WHITE else [-9, -7]
        
        for offset in capture_offsets:
            target = sq + offset
            if target == board.en_passant_square:
                if self._is_valid_move(sq, target, offset):
                    moves.append(Move(sq, target, EN_PASSANT))
                break


