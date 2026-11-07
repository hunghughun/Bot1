"""Test-only network interlock, inherited by Python subprocesses via PYTHONPATH.

No effect unless BOT1_TEST_OFFLINE=1. Never a replacement for an OS firewall.
"""
import os


def install() -> None:
    import socket

    if getattr(socket.socket, "_bot1_denied", False):
        return

    def denied(*args, **kwargs):
        raise RuntimeError("BOT1_OFFLINE_NETWORK_DISABLED")

    class DisabledSocket(socket.socket):
        _bot1_denied = True

        def __init__(self, *args, **kwargs):
            denied()

    socket.socket = DisabledSocket
    socket.SocketType = DisabledSocket
    import _socket
    _socket.socket = DisabledSocket
    socket.create_connection = denied
    socket.getaddrinfo = denied
    socket.gethostbyname = denied
    socket.gethostbyname_ex = denied


if os.environ.get("BOT1_TEST_OFFLINE") == "1":
    install()
