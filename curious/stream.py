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
    `Stream`s abstract over the supported application protocols and give a unified api
    for interacting with the concept of a stream bi-directional data stream.
    """
    def __init__(self, request, remote_addr):
        self._parse_raw_request(request)
        self.remote_ip = remote_addr[0]

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

    def __str__(self):
        return f"Stream({self.method}: {self.path}, {self.query}. Headers={self.headers})"

class H11Stream(Stream):
    def _parse_raw_request(self, h11_req):
        self._request = h11_req
        self.method = Method.from_string(h11_req.method.decode("ascii"))
        self._target = h11_req.target.decode("ascii")
        parsed_url = urlparse(self._target)

        self.path = parsed_url.path
        self._raw_query = parsed_url.query
        self._raw_headers = h11_req.headers
        self._query = None
        self._headers = None
        self._body = None

    @property
    def headers(self):
        if self._headers:
            return self._headers
        decoded = [(name.decode("ascii"), value.decode("ascii")) \
            for name, value in self._raw_headers]
        self._headers = ImmutableOrderedMultiDict(decoded)
        return self._headers

class H2Stream(Stream):
    def _parse_raw_request(self, h2_req):
        self._request = h2_req
        self._raw_headers = h2_req.headers
        self._headers = None
        self.method = self.headers[':method']
        self._target = self.headers[':path']
        parsed_url = urlparse(self._target)

        self.path = parsed_url.path
        self._raw_query = parsed_url.query
        self._query = None
        self._body = None


    @property
    def headers(self):
        if self._headers:
            return self._headers
        self._headers = ImmutableOrderedMultiDict(self._raw_headers)
        return self._headers
