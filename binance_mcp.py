#!/usr/bin/env python3
"""
Binance MCP Server v1.0.1

A Model Context Protocol server for interacting with Binance's public Spot API.
Enables LLMs to fetch cryptocurrency market data, trading pairs, and exchange statistics.

All endpoints are public and do not require authentication.

Version History:
- v1.0.0 (2025-01-15): Initial release
- v1.0.1 (2025-01-15): Fixed symbols parameter encoding for Binance API compliance
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Callable
from urllib.parse import urlencode

import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator

# Constants
CHARACTER_LIMIT = 25000
BINANCE_API_BASE = "https://data-api.binance.vision"
REQUEST_TIMEOUT = 10.0  # Binance recommends 10 second timeout

# Valid intervals for kline data
VALID_INTERVALS = [
    "1s", "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M"
]

# Initialize MCP server
mcp = FastMCP("binance_mcp")


# ==================== Input Models ====================

class ResponseFormat(BaseModel):
    """Base model with response format"""
    response_format: Literal["markdown", "json"] = Field(
        default="markdown",
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class TickerInput(ResponseFormat):
    """Input for getting ticker information"""
    symbols: List[str] = Field(
        description="List of trading pair symbols (e.g., ['BTCUSDT', 'ETHUSDT'])",
        min_length=1,
        max_length=100,
        examples=[["BTCUSDT"], ["BTCUSDT", "ETHUSDT", "BNBUSDT"]]
    )
    type: Literal["FULL", "MINI"] = Field(
        default="FULL",
        description="FULL: complete statistics, MINI: essential fields only"
    )
    
    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, v: List[str]) -> List[str]:
        """Normalize symbols to uppercase"""
        return [s.upper().strip() for s in v]


class SearchSymbolsInput(ResponseFormat):
    """Input for searching trading pairs"""
    base_asset: Optional[str] = Field(
        default=None,
        description="Base asset to filter by (e.g., 'BTC', 'ETH')",
        examples=["BTC", "ETH", "BNB"]
    )
    quote_asset: Optional[str] = Field(
        default=None,
        description="Quote asset to filter by (e.g., 'USDT', 'BUSD')",
        examples=["USDT", "BUSD", "BTC"]
    )
    search_term: Optional[str] = Field(
        default=None,
        description="Search term to match in symbol names",
        examples=["DOGE", "SHIB"]
    )
    status: Literal["TRADING", "ALL"] = Field(
        default="TRADING",
        description="Filter by trading status: TRADING (active only) or ALL"
    )
    
    @field_validator("base_asset", "quote_asset", "search_term")
    @classmethod
    def uppercase_assets(cls, v: Optional[str]) -> Optional[str]:
        """Normalize to uppercase"""
        return v.upper().strip() if v else None


class OrderBookInput(ResponseFormat):
    """Input for getting order book depth"""
    symbol: str = Field(
        description="Trading pair symbol (e.g., 'BTCUSDT')",
        examples=["BTCUSDT", "ETHUSDT"]
    )
    limit: int = Field(
        default=100,
        description="Depth level: 5, 10, 20, 50, 100, 500, 1000, or 5000"
    )
    
    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.upper().strip()
    
    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        valid_limits = [5, 10, 20, 50, 100, 500, 1000, 5000]
        if v not in valid_limits:
            raise ValueError(
                f"Invalid limit {v}. Valid limits: {', '.join(map(str, valid_limits))}"
            )
        return v


class KlinesInput(ResponseFormat):
    """Input for getting candlestick data"""
    symbol: str = Field(
        description="Trading pair symbol (e.g., 'BTCUSDT')",
        examples=["BTCUSDT", "ETHUSDT"]
    )
    interval: str = Field(
        description="Kline interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M",
        examples=["1h", "1d", "1w"]
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of klines to return (1-1000)"
    )
    start_time: Optional[int] = Field(
        default=None,
        description="Start time in milliseconds (Unix timestamp)"
    )
    end_time: Optional[int] = Field(
        default=None,
        description="End time in milliseconds (Unix timestamp)"
    )
    
    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.upper().strip()
    
    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: str) -> str:
        if v not in VALID_INTERVALS:
            raise ValueError(
                f"Invalid interval '{v}'. Valid intervals: {', '.join(VALID_INTERVALS)}"
            )
        return v


class RecentTradesInput(ResponseFormat):
    """Input for getting recent trades"""
    symbol: str = Field(
        description="Trading pair symbol (e.g., 'BTCUSDT')",
        examples=["BTCUSDT", "ETHUSDT"]
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of trades to return (1-1000)"
    )
    
    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.upper().strip()


class ExchangeInfoInput(ResponseFormat):
    """Input for getting exchange information"""
    symbols: Optional[List[str]] = Field(
        default=None,
        description="Optional list of symbols to get info for. If omitted, returns all symbols.",
        examples=[["BTCUSDT", "ETHUSDT"]]
    )
    
    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Normalize symbols to uppercase"""
        return [s.upper().strip() for s in v] if v else None


