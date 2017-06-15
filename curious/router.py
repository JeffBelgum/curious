import h11

from .errors import *
from .response import respond

class Router:
    def __init__(self):
        self.routes = []
        self.error_routes = {
            500: self.base_error_handler,
        }

    async def base_error_handler(self, exc):
        status_code = self.get_status_code_from_error(exc)
        body = str(exc)
        await respond(status_code, "text/plain; charset=utf-8", body)

    def add(self, rules, handler):
        """ add a new route -> handler mapping """
        self.routes.append((rules, handler))

    def add_error(self, status_code, handler):
        """ add a new status code -> handler mapping """
        self.error_routes[status_code] = handler

    def match(self, request):
        """ match against request path and return handler """
        matching_path = False
        for rules, handler in self.routes:
            if request.path == rules["path"]:
                matching_path = True
                if "methods" not in rules:
                    rules["methods"] = {Method.GET}
                if request.method in rules["methods"]:
                    return handler
        if matching_path:
            raise MethodNotAllowed
        raise NotFound

    def get_status_code_from_error(self, exc):
        if isinstance(exc, h11.RemoteProtocolError):
            return exc.error_status_hint
        elif isinstance(exc, CuriousError):
            return exc.status_code
        else:
            return 500

    def match_error(self, exc):
        """ match against the exception type and return handler """
        status_code = self.get_status_code_from_error(exc)
        if status_code in self.error_routes:
            return self.error_routes[status_code]
        else:
            return self.error_routes[500]

