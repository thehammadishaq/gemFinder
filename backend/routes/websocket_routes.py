"""
WebSocket Routes for Real-time Stock Prices
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
from services.finnhub_websocket_service import finnhub_ws_service

router = APIRouter(prefix="/ws", tags=["WebSocket"])

# Store active WebSocket connections
active_connections: List[WebSocket] = []


async def broadcast_to_clients(message: dict):
    """Broadcast message to all connected clients"""
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            print(f"Error sending message to client: {e}")
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        active_connections.remove(conn)


async def handle_finnhub_message(data: dict):
    """Handle incoming message from Finnhub WebSocket"""
    await broadcast_to_clients(data)


@router.websocket("/stock-prices")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time stock prices"""
    await websocket.accept()
    active_connections.append(websocket)
    
    # Add message handler if not already added
    if handle_finnhub_message not in finnhub_ws_service.message_handlers:
        finnhub_ws_service.add_message_handler(handle_finnhub_message)
    
    # Connect to Finnhub if not connected (only one connection shared across all clients)
    if not finnhub_ws_service.connected and not finnhub_ws_service._connecting:
        try:
            await finnhub_ws_service.connect()
            
            # Subscribe to top 25 US stocks only once when connecting to Finnhub
            default_symbols = [
                "AAPL",   # 1
                "MSFT",   # 2
                "NVDA",   # 3
                "GOOGL",  # 4
                "GOOG",   # 5
                "AMZN",   # 6
                "META",   # 7
                "BRK.B",  # 8
                "TSLA",   # 9
                "AVGO",   # 10
                "UNH",    # 11
                "JNJ",    # 12
                "V",      # 13
                "WMT",    # 14
                "MA",     # 15
                "HD",     # 16
                "PG",     # 17
                "DIS",    # 18
                "NKE",    # 19
                "JPM",    # 20
                "BAC",    # 21
                "XOM",    # 22
                "CVX",    # 23
                "KO",     # 24
                "MRK"     # 25
            ]
            
            # Subscribe to default symbols
            for symbol in default_symbols:
                await finnhub_ws_service.subscribe(symbol)
                
        except ValueError as e:
            # Missing API key
            await websocket.send_json({
                "type": "error",
                "message": f"Finnhub API key not configured. Please set FINNHUB_API_KEY in backend .env file. Error: {str(e)}"
            })
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                await websocket.send_json({
                    "type": "error",
                    "message": "Rate limited: Too many requests to Finnhub. Please wait 60 seconds. Using cached/quote data instead."
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Failed to connect to Finnhub: {str(e)}"
                })
    
    try:
        
        # Listen for client messages (subscribe/unsubscribe requests)
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "subscribe":
                    symbol = message.get("symbol")
                    if symbol:
                        await finnhub_ws_service.subscribe(symbol)
                        await websocket.send_json({
                            "type": "subscribed",
                            "symbol": symbol
                        })
                
                elif message.get("type") == "unsubscribe":
                    symbol = message.get("symbol")
                    if symbol:
                        await finnhub_ws_service.unsubscribe(symbol)
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "symbol": symbol
                        })
                        
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print(f"Client disconnected. Active connections: {len(active_connections)}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

