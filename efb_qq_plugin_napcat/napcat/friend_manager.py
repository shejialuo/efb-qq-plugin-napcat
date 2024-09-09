import logging
from typing import Optional, TypedDict

from efb_qq_plugin_napcat.napcat.napcat_bot import NapCatBot
from efb_qq_plugin_napcat.napcat.types.friend import Friend


class _GetFriendListRequest(TypedDict):
    no_cache: bool


_GetFriendListResponse = list[Friend]


class NapCatFriendManager:

    _napcat_bot: NapCatBot
    """
    The NapCatBot instance
    """

    _friend_list: list[Friend]
    """
    The friend list of the qq account
    """

    _uid_to_friend: dict[int, Friend]
    """
    The mapping from the user id to the friend instance
    """

    _logger: logging.Logger
    """
    The logger instance
    """

    def __init__(self, napcat_bot: NapCatBot) -> None:
        self._napcat_bot = napcat_bot
        self._friend_list = []
        self._uid_to_friend = {}
        self._logger = logging.getLogger(__name__)

    @property
    def friend_list(self) -> list[Friend]:
        return self._friend_list

    @property
    def uid_to_friend(self) -> dict[int, Friend]:
        return self._uid_to_friend

    async def _get_friend_list(
        self, request: _GetFriendListRequest
    ) -> _GetFriendListResponse:
        """
        Get the friend list of the qq account.
        """

        res = await self._napcat_bot.call_action("get_friend_list", **request)
        return res

    def _update_friend_list_callback(self, qq_friends: _GetFriendListResponse) -> None:
        """
        When successfully updating the friend list, we will update the
        `_friend_list` and `_uid_to_friend` attributes. Because the
        `response` may contain many unused fields. It's not suitable just
        assign the `response` to the `_friend_list` attribute. Because
        Python is a dynamic language, it will cost a lot of memory to
        store the unused fields. So we will only store the fields we need.

        Then we populate the mapping from the user id to the friend instance.
        We will never clear the mapping. We will only update the mapping
        when we update the friend list.

        So there may be some friends that are not in the friend list but
        in the mapping. However, we will not remove them from the mapping.
        Only when you delete a friend from the QQ account, this situation
        will happen, if you delete one, I guess you will not care about
        this so called friend anymore. :)
        """

        self._friend_list.clear()

        for qq_friend in qq_friends:

            new_friend = Friend(
                user_id=qq_friend["user_id"],
                nickname=qq_friend["nickname"],
                remark=(
                    qq_friend["remark"]
                    if qq_friend["remark"] != ""
                    else qq_friend["nickname"]
                ),
            )

            self._friend_list.append(new_friend)
            self._uid_to_friend[new_friend["user_id"]] = new_friend

    async def update_friend_list(self, no_cache: bool = True) -> None:
        """
        Get the friend list of the qq account. However, the res should
        never be None. If the res is None, we will log a warning message.
        It may be a bug from the NapCat upstream.
        """

        request: _GetFriendListRequest = {"no_cache": no_cache}
        qq_friends = await self._get_friend_list(request)

        if qq_friends:
            self._logger.debug("Updated friend list")

            self._update_friend_list_callback(qq_friends)
        else:
            self._logger.warning("Failed to update the friend list")

    async def get_friend_remark(self, uid: int) -> Optional[str]:
        """
        Get the remark of one friend by uid. If we cannot find the friend,
        we will first forcedly update the friend list and try again. If
        we still cannot find the friend, we will return None. Otherwise,
        we will return the remark of the friend.
        """

        if (not self._friend_list) or (uid not in self._uid_to_friend):
            await self.update_friend_list()

        if uid not in self._uid_to_friend:
            return None

        return self._uid_to_friend[uid]["remark"]
