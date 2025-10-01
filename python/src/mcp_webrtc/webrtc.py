import asyncio
import logging
from contextlib import asynccontextmanager

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from pydantic import BaseModel
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import (
    BYE,
    BaseSignaling,
)
from mcp.shared.message import SessionMessage
import mcp.types as types

logger = logging.getLogger(__name__)


class WebRTCParameters(BaseModel):
    initiator: bool = False


@asynccontextmanager
async def webrtc_transport(
    signaling: BaseSignaling, params: WebRTCParameters = WebRTCParameters()
):
    read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
    read_stream_writer: MemoryObjectSendStream[SessionMessage | Exception]

    write_stream: MemoryObjectSendStream[SessionMessage]
    write_stream_reader: MemoryObjectReceiveStream[SessionMessage]

    read_stream_writer, read_stream = anyio.create_memory_object_stream(10)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(10)

    pc = RTCPeerConnection()

    async def consume_signaling():
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

    async def message_writer():
        try:
            async with write_stream_reader:
                async for session_message in write_stream_reader:
                    json = session_message.message.model_dump_json(
                        by_alias=True, exclude_none=True
                    )
                    await channel_opened.wait()
                    channel.send(json)
        except anyio.ClosedResourceError:
            await anyio.lowlevel.checkpoint()

    await signaling.connect()
    channel_opened = asyncio.Event()
    channel_closed = asyncio.Event()
    if params.initiator:
        channel = pc.createDataChannel("mcp")

        @channel.on("message")
        def on_message(message):
            try:
                message = types.JSONRPCMessage.model_validate_json(message)
            except Exception as exc:
                read_stream_writer.send_nowait(exc)
            read_stream_writer.send_nowait(SessionMessage(message))

        @channel.on("open")
        def on_open():
            channel_opened.set()

        @channel.on("close")
        def on_close():
            channel_closed.set()

        await pc.setLocalDescription(await pc.createOffer())
        await signaling.send(pc.localDescription)
    else:
        channel = None

        @pc.on("datachannel")
        def on_datachannel(datachannel):
            nonlocal channel
            channel = datachannel
            channel_opened.set()

            @channel.on("message")
            def on_message(message):
                try:
                    message = types.JSONRPCMessage.model_validate_json(message)
                except Exception as exc:
                    read_stream_writer.send_nowait(exc)
                read_stream_writer.send_nowait(SessionMessage(message))

    async with anyio.create_task_group() as tg:
        tg.start_soon(consume_signaling)
        # messages are read via event listener
        tg.start_soon(message_writer)
        try:
            yield read_stream, write_stream
        finally:
            await write_stream_reader.aclose()
            await write_stream.aclose()
            await read_stream_writer.aclose()
            await read_stream.aclose()
            await pc.close()
            await signaling.close()
            tg.cancel_scope.cancel()


@asynccontextmanager
async def webrtc_client_transport(
    signaling: BaseSignaling,
    params: WebRTCParameters = WebRTCParameters(initiator=False),
):
    async with webrtc_transport(signaling=signaling, params=params) as (read, write):
        yield read, write


@asynccontextmanager
async def webrtc_server_transport(
    signaling: BaseSignaling,
    params: WebRTCParameters = WebRTCParameters(initiator=True),
):
    async with webrtc_transport(signaling=signaling, params=params) as (read, write):
        yield read, write
