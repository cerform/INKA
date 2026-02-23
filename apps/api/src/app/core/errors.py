class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    pass


class PermissionError(DomainError):
    pass
