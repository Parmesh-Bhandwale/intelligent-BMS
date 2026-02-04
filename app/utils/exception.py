class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

class NotFoundException(AppException):
    def __init__(self, message="Resource not found"):
        super().__init__(message, 404)

class UnauthorizedException(AppException):
    def __init__(self, message="Unauthorized"):
        super().__init__(message, 401)

class InternalServerException(AppException):
    def __init__(self, message="Internal server error"):
        super().__init__(message, 500)
