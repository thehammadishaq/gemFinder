"""
Finnhub WebSocket Service
Handles real-time stock price updates via Finnhub WebSocket API
"""
import asyncio
import json
import time
import websockets
from typing import Set, Dict, Callable, Optional
from config.settings import settings


class FinnhubWebSocketService:
    """Service to manage Finnhub WebSocket connections"""
    
    def __init__(self):
        self.api_key = settings.FINNHUB_API_KEY
        self.ws_url = "wss://ws.finnhub.io"
        self.websocket = None
        self.connected = False
        self.subscribed_symbols: Set[str] = set()
        self.message_handlers: Set[Callable] = set()
        self.reconnect_task: Optional[asyncio.Task] = None
        self._running = False
        self._connecting = False  # Lock to prevent multiple simultaneous connections
        self._rate_limited = False  # Track if we're rate limited
        self._last_429_time = None  # Track when we got 429 error
        
    async def connect(self):
        """Connect to Finnhub WebSocket"""
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY is not set in environment variables")
        
        # Prevent multiple simultaneous connection attempts
        if self._connecting:
            print("Connection already in progress, waiting...")
            # Wait for existing connection attempt
            while self._connecting:
                await asyncio.sleep(0.1)
            return
        
        # Check if we're rate limited
        if self._rate_limited and self._last_429_time:
            time_since_429 = time.time() - self._last_429_time
            if time_since_429 < 60:  # Wait 60 seconds after 429 error
                wait_time = 60 - time_since_429
                print(f"Rate limited. Waiting {wait_time:.1f} seconds before retry...")
                await asyncio.sleep(wait_time)
        
        self._connecting = True
        try:
            ws_url_with_token = f"{self.ws_url}?token={self.api_key}"
            self.websocket = await websockets.connect(ws_url_with_token)
            self.connected = True
            self._rate_limited = False
            self._last_429_time = None
            print(f"Connected to Finnhub WebSocket")
            
            # Resubscribe to all symbols
            for symbol in self.subscribed_symbols:
                await self.subscribe(symbol)
                
            # Start listening for messages in background
            if not self._running:
                self._running = True
                # Create task but don't await it - let it run in background
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self._listen())
                except RuntimeError:
                    # If no event loop, create one
                    asyncio.ensure_future(self._listen())
                
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 429:
                # Rate limited
                self._rate_limited = True
                self._last_429_time = time.time()
                self.connected = False
                print(f"⚠️ Rate limited by Finnhub (HTTP 429). Please wait before retrying.")
                raise Exception("Rate limited: Too many requests. Please wait 60 seconds.")
            else:
                print(f"Error connecting to Finnhub WebSocket: {e}")
                self.connected = False
                raise
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                self._rate_limited = True
                self._last_429_time = time.time()
                print(f"⚠️ Rate limited by Finnhub. Please wait before retrying.")
            print(f"Error connecting to Finnhub WebSocket: {e}")
            self.connected = False
            raise
        finally:
            self._connecting = False
    
    async def disconnect(self):
        """Disconnect from Finnhub WebSocket"""
        self._running = False
        if self.reconnect_task:
            self.reconnect_task.cancel()
            try:
                await self.reconnect_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print("Disconnected from Finnhub WebSocket")
    
    async def subscribe(self, symbol: str):
        """Subscribe to a symbol"""
        if not self.connected or not self.websocket:
            self.subscribed_symbols.add(symbol)
            await self.connect()
            return
        
        try:
            message = json.dumps({"type": "subscribe", "symbol": symbol})
            await self.websocket.send(message)
            self.subscribed_symbols.add(symbol)
            print(f"Subscribed to {symbol}")
        except Exception as e:
            print(f"Error subscribing to {symbol}: {e}")
    
    async def unsubscribe(self, symbol: str):
        """Unsubscribe from a symbol"""
        if not self.connected or not self.websocket:
            self.subscribed_symbols.discard(symbol)
            return
        
        try:
            message = json.dumps({"type": "unsubscribe", "symbol": symbol})
            await self.websocket.send(message)
            self.subscribed_symbols.discard(symbol)
            print(f"Unsubscribed from {symbol}")
        except Exception as e:
            print(f"Error unsubscribing from {symbol}: {e}")
    
    def add_message_handler(self, handler: Callable):
        """Add a message handler callback"""
        self.message_handlers.add(handler)
    
    def remove_message_handler(self, handler: Callable):
        """Remove a message handler callback"""
        self.message_handlers.discard(handler)
    
    async def _listen(self):
        """Listen for messages from WebSocket"""
        while self._running and self.connected:
            try:
                if not self.websocket:
                    break
                    
                message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                data = json.loads(message)
                
                # Log trade messages for debugging
                if data.get("type") == "trade":
                    print(f"Received trade data: {data}")
                elif data.get("type") == "ping":
                    # Respond to ping with pong
                    pong_message = json.dumps({"type": "pong"})
                    await self.websocket.send(pong_message)
                    continue
                
                # Notify all handlers
                for handler in self.message_handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(data)
                        else:
                            handler(data)
                    except Exception as e:
                        print(f"Error in message handler: {e}")
                        
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed, attempting to reconnect...")
                self.connected = False
                await self._reconnect()
                break
            except Exception as e:
                print(f"Error listening to WebSocket: {e}")
                await asyncio.sleep(1)
    
    async def _reconnect(self):
        """Reconnect to WebSocket"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries and self._running:
            try:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                await self.connect()
                return
            except Exception as e:
                retry_count += 1
                print(f"Reconnection attempt {retry_count} failed: {e}")
        
        if retry_count >= max_retries:
            print("Max reconnection attempts reached")


# Global instance
finnhub_ws_service = FinnhubWebSocketService()

