import json as json_module
from urllib.parse import urlparse, parse_qsl

import h11
import h2.connection
import wsproto.connection

from werkzeug.datastructures import Headers, ImmutableOrderedMultiDict

from .methods import Method

class Stream:
    """
    A `Stream` represents a handle to the client. Data can be received and sent to the client.
    `Stream`s abstract over the supported transport protocols and give a unified api
    for interacting with the concept of a stream bi-directional data stream.
    """
    def __init__(self, request, remote_addr):
        if isinstance(request, h11.Request):
            self._extract_h11_request(request)
        elif isinstance(request, h2.connection.H2Connection):
            self._extract_h2_request(request)
        elif isinstance(request, wsproto.connection.WSConnection):
            self._extract_h2_request(request)
        else:
            raise ValueError(f"Unsupported transport protocol. Request type '{type(request)}'")

        self.remote_ip = remote_addr[0]

    def _extract_h11_request(self, h11_req):
        self._request = h11_req
        self.method = Method.from_string(h11_req.method.decode("ascii"))
        self._target = h11_req.target.decode("ascii")
        parsed_url = urlparse(self._target)

        self.path = parsed_url.path
        self._raw_query = parsed_url.query
        self._query = None
        self._headers = None
        self._body = None

    @property
    def query(self):
        """
        Return an `ImmutableOrderedMultiDict` representation of a `Stream`'s query parameteres.

        The `query` is lazily constructed the first time it is accessed.
        """
        if self._query:
            return self._query
        self._query = ImmutableOrderedMultiDict(parse_qsl(self._raw_query))
        return self._query
