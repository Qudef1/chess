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

    def _generate_castling_moves(self,board:Board,sq:int,color:int,moves:list):
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
        direction = -8 if color == WHITE else 8  # Белые идут вверх (-), чёрные вниз (+)
        
        # === 1. Тихие ходы (вперёд) ===
        target = sq + direction
        if board.get_piece(target) == EMPTY:
            # Проверка на promotion
            if (color == WHITE and rank_of(target) == 0) or (color == BLACK and rank_of(target) == 7):
                moves.append(Move(sq, target, PROMOTION, WHITE_QUEEN))  # По умолчанию ферзь
            else:
                moves.append(Move(sq, target, NORMAL))
                
                # Двойной ход
                if (color == WHITE and rank == 1) or (color == BLACK and rank == 6):
                    double_target = sq + direction * 2
                    if board.get_piece(double_target) == EMPTY:
                        moves.append(Move(sq, double_target, DOUBLE_PAWN_PUSH))
        
        # === 2. Взятия ===
        for offset in [-7, 7]:  # Диагональные взятия
            target = sq + offset
            if not self._is_valid_move(sq, target, offset):
                continue
            
            piece = board.get_piece(target)
            if piece != EMPTY and get_piece_color(piece) != color:
                # Проверка на promotion
                if (color == WHITE and rank_of(target) == 0) or (color == BLACK and rank_of(target) == 7):
                    moves.append(Move(sq, target, PROMOTION, WHITE_QUEEN))
                else:
                    moves.append(Move(sq, target, CAPTURE))
        
        # === 3. En passant ===
        self._generate_en_passant(board, sq, color, moves)

    def _generate_en_passant(self,board:Board,sq:int,color:int,moves:int):
        pass




