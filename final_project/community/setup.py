import random
import time
from dataclasses import asdict
import json


from ipv8.community import Community
from ipv8.peerdiscovery.network import PeerObserver
from ipv8.types import Peer
from ipv8_service import IPv8
from ipv8.lazy_community import lazy_wrapper

from db.mempool import Mempool
from manager.blockchain_manager import BlockChainManager


from messages.betpayload import BetPayload
from messages.transaction import TransactionsRequest, TransactionsResponse
from messages.blockchain import BlockChain
from messages.result import LotteryResult


class MyCommunity(Community, PeerObserver):
    community_id = b'harbourspaceuniverse'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Connected Peers
        self._connected_peers = set()
        self.latest_tx_timestamps = {}  # Track the latest timestamp received from each peer

        # Connections
        self.tx_mempool = Mempool()
        self.chain = BlockChain(chain=[], round=1)
        self.chain_manager = BlockChainManager(chain=self.chain)

        # Broadcast
        self.is_lottery_broadcaster = False

        # Tasks
        self.register_task("ensure_full_connectivity",
                           self.ensure_full_connectivity, interval=10.0, delay=3.0)
        self.register_task('request_transactions',
                           self.request_transactions, interval=5.0, delay=1.0)

        self.register_task('create_genesis_block',
                           self.chain_manager.create_genesis_block)

        self.register_task('create_block',
                           self.chain_manager.create_block,
                           interval=10.0, delay=5.0)

        self.register_task('select_lottery_broadcaster',
                           self.select_lottery_broadcaster,
                           interval=20,
                           delay=10.0  # Stagger the selection slightly
                           )

        self.register_task('broadcast_lottery',
                           self.broadcast_lottery,
                           interval=20.0,

                           )

        # Message Handlers
        self.add_message_handler(
            TransactionsRequest, self.on_get_transactions_request)
        self.add_message_handler(TransactionsResponse,
                                 self.on_transactions_response)
        self.add_message_handler(LotteryResult, self.on_lottery_result)

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

        block = {
            "bettor_id": bettor_id,
            "bet_number": bet_number,
            "bet_amount": bet_amount,
            "timestamp": timestamp
        }

        signature = self.crypto.create_signature(
            self.my_peer.key, str(block).encode())

        payload = BetPayload(
            bettor_id=bettor_id,
            bet_number=bet_number,
            bet_amount=bet_amount,
            timestamp=timestamp,
            signature=signature.hex(),
        )

        self.tx_mempool.add_transaction(payload._generate_txid(), payload)
        print(f"Generated and stored transaction: {payload._generate_txid()}")

    # Removed the dual-purpose request, now a dedicated request
    async def request_transactions(self):
        # print("Requesting latest transactions from peers...")
        for peer in self.get_peers():
            peer_id_hex = peer.public_key.key_to_bin().hex()
            last_seen = self.latest_tx_timestamps.get(peer_id_hex, 0.0)
            self.ez_send(peer, TransactionsRequest(
                last_seen_timestamp=last_seen))

    @lazy_wrapper(BetPayload)
    def on_transaction_message(self, peer: Peer, payload: BetPayload):
        # This handler is now solely for processing incoming transactions
        public_key = self.crypto.key_from_public_bin(
            bytes.fromhex(payload.bettor_id))

        enocde_byte = str(payload).encode()

        signature_bytes = bytes.fromhex(payload.signature)

        if self.crypto.is_valid_signature(public_key, enocde_byte, signature_bytes):
            txid = payload._generate_txid()
            if not self.tx_mempool.get_transaction(txid):
                self.tx_mempool.add_transaction(payload)
                print(
                    f"Received and added valid transaction {txid} from {peer.address.port}")
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

    @lazy_wrapper(TransactionsRequest)
    def on_get_transactions_request(self, peer: Peer, payload: TransactionsRequest):
        print(
            f"Received request for transactions since {payload.last_seen_timestamp} from {peer.address.port}")
        latest_txs = self.tx_mempool.get_latest_transactions(
            payload.last_seen_timestamp)
        # Convert the list of transaction dictionaries to a JSON string
        self.ez_send(peer, TransactionsResponse(
            transactions=json.dumps([asdict(tx) for tx in latest_txs])))

    @lazy_wrapper(TransactionsResponse)
    def on_transactions_response(self, peer: Peer, payload: TransactionsResponse):
        print(f"Received transactions from {peer.address.port}")
        try:
            transactions_data = json.loads(payload.transactions)
            for tx_data in transactions_data:
                tx = BetPayload(**tx_data)
                txid = tx._generate_txid()
                if not self.tx_mempool.get_transaction(txid):
                    self.tx_mempool.add_transaction(tx_data)
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

    async def broadcast_lottery(self):

        if self.is_lottery_broadcaster:
            lottery_result = self.chain_manager.get_winning_number()
            if lottery_result is not None:
                for peer in self.get_peers():
                    self.ez_send(peer, LotteryResult(
                        round=self.chain.round, winning_number=lottery_result))
                self.is_lottery_broadcaster = False  # Reset after broadcasting

    async def select_lottery_broadcaster(self):
        all_peers = list(self.get_peers()) + [self.my_peer]
        if all_peers:
            sorted_peers = sorted(
                all_peers, key=lambda p: p.public_key.key_to_bin().hex())
            broadcaster = sorted_peers[0]
            if broadcaster == self.my_peer:
                self.is_lottery_broadcaster = True
            else:
                self.is_lottery_broadcaster = False
            print(
                f"{broadcaster.address.port} is the lottery broadcaster (lowest peer ID).")
        else:
            print("No peers available to select a lottery broadcaster.")
            self.is_lottery_broadcaster = False

    @lazy_wrapper(LotteryResult)
    def on_lottery_result(self, peer: Peer, payload: LotteryResult):
        print(
            f"Received lottery result for round {payload.round} from {peer.address.port}: Winning number is {payload.winning_number}")

    def started(self) -> None:
        self.network.add_peer_observer(self)
        self.add_message_handler(BetPayload, self.on_transaction_message)

        self.register_task('generate_transaction',
                           self.generate_transaction, interval=2.0, delay=0)
