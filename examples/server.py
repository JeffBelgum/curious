import json
import logging
logging.basicConfig(level=logging.DEBUG)

import curio
from curious import Web, Method, respond, Json

# Stub users
class User:
    """ Represents a logged in user """
    pass

class AdminUser(User):
    """ Represents a logged in admin user """
    pass


app = Web(__name__)

# Routes

# should we only allow a single method per handler?
@app.route("/echo", methods={Method.GET, Method.POST})
async def echo(request) -> Json:
    response_json = {
        "method": request.method.name,
        "path": request.path,
        "headers": [(name, value) for (name, value) in request.headers],
        "body": "",
    }
    response_json["body"] = await request.body()

    return 200, response_json

@app.route("/stream", methods={Method.POST})
async def stream(request) -> str:
    total_bytes_read = 0
    async for data_chunk in request.stream:
        total_bytes_read += len(data_chunk)
        logging.info("read %d bytes", len(data_chunk))

    return 201, f"Streamed {total_bytes_read} bytes from your request"

@app.route("/slow/<s:int>")
async def slow(request, s) -> str:
    await curio.sleep(s)
    return 200, "gave you a slow response"

@app.route("/admin")
async def admin(request, user: AdminUser) -> str:
    """ guaranteed to be logged in as an administrator """
    raise NotImplementedError("This functionality is not yet implemented")
    return 200, "admin page successfully reached"

@app.route("/admin")
async def admin(request, user: User) -> str:
    """ guaranteed to have a logged in user present """
    raise NotImplementedError("This functionality is not yet implemented")
    return 200, "level up your user status by being cordial"

@app.route("/login", methods={Method.POST}, content_type=Json)
async def login(request) -> Json:
    """ body is guaranteed to be json """
    body = json.loads(await request.body())
    return 200, body

@app.route("/dynamic/<i:int>/<f : float><s: string>/<u :uuid>")
async def dynamic(request, i, f, s, u) -> str:
    return 200, f"int: {i}\nfloat: {f}\nstring: {s}\nuuid: {u}"

@app.error(404)
async def error_response(exc):
    body = f"custom {str(exc)}"
    return 404, body

# Run server
if __name__ == "__main__":
    app.run("localhost", 8080)
