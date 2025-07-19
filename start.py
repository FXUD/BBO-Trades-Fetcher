#!/usr/bin/env python3
"""
一键运行所有市场数据连接器
One-click runner for all market data connectors
"""

import asyncio
import signal
import sys
import subprocess
from pathlib import Path

# 添加exchanges目录到路径
sys.path.append(str(Path(__file__).parent / "exchanges"))

from binance_connector import BinanceConnector
from kucoin_connector import KuCoinConnector

class DataFetcher:
    def __init__(self):
        self.running = True
        
    def install_dependencies(self):
        print("检查并安装依赖...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("依赖安装完成")
        except subprocess.CalledProcessError:
            print("依赖安装失败，请手动运行: pip install -r requirements.txt")
            
    def signal_handler(self, signum, frame):
        print("\n正在停止数据采集...")
        self.running = False
        # 启动强制退出定时器
        import threading
        import os
        def force_exit():
            import time
            time.sleep(3)  # 给3秒时间正常关闭
            print("强制退出...")
            os._exit(0)
        threading.Thread(target=force_exit, daemon=True).start()
        
    async def run_binance(self):
        connector = BinanceConnector()
        while self.running:
            try:
                await connector.connect()
                if self.running:
                    print("Binance连接断开，3秒后重连...")
                    await asyncio.sleep(3)
            except Exception as e:
                print(f"Binance错误: {e}")
                if self.running:
                    await asyncio.sleep(5)
                    
    async def run_kucoin(self):
        connector = KuCoinConnector()
        while self.running:
            try:
                await connector.connect()
                if self.running:
                    print("KuCoin连接断开，3秒后重连...")
                    await asyncio.sleep(3)
            except Exception as e:
                print(f"KuCoin错误: {e}")
                if self.running:
                    await asyncio.sleep(5)
                    
    async def status_reporter(self):
        import time
        start_time = time.time()
        while self.running:
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] 数据采集运行中... 按 Ctrl+C 停止")
            await asyncio.sleep(10)
    
    async def main(self):
        self.install_dependencies()
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("开始采集市场数据 (BBO + Trades)...")
        print("按 Ctrl+C 停止")
        
        tasks = [
            asyncio.create_task(self.run_binance()),
            asyncio.create_task(self.run_kucoin()),
            asyncio.create_task(self.status_reporter())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            for task in tasks:
                task.cancel()
            print("数据采集已停止")

if __name__ == "__main__":
    fetcher = DataFetcher()
    asyncio.run(fetcher.main())