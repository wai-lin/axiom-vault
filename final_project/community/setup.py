# main.py (or your community file)
import random
import time
from dataclasses import asdict
import json


from ipv8.community import Community
from ipv8.peerdiscovery.network import PeerObserver
from ipv8.types import Peer
from ipv8_service import IPv8
from ipv8.lazy_community import lazy_wrapper

from db.instance import Mempool
from messages.betpayload import BetPayload, GetTransactionsRequest, TransactionsResponse


class MyCommunity(Community, PeerObserver):
    community_id = b'harbourspaceuniverse'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._connected_peers = set()
        self.tx_db = Mempool()
        self.latest_tx_timestamps = {}  # Track the latest timestamp received from each peer

        self.register_task("ensure_full_connectivity",
                           self.ensure_full_connectivity, interval=10.0, delay=5.0)
        self.register_task('request_transactions',
                           self.request_transactions, interval=5.0, delay=2.0)

        self.add_message_handler(
            GetTransactionsRequest, self.on_get_transactions_request)
        self.add_message_handler(TransactionsResponse,
                                 self.on_transactions_response)

    # Peer Set up

    def on_peer_added(self, peer: Peer) -> None:
        print("I am:", self.my_peer, "I found:", peer)
        self.walk_to(peer.address)
        self._connected_peers.add(peer)
        # Initialize timestamp
        self.latest_tx_timestamps[peer.public_key.key_to_bin().hex()] = 0.0

    def on_peer_removed(self, peer: Peer) -> None:
        peer_id = peer.public_key.key_to_bin().hex()
        if peer in self._connected_peers:
            self._connected_peers.remove(peer)
        if peer_id in self.latest_tx_timestamps:
            del self.latest_tx_timestamps[peer_id]

    async def ensure_full_connectivity(self):
        connected_peers = set(self.network.verified_peers)
        for peer in connected_peers:
            peer_id = peer.public_key.key_to_bin().hex()
            if peer not in self._connected_peers:
                self._connected_peers.add(peer)
                self.walk_to(peer.address)
                self.latest_tx_timestamps[peer_id] = 0.0
                print(f"Connecting to previously discovered peer: {peer}")

    # Generate Transaction (remains the same, won't be proactively sent)
    async def generate_transaction(self) -> None:
        print("Generating transaction...")
        bettor_id = self.crypto.key_to_bin(self.my_peer.public_key).hex()
        bet_number = random.randint(1, 100)
        bet_amount = random.randint(1, 100)
        timestamp = time.time()
        signature = self.crypto.create_signature(
            self.my_peer.key, str(timestamp).encode())
        payload = BetPayload(
            bettor_id=bettor_id,
            bet_number=bet_number,
            bet_amount=bet_amount,
            timestamp=timestamp,
            signature=signature.hex(),
        )
        self.tx_db.add_transaction(payload._generate_txid(), payload)
        print(f"Generated and stored transaction: {payload._generate_txid()}")

    # Removed the dual-purpose request, now a dedicated request
    async def request_transactions(self):
        print("Requesting latest transactions from peers...")
        for peer in self.get_peers():
            peer_id_hex = peer.public_key.key_to_bin().hex()
            last_seen = self.latest_tx_timestamps.get(peer_id_hex, 0.0)
            self.ez_send(peer, GetTransactionsRequest(
                last_seen_timestamp=last_seen))

    @lazy_wrapper(BetPayload)
    def on_transaction_message(self, peer: Peer, payload: BetPayload):
        # This handler is now solely for processing incoming transactions
        bettor_id_key = self.crypto.key_from_public_bin(
            bytes.fromhex(payload.bettor_id))
        timestamp_bytes = str(payload.timestamp).encode()
        signature_bytes = bytes.fromhex(payload.signature)

        if self.crypto.is_valid_signature(bettor_id_key, timestamp_bytes, signature_bytes):
            txid = payload._generate_txid()
            if not self.tx_db.get_transaction(txid):
                tx_dict = asdict(payload)
                self.tx_db.db[txid] = tx_dict
                print(
                    f"Received and added valid transaction {txid} from {peer.address.port}")
                # Update timestamp upon receiving a new transaction
                peer_id_hex = peer.public_key.key_to_bin().hex()
                self.latest_tx_timestamps[peer_id_hex] = max(
                    self.latest_tx_timestamps.get(peer_id_hex, 0.0), payload.timestamp)
            else:
                # Optionally update timestamp even if transaction exists
                peer_id_hex = peer.public_key.key_to_bin().hex()
                self.latest_tx_timestamps[peer_id_hex] = max(
                    self.latest_tx_timestamps.get(peer_id_hex, 0.0), payload.timestamp)
        else:
            print(f"Received invalid transaction from {peer.address.port}")

    @lazy_wrapper(GetTransactionsRequest)
    def on_get_transactions_request(self, peer: Peer, payload: GetTransactionsRequest):
        print(
            f"Received request for transactions since {payload.last_seen_timestamp} from {peer.address.port}")
        latest_txs = self.get_latest_transactions(payload.last_seen_timestamp)
        # Convert the list of transaction dictionaries to a JSON string
        self.ez_send(peer, TransactionsResponse(
            transactions=json.dumps([asdict(tx) for tx in latest_txs])))

    @lazy_wrapper(TransactionsResponse)
    def on_transactions_response(self, peer: Peer, payload: TransactionsResponse):
        print(f"Received transactions from {peer.address.port}")
        try:
            # Deserialize the JSON string back into a list of transaction dictionaries
            transactions_data = json.loads(payload.transactions)
            for tx_data in transactions_data:
                tx = BetPayload(**tx_data)
                txid = tx._generate_txid()
                if not self.tx_db.get_transaction(txid):
                    self.tx_db.db[txid] = tx_data
                    print(f"Added received transaction: {txid}")
                    peer_id_hex = peer.public_key.key_to_bin().hex()
                    self.latest_tx_timestamps[peer_id_hex] = max(
                        self.latest_tx_timestamps.get(peer_id_hex, 0.0), tx.timestamp)
                else:
                    peer_id_hex = peer.public_key.key_to_bin().hex()
                    self.latest_tx_timestamps[peer_id_hex] = max(
                        self.latest_tx_timestamps.get(peer_id_hex, 0.0), tx.timestamp)
        except json.JSONDecodeError as e:
            print(
                f"Error decoding transactions response from {peer.address.port}: {e}")

    def get_latest_transactions(self, last_seen_timestamp: float) -> list[BetPayload]:
        latest_txs = []
        for txid, tx_data in self.tx_db.db.items():
            if tx_data and tx_data.get('timestamp', 0.0) > last_seen_timestamp:
                latest_txs.append(BetPayload(**tx_data))
        return latest_txs

    def started(self) -> None:
        self.network.add_peer_observer(self)
        self.add_message_handler(BetPayload, self.on_transaction_message)

        self.register_task('generate_transaction',
                           self.generate_transaction, interval=2.0, delay=0)
