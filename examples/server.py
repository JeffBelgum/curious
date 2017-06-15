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


web = Web(__name__)

# Routes

# should we only allow a single method per handler?
@web.route("/echo", methods={Method.GET, Method.POST})
async def echo(request) -> Json:
    response_json = {
        "method": request.method.name,
        "path": request.path,
        "headers": [(name, value) for (name, value) in request.headers],
        "body": "",
    }
    response_json["body"] = await request.body()

    return 200, response_json

@web.route("/stream", methods={Method.POST})
async def stream(request) -> str:
    async for data_chunk in request.stream:
        logging.info("read %d bytes", len(data_chunk))
    return 201, response_json

@web.route("/slow/<s:int>")
async def slow(request, s) -> str:
    await curio.sleep(s)
    return 200, "gave you a slow response"

@web.route("/admin")
async def admin(request, user: AdminUser) -> str:
    """ guaranteed to be logged in as an administrator """
    return 200, "admin page successfully reached"

@web.route("/admin")
async def admin(request, user: User) -> str:
    """ guaranteed to have a logged in user present """
    return 200, "level up your user status by being cordial"

@web.route("/login", methods={Method.POST}, content_type=Json)
async def login(request) -> Json:
    """ body is guaranteed to be json """
    body = await request.json()
    return 200, body

@web.route("/dynamic/<i:int>/<f : float><s: string>/<u :uuid>")
async def dynamic(request, i, f, s, u) -> str:
    return 200, f"int: {i}\nfloat: {f}\nstring: {s}\nuuid: {u}"

@web.error(404)
async def error_response(exc):
    body = f"custom {str(exc)}"
    return 404, body

# Run server
if __name__ == "__main__":
    web.run("localhost", 8080)
