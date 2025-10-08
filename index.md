# WebRTC Transport for Model Context Protocol

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard designed to connect AI applications to external systems, such as tools and data sources. It currently supports two transport mechanisms for client-server communication: STDIO (via standard input/output) and Streamable HTTP (for network-based connectivity).

However, certain environments—such as web browsers or networks behind firewalls—pose challenges where neither STDIO nor Streamable HTTP can reliably establish a connection between an MCP client and server. In these situations, WebRTC offers a robust peer-to-peer alternative. [WebRTC](https://webrtc.org/) enables real-time communication by leveraging ICE (Interactive Connectivity Establishment) for NAT traversal, provided a signaling channel (e.g., via WebSockets or another mechanism) is available to facilitate the initial peer negotiation.

## Problem

Imagine a scenario where a remote MCP client must connect to a local MCP server to provide contextual data for an AI application or agent. For instance, a remote [A2A](https://a2a-protocol.org) agent requires access to the filesystem on a user's desktop machine where the A2A client is executing.

This setup introduces two primary challenges: **network connectivity** and **security**.

- **Network Connectivity**: Ideally, the MCP server could be exposed via Streamable HTTP, allowing the client to connect over the network. However, this requires the server to have a publicly accessible IP address, which is often not feasible due to NATs, firewalls, or private networks.
- **Security**: Even if connectivity is established, the server must authenticate the client to ensure only authorized parties can connect. In contrast, STDIO transport inherently avoids these issues since it operates locally without network exposure.

In essence, the goal is to create a setup that mimics the simplicity and security of STDIO but functions over the network—without relying on public IPs—and ensures secure, authenticated communication between peers.

## Solution

WebRTC addresses these challenges effectively by enabling direct peer-to-peer connections:

- **NAT Traversal and Connectivity**: Peers negotiate ICE candidates using STUN (Session Traversal Utilities for NAT) servers to punch holes through NATs and firewalls, establishing a direct connection without needing public IP addresses.
- **Secure Communication**: WebRTC uses DTLS (Datagram Transport Layer Security) to encrypt data channels, ensuring end-to-end security. Authentication is also handled by DTLS based on certificate fingerprints exchanged during the signaling phase.
- **Data Transmission**: WebRTC's data channels support bidirectional transmission of arbitrary binary or text data. For MCP, this can carry JSON-RPC messages, which form the core of the protocol's communication.

This approach assumes an existing signaling channel (e.g., via A2A protocols, WebSockets, or another out-of-band method) to exchange session descriptions (SDPs) and ICE candidates between the peers.
By implementing WebRTC as a transport layer for MCP, we can achieve seamless, secure connectivity in restricted environments while maintaining the protocol's flexibility.

## Additional Use Cases

WebRTC also shines in environments where traditional port-binding APIs are unavailable, such as web browsers. In these cases, Streamable HTTP may not be viable, but WebRTC's APIs remain accessible for peer-to-peer communication.

Note that the current JavaScript MCP library relies on Node.js-specific APIs, which may limit browser compatibility. To fully leverage WebRTC in browser-based scenarios, the library would need updates to support browser-native APIs.
