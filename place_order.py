from mcp.server import Server
from mcp import types
from mcp.server import stdio

import requests
import asyncio

app = Server("alpaca-order-server")

ALPACA_API_KEY = "your_api_key"
ALPACA_API_SECRET = "your_api_secret"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets/v2"

HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_API_SECRET,
    "Content-Type": "application/json",
}


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="place_stock_order",
            description="Place a stock trade via the Alpaca paper trading API",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "qty": {"type": "integer"},
                    "side": {"type": "string", "enum": ["buy", "sell"]},
                    "order_type": {"type": "string", "enum": ["market", "limit"]},
                    "time_in_force": {"type": "string", "enum": ["day", "gtc"]},
                    "limit_price": {"type": "number"},
                },
                "required": ["symbol", "qty", "side", "order_type", "time_in_force"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name != "place_stock_order":
        raise ValueError(f"Tool not found: {name}")

    symbol = arguments["symbol"].upper()
    qty = arguments["qty"]
    side = arguments["side"].lower()
    order_type = arguments["order_type"].lower()
    time_in_force = arguments["time_in_force"].lower()
    limit_price = arguments.get("limit_price")

    order_payload = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": order_type,
        "time_in_force": time_in_force,
    }

    if order_type == "limit" and limit_price:
        order_payload["limit_price"] = limit_price

    try:
        response = requests.post(
            f"{ALPACA_BASE_URL}/orders", headers=HEADERS, json=order_payload
        )
        data = response.json()
        message = f"Order placed: {side.upper()} {qty} {symbol} @ {order_type.upper()}"
        return [types.TextContent(type="text", text=message)]

    except Exception as e:
        error_msg = f"Failed to place order for {symbol}: {str(e)}"
        return [types.TextContent(type="text", text=error_msg)]


# -- Transport setup
async def main():
    async with stdio.stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
