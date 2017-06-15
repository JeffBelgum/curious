class CuriousError(Exception):
    status_code = 500
    string = "Curious Error"
    def __str__(self):
        return f"{self.status_code} {self.string}"

class BadRequest(CuriousError):
    status_code = 400
    string = "Bad Request"
class Unauthorized(CuriousError):
    status_code = 401
    string = "Unauthorized"
class Forbidden(CuriousError):
    status_code = 403
    string = "Forbidden"
class NotFound(CuriousError):
    status_code = 404
    string = "Not Found"
class MethodNotAllowed(CuriousError):
    status_code = 405
    string = "Method Not Allowed"
class RequestTimeout(CuriousError):
    status_code = 408
    string = "Request Timeout"
class InternalServerError(CuriousError):
    status_code = 500
    string = "Internal Server Error"
class NotImplemented(CuriousError):
    status_code = 501
    string = "Not Implemented"
class BadGateway(CuriousError):
    status_code = 502
    string = "Bad Gateway"
class HTTPVersionNotSupported(CuriousError):
    status_code = 505
    string = "HTTP Version Not Supported"

