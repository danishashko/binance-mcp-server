<h1 align="center">Binance MCP Server</h1>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-compatible-purple.svg" alt="MCP"></a>
  <a href="https://www.binance.com/"><img src="https://img.shields.io/badge/Binance-API-yellow.svg" alt="Binance API"></a>
  <img src="https://img.shields.io/badge/status-active-success.svg" alt="Status">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

<p align="center">
<img width="1032" height="879" alt="image" src="https://github.com/user-attachments/assets/6f00b820-11a4-4d01-ade9-96127852b3d0" />
</p>

---

A Model Context Protocol (MCP) server that provides access to Binance's public Spot API, enabling LLMs to fetch real-time cryptocurrency market data, trading pairs information, and exchange statistics.

## Features

### 🎯 Core Capabilities

- **Real-time Price Data**: Get current prices and 24-hour statistics for any trading pair
- **Market Discovery**: Search and explore available trading pairs by asset or keyword
- **Order Book Analysis**: Analyze market depth with bid/ask data
- **Historical Data**: Retrieve candlestick/OHLC data for technical analysis
- **Trade Flow**: View recent trades and market activity
- **Exchange Information**: Access trading rules, rate limits, and symbol details

### 🔧 Available Tools

1. **binance_get_ticker** - Get current price and 24hr statistics
2. **binance_search_symbols** - Find trading pairs by asset or keyword
3. **binance_get_order_book** - Get order book depth (bids/asks)
4. **binance_get_klines** - Get candlestick/OHLC data for charting
5. **binance_get_recent_trades** - View recent executed trades
6. **binance_get_exchange_info** - Get comprehensive exchange information
7. **binance_get_price** - Quick price lookup (lightweight)
8. **binance_get_best_price** - Get best bid/ask prices

### ✨ Key Features

- **No Authentication Required**: All endpoints use public API (no API keys needed)
- **Dual Response Formats**: Both human-readable Markdown and machine-readable JSON
- **Smart Truncation**: Automatically handles large responses with helpful guidance
- **Actionable Errors**: Clear error messages that guide users to correct usage
- **Rate Limit Aware**: Respects Binance API rate limits and provides guidance

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python -m py_compile binance_mcp.py
   ```

## Usage

### With Claude Desktop

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "binance": {
      "command": "python",
      "args": ["/absolute/path/to/binance_mcp.py"]
    }
  }
}
```

Replace `/absolute/path/to/binance_mcp.py` with the actual path to the file.

### Testing

You can test the server using the MCP inspector or by calling tools directly:

```python
# Example: Get current Bitcoin price
binance_get_price(symbols=["BTCUSDT"])

# Example: Search for all BTC trading pairs
binance_search_symbols(base_asset="BTC")

# Example: Get 24hr statistics
binance_get_ticker(symbols=["BTCUSDT", "ETHUSDT"])

# Example: Get hourly candlestick data
binance_get_klines(symbol="BTCUSDT", interval="1h", limit=24)
```

## Tool Details

### binance_get_ticker

Get current price and 24-hour trading statistics.

**Parameters**:
- `symbols`: List of trading pair symbols (required)
- `type`: "FULL" or "MINI" (default: "FULL")
- `response_format`: "markdown" or "json" (default: "markdown")

**Example**:
```python
binance_get_ticker(symbols=["BTCUSDT", "ETHUSDT"], type="FULL")
```

**Returns**: Current price, 24h change %, high/low, volume, bid/ask, etc.

---

### binance_search_symbols

Find trading pairs by filtering on base asset, quote asset, or keyword.

**Parameters**:
- `base_asset`: Base currency filter (e.g., "BTC")
- `quote_asset`: Quote currency filter (e.g., "USDT")
- `search_term`: Keyword to search in symbol names
- `status`: "TRADING" or "ALL" (default: "TRADING")
- `response_format`: "markdown" or "json" (default: "markdown")

**Example**:
```python
# Find all BTC pairs
binance_search_symbols(base_asset="BTC")

# Find all USDT pairs
binance_search_symbols(quote_asset="USDT")

# Find specific pair
binance_search_symbols(base_asset="BTC", quote_asset="USDT")

# Search by keyword
binance_search_symbols(search_term="DOGE")
```

**Returns**: List of matching trading pairs with status and features.

---

### binance_get_order_book

Get order book depth showing bids and asks.

**Parameters**:
- `symbol`: Trading pair symbol (required)
- `limit`: Depth level - 5, 10, 20, 50, 100, 500, 1000, or 5000 (default: 100)
- `response_format`: "markdown" or "json" (default: "markdown")

**Example**:
```python
binance_get_order_book(symbol="BTCUSDT", limit=20)
```

**Returns**: Order book with prices, quantities, and spread analysis.

---

### binance_get_klines

Get candlestick/OHLC data for technical analysis.

**Parameters**:
- `symbol`: Trading pair symbol (required)
- `interval`: Time interval (required) - "1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"
- `limit`: Number of candles (default: 100, max: 1000)
- `start_time`: Optional start timestamp in milliseconds
- `end_time`: Optional end timestamp in milliseconds
- `response_format`: "markdown" or "json" (default: "markdown")

**Example**:
```python
# Last 24 hours of hourly data
binance_get_klines(symbol="BTCUSDT", interval="1h", limit=24)

# Last 30 days of daily data
binance_get_klines(symbol="ETHUSDT", interval="1d", limit=30)

# Last year of weekly data
binance_get_klines(symbol="BNBUSDT", interval="1w", limit=52)
```

**Returns**: OHLC data with volume, trade count, and change percentages.

---

### binance_get_recent_trades

Get recent executed trades for a symbol.

**Parameters**:
- `symbol`: Trading pair symbol (required)
- `limit`: Number of trades (default: 100, max: 1000)
- `response_format`: "markdown" or "json" (default: "markdown")

