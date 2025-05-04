import json
import random
import time

from ipv8.community import Community
from ipv8.lazy_community import lazy_wrapper
from ipv8.types import Peer
from ipv8.peerdiscovery.network import PeerObserver
from ipv8.peerdiscovery.discovery import RandomWalk
from messages import Message, MessagesCollection, GetMessages

from db import Database

db = Database()


class MessageContainer:
    def __init__(self, msg: Message):
        self.__ttl: float = time.time()
        self.__msg: Message = msg

    def expired(self, timestamp: float) -> bool:
        return timestamp - self.__ttl > 60

    def message(self) -> Message:
        return self.__msg


class DenseRandomWalk(RandomWalk):
    """
    Dense And Sparse Random Walk Strategy
    return:
    """

    def __init__(self, overlay, **kwargs):
        super().__init__(overlay, **kwargs)
        self.community = overlay

    def take_step(self) -> None:
        for peer in self.community.network.verified_peers:
            if peer not in self.community._connected_peers:
                self.community.walk_to(peer.address)
                self.community._connected_peers.add(peer)

        super().take_step()


class BlockchainCommunity(Community, PeerObserver):
    community_id = b'axiom_vaultcommunity'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Track peers that have already been connected to avoid redundancy
        self._connected_peers = set()
        self.__messages = {}  # Initialize messages dictionary

        self.register_task("ensure_full_connectivity",
                           self.ensure_full_connectivity, interval=10.0, delay=5.0)

    async def ensure_full_connectivity(self):
        # Use verified_peers directly instead of trying to access graph
        connected_peers = set(self.network.verified_peers)
        for peer in connected_peers:
            if peer not in self._connected_peers:
                self._connected_peers.add(peer)
                self.walk_to(peer.address)
                print(f"Connecting to previously discovered peer: {peer}")

    def on_peer_added(self, peer: Peer) -> None:
        print("I am:", self.my_peer, "I found:", peer)
        self.walk_to(peer.address)
        self._connected_peers.add(peer)

    def on_peer_removed(self, peer: Peer) -> None:
        if peer in self._connected_peers:
            self._connected_peers.remove(peer)

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
        print(
            f"{self.my_peer.address.port}: received from {peer.address.port}", payload.messages)

        db.update(peer.address.port, self.my_peer.address.port)

        decoded_messages = json.loads(payload.messages)
        for msg_content in decoded_messages:
            message = Message(content=msg_content)
            message_hash = message.hash()

            if message_hash not in self.__messages:
                self.__messages[message_hash] = MessageContainer(message)

    async def clear_expired_messages(self):
        current_time = time.time()

        expired_keys = [k for k, v in self.__messages.items()
                        if v.expired(current_time)]
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
        self.network.add_peer_observer(self)  # Register as a peer observer

        self.register_task(
            "dense_random_walk",
            lambda: DenseRandomWalk(self, timeout=3.0).take_step(),
            interval=10.0,
            delay=5.0
        )

        test_message = Message(f"Random number is {random.randint(1, 100)}")
        self.__messages[test_message.hash()] = MessageContainer(test_message)

        self.add_message_handler(GetMessages, self.return_messages_handler)
        self.add_message_handler(
            MessagesCollection, self.messages_collection_handler)

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
