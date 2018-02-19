import curio
from curious.server import Server

if __name__ == "__main__":
    app = Server(__name__)

    @app.route("/a/b/c")
    async def abc_handler(stream) -> str:
        return 200, 'hello from abc handler'

    @app.route("/stream")
    async def streaming_handler(stream) -> str:
        await stream.send_headers(200, {})
        await stream.send_data(b"hello from the streaming handler\n")
        await stream.send_data(b"some more data")

    @app.error(404)
    async def error_response(exc):
        body = f"custom {str(exc)}"
        return 404, body

    curio.run(app.run)