class PriceInput(ResponseFormat):
    """Input for getting latest prices"""
    symbols: List[str] = Field(
        description="List of trading pair symbols (e.g., ['BTCUSDT', 'ETHUSDT'])",
        min_length=1,
        max_length=100,
        examples=[["BTCUSDT"], ["BTCUSDT", "ETHUSDT"]]
    )
    
    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, v: List[str]) -> List[str]:
        """Normalize symbols to uppercase"""
        return [s.upper().strip() for s in v]


# ==================== Utility Functions ====================

async def make_api_request(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    base_url: str = BINANCE_API_BASE
) -> Dict[str, Any]:
    """
    Make an API request to Binance with proper error handling.
    
    Args:
        endpoint: API endpoint path (e.g., "/api/v3/ticker/24hr")
        params: Query parameters
        base_url: Base URL for the API
    
    Returns:
        Parsed JSON response
    
    Raises:
        Exception with actionable error message
    """
    url = f"{base_url}{endpoint}"
    
    # Remove None values from params
    if params:
        params = {k: v for k, v in params.items() if v is not None}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            
            # Handle different HTTP status codes
            if response.status_code == 200:
                return response.json()
            
            elif response.status_code == 429:
                error_data = response.json()
                raise Exception(
                    f"Rate limit exceeded (HTTP 429)\n\n"
                    f"Binance rate limit: 6000 request weight per minute\n"
                    f"Message: {error_data.get('msg', 'Unknown error')}\n\n"
                    f"Action: Wait 60 seconds before making more requests.\n"
                    f"Tip: Use multiple symbols in one request instead of separate requests."
                )
            
            elif response.status_code >= 400 and response.status_code < 500:
                error_data = response.json()
                error_code = error_data.get('code', 'Unknown')
                error_msg = error_data.get('msg', 'Unknown error')
                
                # Provide actionable guidance based on error
                if 'symbol' in error_msg.lower() or error_code == -1121:
                    raise Exception(
                        f"Invalid symbol error: {error_msg}\n\n"
                        f"To find valid trading pairs, use the 'binance_search_symbols' tool:\n"
                        f"- Search by base asset: binance_search_symbols(base_asset='BTC')\n"
                        f"- Search by quote asset: binance_search_symbols(quote_asset='USDT')\n"
                        f"- Search by keyword: binance_search_symbols(search_term='DOGE')"
                    )
                else:
                    raise Exception(
                        f"API Error (HTTP {response.status_code}, Code {error_code}): {error_msg}\n\n"
                        f"Please check your parameters and try again."
                    )
            
            elif response.status_code >= 500:
                raise Exception(
                    f"Binance server error (HTTP {response.status_code})\n\n"
                    f"This is a temporary issue on Binance's side.\n"
                    f"Action: Please retry your request in a few moments."
                )
            
            else:
                raise Exception(f"Unexpected HTTP status code: {response.status_code}")
    
    except httpx.TimeoutException:
        raise Exception(
            f"Request timeout after {REQUEST_TIMEOUT} seconds\n\n"
            f"This could be due to network issues or high API load.\n"
            f"Action: Please try again."
        )
    except httpx.RequestError as e:
        raise Exception(
            f"Network error: {str(e)}\n\n"
            f"Please check your internet connection and try again."
        )


def format_timestamp(timestamp_ms: int) -> str:
    """Convert millisecond timestamp to human-readable format"""
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def format_number(value: str | float, decimals: int = 2) -> str:
    """Format number with thousands separator"""
    try:
        num = float(value)
        if num >= 1_000_000_000:
            return f"${num/1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"${num/1_000:.2f}K"
        else:
            return f"${num:,.{decimals}f}"
    except:
        return str(value)


