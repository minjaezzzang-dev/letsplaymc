import os
import random
import re
import socket
import struct
import string
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from backend.log import logger

_RCON_PORT = 25575
_PASSWORD_LEN = 16

_PACKET_AUTH = 3
_PACKET_COMMAND = 2
_PACKET_RESPONSE = 0


@dataclass
class RCONConnection:
    host: str = "127.0.0.1"
    port: int = _RCON_PORT
    password: str = ""
    _sock: socket.socket | None = None
    _request_id: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def connect(self) -> None:
        if self._sock:
            return
        self._sock = socket.create_connection((self.host, self.port), timeout=5)
        self._authenticate()

    def _authenticate(self) -> None:
        self._request_id = random.randint(1, 2**31 - 1)
        payload = struct.pack("<ii", self._request_id, _PACKET_AUTH)
        payload += self.password.encode("utf-8") + b"\x00\x00"
        self._sock.sendall(struct.pack("<i", len(payload)) + payload)
        _, resp_id = self._recv_packet()
        if resp_id == -1:
            raise PermissionError("RCON authentication failed")

    def _recv_packet(self) -> tuple[int, int, bytes]:
        raw_len = self._sock.recv(4)
        if len(raw_len) < 4:
            raise ConnectionError("RCON connection closed")
        length = struct.unpack("<i", raw_len)[0]
        data = b""
        while len(data) < length:
            chunk = self._sock.recv(length - len(data))
            if not chunk:
                raise ConnectionError("RCON connection closed")
            data += chunk
        req_id, pkt_type = struct.unpack("<ii", data[:8])
        body = data[8:-2]
        return pkt_type, req_id, body

    def command(self, cmd: str, retries: int = 5, retry_delay: float = 3.0) -> str:
        last_error = None
        for attempt in range(retries):
            try:
                with self._lock:
                    self.connect()
                    self._request_id += 1
                    payload = struct.pack("<ii", self._request_id, _PACKET_COMMAND)
                    payload += cmd.encode("utf-8") + b"\x00\x00"
                    self._sock.sendall(struct.pack("<i", len(payload)) + payload)

                    _, _, body = self._recv_packet()
                    return body.decode("utf-8", errors="replace")
            except (ConnectionError, OSError, PermissionError) as e:
                last_error = e
                self.close()
                if attempt < retries - 1:
                    time.sleep(retry_delay)
        raise last_error or ConnectionError("RCON command failed")

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None


def generate_rcon_password() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=_PASSWORD_LEN))


def setup_rcon_properties(server_dir: str, password: str) -> None:
    prop_file = os.path.join(server_dir, "server.properties")
    if not os.path.exists(prop_file):
        return

    with open(prop_file, "r") as f:
        lines = f.read().splitlines()

    settings_map = {
        "enable-rcon": "true",
        "rcon.password": password,
        "rcon.port": str(_RCON_PORT),
    }

    new_lines = []
    found = set()
    for line in lines:
        if "=" in line:
            key = line.split("=")[0].strip()
            if key in settings_map:
                new_lines.append(f"{key}={settings_map[key]}")
                found.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    for key, val in settings_map.items():
        if key not in found:
            new_lines.append(f"{key}={val}")

    with open(prop_file, "w") as f:
        f.write("\n".join(new_lines))


_rcon_instances: dict[str, RCONConnection] = {}
_rcon_passwords: dict[str, str] = {}


def get_rcon(name: str) -> RCONConnection | None:
    return _rcon_instances.get(name)


def init_server_rcon(name: str, server_dir: str) -> RCONConnection:
    password = generate_rcon_password()
    _rcon_passwords[name] = password
    setup_rcon_properties(server_dir, password)

    rcon = RCONConnection(password=password)
    _rcon_instances[name] = rcon
    logger.info("RCON initialized for server %s", name)
    return rcon


def close_rcon(name: str) -> None:
    rcon = _rcon_instances.pop(name, None)
    if rcon:
        rcon.close()
    _rcon_passwords.pop(name, None)


def parse_player_list(response: str) -> list[dict]:
    """Parse the output of the Minecraft `list` command.
    
    Format: "There are 3 of a max of 20 players online: Steve, Alex, Notch"
    Returns empty list if no players are online.
    """
    if ":" not in response:
        return []
    names_part = response.split(":")[-1].strip()
    if not names_part:
        return []
    return [{"name": n.strip()} for n in names_part.split(",") if n.strip()]


def parse_player_data(response: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for line in response.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            data[key.strip().lower().replace(" ", "_")] = val.strip()
    return data


def extract_inventory(response: str) -> list[dict]:
    """Extract inventory items from `/data get entity <player>` NBT response.

    Returns list of dicts with keys: id, Count, Slot (optional).
    Unrecognized NBT keys are included as-is.
    """
    body = response
    if "entity data:" in response:
        body = response.split("entity data:", 1)[-1].strip()

    items = []
    depth = 0
    current = ""
    in_string = False

    for char in body:
        if char == '"':
            in_string = not in_string
        if not in_string:
            if char == '{':
                if depth == 0:
                    current = ""
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and current.strip():
                    item = _parse_nbt_compound("{" + current.strip() + "}")
                    if "id" in item:
                        items.append(item)
                    current = ""
                    continue
        if depth > 0:
            current += char

    return items


def _parse_nbt_compound(text: str) -> dict:
    """Parse a simple NBT compound like {id:\"stone\",Count:64b} into a dict."""
    result = {}
    inner = text.strip("{} ")
    if not inner:
        return result
    for part in _split_nbt_pairs(inner):
        if ":" not in part:
            continue
        key, _, val = part.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        else:
            val = re.sub(r'[bBsSlLfFdD]$', '', val)
        result[key] = val
    return result


def _split_nbt_pairs(text: str) -> list:
    """Split NBT compound contents on commas, respecting nesting and strings."""
    parts = []
    depth = 0
    in_str = False
    current = ""
    for ch in text:
        if ch == '"':
            in_str = not in_str
        if not in_str:
            if ch in ("{", "["):
                depth += 1
            elif ch in ("}", "]"):
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append(current)
                current = ""
                continue
        current += ch
    if current.strip():
        parts.append(current)
    return parts
