import asyncio
from asyncio import Queue
from collections.abc import Generator
from typing import Any, Optional

import mcp.types as types
import pytest
from aiortc.contrib.signaling import BYE, BaseSignaling, _SignalingObject
from mcp import ClientSession
from mcp.server.lowlevel import Server
from mcp_webrtc import webrtc_client_transport, webrtc_server_transport


class MemorySignaling(BaseSignaling):
    def __init__(
        self,
        *,
        read_queue: Queue[_SignalingObject],
        write_queue: Queue[_SignalingObject],
    ) -> None:
        super().__init__()
        self.read_queue = read_queue
        self.write_queue = write_queue

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        await self.write_queue.put(BYE)

    async def send(self, descr: _SignalingObject) -> None:
        await self.write_queue.put(descr)

    async def receive(self) -> _SignalingObject | None:
        return await self.read_queue.get()


@pytest.fixture
def signaling_pair() -> Generator[tuple[MemorySignaling, MemorySignaling]]:
    wire_one = Queue()
    wire_two = Queue()
    yield (
        MemorySignaling(read_queue=wire_one, write_queue=wire_two),
        MemorySignaling(read_queue=wire_two, write_queue=wire_one),
    )


@pytest.fixture
def greeter_server() -> Generator[Server]:
    app = Server("mcp-greeter")

    @app.call_tool()
    async def greet_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        if name != "greet":
            raise ValueError(f"Unknown tool: {name}")
        return "Howdy!"

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="greet",
                description="Greets the caller",
                inputSchema={
                    "type": "object",
                    "required": [],
                    "properties": {},
                },
            )
        ]

    yield app


@pytest.mark.asyncio
async def test_transport(signaling_pair: tuple[MemorySignaling, MemorySignaling], greeter_server: Server) -> None:
    client_signaling, server_signaling = signaling_pair

    async with webrtc_server_transport(server_signaling) as (read, write):
        server_task = asyncio.create_task(
            greeter_server.run(read, write, greeter_server.create_initialization_options())
        )

        async with (
            webrtc_client_transport(client_signaling) as (
                read,
                write,
            ),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            result = await session.list_tools()
            assert result.tools[0].name == "greet"

        await server_task
