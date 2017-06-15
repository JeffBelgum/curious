from functools import wraps
import logging

import curio
import h11

from . import _request_local, log, Request, Router
from .transport import CurioHTTPTransport

TIMEOUT = 10

class Web:
    def __init__(self, name):
        self.name = name
        self.router = Router()

    def run(self, host, port):
        kernel = curio.Kernel()
        logging.info(f"Listening on http://{host}:{port}")
        kernel.run(curio.tcp_server(host, port, self.http_serve))

    def route(self, path, **rules):
        def decorator(handler):
            logging.debug(f"building route {path} -> {handler.__name__}")
            rules["path"] = path
            self.router.add(rules, handler)
            return handler
        return decorator

    # err_code doesn't really make sense as this is used
    def error(self, status_code):
        def decorator(handler):
            logging.debug(f"building error handler for {status_code} -> {handler.__name__}")
            @wraps(handler)
            def wrapper(*args, **kwargs):
                log.info("trying to send error response...")
                if _request_local.transport.conn.our_state not in {h11.IDLE, h11.SEND_RESPONSE}:
                    log.info(f"...but I can't, because our state is {_request_local.transport.conn.our_state}")
                    return
                try:
                    return handler(*args, **kwargs)
                except Exception as exc:
                    log.info(f"error while sending error response: {exc}")

            self.router.add_error(status_code, wrapper)
            return wrapper
        return decorator

    async def http_serve(self, sock, addr):
        transport = CurioHTTPTransport(sock)
        _request_local.transport = transport
        _request_local.end_of_message = False
        while True:
            assert transport.conn.states == {
                h11.CLIENT: h11.IDLE, h11.SERVER: h11.IDLE}

            try:
                async with curio.timeout_after(TIMEOUT):
                    log.info("Server main loop waiting for request")
                    event = await transport.next_event()
                    log.info(f"Server main loop got event: {event}")
                    if type(event) is h11.Request:
                        request = Request(event)
                        await self.router.match(request)(request)
            except Exception as exc:
                log.info(f"Error during response handler: {exc}")
                await self.router.match_error(exc)(exc)

            if transport.conn.our_state is h11.MUST_CLOSE:
                log.info("connection is not reusable, so shutting down")
                await transport.shutdown_and_clean_up()
                return
            else:
                try:
                    log.info("trying to re-use connection")
                    transport.conn.start_next_cycle()
                except h11.ProtocolError:
                    states = transport.conn.states
                    log.info(f"unexpected state {states} -- bailing out")
                    exc = RuntimeError("unexpected state {}".format(states))
                    await self.router.match_error(exc)(exc)
                    await transport.shutdown_and_clean_up()
                    return


