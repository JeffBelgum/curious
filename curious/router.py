from functools import partial
import uuid

import h11

from .errors import *
from .methods import Method
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
        rules["path"] = PathMatcher(rules["path"])
        if "methods" not in rules:
            rules["methods"] = {Method.GET}
        self.routes.append((rules, handler))

    def add_error(self, status_code, handler):
        """ add a new status code -> handler mapping """
        self.error_routes[status_code] = handler

    def match(self, request):
        """ match against request path and return handler """
        matching_path = False
        matching_method = False

        for rules, handler in self.routes:
            (is_match, kwargs) = rules["path"].matches(request.path)
            if is_match:
                matching_path = True
                if request.method in rules["methods"]:
                    matching_method = True
                    if "content_type" in rules:
                        actual_type = request.headers["content-type"]
                        if rules["content_type"] is Json:
                            if actual_type.startswith("application/json"):
                                curried = partial(handler, **kwargs)
                                curried.__annotations__ = handler.__annotations__
                                return curried
                        # TODO other rules
                    else:
                        curried = partial(handler, **kwargs)
                        curried.__annotations__ = handler.__annotations__
                        return curried
        if matching_path:
            if matching_method:
                raise BadRequest
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

import re

class PathMatcher:
    ident_re = r"[^\d\W]\w*"
    type_re = r"(?:int)|(?:float)|(?:string)|(?:uuid)"
    segment_re = re.compile(rf"^(?P<name>{ident_re})\s*:\s*(?P<type>{type_re})\Z")

    int_re = r"[-+]?\d+"
    float_re = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
    string_re = r"[^/.]+"
    uuid_re = r"[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-4[a-fA-F0-9]{3}-[89aAbB][a-fA-F0-9]{3}-[a-fA-F0-9]{12}"

    def __init__(self, raw_pattern):
        self.raw_pattern = raw_pattern
        self.type_map = {}

        segments = []
        current_segment = []
        in_dynamic_segment = False

        for i, c in enumerate(raw_pattern):
            if c == "<":
                if in_dynamic_segment:
                    raise ValueError(f"Malformed url rule at col {i}: {raw_pattern}")
                in_dynamic_segment = True
                segments.append("".join(current_segment))
                current_segment = []
            elif c == ">":
                if not in_dynamic_segment:
                    raise ValueError(f"Malformed url rule at col {i}: {raw_pattern}")
                in_dynamic_segment = False
                segment = "".join(current_segment)
                current_segment = []
                match = self.segment_re.match(segment)
                if match is None:
                    raise ValueError(f"Malformed url rule at col {i-len(segment)}: {raw_pattern}")
                segment_name = match.group("name")
                segment_type = match.group("type")
                if segment_type == "int":
                    if segment_name in self.type_map:
                        raise ValueError(f"Malformed url rule at col {i-len(segment)}: {raw_pattern} -- Cannot have duplicate identifier")
                    self.type_map[segment_name] = int
                    dynamic_segment = rf"(?P<{segment_name}>{self.int_re})"
                elif segment_type == "float":
                    if segment_name in self.type_map:
                        raise ValueError(f"Malformed url rule at col {i-len(segment)}: {raw_pattern} -- Cannot have duplicate identifier")
                    self.type_map[segment_name] = float
                    dynamic_segment = rf"(?P<{segment_name}>{self.float_re})"
                elif segment_type == "string":
                    if segment_name in self.type_map:
                        raise ValueError(f"Malformed url rule at col {i-len(segment)}: {raw_pattern} -- Cannot have duplicate identifier")
                    self.type_map[segment_name] = str
                    dynamic_segment = rf"(?P<{segment_name}>{self.string_re})"
                elif segment_type == "uuid":
                    if segment_name in self.type_map:
                        raise ValueError(f"Malformed url rule at col {i-len(segment)}: {raw_pattern} -- Cannot have duplicate identifier")
                    self.type_map[segment_name] = uuid.UUID
                    dynamic_segment = rf"(?P<{segment_name}>{self.uuid_re})"
                else:
                    raise ValueError(f"Malformed url rule at col{i-len(segment)}: {raw_pattern}")

                segments.append(dynamic_segment)
            else:
                current_segment.append(c)

        # append final segment
        if current_segment:
            segments.append("".join(current_segment))

        self.regex = re.compile(rf"^{''.join(segments)}\Z")

    def matches(self, path):
        match = self.regex.match(path)
        if match is None:
            return (False, None)
        # convert stringly typed matches to specified types
        typed_matches = {k: self.type_map[k](v) for k, v in match.groupdict().items()}
        return (True, typed_matches)
