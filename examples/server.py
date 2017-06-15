import json
import logging
logging.basicConfig(level=logging.DEBUG)

from curious import Web, Method, respond

web = Web(__name__)


# should we only allow a single method per handler?
@web.route("/echo", methods={Method.GET, Method.POST})
async def send_echo_response(request):
    print("echo")
    response_json = {
        "method": request.method.name,
        "path": request.path,
        "headers": [(name, value) for (name, value) in request.headers],
        "body": "",
    }
    # FIXME XXX What happens when we respond before end of message?!
    response_json["body"] = await request.body()
    # OR
    # async for data_chunk in request.stream:
    #     response_json["body"] += data_chunk


    response_body = json.dumps(response_json,
        sort_keys=True,
        indent=4,
        separators=(",", ": "))
    await respond(200, "application/json; charset=utf-8", response_body)

@web.route("/slow")
async def slow(request):
    print("slow")
    await curio.sleep(5)
    await respond(200, "text/plain; charset=utf-8", "gave you a slow response")


@web.error(404)
async def error_response(exc):
    body = f"custom {str(exc)}"
    await respond(404, "text/plain; charset=utf-8", body)


if __name__ == "__main__":
    web.run("localhost", 8080)
