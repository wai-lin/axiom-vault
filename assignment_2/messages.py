from ipv8.messaging.payload_dataclass import dataclass

from hashlib import sha256

@dataclass(msg_id=1)
class GetMessages:
    pass


@dataclass(msg_id=2)
class Message:
    content: str

    def hash(self) -> str:
        return sha256(self.content.encode()).hexdigest()



# pull-based currently we are sending out all the messages
# can apply bloom filters (arr of bits)
# enables you to check if an element is present (XOR) in a set using a very small memory space
@dataclass(msg_id=3)
class MessagesCollection:
    messages: str