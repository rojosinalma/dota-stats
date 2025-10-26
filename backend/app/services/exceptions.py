"""Custom exceptions for API services"""


class APIException(Exception):
    """Exception raised when API request fails"""

    def __init__(self, message: str, status_code: int = None):
        """
        Args:
            message: Error message
            status_code: HTTP status code from the failed request
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        if self.status_code:
            return f"API Error {self.status_code}: {self.message}"
        return f"API Error: {self.message}"
