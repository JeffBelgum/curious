from enum import Enum, unique

SAFE_FLAG = 0b1
IDEMPOTENT_FLAG = 0b10

@unique
class Method(Enum):
    OPTIONS = (1 << 2) | IDEMPOTENT_FLAG
    GET =     (2 << 2) | IDEMPOTENT_FLAG | SAFE_FLAG
    HEAD =    (3 << 2) | IDEMPOTENT_FLAG | SAFE_FLAG
    POST =    (4 << 2)
    PUT =     (5 << 2) | IDEMPOTENT_FLAG
    DELETE =  (6 << 2) | IDEMPOTENT_FLAG
    TRACE =   (7 << 2) | IDEMPOTENT_FLAG
    CONNECT = (8 << 2)

    def is_safe(self):
        return (self.value & SAFE_FLAG) == SAFE_FLAG

    def is_idempotent(self):
        return (self.value & IDEMPOTENT_FLAG) == IDEMPOTENT_FLAG

    @staticmethod
    def from_string(string):
        if string == "OPTIONS":
            return Method.OPTIONS
        elif string == "GET":
            return Method.GET
        elif string == "HEAD":
            return Method.HEAD
        elif string == "POST":
            return Method.POST
        elif string == "PUT":
            return Method.PUT
        elif string == "DELETE":
            return Method.DELETE
        elif string == "TRACE":
            return Method.TRACE
        elif string == "CONNECT":
            return Method.CONNECT
        else:
            return None
