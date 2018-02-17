"""
Settings file hardcodes all constants for now.
If this becomes more than an example, this code would pull
in settings from command line args, environment variables, and
config files and pass them as config. Preferably using a library.
(See 12 factor app.)
"""

MAX_RECV = 2 * 16 # Maximum number of bytes the server will accept from a client for a given request
TIMEOUT_S = 10 # Timeout before a connection will be closed

ENABLE_HTTP = True
HTTP_PORT = 8080

ENABLE_HTTPS = True
HTTPS_PORT = 8081

CERTFILE = "cert/localhost.crt"
KEYFILE = "cert/localhost.key"
TLS_CIPHERS = "ECDHE+AESGCM"
