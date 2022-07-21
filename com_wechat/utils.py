import socket


def get_free_port():
    s = socket.socket()
    s.bind(("", 0))
    ip, port = s.getsockname()
    s.close()
    return port
