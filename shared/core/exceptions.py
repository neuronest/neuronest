class BaseError(Exception):
    pass


class DependencyError(BaseError):
    pass


class AlreadyExistingError(BaseError):
    pass


class AlreadyProcessingError(BaseError):
    pass
