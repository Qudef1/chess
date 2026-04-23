import json
from fastapi import WebSocket
from server.models import ClientMessage
from server.room import Room


class RoomManager:
    def __init__(self):
        self.waiting: WebSocket | None = None
        self.player_rooms: dict[int, Room] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        if self.waiting is None:
            self.waiting = websocket
            await websocket.send_json({'type': 'waiting', 'message': 'Ожидание соперника...'})
        else:
            room = Room(self.waiting, websocket)
            self.player_rooms[id(self.waiting)] = room
            self.player_rooms[id(websocket)] = room
            await room.players[0].send_json({'type': 'game_start', 'payload': {'color': 'white'}})
            await room.players[1].send_json({'type': 'game_start', 'payload': {'color': 'black'}})
            self.waiting = None

    async def disconnect(self, websocket: WebSocket):
        if self.waiting is websocket:
            self.waiting = None
            return

        room = self.player_rooms.pop(id(websocket), None)
        if room is None:
            return

        opponent = room.get_opponent(websocket)
        if opponent is not None:
            await opponent.send_json({'type': 'opponent_left', 'message': 'Соперник отключился.'})
            self.player_rooms.pop(id(opponent), None)

    async def handle_message(self, websocket: WebSocket, raw_text: str):
        try:
            payload = ClientMessage.parse_raw(raw_text)
        except Exception:
            await websocket.send_json({'type': 'error', 'message': 'Неверный формат сообщения.'})
            return

        if payload.type == 'join':
            await websocket.send_json({'type': 'joined', 'message': 'Вы подключены. Ожидайте соперника.'})
            return

        room = self.player_rooms.get(id(websocket))
        if room is None:
            await websocket.send_json({'type': 'error', 'message': 'Вы ещё не в комнате.'})
            return

        opponent = room.get_opponent(websocket)
        if payload.type == 'move' and payload.move is not None:
            await room.broadcast({'type': 'opponent_move', 'payload': payload.move.dict()}, exclude=websocket)
        elif payload.type == 'resign':
            await room.broadcast({'type': 'opponent_resigned', 'message': 'Соперник сдался.'}, exclude=websocket)
        elif payload.type == 'offer_draw':
            await room.broadcast({'type': 'draw_offer', 'message': 'Соперник предлагает ничью.'}, exclude=websocket)
        elif payload.type == 'accept_draw':
            # Send draw_accepted to both players (not just opponent)
            await room.broadcast({'type': 'draw_accepted', 'message': 'Ничья принята.'})
        elif payload.type == 'reject_draw':
            await room.broadcast({'type': 'draw_rejected', 'message': 'Предложение ничьи отклонено.'}, exclude=websocket)
        else:
            await websocket.send_json({'type': 'error', 'message': 'Неизвестный тип сообщения.'})
