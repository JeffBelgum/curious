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

Check out the example(s) in the `examples` directory to see how to use the library
