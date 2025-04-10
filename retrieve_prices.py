import asyncio
from mcp.server import Server
from mcp import types
from mcp.server import stdio
from mcp.server import InitializationOptions, NotificationOptions
from pydantic import AnyUrl
import requests

app = Server("stock-earnings-server")


@app.list_resources()
async def list_resources() -> list[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            uriTemplate="stock://{symbol}/earnings",
            name="Stock Earnings",
            description="Quarterly and annual earnings for a given stock symbol",
            mimeType="application/json",
        )
    ]


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
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
async def main():
    async with stdio.stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
