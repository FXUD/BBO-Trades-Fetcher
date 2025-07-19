import asyncio
import json
import websockets
import yaml
from datetime import datetime
from pathlib import Path

class BinanceConnector:
    def __init__(self, config_path="pair_config.yml"):
        self.config_path = config_path
        self.ws_url = "wss://fstream.binance.com/ws/"
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def load_config(self):
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('binance', {}).get('symbols', [])
    
    def create_stream_name(self, symbols):
        streams = []
        for symbol in symbols:
            streams.append(f"{symbol.lower()}@bookTicker")  # BBO数据
            streams.append(f"{symbol.lower()}@aggTrade")    # 交易数据
        return "/".join(streams)
    
    async def connect(self):
        symbols = self.load_config()
        if not symbols:
            print("No Binance symbols configured")
            return
            
        stream_name = self.create_stream_name(symbols)
        uri = f"{self.ws_url}{stream_name}"
        
        print(f"Connecting to Binance: {uri}")
        
        async with websockets.connect(uri) as websocket:
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    self.save_data(data)
                except websockets.exceptions.ConnectionClosed:
                    print("Binance connection closed, reconnecting...")
                    break
                except Exception as e:
                    print(f"Binance error: {e}")
    
    def save_data(self, data):
        timestamp = datetime.now().isoformat()
        symbol = data.get('s', 'unknown')
        event_type = data.get('e')
        
        if event_type == 'bookTicker':
            data_type = 'bbo'
        elif event_type == 'aggTrade':
            data_type = 'trade'
        else:
            data_type = 'unknown'
            
        symbol_dir = self.data_dir / symbol.upper()
        symbol_dir.mkdir(exist_ok=True)
        filename = f"binance_{symbol.lower()}_{data_type}_{datetime.now().strftime('%Y%m%d')}.jsonl"
        filepath = symbol_dir / filename
        
        with open(filepath, 'a') as f:
            output = {
                "timestamp": timestamp,
                "exchange": "binance",
                "symbol": symbol,
                "type": data_type,
                "data": data
            }
            f.write(json.dumps(output) + '\n')

if __name__ == "__main__":
    connector = BinanceConnector()
    asyncio.run(connector.connect())