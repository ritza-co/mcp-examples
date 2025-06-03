from mcp.server import Server, stdio
import mcp.types as types

import asyncio

app = Server("git-prompts-server")


@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="git-commit",
            description="Generate a Git commit message from a code diff or change summary",
            arguments=[
                types.PromptArgument(
                    name="changes",
                    description="Code diff or explanation of the changes made",
                    required=True,
                )
            ],
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str]) -> types.GetPromptResult:
    if name != "git-commit":
        raise ValueError("Unknown prompt")

    changes = arguments.get("changes", "")

    return types.GetPromptResult(
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=(
                        "Generate a Git commit message summarizing these changes:\n\n"
                        f"{changes}"
                    ),
                ),
            )
        ]
    )


# -- Transport setup
async def main():
    async with stdio.stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())