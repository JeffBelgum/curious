import curio
from curio import socket

import pytest
import h11
import h2
from curious.connection import Connection, H11Connection, H2Connection, MAX_RECV


@pytest.mark.skip
def test_create_connection():
    c1 = Connection(None)
    c2 = Connection(None)
    assert isinstance(c1._id, int)
    assert c1._id != c2._id


@pytest.mark.skip
def test_basic_headers():
    headers = Connection.basic_headers()
    assert len(headers) == 2
    assert headers[0][0] == "Date"
    assert isinstance(headers[0][1], bytes)
    assert headers[1][0] == "Server"
    assert headers[1][1] == Connection.ident


@pytest.mark.skip
def test_h11_connection():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("localhost", 8080))
    sock.listen()

    async def test_send_data(sock):
        sock, _ = await sock.accept()
        conn = H11Connection(sock)
        await conn.initiate_connection()
        while True:
            event = await conn.next_event()
            if type(event) is h11.EndOfMessage:
                break
        headers = conn.basic_headers()
        data = b'hello world'
        headers.append(('Content-Length', len(data)))
        await conn.send(h11.Response(status_code=200, headers=conn.basic_headers()))
        await conn.send(h11.Data(data=data))
        await conn.send(h11.EndOfMessage())
        await conn.close()
        print(event)
        print(type(event))
        print("!!!!!!!!!!!")

    curio.run(test_send_data, sock)

def test_h2_connection():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("localhost", 8081))
    sock.listen()


    async def test_send_data(sock):
        sock, _ = await sock.accept()
        conn = H2Connection(sock)
        print("Initiating")
        await conn.initiate_connection()
        print("initiated")
        while True:
            print("receiving more data")
            data = await sock.recv(MAX_RECV)
            if not data:
                print("eof")
                break
            print("get events")
            events = conn.conn.receive_data(data)
            for event in events:
                print("event", event)
                if isinstance(event, h2.events.RequestReceived):
                    conn.send(event)
            print("get data to send")
            data_to_send = conn.conn.data_to_send()
            if data_to_send:
                print("sending data")
                await conn.sock.sendall(data_to_send)

    curio.run(test_send_data, sock)
