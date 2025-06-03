import asyncio
from mcp.server import FastMCP
from mcp import types
from mcp.server import stdio
from mcp.server import InitializationOptions, NotificationOptions
from pydantic import AnyUrl
import requests

app = FastMCP("stock-earnings-server")


@app.resource("stock://{symbol}/earnings")
async def list_resources_handler() -> list[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            uriTemplate="stock://{symbol}/earnings",
            name="Stock Earnings",
            description="Quarterly and annual earnings for a given stock symbol",
            mimeType="application/json",
        )
    ]


@app.resource("stock://{symbol}/earnings")
async def read_resource_handler(uri: AnyUrl) -> str:
    parsed = str(uri)

    if not parsed.startswith("stock://") or not parsed.endswith("/earnings"):
        raise ValueError("Unsupported resource URI")

    symbol = parsed.split("://")[1].split("/")[0].upper()

    url = (
        "https://www.alphavantage.co/query"
        "?function=EARNINGS"
        f"&symbol={symbol}"
        "&apikey=demo"
    )

    response = requests.get(url)
    return response.text


# -- Transport setup
async def serve():
    async with stdio.stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())