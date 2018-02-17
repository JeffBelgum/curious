"""
Server opens both an tls and tcp socket and serves from both.
Server supports http2 clear text connections with Connection: Upgrade
Server supports http2 tls connections with ALPN
Server does _not_ support http2 using prior knowledge
"""

from functools import wraps
import signal

from curio import run, spawn, SignalQueue, CancelledError, tcp_server, socket, ssl
from curious.connection import Connection, H11Connection, H2Connection
from curious.errors import CuriousError
import h11
import h2

from . import settings
from .router import Router
from .response import response_to_bytes
from .stream import H11Stream, H2Stream

class Server:
    def __init__(self, name):
        self.name = name
        self.certfile = settings.CERTFILE
        self.keyfile = settings.KEYFILE
        self.tls_ciphers = settings.TLS_CIPHERS
        self.router = Router()

    def create_ssl_context(self):
        """
        Create an SSL context that has reasonable settings and supports alpn for
        h2 and http/1.1 in that order.
        """
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.options |= ssl.OP_NO_TLSv1
        ssl_context.options |= ssl.OP_NO_TLSv1_1
        ssl_context.options |= ssl.OP_NO_COMPRESSION
        ssl_context.set_ciphers(self.tls_ciphers)
        ssl_context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
        ssl_context.set_alpn_protocols(["h2", "http/1.1"])
        return ssl_context

    async def serve_https(self, sock, addr):
        """
        Handle incoming https connections. The socket is wrapped in an SSLSocket.
        """
        ssl_context = self.create_ssl_context()
        sock = await ssl_context.wrap_socket(sock, server_side=True)

        protocol = sock.selected_alpn_protocol()
        if protocol is None:
            protocol = "http/1.1"

        if protocol == "http/1.1":
            await self.handle_h11(sock)
        else:
            await self.handle_h2(sock)


    async def serve_http(self, sock, addr):
        """
        Handle incoming http connections. Always start with h11 -- an h11 connection
        can be upgraded to h2 by the client.
        """
        await self.handle_h11(sock)


    @staticmethod
    def should_upgrade_to_h2(event):
        """
        Check if the client is requesting an upgrade to h2.
        Returns h2 upgrade settings or None if no upgrade is requested.
        """
        should_upgrade = False
        h2_settings = None

        for name, value in event.headers:
            if name == b"upgrade" and value == b"h2c":
                # TODO: upgrade should be `h2c` for clear text upgrades and
                #       `h2` for tls encrypted upgrades. We could support h2 upgrades
                #       of tls using h2.
                should_upgrade = True
            if name == b"http2-settings":
                if h2_settings is not None:
                    # TODO: raise bad client request exception if http2-settings header
                    #       is seend more than once per RFC7230
                    pass
                h2_settings = value

        if should_upgrade:
            # TODO: raise bad client request exception if h2_settings is `None`
            #       if an upgrade is requested.
            return h2_settings
        else:
            return None


    async def handle_h11(self, sock):
        """
        Handle a raw socket that is speaking h11.
        """
        h11_conn = H11Connection(sock)
        while True:
            event = await h11_conn.next_event()
            if type(event) is h11.ConnectionClosed:
                break
            if type(event) is h11.EndOfMessage:
                break
            if type(event) is h11.Request:
                upgrade_settings = self.should_upgrade_to_h2(event)
                if upgrade_settings is not None:
                    print("Upgrading to h2")
                    h2_conn = await H2Connection.from_h11_connection(h11_conn, upgrade_settings)
                    # TODO handle errors negotiating h2 upgrade
                    await self.handle_h2_connection(h2_conn, event)
                    # after the h2 connection has been handled, there is nothing left to do
                    break
                else:
                    print("Responding to h11 request")
                    await self.respond_to_h11(h11_conn, event)

    async def respond_to_h11(self, h11_conn, event):
        """
        Most generic response to an h11 connection possible.
        """
        stream = H11Stream(event, (None,None))
        print("stream:", stream)
        handler = self.router.match(stream)
        print("handler:", handler)
        print("htype:", type(handler))
        status, response = await handler(stream)
        print("response:", response)
        content_type, response = response_to_bytes(handler, response)
        content_length = str(len(response))
        headers = h11_conn.basic_headers()
        headers.append(('Content-Type', content_type))
        headers.append(('Content-Length', content_length))
        resp = h11.Response(status_code=status, headers=headers)
        await h11_conn.send(resp)
        await h11_conn.send(h11.Data(data=response))
        await h11_conn.send(h11.EndOfMessage())
        await h11_conn.close()


    async def handle_h2(self, sock):
        """
        Handle a raw socket that is speaking h2
        """
        h2_conn = await H2Connection.new(sock)
        await self.handle_h2_connection(h2_conn)

    async def handle_h2_connection(self, h2_conn, initial_h11_request=None):
        """
        Handle an initiated h2 connection.
        """
        while True:
            data = await h2_conn.socket.recv(2**16)
            if not data:
                print("eof")
                break
            events = h2_conn._conn.receive_data(data)
            for event in events:
                if isinstance(event, h2.events.RequestReceived):
                    stream = H2Stream(event, (None, None))
                    print(stream)
                    try:
                        handler = self.router.match(stream)
                    except CuriousError as exc:
                        handler = self.router.match_error(exc)
                    print(handler)
                    status = "200"
                    datatype = "plain/text"
                    data = b"hello world from h2"
                    h2_conn.send(event.stream_id, status, datatype, data)
                elif isinstance(event, h2.events.DataReceived):
                    h2_conn._conn.reset_stream(event.stream_id)
                elif isinstance(event, h2.events.WindowUpdated):
                    # TODO: update control flow windows and unblock and blocked streams
                    # FIXME: Right now we're just sending a response on stream_id WindowUpdated + 1
                    #        This is a bit of a hack around the fact that we need to send a response
                    #        to a message we received in h11 land and need to use a new stream id to
                    #        do it.
                    if initial_h11_request is not None:
                        h2_conn.send(
                            event.stream_id + 1,
                            "200",
                            "plain/text",
                            b"hello world from h2"
                        )
                        initial_h11_request = None
            await h2_conn.sendall()

    # TODO modify return annotations to include status code to make mypy happy
    def route(self, path, **rules):
        def decorator(handler):
            print(f"building route {path} -> {handler.__name__}")
            rules["path"] = path
            self.router.add(rules, handler)
            return handler
        return decorator

    # err_code doesn't really make sense as this is used
    def error(self, status_code):
        def decorator(handler):
            print(f"building error handler for {status_code} -> {handler.__name__}")
            @wraps(handler)
            def wrapper(*args, **kwargs):
                print("trying to send error response...")
                # if _request_local.transport.conn.our_state not in {h11.IDLE, h11.SEND_RESPONSE}:
                #     print(f"...but I can't, because our state is {_request_local.transport.conn.our_state}")
                #     return
                try:
                    return handler(*args, **kwargs)
                except Exception as exc:
                    print(f"error while sending error response: {exc}")

            self.router.add_error(status_code, wrapper)
            return wrapper
        return decorator

    async def run(self):
        """
        Main loop to spawn http and https servers and handle signal interrupts
        """
        print("Server starting up")
        async with SignalQueue(signal.SIGHUP, signal.SIGINT, signal.SIGTERM) as sig:
            while True:
                # Spin up tcp servers
                if settings.ENABLE_HTTP:
                    serve_http_task = await spawn(tcp_server, "localhost", settings.HTTP_PORT, self.serve_http)
                if settings.ENABLE_HTTPS:
                    serve_https_task = await spawn(tcp_server, "localhost", settings.HTTPS_PORT, self.serve_https)

                # wait for signal intterupts
                signo = await sig.get()
                await serve_http_task.cancel()
                await serve_https_task.cancel()
                if signo == signal.SIGHUP:
                    print("Server restarting")
                    # TODO reload configuration
                else:
                    print("Server shutting down")
                    break
