import curio
from curious.server import Server

if __name__ == "__main__":
    server = Server()

    curio.run(server.serve)
