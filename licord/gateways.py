from .constants import PROXY_CONNECT_REQUEST, GATEWAY_UPGRADE_REQUEST
from .utils import parse_proxy_string, create_ssl_context
from .exceptions import *
from .agents import get_latest_windows_client_agent
from base64 import b64encode
from os import urandom
import threading
import logging
import time
import socket
import zlib
import erlpack

class Gateway:
    _ssl_context = create_ssl_context()

    def __init__(self,
                 token, agent=get_latest_windows_client_agent(),
                 connect_timeout=5, read_timeout=60,
                 reconnect_delay=2, http_proxy=None):
        self.token = token
        self.agent = agent
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.reconnect_delay = reconnect_delay

        self._http_proxy = http_proxy and parse_proxy_string(http_proxy)
        self._zlib_inflator = None
        self._ack_interval = None
        self._ack_thread = None
        self._last_sq_num = None
        self._sock = None

        self._connect()

    def __enter__(self):
        return self
    
    def __exit__(self, *_):
        self.close()

    def close(self):
        if self._ack_thread:
            self._ack_thread = None
        
        if self._sock:
            try:
                self._sock.shutdown(2)
            except OSError:
                pass
            self._sock.close()

    def send(self, data):
        if not isinstance(data, bytes):
            data = erlpack.pack(data)
    
        key = urandom(4)
        length = len(data)
        masked_data = bytes(
            data[i] ^ key[i % 4]
            for i in range(length))
        header = b"\x82"

        if length < 126:
            header += bytes([length + 128])
        elif length < 65536:
            header += b"\xfe" + length.to_bytes(2, "big")
        else:
            header += b"\xff" + length.to_bytes(8, "big")
        
        try:
            self._sock.sendall(header + key + masked_data)

        except Exception as err:
            logging.warn(f"Error while sending: {err!r}")
            self._connect()
            return self.send(data)

    def recv(self):
        try:
            buf = None
            buf = self._sock.recv(1048576)
            data_length = buf[1] & 0x7f
            buf = buf[2:]
            
            if data_length == 126:
                data_length = int.from_bytes(buf[:2], "big")
                buf = buf[2:]

            while len(buf) < data_length:
                ch = self._sock.recv(data_length - len(buf))
                buf += ch

            if buf.endswith(b"\x00\x00\xff\xff"):
                buf = self._zlib_inflator.decompress(buf)

            if buf == b"\x0f\xa4Authentication failed.":
                raise AuthenticationFailed()

            payload = erlpack.unpack(buf)

        except LicordError:
            raise
            
        except Exception as err:
            logging.warn(f"Error while receiving: {err!r} (Buf: {buf and buf[:1024]}")
            self._connect()
            return self.recv()

        if payload.get("s") and (
                not self._last_sq_num
                or payload["s"] > self._last_sq_num
            ):
            self._last_sq_num = payload["s"]

        if payload.get("op") == 9:
            logging.info("Opcode 9 raised")
            self._connect()
            return self.recv()

        return payload

    def _authenticate(self):
        self.send({
            "op": 2,
            "d": {
                "token": self.token,
                "capabilities": 125,
                "properties": {
                    "os": "Windows",
                    "browser": "Discord Client",
                    "release_channel": "stable",
                    "client_version": self.agent.client_version,
                    "os_version": self.agent.os_version,
                    "os_arch": "x64",
                    "system_locale": "en-US",
                    "client_build_number": self.agent.client_build_num,
                    "client_event_source": None
                },
                "presence": {
                    "status": "online",
                    "since": 0,
                    "activities": [],
                    "afk": False
                },
                "compress": False,
                "client_state": {
                    "guild_hashes": {},
                    "highest_last_message_id": "0",
                    "read_state_version": 0,
                    "user_guild_settings_version": -1
                }
            }
        })

    def _ack_sender(self):
        time.sleep(self._ack_interval)
        while self._ack_thread:
            try:
                self.send({"op": 1, "d": self._last_sq_num})
            except Exception as err:
                logging.warning(f"Error while sending ACK: {err!r}")
            time.sleep(self._ack_interval)

    def _connect(self):
        if self._sock:
            try:
                self._sock.shutdown(2)
            except OSError:
                pass
            self._sock.close()
            time.sleep(self.reconnect_delay)
            logging.debug("Reconnecting to gateway.")
        else:
            logging.debug("Connecting to gateway.")

        self._last_sq_num = None
        self._zlib_inflator = zlib.decompressobj()
        self._sock = socket.socket()
        self._sock.settimeout(self.connect_timeout)

        if not self._http_proxy:
            # Connect socket to gateway.
            self._sock.connect(("gateway.discord.gg", 443))
        else:
            # Connect socket to gateway through proxy tunnel.
            proxy_auth, proxy_addr = self._http_proxy
            self._sock.connect(proxy_addr)
            self._sock.sendall(PROXY_CONNECT_REQUEST\
                .format(
                    headers=f"Proxy-Authorization: {proxy_auth}\r\n" \
                            if proxy_auth else "")
                .encode())
            if self._sock.recv(4096).split(b" ", 2)[1] != b"200":
                raise Exception("HTTP proxy refused CONNECT request.")

        # Add SSL encryption to connection.
        self._sock = self._ssl_context.wrap_socket(
            sock=self._sock,
            do_handshake_on_connect=False,
            suppress_ragged_eofs=False,
            server_hostname="gateway.discord.gg")
        self._sock.do_handshake()

        # Upgrade protocol to WebSocket.
        websocket_key = b64encode(urandom(16)).decode()
        self._sock.sendall(GATEWAY_UPGRADE_REQUEST\
            .format(
                user_agent=self.agent.user_agent,
                websocket_key=websocket_key)\
            .encode())
        self._sock.recv(4096)

        # Wait for ACK Hello payload and start thread.
        while (payload := self.recv())["op"] != 10:
            pass
        self._ack_interval = payload["d"]["heartbeat_interval"]/1000
        if not self._ack_thread:
            self._ack_thread = threading.Thread(target=self._ack_sender)
            self._ack_thread.start()

        self._sock.settimeout(self.read_timeout)
        self._authenticate()