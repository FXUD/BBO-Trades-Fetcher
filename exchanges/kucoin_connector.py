import asyncio
import json
import websockets
import yaml
import requests
from datetime import datetime
from pathlib import Path

class KuCoinConnector:
    def __init__(self, config_path="pair_config.yml"):
        self.config_path = config_path
        self.api_url = "https://api-futures.kucoin.com"
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def load_config(self):
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        symbols = config.get('kucoin', {}).get('symbols', [])
        # 映射到KuCoin期货合约名称 - 大部分直接加M，特殊的单独映射
        special_map = {
            "BTCUSDT": "XBTUSDTM"
        }
        result = []
        for s in symbols:
            if s in special_map:
                result.append(special_map[s])
            else:
                result.append(s + "M")  # 默认加M
        return result
    
    def get_ws_token(self):
        response = requests.post(f"{self.api_url}/api/v1/bullet-public")
        return response.json()['data']
    
    async def connect(self):
        symbols = self.load_config()
        if not symbols:
            print("No KuCoin symbols configured")
            return
            
        ws_info = self.get_ws_token()
        ws_url = f"{ws_info['instanceServers'][0]['endpoint']}?token={ws_info['token']}"
        
        print(f"Connecting to KuCoin: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            for symbol in symbols:
                # 订阅BBO数据
                bbo_msg = {
                    "id": int(datetime.now().timestamp() * 1000),
                    "type": "subscribe",
                    "topic": f"/contractMarket/tickerV2:{symbol}",
                    "response": True
                }
                await websocket.send(json.dumps(bbo_msg))
                
                # 订阅交易数据
                trade_msg = {
                    "id": int(datetime.now().timestamp() * 1000) + 1,
                    "type": "subscribe", 
                    "topic": f"/contractMarket/execution:{symbol}",
                    "response": True
                }
                await websocket.send(json.dumps(trade_msg))
            
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    if data.get('type') == 'message':
                        self.save_data(data)
                except websockets.exceptions.ConnectionClosed:
                    print("KuCoin connection closed, reconnecting...")
                    break
                except Exception as e:
                    print(f"KuCoin error: {e}")
    
    def save_data(self, data):
        timestamp = datetime.now().isoformat()
        topic = data.get('topic', '')
        symbol = 'unknown'
        data_type = 'unknown'
        
        if '/contractMarket/tickerV2:' in topic:
            symbol = topic.split(':')[1]
            data_type = 'bbo'
        elif '/contractMarket/execution:' in topic:
            symbol = topic.split(':')[1] 
            data_type = 'trade'
            
        # 映射回标准符号名称
        if symbol == "XBTUSDTM":
            standard_symbol = "BTCUSDT"
        elif symbol.endswith("M"):
            standard_symbol = symbol[:-1]  # 去掉末尾的M
        else:
            standard_symbol = symbol
        
        symbol_dir = self.data_dir / standard_symbol.upper()
        symbol_dir.mkdir(exist_ok=True)
        filename = f"kucoin_{standard_symbol.lower()}_{data_type}_{datetime.now().strftime('%Y%m%d')}.jsonl"
        filepath = symbol_dir / filename
        
        with open(filepath, 'a') as f:
            output = {
                "timestamp": timestamp,
                "exchange": "kucoin",
                "symbol": standard_symbol,
                "type": data_type,
                "data": data
            }
            f.write(json.dumps(output) + '\n')

if __name__ == "__main__":
    connector = KuCoinConnector()
    asyncio.run(connector.connect())