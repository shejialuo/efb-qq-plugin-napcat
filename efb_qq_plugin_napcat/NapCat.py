import asyncio
import logging
import threading
from typing import Any, Dict

from efb_qq_slave import BaseClient, QQMessengerChannel
from ehforwarderbot import Message, Status


class NapCat(BaseClient):

    client_name = "NapCat Client"
    client_id = "NapCat"

    channel: QQMessengerChannel
    logger: logging.Logger

    def __init__(
        self, client_id: str, config: Dict[str, Any], channel: QQMessengerChannel
    ):
        super().__init__(client_id, config)

        self.channel = channel
        self.logger = logging.getLogger(__name__)

        # Create a new event loop for the slave instance to isolate the event loop
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)

    def login(self) -> None:
        raise NotImplementedError

    def logout(self) -> None:
        raise NotImplementedError

    def relogin(self) -> None:
        raise NotImplementedError

    def send_message(self, msg: Message) -> Message:
        raise NotImplementedError

    def send_status(self, status: Status) -> None:
        raise NotImplementedError

    def receive_message(self) -> None:
        raise NotImplementedError

    def get_friends(self) -> None:
        raise NotImplementedError

    def get_groups(self) -> None:
        raise NotImplementedError

    def get_login_info(self) -> dict[Any, Any]:
        raise NotImplementedError

    def poll(self) -> None:
        """
        EFB will create a thread for each slave instance to call this method to start
        the slave. However, we need to create a new thread to isolate the event loop.
        Otherwise, there may be some unexpected behaviors.
        """

        def _run():
            self.event_loop.run_forever()

        self.t = threading.Thread(target=_run)
        self.t.daemon = True
        self.t.start()

    def stop_polling(self) -> None:
        """
        EFB will call this method to stop the slave instance. However, we cannot simply
        use `self.event_loop.stop()` here, because when calling `self.event_loop.stop()`
        outside the current thread where the event loop is running, it may cause
        deadlock. So we need to use `call_soon_threadsafe` to call
        `self.event_loop.stop()` in the event loop thread to avoid deadlock.
        """

        self.logger.debug("Stopping the NapCat client...")

        self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        self.t.join()
