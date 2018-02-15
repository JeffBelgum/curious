# Curious

Curious is a web framework built on top of curio async that supports http/1.1

The framework is designed to include seamless http2 and websockets support in
the future.

It's an experiment in using curio on a real world problem, using type annotations
to give stronger guarantees about the inputs and outputs of a web server, and, in the future,
using the notion of a `stream` to abstract over the lifecycle of http/1.1, http2, and websocket
protocols.

## Development

Switching to tox for development and testing would be an easy improvement to make here.

## Quickstart

```python
from curious import Web, Method, Json

# Create new curious web app
app = Web(__name__)

# Define routes:

# Echos a GET or POST request as json serialized data.
@app.route("/echo", methods={Method.GET, Method.POST})
async def echo(request) -> Json:
    ordered_headers = [(name, value) for (name, value) in request.headers.items()],
    body = await request.body()

    response_json = {
        "method": request.method.name,
        "path": request.path,
        "headers": ordered_headers,
        "body": body,
    }

    return 200, response_json


# Run the server
if __name__ == "__main__":
    app.run("localhost", 8080)
```

Check out more example(s) in the `examples` directory.
