NORMAL = 0
CAPTURE = 1
CASTLING = 2
EN_PASSANT = 3 
PROMOTION = 4
DOUBLE_PAWN_PUSH = 5

from figures import *

class Move:
    def __init__(self,from_square:int,to_square:int,flag:int,promotion:int=0):
        self.from_square = from_square
        self.to_square = to_square
        self.flag = flag
        self.promotion = promotion

    def __repr__(self) -> str:
        flag_names = {
            NORMAL: 'N',
            CAPTURE: 'C',
            CASTLING: 'K',
            EN_PASSANT: 'E',
            PROMOTION: 'P',
            DOUBLE_PAWN_PUSH: 'D'
        }
        promo_str = ''
        if self.promotion:
            promo_symbols = {
                WHITE_QUEEN: 'Q', WHITE_ROOK: 'R', WHITE_BISHOP: 'B', WHITE_KNIGHT: 'N',
                BLACK_QUEEN: 'q', BLACK_ROOK: 'r', BLACK_BISHOP: 'b', BLACK_KNIGHT: 'n'
            }
            promo_str = f'={promo_symbols.get(self.promotion, "?")}'
        
        from_name = square_name(self.from_square)
        to_name = square_name(self.to_square)
        return f"{from_name}{to_name}{promo_str}({flag_names.get(self.flag, '?')})"
    
    def __eq__(self,other:object) -> bool:
        if not isinstance(other, Move):
            return False
        return (
            self.from_square == other.from_square and
            self.to_square == other.to_square and
            self.flag == other.flag and
            self.promotion == other.promotion
        )
    
    # for network transfer
    # def encode(self) -> int:
    #     """Кодировать ход в одно число (для сети)."""
    #     return (
    #         self.from_square |
    #         (self.to_square << 6) |
    #         (self.promotion << 12) |
    #         (self.flag << 15)
    #     )
    
    # @staticmethod
    # def decode(value: int) -> 'Move':
    #     """Декодировать ход из числа."""
    #     return Move(
    #         from_square=value & 0x3F,
    #         to_square=(value >> 6) & 0x3F,
    #         promotion=(value >> 12) & 0x7,
    #         flag=(value >> 15) & 0x7
    #     )
