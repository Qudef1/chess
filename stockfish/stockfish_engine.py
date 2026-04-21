import os
import shutil
import subprocess
from typing import Optional

from engine.board import Board
from engine.move import Move
from engine.figures import WHITE, BLACK, WHITE_QUEEN, WHITE_ROOK, WHITE_BISHOP, WHITE_KNIGHT, BLACK_QUEEN, BLACK_ROOK, BLACK_BISHOP, BLACK_KNIGHT


class StockfishEngine:
    def __init__(self, binary_path: Optional[str] = None, depth: int = 10):
        self.binary_path = binary_path or os.path.join(os.path.dirname(__file__), 'stockfish.exe')  # Windows binary
        self.depth = depth
        self.available = self._find_binary() is not None
        self.binary = self._find_binary()

    def _find_binary(self) -> Optional[str]:
        if self.binary_path and os.path.exists(self.binary_path):
            return self.binary_path
        return shutil.which('stockfish')

    def is_available(self) -> bool:
        return self.available

    def get_best_move(self, board: Board) -> Optional[Move]:
        legal_moves = board.generate_legal_moves() if hasattr(board, 'generate_legal_moves') else None
        if not self.available:
            return self._fallback_move(board)

        fen = self._board_to_fen(board)
        try:
            proc = subprocess.Popen(
                [self.binary],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
            assert proc.stdin and proc.stdout
            proc.stdin.write('uci\n')
            proc.stdin.write('isready\n')
            proc.stdin.write('ucinewgame\n')
            proc.stdin.write(f'position fen {fen}\n')
            proc.stdin.write(f'go depth {self.depth}\n')
            proc.stdin.flush()

            best_move = None
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                if line.startswith('bestmove'):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] != '(none)':
                        best_move = parts[1]
                    break

            proc.stdin.write('quit\n')
            proc.stdin.flush()
            proc.wait(timeout=5)  # Increase timeout

            if best_move:
                return self._decode_uci(best_move, board)
        except Exception as e:
            print(f"Stockfish error: {e}")
            return self._fallback_move(board)

        return self._fallback_move(board)

    def _fallback_move(self, board: Board) -> Optional[Move]:
        from random import choice
        legal_moves = board.generate_legal_moves() if hasattr(board, 'generate_legal_moves') else []
        return choice(legal_moves) if legal_moves else None

    def _decode_uci(self, uci_move: str, board: Board) -> Optional[Move]:
        if len(uci_move) < 4:
            return None

        from_square = self._uci_square_to_index(uci_move[0:2])
        to_square = self._uci_square_to_index(uci_move[2:4])
        promotion = 0
        flag = 0
        if len(uci_move) == 5:
            promo = uci_move[4]
            promotion = {
                'q': BLACK_QUEEN if board.side_to_move == BLACK else WHITE_QUEEN,
                'r': BLACK_ROOK if board.side_to_move == BLACK else WHITE_ROOK,
                'b': BLACK_BISHOP if board.side_to_move == BLACK else WHITE_BISHOP,
                'n': BLACK_KNIGHT if board.side_to_move == BLACK else WHITE_KNIGHT,
            }.get(promo, 0)
            flag = 4 if promotion else 0

        return Move(from_square, to_square, flag, promotion)

    def _uci_square_to_index(self, square: str) -> int:
        file_map = 'abcdefgh'
        rank_map = '12345678'
        file = file_map.index(square[0])
        rank = rank_map.index(square[1])
        return rank * 8 + file

    def _board_to_fen(self, board: Board) -> str:
        rows = []
        for rank in range(7, -1, -1):
            empty_count = 0
            row = ''
            for file in range(8):
                sq = rank * 8 + file
                piece = board.get_piece(sq)
                if piece == 0:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row += str(empty_count)
                        empty_count = 0
                    row += self._piece_to_fen(piece)
            if empty_count > 0:
                row += str(empty_count)
            rows.append(row)

        castling = ''
        if board.castling_rights & 1:
            castling += 'K'
        if board.castling_rights & 2:
            castling += 'Q'
        if board.castling_rights & 4:
            castling += 'k'
        if board.castling_rights & 8:
            castling += 'q'
        if castling == '':
            castling = '-'

        en_passant = '-'
        if board.en_passant_square != -1:
            en_passant = self._index_to_uci(board.en_passant_square)

        halfmove = board.halfmove_clock
        fullmove = board.fullmove_number
        active_color = 'w' if board.side_to_move == WHITE else 'b'
        return f"{'/'.join(rows)} {active_color} {castling} {en_passant} {halfmove} {fullmove}"

    def _piece_to_fen(self, piece: int) -> str:
        mapping = {
            1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K',
            -1: 'p', -2: 'n', -3: 'b', -4: 'r', -5: 'q', -6: 'k',
        }
        return mapping.get(piece, '?')

    def _index_to_uci(self, index: int) -> str:
        file_map = 'abcdefgh'
        rank_map = '12345678'
        file = index % 8
        rank = index // 8
        return f"{file_map[file]}{rank_map[rank]}"
