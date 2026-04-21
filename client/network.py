import asyncio
import json
import threading
from queue import Queue
from typing import Callable, Optional

import websockets


class NetworkClient:
    def __init__(self, uri: str, on_message: Callable[[dict], None]):
        self.uri = uri
        self.on_message = on_message
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.websocket = None
        self.send_queue: Optional[asyncio.Queue] = None
        self.connected = False
        self.stop_event = threading.Event()

    def connect(self):
        if self.thread is not None and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.send_queue = asyncio.Queue()
        try:
            self.loop.run_until_complete(self._run())
        finally:
            self.loop.close()

    async def _run(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                self.connected = True
                self.on_message({'type': 'connected', 'message': 'Соединение установлено.'})
                receiver = asyncio.create_task(self._receive_loop())
                sender = asyncio.create_task(self._send_loop())
                done, pending = await asyncio.wait(
                    [receiver, sender],
                    return_when=asyncio.FIRST_EXCEPTION,
                )
                for task in pending:
                    task.cancel()
        except Exception as exc:
            self.on_message({'type': 'error', 'message': str(exc)})
        finally:
            self.connected = False
            self.on_message({'type': 'disconnected', 'message': 'Соединение разорвано.'})

    async def _receive_loop(self):
        assert self.websocket is not None
        async for message in self.websocket:
            try:
                payload = json.loads(message)
            except Exception:
                payload = {'type': 'error', 'message': 'Неверное сообщение от сервера.'}
            self.on_message(payload)

    async def _send_loop(self):
        assert self.websocket is not None
        assert self.send_queue is not None
        while True:
            message = await self.send_queue.get()
            if message is None:
                break
            await self.websocket.send(json.dumps(message))

    def send(self, message: dict):
        if self.loop is None or self.send_queue is None:
            return
        fut = asyncio.run_coroutine_threadsafe(self.send_queue.put(message), self.loop)
        try:
            fut.result(timeout=1)
        except Exception:
            pass

    def send_join(self, nickname: str = 'Player'):
        self.send({'type': 'join', 'nickname': nickname})

    def send_move(self, move: dict):
        self.send({'type': 'move', 'move': move})

    def send_resign(self):
        self.send({'type': 'resign'})

    def send_offer_draw(self):
        self.send({'type': 'offer_draw'})

    def send_accept_draw(self):
        self.send({'type': 'accept_draw'})

    def send_reject_draw(self):
        self.send({'type': 'reject_draw'})

    def disconnect(self):
        if self.loop is None or self.send_queue is None:
            return
        asyncio.run_coroutine_threadsafe(self.send_queue.put(None), self.loop)
