import json
import random
import time
from typing import Dict, Any, List

from ipv8.community import Community, CommunitySettings
from ipv8.lazy_community import lazy_wrapper
from ipv8.types import Peer

from messages import Message, MessagesCollection, GetMessages


class MessageContainer:
    def __init__(self, msg: Message):
        self.__ttl: float = time.time()
        self.__msg: Message = msg

    def expired(self, timestamp: float) -> bool:
        return timestamp - self.__ttl > 60

    def message(self) -> Message:
        return self.__msg


class BlockchainCommunity(Community):
    community_id = b'axiom_vaultcommunity'

    def __init__(self, settings: CommunitySettings):
        super().__init__(settings)

        self.__messages: Dict[str, MessageContainer] = dict()

    @lazy_wrapper(GetMessages)
    async def return_messages_handler(self, peer: Peer, payload: GetMessages):
        current_time = time.time()

        messages = []
        for container in self.__messages.values():
            if not container.expired(current_time):
                messages.append(container.message().content)

        print(f"{self.my_peer.address.port}: sending", messages)

        encoded_messages = json.dumps(messages)
        self.ez_send(peer, MessagesCollection(messages=encoded_messages))

    @lazy_wrapper(MessagesCollection)
    async def messages_collection_handler(self, peer: Peer, payload: MessagesCollection):
        print(f"{self.my_peer.address.port}: received from {peer.address.port}", payload.messages)

        decoded_messages = json.loads(payload.messages)
        for msg_content in decoded_messages:
            message = Message(content=msg_content)
            message_hash = message.hash()

            if message_hash not in self.__messages:
                self.__messages[message_hash] = MessageContainer(message)

    async def clear_expired_messages(self):
        current_time = time.time()

        expired_keys = [k for k, v in self.__messages.items() if v.expired(current_time)]
        for k in expired_keys:
            del self.__messages[k]

        print(f"{self.my_peer.address.port}: my messages", len(self.__messages))

    async def request_messages(self):
        for peer in self.get_peers():
            self.ez_send(peer, GetMessages())

    def started(self) -> None:
        """
        Responsible for handling messages and registering tasks
        :return:
        """

        test_message = Message(f"Random number is {random.randint(1, 100)}")
        self.__messages[test_message.hash()] = MessageContainer(test_message)

        self.add_message_handler(GetMessages, self.return_messages_handler)
        self.add_message_handler(MessagesCollection, self.messages_collection_handler)

        self.register_task(
            'clear_expired_messages',
            self.clear_expired_messages,
            interval=10,
            delay=30
        )

        self.register_task(
            'request_messages',
            self.request_messages,
            interval=10,
            delay=0
        )

