import asyncio
import logging
from typing import Any, TypedDict

import aiocqhttp

from efb_qq_plugin_napcat.napcat.exceptions import (
    NapCatAPIFailureException,
    NapCatDisconnectedException,
    NapCatException,
    NapCatOfflineException,
    NapCatUnknownException,
)


class _GetStatusRequest(TypedDict):
    pass


class _GetStatusResponse(TypedDict):
    online: bool
    good: bool


class NapCatBot:
    """
    The NapCatBot class is used to interact with the NapCat client.
    It provides the following functionalities:

    1. Check the status of the NapCat client.
    2. Check the status of the NapCat client periodically.
    3. Call actions of the NapCat client (generic).

    The caller should create a new class which contains the NapCatBot instance
    and provide more high-level functionalities.
    """

    _qq_bot: aiocqhttp.CQHttp

    """
    The coolq bot instance
    """

    _logged_in: bool
    """
    The login status of the bot
    """

    _connected: bool
    """
    The connection status of the bot
    """

    _repeat_num: int
    """
    The number of repeated times to send the failure information to the user
    """

    _logger: logging.Logger
    """
    The logger instance
    """

    _check_status_interval: int
    """
    The interval to check the status of the NapCat client
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._qq_bot = aiocqhttp.CQHttp(
            api_root=config["api_root"],
            access_token=config["access_token"],
            api_timeout_sec=config["api_timeout"],
        )
        self._logged_in = False
        self._connected = False
        self._repeat_num = 0
        self._logger = logging.getLogger(__name__)
        self._check_status_interval = 300

    def is_logged_in(self) -> bool:
        return self._logged_in

    def is_connected(self) -> bool:
        return self._connected

    async def _call_action_wrapper(self, action_name: str, **kwargs: Any) -> Any:
        """
        Wrapper for calling actions. This method will handle the exceptions raised
        by the aiocqhttp client. It will raise the following exceptions:

        1. NapCatDisconnectedException: The NapCat client is disconnected.
        2. NapCatAPIFailureException: The NapCat HTTP API fails.

        If the action is called successfully, the return value will be returned. This
        method is generic and can be used to call any action of the NapCat client.

        Caller should never call this method directly, instead, they should call
        `call_action` method.
        """

        try:
            res = await self._qq_bot.call_action(action_name, **kwargs)  # type: ignore
        except aiocqhttp.NetworkError as e:
            raise NapCatDisconnectedException(
                f"Unable to connect to napcat client!. Error message: {e}"
            )
        except aiocqhttp.Error as ex:
            status_code = getattr(ex, "status_code", None)
            ret_code = getattr(ex, "retcode", None)

            raise NapCatAPIFailureException(status_code, ret_code)
        else:
            return res

    async def call_action(self, action_name: str, **kwargs: Any) -> Any:
        if self._logged_in and self._connected:
            return await self._call_action_wrapper(action_name, **kwargs)

        if self._repeat_num < 3:
            # TODO: Send the failure information to the user
            self._repeat_num += 1

    async def _get_status(self) -> _GetStatusResponse:
        """
        Get the status of the NapCat client. In this function, we use
        the `_call_action_wrapper` method to call the `get_status` action
        of the NapCat client. We do not use the `call_action` method here,
        because `self._logged_in` and `self._connected` should not be checked
        in this function.
        """

        request = _GetStatusRequest()
        res = await self._call_action_wrapper("get_status", **request)

        return res

    async def _check_running_status(self) -> bool | None:
        """
        Check the running status of the NapCat client.
        """

        res: _GetStatusResponse = await self._get_status()
        if res["good"] or res["online"]:
            return True
        else:
            raise NapCatOfflineException("NapCat client isn't working correctly!")

    def _status_bad_callback(self, exception: NapCatException) -> None:
        """
        Callback function when the status of the NapCat client is bad.
        """

        if self._repeat_num < 3:
            # TODO: Send the failure information to the user
            self._repeat_num += 1

        self._connected = False
        self._logged_in = False
        self._check_status_interval = 3600

    def _status_good_callback(self) -> None:
        """
        Callback function when the status of the NapCat client is good.
        """

        self._connected = True
        self._logged_in = True
        self._check_status_interval = 300
        self._repeat_num = 0

    async def check_status_periodically(self, run_once: bool = False) -> None:
        """
        Check the status of the NapCat client periodically. There could be three
        possible exceptions raised here:

        1. NapCatDisconnectedException: The NapCat client is disconnected.
        2. NapCatAPIFailureException: The NapCat HTTP API fails.
        3. NapCatOfflineException: The NapCat client is offline.

        If the status is still bad, we will create a new exception called
        "NapCatUnknownException" to indicate that an unknown error occurred
        and call the `_status_bad_callback` method. Otherwise, the status is good,
        and the `_status_good_callback` method will be called.
        """

        while True:
            self._logger.debug("Checking the status of the NapCat client...")
            flag = True

            try:
                flag = await self._check_running_status()
            except (
                NapCatDisconnectedException,
                NapCatOfflineException,
                NapCatAPIFailureException,
            ) as e:
                self._status_bad_callback(e)
            else:
                if not flag:
                    self._status_bad_callback(
                        NapCatUnknownException("Unknown error occurred!")
                    )
                else:
                    self._status_good_callback()

            if run_once:
                return

            await asyncio.sleep(self._check_status_interval)
