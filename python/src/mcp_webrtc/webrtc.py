import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import anyio
import mcp.types as types
from aiortc import (
    RTCDataChannel,
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.signaling import (
    BYE,
    BaseSignaling,
)
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp.shared.message import SessionMessage
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WebRTCParameters(BaseModel):
    initiator: bool
    channel_name: str = "mcp"


@asynccontextmanager
async def webrtc_transport(
    signaling: BaseSignaling, params: WebRTCParameters
) -> AsyncGenerator[
    tuple[MemoryObjectReceiveStream[SessionMessage | Exception], MemoryObjectReceiveStream[SessionMessage]]
]:
    read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
    read_stream_writer: MemoryObjectSendStream[SessionMessage | Exception]

    write_stream: MemoryObjectSendStream[SessionMessage]
    write_stream_reader: MemoryObjectReceiveStream[SessionMessage]

    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    pc = RTCPeerConnection()

    async def consume_signaling() -> None:
        while True:
            obj = await signaling.receive()
            if isinstance(obj, RTCSessionDescription):
                await pc.setRemoteDescription(obj)
                if obj.type == "offer":
                    await pc.setLocalDescription(await pc.createAnswer())
                    await signaling.send(pc.localDescription)
            elif isinstance(obj, RTCIceCandidate):
                await pc.addIceCandidate(obj)
            elif obj is BYE:
                break

    async def message_writer() -> None:
        try:
            async with write_stream_reader:
                async for session_message in write_stream_reader:
                    json = session_message.message.model_dump_json(by_alias=True, exclude_none=True)
                    await channel_opened.wait()
                    channel.send(json)
        except anyio.ClosedResourceError:
            await anyio.lowlevel.checkpoint()

    async def message_handler(message) -> None:
        try:
            message = types.JSONRPCMessage.model_validate_json(message)
        except Exception as exc:
            await read_stream_writer.send(exc)
        await read_stream_writer.send(SessionMessage(message))

    await signaling.connect()
    channel_opened = asyncio.Event()
    channel_closed = asyncio.Event()
    if params.initiator:
        channel = pc.createDataChannel(params.channel_name)

        channel.on("message")(message_handler)

        @channel.on("open")
        def on_open() -> None:
            channel_opened.set()

        @channel.on("close")
        def on_close() -> None:
            channel_closed.set()

        await pc.setLocalDescription(await pc.createOffer())
        await signaling.send(pc.localDescription)
    else:
        channel = None

        @pc.on("datachannel")
        def on_datachannel(datachannel: RTCDataChannel) -> None:
            nonlocal channel
            channel = datachannel
            channel.on("message")(message_handler)
            channel_opened.set()

    async with anyio.create_task_group() as tg:
        tg.start_soon(consume_signaling)
        # messages are read via event listener
        tg.start_soon(message_writer)
        try:
            yield read_stream, write_stream
        finally:
            await write_stream.aclose()
            await read_stream.aclose()
            await pc.close()
            await signaling.close()
            tg.cancel_scope.cancel()


class WebRTCClientParameters(WebRTCParameters):
    initiator: bool = False


@asynccontextmanager
async def webrtc_client_transport(
    signaling: BaseSignaling,
    params: WebRTCClientParameters | None = None,
) -> AsyncGenerator[
    tuple[MemoryObjectReceiveStream[SessionMessage | Exception], MemoryObjectReceiveStream[SessionMessage]]
]:
    async with webrtc_transport(signaling=signaling, params=params or WebRTCClientParameters()) as (
        read,
        write,
    ):
        yield read, write


class WebRTCServerParameters(WebRTCParameters):
    initiator: bool = True


@asynccontextmanager
async def webrtc_server_transport(
    signaling: BaseSignaling,
    params: WebRTCServerParameters | None = None,
) -> AsyncGenerator[
    tuple[MemoryObjectReceiveStream[SessionMessage | Exception], MemoryObjectReceiveStream[SessionMessage]]
]:
    async with webrtc_transport(signaling=signaling, params=params or WebRTCServerParameters()) as (
        read,
        write,
    ):
        yield read, write
