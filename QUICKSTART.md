# Binance MCP Server - Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Install Dependencies

```bash
pip install fastmcp httpx pydantic
```

### Step 2: Configure Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "binance": {
      "command": "python",
      "args": ["/path/to/binance_mcp.py"]
    }
  }
}
```

**Config file locations**:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop. You should see the Binance tools available!

---

## 🎯 Quick Examples

### Example 1: Check Bitcoin Price
```
What's the current price of Bitcoin?
```
*Claude will use: `binance_get_price(symbols=["BTCUSDT"])`*

### Example 2: Get 24hr Statistics
```
Show me the 24-hour performance for Bitcoin and Ethereum
```
*Claude will use: `binance_get_ticker(symbols=["BTCUSDT", "ETHUSDT"])`*

### Example 3: Find Trading Pairs
```
What trading pairs are available for Dogecoin?
```
*Claude will use: `binance_search_symbols(search_term="DOGE")`*

### Example 4: Technical Analysis
```
Get me hourly candlestick data for Bitcoin over the last 24 hours
```
*Claude will use: `binance_get_klines(symbol="BTCUSDT", interval="1h", limit=24)`*

### Example 5: Order Book Analysis
```
Show me the order book depth for Ethereum
```
*Claude will use: `binance_get_order_book(symbol="ETHUSDT", limit=100)`*

### Example 6: Recent Trades
```
What are the recent trades for Bitcoin?
```
*Claude will use: `binance_get_recent_trades(symbol="BTCUSDT", limit=100)`*

---

## 💡 Pro Tips

1. **Don't know the symbol?** Just ask naturally:
   - "What's the Bitcoin price?" → Claude finds BTCUSDT
   - "Show me Ethereum pairs" → Claude uses search_symbols

2. **Want more detail?** Ask for it:
   - "Show me detailed 24hr stats" → Uses type="FULL"
   - "Just the prices" → Uses binance_get_price

3. **Technical analysis?** Be specific:
   - "Show me daily data for the last month"
   - "Get hourly candles for today"
   - "What's the weekly trend for the last quarter?"

4. **Multiple assets?** Just list them:
   - "Compare Bitcoin, Ethereum, and BNB prices"
   - "Show me stats for the top 5 cryptos"

---

## 🔍 What You Can Ask

### Price Queries
- What's the current price of [coin]?
- How much is Bitcoin worth?
- Show me prices for BTC, ETH, and BNB

### Market Performance
- What's Bitcoin's 24-hour performance?
- Show me the change in Ethereum price today
- Which coins are up the most today?

### Trading Pairs
- What pairs are available for Bitcoin?
- Find all USDT trading pairs
- Is there a [COIN]/USDT pair?

### Technical Analysis
- Show me hourly price data for Bitcoin
- Get me daily candles for the last month
- What's the trend for Ethereum this week?

### Market Depth
- Show me the order book for Bitcoin
- What's the spread on Ethereum?
- How liquid is [trading pair]?

### Recent Activity
- What are the recent trades for Bitcoin?
- Show me market activity for Ethereum
- What's the buy/sell ratio for [coin]?

---

## ⚠️ Important Notes

- **No Authentication Required**: All data is from public API endpoints
- **Rate Limits**: 6,000 requests per minute (automatically managed)
- **Symbol Format**: Use format like "BTCUSDT" not "BTC/USDT"
- **Case Insensitive**: BTCUSDT, btcusdt, BtcUsdt all work

---

## 🐛 Troubleshooting

### "Symbol not found"
→ Use `binance_search_symbols` to find the correct symbol format

### "Rate limit exceeded"
→ Wait 60 seconds. Try combining requests (multiple symbols in one query)

### "Connection error"
→ Check internet connection. Verify Binance API is accessible.

---

## 📚 Full Documentation

See `README.md` for complete tool documentation and examples.

---

**Happy trading! 🚀📈**
