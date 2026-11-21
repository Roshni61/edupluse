from fastapi import HTTPException, status


class PermissionDeniedException(HTTPException):
    def __init__(self, detail: str = "Permission denied: access restricted to authorized roles."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class SchoolMismatchException(HTTPException):
    def __init__(self, detail: str = "Access denied: resource belongs to a different school."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ParentAccessDeniedException(HTTPException):
    def __init__(self, detail: str = "Access denied: parents may only access records for their own child."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class SensitiveAttributeException(HTTPException):
    def __init__(self, detail: str = "Violation: storage or querying of sensitive socio-economic attributes is forbidden."):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class InvalidCallWindowException(HTTPException):
    def __init__(self, detail: str = "Parent call windows must stay inside school hours; evening slots allowed only Tue and Thu."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
