import asyncio
from pathlib import Path
from typing import Sequence
import json

from mcp.server import Server, InitializationOptions, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, EmbeddedResource
from mcp.shared.exceptions import McpError

NOTES_DIR = Path("notes")
NOTES_DIR.mkdir(exist_ok=True)

server = Server("mcp-notes-server")

#### TOOL HANDLERS ####

def write_note(slug: str, content: str) -> str:
    note_path = NOTES_DIR / f"{slug}.txt"
    note_path.write_text(content.strip(), encoding="utf-8")
    return f"Note '{slug}' saved."

def list_notes(root: str | None = None) -> list[str]:
    all_slugs = [f"note://{f.stem}" for f in NOTES_DIR.glob("*.txt")]
    if root:
        return [slug for slug in all_slugs if slug.startswith(root)]
    return all_slugs

#### RESOURCE HANDLERS ####

def read_note(slug: str) -> str:
    note_path = NOTES_DIR / f"{slug}.txt"
    if not note_path.exists():
        return "Note not found."
    return note_path.read_text(encoding="utf-8")

#### PROMPT HANDLERS ####

def suggest_note_prompt(topic: str) -> str:
    return f"""
Write a short, thoughtful note for someone who needs advice about: {topic}
""".strip()

#### TOOL SCHEMAS ####

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="write_note",
            description="Save a note to the local notes directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Unique slug for the note"},
                    "content": {"type": "string", "description": "Content of the note"},
                },
                "required": ["slug", "content"],
            },
        ),
        Tool(
            name="list_notes",
            description="List all saved notes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "root": {"type": "string", "description": "Optional root URI filter"},
                },
                "required": [],
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent | EmbeddedResource]:
    try:
        match name:
            case "write_note":
                slug = arguments.get("slug")
                content = arguments.get("content")
                if not slug or not content:
                    raise ValueError("Missing slug or content.")
                result = write_note(slug, content)
                return [TextContent(type="text", text=result)]

            case "list_notes":
                root = arguments.get("root")
                result = list_notes(root)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            case _:
                raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        raise McpError(f"Error in tool '{name}': {str(e)}")

@server.get_resource()
async def get_resource(uri: str) -> EmbeddedResource:
    try:
        if uri.startswith("note://"):
            slug = uri.replace("note://", "")
            content = read_note(slug)
            return EmbeddedResource(
                uri=uri,
                content=TextContent(type="text", text=content),
            )
        raise McpError(f"Unknown resource URI: {uri}")
    except Exception as e:
        raise McpError(f"Error retrieving resource '{uri}': {str(e)}")

@server.get_prompt()
async def get_prompt(name: str, args: dict) -> str:
    if name == "suggest_note_prompt":
        topic = args.get("topic")
        if not topic:
            raise ValueError("Missing topic.")
        return suggest_note_prompt(topic)
    raise ValueError(f"Unknown prompt name: {name}")

#### ENTRYPOINT ####

async def main():
    options = InitializationOptions(
        server_name="mcp-notes-server",
        server_version="0.1.0",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        )
    )
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)

if __name__ == "__main__":
    asyncio.run(main())
