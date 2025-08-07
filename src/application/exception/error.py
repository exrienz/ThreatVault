

class UnauthorizedError(Exception):
    pass


class InvalidAuthentication(Exception):
    pass


class InactiveUser(Exception):
    pass


class InvalidFile(Exception):
    def __init__(self, file_type: str) -> None:
        self.msg = f"Expected file format: {file_type}"


class InvalidInput(Exception):
    pass


class SchemaException(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class JWTExpiredException(Exception):
    def __init__(self, is_api: bool):
        self.is_api = is_api
