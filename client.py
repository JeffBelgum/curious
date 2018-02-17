import ssl
import curio
import h11
import h2
import h2.config
import h2.connection


TCP_PORT=1080
TLS_PORT=1443


async def get_plaintext_socket():
    return await curio.open_connection("localhost", TCP_PORT)

async def get_encrypted_socket(alpn=None):
    ctx = curio.ssl.create_default_context()
    if alpn:
        ctx.set_alpn_protocols(alpn)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return await curio.open_connection("localhost", TLS_PORT, ssl=ctx)

async def make_h2_request(socket):
    h2_config = h2.config.H2Configuration(client_side=True, header_encoding='utf-8')
    conn = h2.connection.H2Connection(h2_config)
    conn.initiate_connection()
    data_to_send = conn.data_to_send()
    if data_to_send:
        await socket.sendall(data_to_send)


async def make_h11_request(socket):
    conn = h11.Connection(our_role=h11.CLIENT)
    req = h11.Request(
        method="GET",
        target="/",
        headers=[
            ("Host", "localhost"),
            ("Connection", "close"),
        ],
    )
    data = conn.send(req)
    await socket.sendall(data)
    req = h11.EndOfMessage()
    data = conn.send(req)
    await socket.sendall(data)

    async def next_event():
        while True:
            event = conn.next_event()
            if event is h11.NEED_DATA:
                data = await socket.recv(2*16)
                conn.receive_data(data)
                continue
            return event

    while True:
        print("getting event")
        event = await next_event()
        print(event)
        if type(event) is h11.EndOfMessage:
            break

async def main():
    # socket = await get_plaintext_socket()
    # await make_h11_request(socket)
    # await socket.close()

    socket = await get_encrypted_socket(['h2'])
    await make_h2_request(socket)
    await socket.close()

curio.run(main)
