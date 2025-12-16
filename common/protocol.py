# common/protocol.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Tuple


class ProtocolError(Exception):
    pass


def encode_message(payload: Dict[str, Any]) -> bytes:
    try:
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")
    except Exception as e:
        raise ProtocolError(f"encode_message failed: {e}") from e


def decode_message(raw: bytes) -> Dict[str, Any]:
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise ProtocolError(f"decode_message failed: {e}") from e


@dataclass(frozen=True)
class PeerEndpoint:
    host: str
    port: int

    def as_tuple(self) -> Tuple[str, int]:
        return (self.host, self.port)


def get_advertised_endpoint(msg: Dict[str, Any], fallback_addr: Tuple[str, int]) -> PeerEndpoint:
    host = msg.get("host") or fallback_addr[0]
    port = msg.get("port") or fallback_addr[1]
    try:
        port_i = int(port)
    except Exception as e:
        raise ProtocolError(f"Invalid port in message: {port}") from e
    return PeerEndpoint(host=host, port=port_i)
