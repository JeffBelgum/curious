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
    if isinstance(body, str):
        body = body.encode("utf-8")
    await _request_local.transport.send(h11.Data(data=body))
    await _request_local.transport.send(h11.EndOfMessage())

