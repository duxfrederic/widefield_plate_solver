class CustomException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class CouldNotSolveError(CustomException):
    def __init__(self, message="Raised if no astrometric solution was found"):
        super().__init__(message)


class APIKeyNotFound(CustomException):
    def __init__(self, message="""
Please set your astrometry.net key under the `astrometry_net_aòpi_key` environment variable.
Either with `os.environ['astrometry_net_aòpi_key'] = '(your astrometry.net api key)'` within python, or
in your shell with `export astrometry_net_api_key='(your astrometry.net api key)'`.
    """):
        super().__init__(message)
