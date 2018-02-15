from curio import socket, spawn, ssl
import h2


async def create_tls_socket(address, certfile, keyfile):
    """
    Create and return a TLS socket listening on a given address.
    """
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.options |= ssl.OP_NO_TLSv1
    ssl_context.options |= ssl.OP_NO_TLSv1_1
    ssl_context.options |= ssl.OP_NO_COMPRESSION
    ssl_context.set_ciphers("ECDHE+AESGCM")
    ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    ssl_context.set_alpn_protocols(["h2", "http/1.1"])
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock = await ssl_context.wrap_socket(sock, server_side=True)
    sock.bind(address)
    sock.listen()
    return sock


async def create_server(address, certfile, keyfile):
    sock = await create_tls_socket(address, certfile, keyfile)

    async with sock:
        while True:
            client, raddr = await sock.accept()
            print(client.selected_alpn_protocol())
            # print(dir(client))
            # print(f"Accepting {client}, {raddr}")
            server = Server(client)
            await spawn(server.run())


class Server:
    def __init__(self, sock):
        self.sock = sock
        config = h2.config.H2Configuration(
            client_side=False,
            header_encoding='utf-8'
        )
        self.conn = h2.connection.H2Connection(config=config)
        self.flow_control_events = {}


    async def run(self):
        pass
