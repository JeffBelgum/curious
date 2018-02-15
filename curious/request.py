import h11
from werkzeug.datastructures import ImmutableOrderedMultiDict

from . import _request_local
from .methods import Method

class Request:
    def __init__(self, h11_req):
        self.h11_req = h11_req
        self._method = None
        self._headers = None
        self._path = None

    @property
    def method(self):
        if self._method:
            return self._method
        self._method = Method.from_string(self.h11_req.method.decode("ascii"))
        return self._method

    @property
    def path(self):
        if self._path:
            return self._path
        self._path = self.h11_req.target.decode("ascii")
        return self._path

    @property
    def headers(self):
        if self._headers:
            return self._headers
        decoded = [(name.decode("ascii"), value.decode("ascii")) \
            for name, value in self.h11_req.headers]
        self._headers = ImmutableOrderedMultiDict(decoded)
        return self._headers

    @property
    def stream(self):
        return DataIterator()

    async def body(self):
        # TODO write with async comprehensions
        buf = []
        it = DataIterator()
        # FIXME check: does this block?
        async for chunk in DataIterator():
            buf.append(chunk)

        return "".join(buf)


class DataIterator:
    async def __aiter__(self):
        return self

    async def __anext__(self):
        # TODO make end of message a local thing
        if _request_local.end_of_message:
            raise RuntimeError("Reading past end of request body")
        while True:
            event = await _request_local.transport.next_event()
            if type(event) is h11.EndOfMessage:
                _request_local.end_of_message = True
                raise StopAsyncIteration
            assert type(event) is h11.Data
            # FIXME is type of data always ascii? probs not
            return event.data.decode("ascii")
