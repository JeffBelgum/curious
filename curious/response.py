import json

import h11

from . import _request_local, log

# Helper function
async def respond(status_code, content_type, body):
    log.info(f"Sending {status_code} response with {len(body)} bytes")
    headers = _request_local.transport.basic_headers()
    headers.append(("Content-Type", content_type))
    headers.append(("Content-Length", str(len(body))))
    res = h11.Response(status_code=status_code, headers=headers)
    await _request_local.transport.send(res)
    await _request_local.transport.send(h11.Data(data=body))
    await _request_local.transport.send(h11.EndOfMessage())

class Json:
    pass

JSON_CONTENT_TYPE = "application/json; charset=utf-8"
TEXT_CONTENT_TYPE = "text/plain; charset=utf-8"
BINARY_CONTENT_TYPE = "application/octet-stream"

def response_to_bytes(handler, response):
    # TODO flesh out with other types such as html, css, javascript
    # media files, etc
    ann = handler.__annotations__
    if "return" in ann:
        if issubclass(ann["return"], Json):
            content_type = JSON_CONTENT_TYPE
            content = json.dumps(response).encode("utf-8")
        elif issubclass(ann["return"], (bytes, bytearray)):
            content_type = BINARY_CONTENT_TYPE
            content = response
        else:
            content_type = TEXT_CONTENT_TYPE
            content = response.encode("utf-8")
    else:
        if isinstance(response, (dict, tuple, list, int, float)):
            content_type = JSON_CONTENT_TYPE
            content = json.dumps(response).encode("utf-8")
        elif isinstance(response, (bytes, bytearray)):
            content_type = BINARY_CONTENT_TYPE
            content = response
        else:
            content_type = TEXT_CONTENT_TYPE
            content = response.encode("utf-8")
    return content_type, content
