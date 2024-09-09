import asyncio

import pytest

from efb_qq_plugin_napcat.napcat.exceptions import NapCatAPIFailureException
from efb_qq_plugin_napcat.napcat.friend_manager import NapCatFriendManager
from efb_qq_plugin_napcat.napcat.napcat_bot import NapCatBot


@pytest.fixture
def friend_manager() -> NapCatFriendManager:

    config = {
        "api_root": "http://localhost:6700",
        "access_token": "",
        "api_timeout": 10,
    }

    bot = NapCatBot(config)
    bot._logged_in = True
    bot._connected = True

    return NapCatFriendManager(bot)


@pytest.fixture(scope="session")
def httpserver_listen_address():
    return ("localhost", 6700)


class TestUpdateFriendList:

    def test_empty_friend(self, friend_manager: NapCatFriendManager, httpserver):

        httpserver.expect_request(
            "/get_friend_list",
            method="POST",
            json={"no_cache": True},
        ).respond_with_json(
            {
                "status": "ok",
                "retcode": 0,
                "data": [],
            }
        )

        asyncio.run(friend_manager.update_friend_list())

        assert len(friend_manager.friend_list) == 0
        assert len(friend_manager.uid_to_friend) == 0

    def test_multiple_update(self, friend_manager: NapCatFriendManager, httpserver):

        httpserver.expect_request(
            "/get_friend_list",
            method="POST",
            json={"no_cache": True},
        ).respond_with_json(
            {
                "status": "ok",
                "retcode": 0,
                "data": [
                    {"user_id": 1, "nickname": "Alice", "remark": "Alice"},
                    {"user_id": 2, "nickname": "Bob", "remark": "Bob"},
                ],
            }
        )

        asyncio.run(friend_manager.update_friend_list())

        assert len(friend_manager.friend_list) == 2
        assert len(friend_manager.uid_to_friend) == 2

        httpserver.clear()
        httpserver.expect_request(
            "/get_friend_list",
            method="POST",
            json={"no_cache": True},
        ).respond_with_json(
            {
                "status": "ok",
                "retcode": 0,
                "data": [
                    {"user_id": 3, "nickname": "Charlie", "remark": "Charlie"},
                ],
            }
        )

        asyncio.run(friend_manager.update_friend_list())

        assert len(friend_manager.friend_list) == 1
        assert len(friend_manager.uid_to_friend) == 3
        assert friend_manager.uid_to_friend[3]["user_id"] == 3
        assert friend_manager.uid_to_friend[3]["nickname"] == "Charlie"
        assert friend_manager.uid_to_friend[3]["remark"] == "Charlie"

    def test_update_error(self, friend_manager: NapCatFriendManager, httpserver):

        httpserver.expect_request(
            "/get_friend_list",
            method="POST",
            json={"no_cache": True},
        ).respond_with_json(
            {
                "status": "failed",
                "retcode": 1,
            }
        )

        with pytest.raises(NapCatAPIFailureException):
            asyncio.run(friend_manager.update_friend_list())


class TestGetFriendRemark:
    def test_sanity_friend_remark(self, friend_manager: NapCatFriendManager, httpserver):
        httpserver.expect_request(
            "/get_friend_list",
            method="POST",
            json={"no_cache": True},
        ).respond_with_json(
            {
                "status": "ok",
                "retcode": 0,
                "data": [
                    {"user_id": 1, "nickname": "Alice", "remark": ""},
                ],
            }
        )

        result = asyncio.run(friend_manager.get_friend_remark(1))
        assert result == "Alice"

    def test_none_friend_remark(self, friend_manager: NapCatFriendManager, httpserver):
        httpserver.expect_request(
            "/get_friend_list",
            method="POST",
            json={"no_cache": True},
        ).respond_with_json(
            {
                "status": "ok",
                "retcode": 0,
                "data": [
                    {"user_id": 1, "nickname": "Alice", "remark": ""},
                ],
            }
        )

        result = asyncio.run(friend_manager.get_friend_remark(3))
        assert result is None

    def test_empty_friend_remark(self, friend_manager: NapCatFriendManager, httpserver):
        httpserver.expect_request(
            "/get_friend_list",
            method="POST",
            json={"no_cache": True},
        ).respond_with_json(
            {
                "status": "ok",
                "retcode": 0,
                "data": [
                    {"user_id": 1, "nickname": "Alice", "remark": ""},
                ],
            }
        )

        result = asyncio.run(friend_manager.get_friend_remark(1))
        assert result == "Alice"
