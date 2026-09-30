class DomainError(Exception):
    """Only this safe message crosses the route boundary."""
    def __init__(self, message='Kho tri thức chưa sẵn sàng. Vui lòng thử lại sau.', status=503):
        super().__init__(message)
        self.status = status

class AuthorityError(Exception):
    pass
