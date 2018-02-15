"""
Settings file hardcodes all constants for now.
If this becomes more than an example, this code would pull
in settings from command line args, environment variables, and
config files and pass them as config. Preferably using a library.
(See 12 factor app.)
"""

CERTFILE = "certs/bn.pem"
KEYFILE = "certs/bn.key"
TLS_CIPHERS = "ECDHE+AESGCM"
MAX_RECV = 2 * 16
TIMEOUT_S = 10
