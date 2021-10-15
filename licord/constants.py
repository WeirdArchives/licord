USER_AGENT_TEMPLATE = ("Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) discord/{client_version} Chrome/91.0.4472.164 "
                       "Electron/13.4.0 Safari/537.36")

PROXY_CONNECT_REQUEST = (
    "CONNECT gateway.discord.gg:443 HTTP/1.1\r\n"
    "{headers}"
    "\r\n")
GATEWAY_UPGRADE_REQUEST = (
    "GET /?encoding=etf&v=9&compress=zlib-stream HTTP/1.1\r\n"
    "Host: gateway.discord.gg\r\n"
    "Connection: Upgrade\r\n"
    "Pragma: no-cache\r\n"
    "Cache-Control: no-cache\r\n"
    "User-Agent: {user_agent}\r\n"
    "Upgrade: websocket\r\n"
    "Origin: https://discord.com\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "Accept-Encoding: gzip, deflate, br\r\n"
    "Accept-Language: en-US\r\n"
    "Sec-WebSocket-Key: {websocket_key}\r\n"
    "Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits\r\n"
    "\r\n")