class DomainError(Exception):
    """Expected business-rule failure."""

class AuthorizationError(DomainError):
    pass

class ResourceNotFound(DomainError):
    pass
