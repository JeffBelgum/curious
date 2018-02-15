from itertools import count
from socket import SHUT_WR
from wsgiref.handlers import format_date_time
import h11
import h2.connection
import h2.config
import curio

from . import __version__
from . import settings


class Connection:
    _id_iter = count(1)
    ident = f"curious-web-server/{__version__}".encode("ascii")

    def __init__(self, socket):
        """
        Construct a new instance with the socket.
        """
        self._id = next(self._id_iter)
        self.socket = socket

    @classmethod
    def basic_headers(cls):
        """
        Headers required on all connections
        """
        return [
            ("Date", format_date_time(None).encode("ascii")),
            ("Server", cls.ident),
        ]


class H2Connection(Connection):
    def __init__(self, socket):
        super().__init__(socket)

        h2_config = h2.config.H2Configuration(client_side=False, header_encoding='utf-8')
        self._conn = h2.connection.H2Connection(h2_config)
        self.h2_flow_control_events = {}

    @classmethod
    async def new(cls, socket):
        instance = cls(socket)
        instance._conn.initiate_connection()
        await instance.sendall()
        return instance


    @classmethod
    async def from_h11_connection(cls, h11_conn, upgrade_settings):
        """
        Take a h11 connection and complete the upgrade
        Returns an initiated h2 connection.
        """

        # Finish h11 part of the connection
        resp = h11.InformationalResponse(
            status_code=101,
            headers=[("Upgrade", "h2c")],
        )
        await h11_conn.send(resp)

        instance = cls(h11_conn.socket)
        instance._conn.initiate_upgrade_connection(settings_header=upgrade_settings)
        await instance.sendall()

        return instance


    async def sendall(self):
        """
        If there is any data ready to be send, send it on the socket.
        """
        data_to_send = self._conn.data_to_send()
        if data_to_send:
            print("data to send")
            await self.socket.sendall(data_to_send)


    def send(self, stream_id, status, datatype, data):
        self._conn.send_headers(
            stream_id=stream_id,
            headers=[
                (":status", status),
                *self.basic_headers(),
                ("content-length", str(len(data))),
                ("content-type", datatype),
            ]
        )
        self._conn.send_data(
            stream_id=stream_id,
            data=data,
            end_stream=True,
        )


class H11Connection(Connection):
    def __init__(self, socket):
        super().__init__(socket)
        self._conn = h11.Connection(h11.SERVER)

    async def _read_from_peer(self):
        if self._conn.they_are_waiting_for_100_continue:
            print("Sending 100 Continue")
            go_ahead = h11.InformationalResponse(status_code=100, headers=self.basic_headers())
            await self.send_h11(go_ahead)
        try:
            print("waiting on data")
            data = await self.socket.recv(settings.MAX_RECV)
        except ConnectionError:
            data = b""
        print("sending data to state machine")
        self._conn.receive_data(data)

    async def next_event(self):
        while True:
            print("getting next event")
            event = self._conn.next_event()
            print("Got event", event)
            if event is h11.NEED_DATA:
                await self._read_from_peer()
                continue
            return event

    async def send(self, event):
        assert type(event) is not h11.ConnectionClosed
        data = self._conn.send(event)
        await self.socket.sendall(data)

    async def close(self):
        await self.socket.shutdown(SHUT_WR)
        print(self.socket)
        async with curio.ignore_after(settings.TIMEOUT_S):
            try:
                while True:
                    data = await self.socket.recv(settings.MAX_RECV)
                    print("DATA")
                    print(data)
                    if not data:
                        break
            finally:
                await self.socket.close()
