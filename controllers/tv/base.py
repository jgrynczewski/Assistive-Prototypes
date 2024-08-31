import os
import time
import argparse

# pip3 install samsungtvws[async,encrypted]
# https://pypi.org/project/samsungtvws/
from samsungtvws import SamsungTVWS

IP = "192.168.100.121"


class RemoteController:
    def __init__(self, ip, port=8002):
        self.ip = ip
        self.port = port
        self.tv = self._initialize_connection()

    def _initialize_connection(self):
        token_file = os.path.dirname(os.path.realpath(__file__)) + '/tv-token.txt'
        return SamsungTVWS(host=self.ip, port=8002, token_file=token_file)

    def channel_up(self):
        self.tv.shortcuts().channel_up()

    def channel_down(self):
        self.tv.shortcuts().channel_down()

    def volume_up(self):
        self.tv.shortcuts().volume_up()

    def volume_down(self):
            self.tv.shortcuts().volume_down()

    def volume_down5(self):
        for item in range(5):
            self.tv.shortcuts().volume_down()
            time.sleep(1)

    def volume_up5(self):
        for item in range(5):
            self.tv.shortcuts().volume_up()
            time.sleep(1)

    def execute_operation(self, operation):
        if hasattr(self, operation):
            getattr(self, operation)()
        else:
            print(f"Unknown operation: {operation}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control your television.")
    parser.add_argument(
        'operation',
        choices=['channel_up', 'channel_down', 'volume_up', 'volume_down', 'volume_up5', 'volume_down5'],
        help="The operation to perform on the TV: channel_up, channel_down, "
             "volume_up, volume_down, volume_up3, volume_down3"
    )

    args = parser.parse_args()

    tv = RemoteController(IP)
    tv.execute_operation(args.operation)
