"""
Exceptions for napcat
"""

from typing import Optional


class NapCatException(Exception):

    def __init__(self, message: str) -> None:

        super().__init__(message)


class NapCatAPIFailureException(NapCatException):
    """
    Exception raised when the NapCat HTTP API fails. There are two possible
    reasons for this exception to be raised:

    1. The request to the NapCat HTTP API failed where `response["status"]` is
       "failed".
    2. The request to the NapCat HTTP API succeeded, but the return code of the
       request is not 0.
    """

    _status_code: Optional[int]
    """
    The status code of the failed request
    """

    _ret_code: Optional[int]
    """
    The return code of the network-ok request
    """

    def __init__(
        self, status_code: Optional[int] = None, ret_code: Optional[int] = None
    ) -> None:
        self._status_code = status_code
        self._ret_code = ret_code

        status_code_str = str(status_code) if status_code is not None else "Unknown"
        ret_code_str = str(ret_code) if ret_code is not None else "Unknown"

        formatted_message = (
            f"NapCat HTTP API encountered an error!. Status code: {status_code_str}, "
            f"Return code: {ret_code_str}"
        )

        super().__init__(formatted_message)


class NapCatCookieExpiredException(NapCatAPIFailureException):
    pass


class NapCatOfflineException(NapCatException):
    pass


class NapCatDisconnectedException(NapCatException):
    pass


class NapCatUnknownException(NapCatException):
    pass
