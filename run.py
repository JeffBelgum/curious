import curio
from curious.server import Server

if __name__ == "__main__":
    app = Server(__name__)

    @app.route("/a/b/c")
    async def abc_handler(stream) -> str:
        pass

    curio.run(app.run)
