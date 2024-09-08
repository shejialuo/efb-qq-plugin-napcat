import asyncio

import pytest

from efb_qq_plugin_napcat.napcat.exceptions import (
    NapCatAPIFailureException,
    NapCatOfflineException,
)
from efb_qq_plugin_napcat.napcat.napcat_bot import NapCatBot


@pytest.fixture
def bot() -> NapCatBot:

    config = {
        "api_root": "http://localhost:6700",
        "access_token": "",
        "api_timeout": 10,
    }

    return NapCatBot(config)


@pytest.fixture(scope="session")
def httpserver_listen_address():
    return ("localhost", 6700)


class TestCallActionWrapper:
    """
    Test the `_call_action_wrapper` method of the NapCatBot class.
    """

    def test_bad_status_code(self, bot: NapCatBot, httpserver):

        httpserver.expect_request("/bad_status_code").respond_with_data(
            "bad_status_code", status=404
        )

        with pytest.raises(NapCatAPIFailureException) as ex_info:
            asyncio.run(bot._call_action_wrapper("bad_status_code"))

        assert ex_info.value._status_code == 404

    def test_bad_status(self, bot: NapCatBot, httpserver):

        httpserver.expect_request("/bad_status").respond_with_json(
            {"status": "failed", "retcode": 22}
        )

        with pytest.raises(NapCatAPIFailureException) as ex_info:
            asyncio.run(bot._call_action_wrapper("bad_status"))

        assert ex_info.value._status_code is None
        assert ex_info.value._ret_code == 22


class TestCheckRunningStatus:
    """
    Test the `_check_running_status` method of the NapCatBot class.
    """

    def test_good_status(self, bot: NapCatBot, httpserver):
        httpserver.expect_request("/get_status").respond_with_json(
            {
                "status": "ok",
                "retcode": 0,
                "data": {"online": False, "good": True},
            }
        )

        status = asyncio.run(bot._check_running_status())

        assert status == True

    def test_online_status(self, bot: NapCatBot, httpserver):
        httpserver.expect_request("/get_status").respond_with_json(
            {
                "status": "ok",
                "retcode": 0,
                "data": {"online": True, "good": False},
            }
        )

        status = asyncio.run(bot._check_running_status())

        assert status == True

    def test_bad_napcat_status(self, bot: NapCatBot, httpserver):
        httpserver.expect_request("/get_status").respond_with_json(
            {
                "status": "ok",
                "retcode": 0,
                "data": {"online": False, "good": False},
            }
        )

        with pytest.raises(NapCatOfflineException):
            asyncio.run(bot._check_running_status())
