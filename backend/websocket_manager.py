"""
WebSocket manager for real-time frontend updates
"""
import asyncio
import json
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)
MAX_WS_CONNECTIONS = 500

class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        if len(self.active_connections) >= MAX_WS_CONNECTIONS:
            await websocket.close(code=1013, reason="WebSocket capacity reached")
            logger.warning("❌ WebSocket connection rejected: capacity reached")
            return False

        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")
        return True
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket"""
        self.active_connections.discard(websocket)
        logger.info(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        # Iterate over a snapshot to avoid runtime errors if the connection set
        # changes while sends are in-flight.
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"❌ Error sending message: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def broadcast_account_update(self, account_data: dict):
        """Broadcast account update to all clients"""
        await self.broadcast({
            "type": "account_update",
            "data": account_data,
            "timestamp": account_data.get("timestamp")
        })
    
    async def broadcast_price_update(self, symbol: str, price_data: dict):
        """Broadcast price update to all clients"""
        await self.broadcast({
            "type": "price_update",
            "symbol": symbol,
            "data": price_data
        })
    
    async def broadcast_order_update(self, order_data: dict):
        """Broadcast order update to all clients"""
        await self.broadcast({
            "type": "order_update",
            "data": order_data
        })
    
    async def broadcast_portfolio_update(self, portfolio_data: dict):
        """Broadcast portfolio update to all clients"""
        await self.broadcast({
            "type": "portfolio_update",
            "data": portfolio_data
        })
    
    async def handle_client(self, websocket: WebSocket):
        """Handle WebSocket client connection"""
        accepted = await self.connect(websocket)
        if not accepted:
            return
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                msg_type = message.get("type")
                
                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
                elif msg_type == "subscribe":
                    symbol = message.get("symbol")
                    logger.info(f"Client subscribed to {symbol}")
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "symbol": symbol
                    }))
                
                elif msg_type == "unsubscribe":
                    symbol = message.get("symbol")
                    logger.info(f"Client unsubscribed from {symbol}")
        
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
            await self.disconnect(websocket)

# Global WebSocket manager instance
manager = WebSocketManager()