**Example**:
```python
binance_get_recent_trades(symbol="BTCUSDT", limit=50)
```

**Returns**: Recent trades with price, quantity, time, and buy/sell side.

---

### binance_get_exchange_info

Get comprehensive exchange information and trading rules.

**Parameters**:
- `symbols`: Optional list of specific symbols
- `response_format`: "markdown" or "json" (default: "markdown")

**Example**:
```python
# Get info for specific symbols
binance_get_exchange_info(symbols=["BTCUSDT", "ETHUSDT"])

# Get info for all symbols (large response)
binance_get_exchange_info()
```

**Returns**: Exchange timezone, rate limits, trading rules, symbol details.

---

### binance_get_price

Get latest price only (lightweight, fast query).

**Parameters**:
- `symbols`: List of trading pair symbols (required)
- `response_format`: "markdown" or "json" (default: "markdown")

**Example**:
```python
binance_get_price(symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"])
```

**Returns**: Current price for each symbol.

---

### binance_get_best_price

Get best bid/ask prices from the order book.

**Parameters**:
- `symbols`: List of trading pair symbols (required)
- `response_format`: "markdown" or "json" (default: "markdown")

**Example**:
```python
binance_get_best_price(symbols=["BTCUSDT"])
```

**Returns**: Best bid/ask prices with quantities and spread analysis.

## Common Use Cases

### 1. Check Current Cryptocurrency Prices

```python
# Simple price check
binance_get_price(symbols=["BTCUSDT", "ETHUSDT"])

# Detailed 24hr statistics
binance_get_ticker(symbols=["BTCUSDT", "ETHUSDT"])
```

### 2. Find Trading Pairs

```python
# Find all Bitcoin pairs
binance_search_symbols(base_asset="BTC")

# Find all USDT pairs
binance_search_symbols(quote_asset="USDT")

# Search for specific coins
binance_search_symbols(search_term="DOGE")
```

### 3. Technical Analysis

```python
# Get hourly data for last 24 hours
binance_get_klines(symbol="BTCUSDT", interval="1h", limit=24)

# Get daily data for last 30 days
binance_get_klines(symbol="BTCUSDT", interval="1d", limit=30)
```

### 4. Market Depth Analysis

```python
# Check order book depth
binance_get_order_book(symbol="BTCUSDT", limit=100)

# Get best bid/ask
binance_get_best_price(symbols=["BTCUSDT"])
```

### 5. Monitor Market Activity

```python
# View recent trades
binance_get_recent_trades(symbol="BTCUSDT", limit=100)
```

## Error Handling

The server provides actionable error messages:

### Invalid Symbol
```
Error: Symbol 'BTCUSD' not found on Binance.

Did you mean: BTCUSDT, BTCBUSD, BTCUSDC?

To find valid trading pairs, use the 'binance_search_symbols' tool:
- Search by base asset: binance_search_symbols(base_asset="BTC")
- Search by quote asset: binance_search_symbols(quote_asset="USDT")
```

### Rate Limit
```
Error: Rate limit exceeded (HTTP 429)

Binance rate limit: 6000 request weight per minute

Action: Wait 60 seconds before making more requests.
Tip: Use multiple symbols in one request instead of separate requests.
```

### Response Too Large
```
Response truncated: Showing 50 of 200 symbols

The full response exceeds the 25,000 character limit.

To get more specific results:
- Filter by asset: binance_search_symbols(base_asset="BTC")
- Request fewer symbols: binance_get_ticker(symbols=["BTCUSDT", "ETHUSDT"])
```

## Rate Limits

Binance API rate limits:
- **Request Weight**: 6,000 per minute
- **Raw Requests**: 61,000 per 5 minutes

The server respects these limits and provides guidance when limits are approached.

## Response Formats

### Markdown (Default)
Human-readable format with:
- Headers and sections
- Tables for structured data
- Emojis for visual indicators
- Human-readable timestamps
- Formatted numbers with currency symbols

### JSON
Machine-readable format with:
- Complete field data
- Consistent structure
- Numeric timestamps
- All metadata included

## Technical Details

### Architecture
- **Language**: Python 3.10+
- **Framework**: FastMCP (MCP Python SDK)
- **HTTP Client**: httpx (async)
- **Validation**: Pydantic v2
- **Transport**: stdio

### API Endpoint
- **Base URL**: `https://data-api.binance.vision`
- **Public API**: No authentication required

### Character Limit
- Maximum response size: 25,000 characters
- Automatic truncation with guidance when exceeded

## Troubleshooting

### Server won't start
- Check Python version: `python --version` (must be 3.10+)
- Verify dependencies: `pip list | grep -E "fastmcp|httpx|pydantic"`
- Test syntax: `python -m py_compile binance_mcp.py`

### Connection errors
- Check internet connection
- Verify Binance API is accessible: `curl https://api.binance.com/api/v3/ping`

### Symbol not found
- Use `binance_search_symbols` to find valid trading pairs
- Ensure symbol is in correct format (e.g., "BTCUSDT" not "BTC-USDT")

## Contributing

Suggestions and improvements are welcome! This MCP server follows the MCP best practices for:
- Tool naming with service prefix
- Comprehensive documentation
- Actionable error messages
- Response format flexibility
- Smart truncation with guidance

## License

MIT License - feel free to use and modify as needed.

## Resources

- [Binance API Documentation](https://developers.binance.com/docs/binance-spot-api-docs)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk)

## Version History

### v1.0.0 (Initial Release)
- 8 comprehensive tools for Binance Spot API
- Public API endpoints (no authentication)
- Dual response formats (Markdown/JSON)
- Smart truncation and error handling
- Complete documentation

---

**Happy Trading! 🚀📈**
