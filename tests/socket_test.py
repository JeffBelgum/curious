import curio
from curious import socket


def test_create_tls_socket():
    certfile = "cert/bn.pem"
    keyfile = "cert/bn.key"
    curio.run(
        socket.create_server,
        ("localhost", 8081),
        certfile,
        keyfile,
    )
