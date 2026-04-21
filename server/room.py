from fastapi import WebSocket
from typing import List, Optional


class Room:
    def __init__(self, white_socket: WebSocket, black_socket: WebSocket):
        self.players: List[WebSocket] = [white_socket, black_socket]
        self.colors = {
            id(white_socket): 'white',
            id(black_socket): 'black'
        }

    def get_opponent(self, websocket: WebSocket) -> Optional[WebSocket]:
        for player in self.players:
            if player != websocket:
                return player
        return None

    def get_color(self, websocket: WebSocket) -> str:
        return self.colors.get(id(websocket), 'white')

    async def broadcast(self, message: dict, exclude: Optional[WebSocket] = None):
        for player in self.players:
            if player == exclude:
                continue
            await player.send_json(message)

    def contains(self, websocket: WebSocket) -> bool:
        return websocket in self.players
