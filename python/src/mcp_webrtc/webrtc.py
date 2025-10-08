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


WebRTCTransportStreams = tuple[
    MemoryObjectReceiveStream[SessionMessage | Exception], MemoryObjectReceiveStream[SessionMessage]
]


@asynccontextmanager
async def webrtc_transport(
    signaling: BaseSignaling, params: WebRTCParameters
) -> AsyncGenerator[WebRTCTransportStreams]:
    read_stream_consumer: MemoryObjectReceiveStream[SessionMessage | Exception]
    read_stream_producer: MemoryObjectSendStream[SessionMessage | Exception]

    write_stream_producer: MemoryObjectSendStream[SessionMessage]
    write_stream_consumer: MemoryObjectReceiveStream[SessionMessage]

    read_stream_producer, read_stream_consumer = anyio.create_memory_object_stream(0)
    write_stream_producer, write_stream_consumer = anyio.create_memory_object_stream(0)

    pc = RTCPeerConnection()
    channel: RTCDataChannel | None = None
    channel_opened = asyncio.Event()

    async def consume_signaling() -> None:
        logger.debug("Signaling reception started")
        try:
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
        except anyio.get_cancelled_exc_class() as exc:
            logger.debug(f"Signalling reception has been cancelled: {exc}")
            raise
        finally:
            logger.debug("Signaling reception ended")

    async def forward_write_stream() -> None:
        logger.debug("Write stream forwarding started")
        try:
            await channel_opened.wait()
            async for session_message in write_stream_consumer:
                json = session_message.message.model_dump_json(by_alias=True, exclude_none=True)
                channel.send(json)
        except anyio.get_cancelled_exc_class() as exc:
            logger.debug(f"Write stream forwarding has been cancelled: {exc}")
            raise
        finally:
            logger.debug("Write stream forwarding ended")

    async def forward_message_to_read_stream(message: str | bytes) -> None:
        try:
            message = types.JSONRPCMessage.model_validate_json(message)
        except Exception as exc:
            await read_stream_producer.send(exc)
        await read_stream_producer.send(SessionMessage(message))

    async def on_channel_open() -> None:
        channel_opened.set()

    async def on_channel_close() -> None:
        await read_stream_producer.aclose()
        await write_stream_consumer.aclose()

    async def init_pc() -> None:
        nonlocal channel
        if params.initiator:
            channel = pc.createDataChannel(params.channel_name)
            channel.on("message")(forward_message_to_read_stream)
            channel.on("open")(on_channel_open)
            channel.on("close")(on_channel_close)
            await pc.setLocalDescription(await pc.createOffer())
            await signaling.send(pc.localDescription)
        else:

            @pc.on("datachannel")
            async def on_datachannel(datachannel: RTCDataChannel) -> None:
                nonlocal channel
                channel = datachannel
                channel.on("message")(forward_message_to_read_stream)
                channel.on("close")(on_channel_close)
                await on_channel_open()

    await signaling.connect()
    async with (
        anyio.create_task_group() as tg,
        read_stream_producer,
        read_stream_consumer,
        write_stream_producer,
        write_stream_consumer,
    ):
        await init_pc()
        tg.start_soon(consume_signaling)
        tg.start_soon(forward_write_stream)
        try:
            yield read_stream_consumer, write_stream_producer
        finally:
            await pc.close()
            await signaling.close()
            tg.cancel_scope.cancel()


class WebRTCClientParameters(WebRTCParameters):
    initiator: bool = False


@asynccontextmanager
async def webrtc_client_transport(
    signaling: BaseSignaling,
    params: WebRTCClientParameters | None = None,
) -> AsyncGenerator[WebRTCTransportStreams]:
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
) -> AsyncGenerator[WebRTCTransportStreams]:
    async with webrtc_transport(signaling=signaling, params=params or WebRTCServerParameters()) as (
        read,
        write,
    ):
        yield read, write
