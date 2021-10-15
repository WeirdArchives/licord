from .constants import USER_AGENT_TEMPLATE
from http.client import HTTPSConnection

class Agent:
    def __init__(self):
        self._get_latest_client_info()
        self.user_agent = USER_AGENT_TEMPLATE.format(
            client_version=self.client_version)
        self.os_version = __import__("platform").version()

    def _get_latest_client_info(self):
        conn = HTTPSConnection("discord.com")

        # Get latest client version string.
        conn.request(
            method="GET",
            url="/api/updates/distributions/app/manifests/latest"
                "?channel=stable&platform=win&arch=x86")
        self.client_version = conn.getresponse().read()\
            .split(b'host_version": [', 1)[1]\
            .split(b"]", 1)[0]\
            .decode()\
            .replace(", ", ".")
        
        # Get latest client build number.
        conn.request(
            method="GET",
            url="/app")
        script_url = conn.getresponse().read()\
            .split(b'<script src="')[-2]\
            .split(b'"', 1)[0]\
            .decode()
        conn.request(
            method="GET",
            url=script_url)
        self.client_build_num = int(conn.getresponse().read()\
            .split(b'"buildNumber","', 1)[1]\
            .split(b'"', 1)[0]\
            .decode())

        conn.close()