def truncate_response(
    data: Any,
    format_func: Callable[[Any], str],
    item_limit: int = None
) -> Tuple[str, bool, Optional[str]]:
    """
    Intelligently truncate responses that exceed CHARACTER_LIMIT.
    
    Returns:
        (formatted_string, was_truncated, truncation_message)
    """
    # Try formatting the full data
    full_result = format_func(data)
    
    if len(full_result) <= CHARACTER_LIMIT:
        return full_result, False, None
    
    # If data is a list, try truncating items
    if isinstance(data, list) and item_limit:
        truncated_count = max(1, len(data) // 2)
        truncated_data = data[:truncated_count]
        truncated_result = format_func(truncated_data)
        
        truncation_msg = (
            f"\n\n⚠️ Response truncated: Showing {truncated_count} of {len(data)} items\n\n"
            f"The full response exceeds the {CHARACTER_LIMIT:,} character limit.\n\n"
            f"To get more specific results:\n"
            f"- Request fewer items\n"
            f"- Use filters to narrow down results\n"
            f"- Request data in multiple smaller queries"
        )
        
        return truncated_result + truncation_msg, True, truncation_msg
    
    # For non-list data, just truncate the string
    truncated = full_result[:CHARACTER_LIMIT]
    truncation_msg = (
        f"\n\n⚠️ Response truncated at {CHARACTER_LIMIT:,} characters\n\n"
        f"The full response was too large. Try using filters to get more specific data."
    )
    
    return truncated + truncation_msg, True, truncation_msg


# ==================== Formatting Functions ====================

def format_ticker_markdown(tickers: List[Dict[str, Any]], ticker_type: str = "FULL") -> str:
    """Format ticker data as Markdown"""
    if not tickers:
        return "No ticker data found."
    
    output = ["# Binance Ticker Information\n"]
    
    for ticker in tickers:
        symbol = ticker.get("symbol", "Unknown")
        output.append(f"## {symbol}\n")
        
        # Price information
        price = ticker.get("lastPrice", ticker.get("price", "N/A"))
        output.append(f"- **Current Price**: ${float(price):,.2f}" if price != "N/A" else "- **Current Price**: N/A")
        
        if ticker_type == "FULL":
            # Change information
            change = ticker.get("priceChange", "0")
            change_pct = ticker.get("priceChangePercent", "0")
            change_float = float(change)
            emoji = "📈" if change_float > 0 else "📉" if change_float < 0 else "➡️"
            output.append(f"- **24h Change**: {emoji} {float(change_pct):.2f}% (${change_float:,.2f})")
            
            # High/Low
            high = ticker.get("highPrice", "N/A")
            low = ticker.get("lowPrice", "N/A")
            output.append(f"- **24h High**: ${float(high):,.2f}" if high != "N/A" else "- **24h High**: N/A")
            output.append(f"- **24h Low**: ${float(low):,.2f}" if low != "N/A" else "- **24h Low**: N/A")
            
            # Volume
            volume = ticker.get("volume", "N/A")
            quote_volume = ticker.get("quoteVolume", "N/A")
            if volume != "N/A":
                base_asset = symbol.replace("USDT", "").replace("BUSD", "").replace("BTC", "").replace("ETH", "")
                output.append(f"- **24h Volume**: {float(volume):,.2f} {base_asset}")
            if quote_volume != "N/A":
                output.append(f"- **24h Quote Volume**: {format_number(quote_volume)}")
            
            # Weighted average price
            if "weightedAvgPrice" in ticker:
                output.append(f"- **Weighted Avg Price**: ${float(ticker['weightedAvgPrice']):,.2f}")
            
            # Bid/Ask
            if "bidPrice" in ticker:
                output.append(f"- **Best Bid**: ${float(ticker['bidPrice']):,.2f} (Qty: {float(ticker.get('bidQty', 0)):,.4f})")
            if "askPrice" in ticker:
                output.append(f"- **Best Ask**: ${float(ticker['askPrice']):,.2f} (Qty: {float(ticker.get('askQty', 0)):,.4f})")
        
        # Timestamp
        close_time = ticker.get("closeTime")
        if close_time:
            output.append(f"- **Last Updated**: {format_timestamp(close_time)}")
        
        output.append("")  # Blank line between symbols
    
    return "\n".join(output)


def format_symbols_markdown(symbols: List[Dict[str, Any]]) -> str:
    """Format symbol search results as Markdown"""
    if not symbols:
        return "No symbols found matching your criteria."
    
    output = [f"# Found {len(symbols)} Trading Pairs\n"]
    
    for sym in symbols:
        symbol = sym.get("symbol", "Unknown")
        status = sym.get("status", "Unknown")
        base = sym.get("baseAsset", "")
        quote = sym.get("quoteAsset", "")
        
        status_emoji = "✅" if status == "TRADING" else "⏸️"
        output.append(f"## {symbol} {status_emoji}")
        output.append(f"- **Base Asset**: {base}")
        output.append(f"- **Quote Asset**: {quote}")
        output.append(f"- **Status**: {status}")
        
        # Trading features
        features = []
        if sym.get("isSpotTradingAllowed"):
            features.append("Spot")
        if sym.get("isMarginTradingAllowed"):
            features.append("Margin")
        if sym.get("ocoAllowed"):
            features.append("OCO")
        if sym.get("otoAllowed"):
            features.append("OTO")
        
        if features:
            output.append(f"- **Supported**: {', '.join(features)}")
        
        output.append("")
    
    return "\n".join(output)


def format_order_book_markdown(data: Dict[str, Any], symbol: str) -> str:
    """Format order book data as Markdown"""
    output = [f"# Order Book for {symbol}\n"]
    
    bids = data.get("bids", [])
    asks = data.get("asks", [])
    
    output.append(f"**Last Update ID**: {data.get('lastUpdateId', 'N/A')}\n")
    
    # Top 10 bids and asks
    output.append("## Top Bids (Buy Orders)")
    output.append("| Price | Quantity | Total |")
    output.append("|-------|----------|-------|")
    
    for i, (price, qty) in enumerate(bids[:10]):
        total = float(price) * float(qty)
        output.append(f"| ${float(price):,.2f} | {float(qty):,.6f} | ${total:,.2f} |")
    
    output.append("\n## Top Asks (Sell Orders)")
    output.append("| Price | Quantity | Total |")
    output.append("|-------|----------|-------|")
    
    for i, (price, qty) in enumerate(asks[:10]):
        total = float(price) * float(qty)
        output.append(f"| ${float(price):,.2f} | {float(qty):,.6f} | ${total:,.2f} |")
    
    # Summary
    if bids and asks:
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100
        
        output.append(f"\n## Spread Analysis")
        output.append(f"- **Best Bid**: ${best_bid:,.2f}")
        output.append(f"- **Best Ask**: ${best_ask:,.2f}")
        output.append(f"- **Spread**: ${spread:,.2f} ({spread_pct:.3f}%)")
    
    output.append(f"\n*Showing top 10 levels. Total bids: {len(bids)}, Total asks: {len(asks)}*")
    
    return "\n".join(output)


def format_klines_markdown(klines: List[List], symbol: str, interval: str) -> str:
    """Format kline/candlestick data as Markdown"""
    if not klines:
        return f"No kline data found for {symbol} with interval {interval}."
    
    output = [f"# Candlestick Data for {symbol} ({interval} interval)\n"]
    output.append("| Time | Open | High | Low | Close | Volume | Change % |")
    output.append("|------|------|------|-----|-------|--------|----------|")
    
    for kline in klines[:50]:  # Show max 50 candles
        open_time = format_timestamp(kline[0])
        open_price = float(kline[1])
        high = float(kline[2])
        low = float(kline[3])
        close = float(kline[4])
        volume = float(kline[5])
        
        change_pct = ((close - open_price) / open_price) * 100 if open_price > 0 else 0
        change_emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
        
        output.append(
            f"| {open_time} | ${open_price:,.2f} | ${high:,.2f} | "
            f"${low:,.2f} | ${close:,.2f} | {volume:,.2f} | "
            f"{change_emoji} {change_pct:+.2f}% |"
        )
    
    # Summary
    if len(klines) > 0:
        first_candle = klines[0]
        last_candle = klines[-1]
        first_close = float(first_candle[4])
        last_close = float(last_candle[4])
        overall_change = ((last_close - first_close) / first_close) * 100 if first_close > 0 else 0
        
        output.append(f"\n## Period Summary")
        output.append(f"- **First Close**: ${first_close:,.2f}")
        output.append(f"- **Last Close**: ${last_close:,.2f}")
        output.append(f"- **Overall Change**: {overall_change:+.2f}%")
        output.append(f"- **Candles Shown**: {min(len(klines), 50)} of {len(klines)}")
    
    if len(klines) > 50:
        output.append(f"\n*Showing first 50 of {len(klines)} candles. Use start_time/end_time to get specific ranges.*")
    
    return "\n".join(output)


def format_trades_markdown(trades: List[Dict[str, Any]], symbol: str) -> str:
    """Format recent trades as Markdown"""
    if not trades:
        return f"No recent trades found for {symbol}."
    
    output = [f"# Recent Trades for {symbol}\n"]
    output.append("| Time | Price | Quantity | Total | Side |")
    output.append("|------|-------|----------|-------|------|")
    
    for trade in trades[:50]:  # Show max 50 trades
        time = format_timestamp(trade.get("time", 0))
        price = float(trade.get("price", 0))
        qty = float(trade.get("qty", 0))
        total = price * qty
        is_buyer_maker = trade.get("isBuyerMaker", False)
        side = "Sell" if is_buyer_maker else "Buy"
        side_emoji = "🔴" if is_buyer_maker else "🟢"
        
        output.append(
            f"| {time} | ${price:,.2f} | {qty:,.6f} | ${total:,.2f} | {side_emoji} {side} |"
        )
    
    # Summary
    buy_volume = sum(float(t["qty"]) for t in trades if not t.get("isBuyerMaker", False))
    sell_volume = sum(float(t["qty"]) for t in trades if t.get("isBuyerMaker", False))
    total_volume = buy_volume + sell_volume
    
    output.append(f"\n## Trading Summary")
    output.append(f"- **Total Trades**: {len(trades)}")
    output.append(f"- **Buy Volume**: {buy_volume:,.6f} ({(buy_volume/total_volume*100):.1f}%)" if total_volume > 0 else "- **Buy Volume**: 0")
    output.append(f"- **Sell Volume**: {sell_volume:,.6f} ({(sell_volume/total_volume*100):.1f}%)" if total_volume > 0 else "- **Sell Volume**: 0")
    
    if len(trades) > 50:
        output.append(f"\n*Showing 50 most recent of {len(trades)} trades.*")
    
    return "\n".join(output)


def format_price_markdown(prices: List[Dict[str, Any]]) -> str:
    """Format price data as Markdown"""
    if not prices:
        return "No price data found."
    
    output = ["# Current Prices\n"]
    
    for price_data in prices:
        symbol = price_data.get("symbol", "Unknown")
        price = price_data.get("price", "N/A")
        
        if price != "N/A":
            output.append(f"- **{symbol}**: ${float(price):,.2f}")
        else:
            output.append(f"- **{symbol}**: N/A")
    
    return "\n".join(output)


# ==================== MCP Tools ====================

@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def binance_get_ticker(params: TickerInput) -> str:
    """
    Get current price and 24-hour statistics for trading pairs.
    
    This tool retrieves real-time price information and 24-hour trading statistics
    for one or more cryptocurrency trading pairs on Binance. It provides comprehensive
    market data including price changes, volumes, and order book snapshots.
    
    Use this tool when:
    - User asks about current cryptocurrency prices
    - User wants to know 24-hour price changes or performance
    - User needs trading volume information
    - User wants to see bid/ask spreads
    - User asks "what's the price of BTC?" or similar queries
    
    Parameters:
    - symbols: List of trading pair symbols (e.g., ["BTCUSDT", "ETHUSDT"])
    - type: "FULL" for complete statistics or "MINI" for essential fields only
    - response_format: "markdown" (default, human-readable) or "json" (structured data)
    
    Returns:
    Current price, 24h change percentage, high/low prices, volume, and more.
    
    Error handling:
    - If symbol is invalid, suggests using binance_search_symbols to find valid pairs
    - If response is too large, automatically truncates with guidance
    - Provides actionable error messages for all failure modes
    
    Example usage:
    - binance_get_ticker(symbols=["BTCUSDT"])
    - binance_get_ticker(symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"], type="FULL")
    """
    try:
        # Build API request
        # Binance requires format: ["BTCUSDT","ETHUSDT"] with no spaces
        symbols_param = '["' + '","'.join(params.symbols) + '"]'
        api_params = {
            "symbols": symbols_param,
            "type": params.type
        }
        
        # Make API request
        data = await make_api_request("/api/v3/ticker/24hr", api_params)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        # Format response
        if params.response_format == "json":
            result = json.dumps({
                "data": data,
                "count": len(data),
                "type": params.type
            }, indent=2)
            return result
        else:
            formatted, truncated, _ = truncate_response(
                data,
                lambda d: format_ticker_markdown(d, params.type),
                len(data)
            )
            return formatted
    
    except Exception as e:
        return f"Error fetching ticker data: {str(e)}"


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def binance_search_symbols(params: SearchSymbolsInput) -> str:
    """
    Search for trading pairs by base asset, quote asset, or keyword.
    
    This tool helps discover available trading pairs on Binance by filtering
    based on base asset (e.g., BTC, ETH), quote asset (e.g., USDT, BUSD),
    or searching for specific keywords. Essential for finding exact symbol names.
    
    Use this tool when:
    - User doesn't know the exact trading pair symbol
    - User wants to explore all pairs for a specific cryptocurrency
    - User asks "what pairs are available for Bitcoin?"
    - User wants to find all USDT pairs
    - Before using other tools that require exact symbol names
    
    Parameters:
    - base_asset: Filter by base currency (e.g., "BTC", "ETH", "BNB")
    - quote_asset: Filter by quote currency (e.g., "USDT", "BUSD")
    - search_term: Keyword to search in symbol names (e.g., "DOGE")
    - status: "TRADING" (active pairs only) or "ALL" (including paused)
    - response_format: "markdown" (default) or "json"
    
    Returns:
    List of matching trading pairs with status, supported features, and asset details.
    
    Error handling:
    - Returns empty result if no symbols match filters
    - Automatically truncates large result sets with filtering guidance
    - Provides suggestions if search returns no results
    
    Example usage:
    - binance_search_symbols(base_asset="BTC")  # All BTC pairs
    - binance_search_symbols(quote_asset="USDT")  # All USDT pairs
    - binance_search_symbols(base_asset="BTC", quote_asset="USDT")  # Specific pair
    - binance_search_symbols(search_term="DOGE")  # Find DOGE-related pairs
    """
    try:
        # Get all exchange info
        data = await make_api_request("/api/v3/exchangeInfo")
        symbols = data.get("symbols", [])
        
        # Apply filters
        filtered_symbols = []
        for sym in symbols:
            # Status filter
            if params.status == "TRADING" and sym.get("status") != "TRADING":
                continue
            
            # Base asset filter
            if params.base_asset and sym.get("baseAsset") != params.base_asset:
                continue
            
            # Quote asset filter
            if params.quote_asset and sym.get("quoteAsset") != params.quote_asset:
                continue
            
            # Search term filter
            if params.search_term:
                symbol_name = sym.get("symbol", "")
                if params.search_term not in symbol_name:
                    continue
            
            filtered_symbols.append(sym)
        
        # Format response
        if params.response_format == "json":
            result = json.dumps({
                "symbols": filtered_symbols,
                "count": len(filtered_symbols),
                "filters": {
                    "base_asset": params.base_asset,
                    "quote_asset": params.quote_asset,
                    "search_term": params.search_term,
                    "status": params.status
                }
            }, indent=2)
            
            # Truncate if needed
            if len(result) > CHARACTER_LIMIT:
                truncated_count = max(10, len(filtered_symbols) // 2)
                truncated_data = filtered_symbols[:truncated_count]
                result = json.dumps({
                    "symbols": truncated_data,
                    "count": truncated_count,
                    "total_matches": len(filtered_symbols),
                    "truncated": True,
                    "message": f"Showing {truncated_count} of {len(filtered_symbols)} results. Add more specific filters."
                }, indent=2)
            
            return result
        else:
            formatted, truncated, _ = truncate_response(
                filtered_symbols,
                format_symbols_markdown,
                len(filtered_symbols)
            )
            return formatted
    
    except Exception as e:
        return f"Error searching symbols: {str(e)}"


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def binance_get_order_book(params: OrderBookInput) -> str:
    """
    Get order book depth (bids and asks) for a trading pair.
    
    This tool retrieves the current order book for a symbol, showing the best
    buy orders (bids) and sell orders (asks) at different price levels. Useful
    for analyzing market depth, liquidity, and identifying support/resistance.
    
    Use this tool when:
    - User wants to analyze buy/sell pressure
    - User needs to check market liquidity
    - User wants to see the bid-ask spread
    - User asks about order book depth or market depth
    - User wants to identify support and resistance levels
    
    Parameters:
    - symbol: Trading pair symbol (e.g., "BTCUSDT")
    - limit: Number of price levels (5, 10, 20, 50, 100, 500, 1000, 5000)
    - response_format: "markdown" (default) or "json"
    
    Returns:
    Order book with bid/ask prices and quantities, spread analysis, and depth summary.
    
    Error handling:
    - Validates limit parameter against allowed values
    - Suggests valid symbols if symbol is invalid
    - Shows top 10 levels in markdown format regardless of limit
    
    Example usage:
    - binance_get_order_book(symbol="BTCUSDT", limit=20)
    - binance_get_order_book(symbol="ETHUSDT", limit=100)
    """
    try:
        # Make API request
        api_params = {
            "symbol": params.symbol,
            "limit": params.limit
        }
        
        data = await make_api_request("/api/v3/depth", api_params)
        
        # Format response
        if params.response_format == "json":
            return json.dumps(data, indent=2)
        else:
            return format_order_book_markdown(data, params.symbol)
    
    except Exception as e:
        return f"Error fetching order book: {str(e)}"


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def binance_get_klines(params: KlinesInput) -> str:
    """
    Get candlestick/OHLC data for technical analysis.
    
    This tool retrieves historical price data in candlestick format, showing
    Open, High, Low, Close prices and volume for each time period. Essential
    for technical analysis, charting, and trend identification.
    
    Use this tool when:
    - User wants to perform technical analysis
    - User needs historical price data
    - User wants to see price trends over time
    - User asks for candlestick or OHLC data
    - User wants to analyze price patterns
    
    Parameters:
    - symbol: Trading pair symbol (e.g., "BTCUSDT")
    - interval: Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
    - limit: Number of candles to return (1-1000, default: 100)
    - start_time: Optional start timestamp in milliseconds
    - end_time: Optional end timestamp in milliseconds
    - response_format: "markdown" (default) or "json"
    
    Returns:
    Candlestick data with OHLC prices, volume, trade count, and change percentages.
    
    Error handling:
    - Validates interval against supported values
    - Shows max 50 candles in markdown format (full data in JSON)
    - Provides period summary with overall trend
    
    Example usage:
    - binance_get_klines(symbol="BTCUSDT", interval="1h", limit=24)  # Last 24 hours
    - binance_get_klines(symbol="ETHUSDT", interval="1d", limit=30)  # Last 30 days
    - binance_get_klines(symbol="BNBUSDT", interval="1w", limit=52)  # Last year
    """
    try:
        # Build API request
        api_params = {
            "symbol": params.symbol,
            "interval": params.interval,
            "limit": params.limit
        }
        
        if params.start_time:
            api_params["startTime"] = params.start_time
        if params.end_time:
            api_params["endTime"] = params.end_time
        
        # Make API request
        data = await make_api_request("/api/v3/klines", api_params)
        
        # Format response
        if params.response_format == "json":
            # Convert to more readable format
            formatted_klines = []
            for kline in data:
                formatted_klines.append({
                    "openTime": kline[0],
                    "open": kline[1],
                    "high": kline[2],
                    "low": kline[3],
                    "close": kline[4],
                    "volume": kline[5],
                    "closeTime": kline[6],
                    "quoteVolume": kline[7],
                    "trades": kline[8],
                    "takerBuyBaseVolume": kline[9],
                    "takerBuyQuoteVolume": kline[10]
                })
            
            return json.dumps({
                "symbol": params.symbol,
                "interval": params.interval,
                "klines": formatted_klines,
                "count": len(formatted_klines)
            }, indent=2)
        else:
            return format_klines_markdown(data, params.symbol, params.interval)
    
    except Exception as e:
        return f"Error fetching klines: {str(e)}"


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def binance_get_recent_trades(params: RecentTradesInput) -> str:
    """
    Get recent trades for a trading pair.
    
    This tool retrieves the most recent executed trades for a symbol, showing
    individual trade prices, quantities, timestamps, and whether the buyer or
    seller was the market maker. Useful for analyzing recent market activity.
    
    Use this tool when:
    - User wants to see recent market activity
    - User needs to analyze trade flow
    - User wants to check recent execution prices
    - User asks about recent trades or transactions
    - User wants to see buy vs sell pressure
    
    Parameters:
    - symbol: Trading pair symbol (e.g., "BTCUSDT")
    - limit: Number of trades to return (1-1000, default: 100)
    - response_format: "markdown" (default) or "json"
    
    Returns:
    Recent trades with price, quantity, time, side (buy/sell), and volume summary.
    
    Error handling:
    - Shows max 50 trades in markdown format (full data in JSON)
    - Provides trading summary with buy/sell volume breakdown
    
    Example usage:
    - binance_get_recent_trades(symbol="BTCUSDT", limit=50)
    - binance_get_recent_trades(symbol="ETHUSDT", limit=100)
    """
    try:
        # Make API request
        api_params = {
            "symbol": params.symbol,
            "limit": params.limit
        }
        
        data = await make_api_request("/api/v3/trades", api_params)
        
        # Format response
        if params.response_format == "json":
            return json.dumps({
                "symbol": params.symbol,
                "trades": data,
                "count": len(data)
            }, indent=2)
        else:
            return format_trades_markdown(data, params.symbol)
    
    except Exception as e:
        return f"Error fetching recent trades: {str(e)}"


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def binance_get_exchange_info(params: ExchangeInfoInput) -> str:
    """
    Get comprehensive exchange information and trading rules.
    
    This tool retrieves detailed information about Binance exchange including
    rate limits, trading rules, symbol filters, and permissions. Essential for
    understanding trading constraints and available features.
    
    Use this tool when:
    - User wants to understand trading rules
    - User needs to check rate limits
    - User wants to see available order types
    - User asks about exchange filters or constraints
    - User needs comprehensive symbol information
    
    Parameters:
    - symbols: Optional list of specific symbols to query (if omitted, returns all)
    - response_format: "markdown" (default) or "json"
    
    Returns:
    Exchange timezone, rate limits, trading rules, and symbol details.
    
    Error handling:
    - Truncates large responses with filtering guidance
    - Provides actionable information about trading constraints
    
    Example usage:
    - binance_get_exchange_info()  # All symbols
    - binance_get_exchange_info(symbols=["BTCUSDT", "ETHUSDT"])
    """
    try:
        # Build API request
        api_params = {}
        if params.symbols:
            # Binance requires format: ["BTCUSDT","ETHUSDT"] with no spaces
            api_params["symbols"] = '["' + '","'.join(params.symbols) + '"]'
        
        # Make API request
        data = await make_api_request("/api/v3/exchangeInfo", api_params)
        
        # Format response
        if params.response_format == "json":
            result = json.dumps(data, indent=2)
            
            # Truncate if needed
            if len(result) > CHARACTER_LIMIT:
                # Keep only essential fields
                simplified = {
                    "timezone": data.get("timezone"),
                    "serverTime": data.get("serverTime"),
                    "rateLimits": data.get("rateLimits", []),
                    "symbols": data.get("symbols", [])[:50],  # First 50 symbols
                    "truncated": True,
                    "message": "Response truncated. Specify symbols parameter for specific pairs."
                }
                result = json.dumps(simplified, indent=2)
            
            return result
        else:
            # Markdown format
            output = ["# Binance Exchange Information\n"]
            
            output.append(f"## General Information")
            output.append(f"- **Timezone**: {data.get('timezone', 'N/A')}")
            output.append(f"- **Server Time**: {format_timestamp(data.get('serverTime', 0))}\n")
            
            # Rate limits
            rate_limits = data.get("rateLimits", [])
            if rate_limits:
                output.append("## Rate Limits")
                for limit in rate_limits:
                    limit_type = limit.get("rateLimitType", "Unknown")
                    interval = limit.get("interval", "")
                    interval_num = limit.get("intervalNum", "")
                    limit_val = limit.get("limit", "")
                    output.append(f"- **{limit_type}**: {limit_val} per {interval_num} {interval}")
                output.append("")
            
            # Symbols
            symbols = data.get("symbols", [])
            output.append(f"## Trading Pairs ({len(symbols)} total)\n")
            
            if params.symbols:
                # Show detailed info for specific symbols
                formatted = format_symbols_markdown(symbols)
                output.append(formatted)
            else:
                # Show summary for all symbols
                if len(symbols) > 100:
                    output.append(f"*Too many symbols to display ({len(symbols)} total).*")
                    output.append(f"*Use 'symbols' parameter to get details for specific pairs.*")
                    output.append(f"\nExample: binance_get_exchange_info(symbols=['BTCUSDT', 'ETHUSDT'])")
                else:
                    formatted = format_symbols_markdown(symbols[:50])
                    output.append(formatted)
                    if len(symbols) > 50:
                        output.append(f"\n*Showing first 50 of {len(symbols)} symbols.*")
            
            result = "\n".join(output)
            
            # Check if too large
            if len(result) > CHARACTER_LIMIT:
                result = result[:CHARACTER_LIMIT] + "\n\n⚠️ Response truncated. Use symbols parameter for specific pairs."
            
            return result
    
    except Exception as e:
        return f"Error fetching exchange info: {str(e)}"


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def binance_get_price(params: PriceInput) -> str:
    """
    Get latest price for trading pairs (fast, lightweight query).
    
    This tool retrieves only the current price for one or more symbols without
    additional statistics. It's the fastest way to check prices when you don't
    need 24-hour statistics or other market data.
    
    Use this tool when:
    - User wants a quick price check
    - User only needs current prices (no statistics)
    - User wants to value a portfolio
    - User asks "what's the current price?" without needing more context
    - Speed is important over comprehensive data
    
    Parameters:
    - symbols: List of trading pair symbols (e.g., ["BTCUSDT", "ETHUSDT"])
    - response_format: "markdown" (default) or "json"
    
    Returns:
    Current price for each requested symbol.
    
    Error handling:
    - Suggests using binance_search_symbols if symbol is invalid
    - Handles multiple symbols efficiently
    
    Example usage:
    - binance_get_price(symbols=["BTCUSDT"])
    - binance_get_price(symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"])
    """
    try:
        # Build API request
        # Binance requires format: ["BTCUSDT","ETHUSDT"] with no spaces
        symbols_param = '["' + '","'.join(params.symbols) + '"]'
        api_params = {
            "symbols": symbols_param
        }
        
        # Make API request
        data = await make_api_request("/api/v3/ticker/price", api_params)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        # Format response
        if params.response_format == "json":
            return json.dumps({
                "prices": data,
                "count": len(data)
            }, indent=2)
        else:
            return format_price_markdown(data)
    
    except Exception as e:
        return f"Error fetching prices: {str(e)}"


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
async def binance_get_best_price(params: PriceInput) -> str:
    """
    Get best bid/ask prices from the order book (top of book).
    
    This tool retrieves the best available bid (buy) and ask (sell) prices
    with their quantities from the order book. Shows the tightest spread and
    immediate execution prices without fetching the full order book depth.
    
    Use this tool when:
    - User wants to check the current spread
    - User needs to estimate execution price
    - User wants to see immediate liquidity
    - User asks about best bid/ask prices
    - User wants order book top level without full depth
    
    Parameters:
    - symbols: List of trading pair symbols (e.g., ["BTCUSDT", "ETHUSDT"])
    - response_format: "markdown" (default) or "json"
    
    Returns:
    Best bid price/quantity and best ask price/quantity for each symbol.
    
    Error handling:
    - Handles multiple symbols efficiently
    - Provides spread analysis for each symbol
    
    Example usage:
    - binance_get_best_price(symbols=["BTCUSDT"])
    - binance_get_best_price(symbols=["BTCUSDT", "ETHUSDT"])
    """
    try:
        # Build API request
        # Binance requires format: ["BTCUSDT","ETHUSDT"] with no spaces
        symbols_param = '["' + '","'.join(params.symbols) + '"]'
        api_params = {
            "symbols": symbols_param
        }
        
        # Make API request
        data = await make_api_request("/api/v3/ticker/bookTicker", api_params)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        # Format response
        if params.response_format == "json":
            return json.dumps({
                "tickers": data,
                "count": len(data)
            }, indent=2)
        else:
            output = ["# Best Bid/Ask Prices\n"]
            
            for ticker in data:
                symbol = ticker.get("symbol", "Unknown")
                bid_price = float(ticker.get("bidPrice", 0))
                bid_qty = float(ticker.get("bidQty", 0))
                ask_price = float(ticker.get("askPrice", 0))
                ask_qty = float(ticker.get("askQty", 0))
                
                spread = ask_price - bid_price
                spread_pct = (spread / bid_price * 100) if bid_price > 0 else 0
                
                output.append(f"## {symbol}")
                output.append(f"- **Best Bid**: ${bid_price:,.2f} (Qty: {bid_qty:,.6f})")
                output.append(f"- **Best Ask**: ${ask_price:,.2f} (Qty: {ask_qty:,.6f})")
                output.append(f"- **Spread**: ${spread:,.2f} ({spread_pct:.3f}%)")
                output.append("")
            
            return "\n".join(output)
    
    except Exception as e:
        return f"Error fetching best prices: {str(e)}"


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()