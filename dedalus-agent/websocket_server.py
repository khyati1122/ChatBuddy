# websocket_server.py
import asyncio
import websockets
import json
from datetime import datetime

class AnalysisBroadcaster:
    def __init__(self):
        self.connected_clients = set()
    
    async def register(self, websocket):
        self.connected_clients.add(websocket)
        print(f"📱 Chrome extension connected. Total clients: {len(self.connected_clients)}")
    
    async def unregister(self, websocket):
        self.connected_clients.remove(websocket)
        print(f"📱 Chrome extension disconnected. Total clients: {len(self.connected_clients)}")
    
    async def broadcast_analysis(self, analysis_data):
        """Send analysis to all connected Chrome extensions"""
        if self.connected_clients:
            message = {
                "type": "reddit_analysis",
                "timestamp": datetime.now().isoformat(),
                "data": analysis_data
            }
            
            disconnected_clients = set()
            for client in self.connected_clients:
                try:
                    await client.send(json.dumps(message))
                    print(f"📨 Sent analysis to extension: {analysis_data['post_title'][:30]}...")
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                self.connected_clients.remove(client)

# Global broadcaster instance
broadcaster = AnalysisBroadcaster()

async def handler(websocket, path):
    await broadcaster.register(websocket)
    try:
        await websocket.wait_closed()
    finally:
        await broadcaster.unregister(websocket)

async def start_websocket_server():
    print("🚀 Starting WebSocket server on port 8765...")
    print("📱 Chrome extensions can connect to: ws://localhost:8765")
    server = await websockets.serve(handler, "localhost", 8765)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_websocket_server())