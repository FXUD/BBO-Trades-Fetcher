# BBO & Trades 实时数据采集器

一个用于采集Binance和KuCoin期货市场实时BBO（Best Bid/Offer）和交易数据的工具，专为跨交易所延迟分析和leadlag策略开发设计。

## 功能特性

- **双交易所支持**: 同时连接Binance期货和KuCoin期货
- **实时数据流**: WebSocket连接获取毫秒级数据
- **数据分类存储**: BBO和Trade数据分别存储，按币对分组
- **自动重连**: 连接断开自动重连，确保数据连续性
- **配置化管理**: 通过YAML文件灵活配置交易对
- **延迟分析优化**: 文件结构专为leadlag策略分析设计

## 数据类型

### BBO数据 (Best Bid/Offer)
- **Binance**: Individual Symbol Book Ticker Stream
- **KuCoin**: Ticker V2 (Level 1 Market Data)
- **用途**: 价格发现、延迟分析主要信号源

### Trade数据
- **Binance**: Aggregate Trade Stream
- **KuCoin**: Execution Data
- **用途**: 交易确认、信号验证

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置交易对
编辑 `pair_config.yml` 文件添加你要监控的交易对：

```yaml
binance:
  symbols:
    - "BTCUSDT"
    - "ETHUSDT"

kucoin:
  symbols:
    - "BTCUSDT"  # 自动映射为XBTUSDTM
    - "ETHUSDT"  # 自动映射为ETHUSDTM
```

### 3. 启动数据采集
```bash
python start.py
```

## 文件结构

```
data/
├── BTCUSDT/
│   ├── binance_btcusdt_bbo_20250719.jsonl
│   ├── binance_btcusdt_trade_20250719.jsonl
│   ├── kucoin_btcusdt_bbo_20250719.jsonl
│   └── kucoin_btcusdt_trade_20250719.jsonl
├── ETHUSDT/
│   └── ...
└── ...
```

## 数据格式

### Binance BBO数据示例
```json
{
  "timestamp": "2025-01-19T10:30:45.123456",
  "exchange": "binance",
  "symbol": "BTCUSDT",
  "type": "bbo",
  "data": {
    "e": "bookTicker",
    "s": "BTCUSDT",
    "b": "42500.00",  // 最佳买价
    "B": "1.23",      // 最佳买量
    "a": "42501.00",  // 最佳卖价
    "A": "2.45"       // 最佳卖量
  }
}
```

### KuCoin BBO数据示例
```json
{
  "timestamp": "2025-01-19T10:30:45.345678",
  "exchange": "kucoin",
  "symbol": "BTCUSDT",
  "type": "bbo",
  "data": {
    "type": "message",
    "topic": "/contractMarket/tickerV2:XBTUSDTM",
    "data": {
      "symbol": "XBTUSDTM",
      "bestBidPrice": "42499.00",
      "bestBidSize": "100",
      "bestAskPrice": "42502.00",
      "bestAskSize": "200"
    }
  }
}
```

## Symbol映射规则

### KuCoin期货合约映射
- **BTCUSDT** → **XBTUSDTM** (特殊映射)
- **其他币对** → **币对名称 + M** (如ETHUSDT → ETHUSDTM)

### 支持的交易对
- BTCUSDT / ETHUSDT / ADAUSDT / SOLUSDT
- XRPUSDT / DOGEUSDT / SUIUSDT
- HUSDT / TONUSDT / AAVEUSDT / PENGUUSDT

## 使用场景

### Leadlag策略开发
1. **延迟分析**: 比较同一币对在两个交易所的BBO变化时间差
2. **套利机会**: 识别价格差异和执行时机
3. **流动性分析**: 分析不同交易所的市场深度变化

### 数据分析示例
```python
import json
import pandas as pd

# 加载BBO数据用于延迟分析
def load_bbo_data(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return pd.DataFrame(data)

# 计算leadlag信号
binance_bbo = load_bbo_data('data/BTCUSDT/binance_btcusdt_bbo_20250719.jsonl')
kucoin_bbo = load_bbo_data('data/BTCUSDT/kucoin_btcusdt_bbo_20250719.jsonl')
```

## 运行监控

程序运行时会每10秒打印状态信息：
```
[10s] 数据采集运行中... 按 Ctrl+C 停止
[20s] 数据采集运行中... 按 Ctrl+C 停止
```

按 `Ctrl+C` 可安全停止程序（3秒超时自动强制退出）。

## 技术架构

- **异步WebSocket**: 使用asyncio和websockets库
- **数据持久化**: JSONL格式，便于流式处理
- **自动重连**: 连接断开后自动重连机制
- **错误处理**: 完善的异常处理和日志记录

## 注意事项

1. **网络稳定性**: 确保网络连接稳定，避免频繁重连
2. **磁盘空间**: 高频数据会产生较大文件，注意磁盘空间
3. **API限制**: 遵守交易所WebSocket连接限制
4. **时区处理**: 所有时间戳使用本地时区

## 许可证

本项目仅供学习和研究使用。

---

**开发环境**: Python 3.12+ | macOS | Anaconda
**作者**: Starr Financial Group - Leadlag Strategies Team
**版本**: v1.0.0