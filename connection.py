from fastapi import FastAPI, WebSocket
from collections import defaultdict


class ConnectionManager:

    def __init__(self):
        self.connections: dict = defaultdict(dict)

    def get_members(self, room_name):
        try:
            return self.connections[room_name]
        except Exception:
            return None

    async def connect(self, websocket: WebSocket, room_name: str):
        await websocket.accept()
        if self.connections[room_name] == {} or len(self.connections[room_name]) == 0:
            self.connections[room_name] = []
        self.connections[room_name].append(websocket)


    def remove(self, websocket: WebSocket, room_name: str):
        self.connections[room_name].remove(websocket)


    async def send_private_message(self, message: str, room_name: str):

        living_connections = []
        
        while len(self.connections[room_name]) > 0:

            websocket = self.connections[room_name].pop()
            await websocket.send_text(message)
            living_connections.append(websocket)
        
        self.connections[room_name] = living_connections
