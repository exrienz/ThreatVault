class UnauthorizedError(Exception):
    pass


class InvalidAuthentication(Exception):
    pass


class InactiveUser(Exception):
    pass


class SchemaException(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg
