from typing import TypedDict


class Friend(TypedDict):
    """
    A friend in the qq account. Although there are many other fields
    in the response of the "get_friend_list" action, we only need these
    three fields at the moment.
    """

    user_id: int
    nickname: str
    remark: str
