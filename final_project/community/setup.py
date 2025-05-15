import random
import time
from dataclasses import asdict
import json
import asyncio


from ipv8.community import Community
from ipv8.peerdiscovery.network import PeerObserver
from ipv8.types import Peer
from ipv8_service import IPv8
from ipv8.lazy_community import lazy_wrapper

from db.mempool import Mempool
from manager.blockchain import BlockChain


from messages.betpayload import BetPayload
from messages.transaction import TransactionsRequest, TransactionsResponse
from messages.block import Block
from messages.result import LotteryResult

from utils.discovery_log import PeerDiscoveryTracker
from utils.transaction_log import TxCoverageTracker

from constant import BLOCKS_PER_ROUND


class MyCommunity(Community, PeerObserver):
    community_id = b"hcustomspaceuniverse"

    def __init__(self, settings) -> None:
        super().__init__(settings)

        # Connected Peers
        self._connected_peers = set()
        self.latest_tx_timestamps = (
            {}
        )  # Track the latest timestamp received from each peer
        self._known_peers = set()  # Keep track of all discovered peers

        # Connections
        self.tx_mempool = Mempool()
        self.chain = BlockChain()

        # Mining
        self.is_miner = False

        # Network Establishment
        self.network_established = False
        # Time to wait for peers (adjust as needed)
        self.establishment_timeout = 10.0
        self.establishment_start_time = time.time()

        # Broadcast
        self.is_lottery_broadcaster = False

        # Utils
        self.node_id = settings.node_id
        self.peer_discovery_tracker = PeerDiscoveryTracker(self.node_id)
        self.tx_tracker = TxCoverageTracker(self.node_id)

        # Tasks
        self.register_task(
            "ensure_full_connectivity",
            self.ensure_full_connectivity,
            interval=5.0,
            delay=3.0,
        )

        self.register_task(
            "request_transactions", self.request_transactions, interval=5.0, delay=1.0
        )

        self.register_task('select_lottery_broadcaster',
                           self.select_lottery_broadcaster,
                           delay=10.0  # Stagger the selection slightly
                           )

        # For Block messages
        self.add_message_handler(Block, self.on_block)

        # For Syncing Mempools
        self.add_message_handler(
            TransactionsRequest, self.on_get_transactions_request)
        self.add_message_handler(TransactionsResponse,
                                 self.on_transactions_response)

        # For Betpayload
        self.add_message_handler(BetPayload, self.on_transaction_message)

        # For Lottery
        self.add_message_handler(LotteryResult, self.on_lottery_result)

        # Task to generate transactions, will be started conditionally
        self.generate_tx_task = None

        # Initial call to start the mining cycle if this node is the initial miner
        self.register_task(
            'mine_and_broadcast', self._mine_and_broadcast, delay=10)

    # Peer Set up

    def on_peer_added(self, peer: Peer) -> None:
        # print("I am:", self.my_peer, "I found:", peer)
        self.walk_to(peer.address)
        self.peer_discovery_tracker.update(
            self.my_peer.mid.hex(), peer.mid.hex())
        self._connected_peers.add(peer)
        # Track discovered peers
        self._known_peers.add(peer.public_key.key_to_bin().hex())
        # Initialize timestamp
        self.latest_tx_timestamps[peer.public_key.key_to_bin().hex()] = 0.0
        self._determine_miner()

    def on_peer_removed(self, peer: Peer) -> None:
        peer_id = peer.public_key.key_to_bin().hex()
        if peer in self._connected_peers:
            self._connected_peers.remove(peer)
        if peer_id in self.latest_tx_timestamps:
            del self.latest_tx_timestamps[peer_id]
        if peer_id in self._known_peers:
            self._known_peers.remove(peer_id)
        self._determine_miner()

    def _determine_miner(self):
        """Selects the miner based on the highest peer ID among connected peers."""
        all_peers = list(self._connected_peers) + [self.my_peer]
        if all_peers:
            sorted_peers = sorted(
                all_peers, key=lambda p: p.public_key.key_to_bin().hex(), reverse=True
            )
            potential_miner = sorted_peers[0]
            if potential_miner == self.my_peer:
                if not self.is_miner:
                    self.is_miner = True
                    print(
                        f"{self.my_peer.address.port} is now the miner (highest peer ID)."
                    )
                    # No need to start a continuous task here, _trigger_mining will handle it
                # Keep can_mine True if still the miner
            else:
                if self.is_miner:
                    self.is_miner = False
        else:
            self.is_miner = False
            print(f"{self.my_peer.address.port}: No peers, not the miner.")

    async def ensure_full_connectivity(self):
        current_time = time.time()
        elapsed_time = current_time - self.establishment_start_time
        num_connected = len(self._connected_peers)

        # Define your criteria for "full establishment" here.
        # For example, wait for a certain number of peers or a timeout.
        if (
            elapsed_time > self.establishment_timeout
            and num_connected > 1
            and not self.network_established
        ):
            self.network_established = True
            print(f"{self.my_peer.address.port}:  Network considered established.")

            if self.is_miner and self.chain._get_length() == 0:
                genesis_block = self.chain.create_genesis_block()
                await self.broadcast_block(genesis_block)

            # Start generating transactions now that the network is established
            if self.generate_tx_task is None:
                print(f"{self.my_peer.address.port}: Start Sending Transaction.")
                self.generate_tx_task = self.register_task(
                    "generate_transaction",
                    self.generate_transaction,
                    interval=5.0,
                    delay=5,
                )
        elif not self.network_established:
            connected_peers = set(self.network.verified_peers)
            for peer in connected_peers:
                peer_id = peer.public_key.key_to_bin().hex()
                if peer not in self._connected_peers:
                    self._connected_peers.add(peer)
                    self._known_peers.add(peer_id)
                    self.walk_to(peer.address)
                    self.latest_tx_timestamps[peer_id] = 0.0
                    # print(f"Connecting to previously discovered peer: {peer}")
            self._determine_miner()  # Re-evaluate miner after new connections

    # Generate Transaction (remains the same, won't be proactively sent)
    async def generate_transaction(self) -> None:

        # Miner Node Will Not Do Transactions
        if self.is_miner:
            return

        # print("Generating transaction...")
        bettor_id = self.crypto.key_to_bin(self.my_peer.public_key).hex()
        bet_number = random.randint(1, 100)
        bet_amount = random.randint(1, 100)
        timestamp = time.time()

        block = {
            "bettor_id": bettor_id,
            "bet_number": bet_number,
            "bet_amount": bet_amount,
            "timestamp": timestamp,
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

        txid = payload._generate_txid()
        self.tx_mempool.add_transaction(txid, payload)
        self.tx_tracker.record(self.chain._get_round_number(), txid, timestamp)
        # print(f"Generated and stored transaction: {txid}")

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
                self.tx_mempool.add_transaction(
                    payload._generate_txid(), payload)
                self.tx_tracker.record(
                    self.chain._get_round_number(), txid, payload.timestamp
                )
                # print(
                #     f"Received and added valid transaction {txid} from {peer.address.port}")
                peer_id_hex = peer.public_key.key_to_bin().hex()
                self.latest_tx_timestamps[peer_id_hex] = max(
                    self.latest_tx_timestamps.get(
                        peer_id_hex, 0.0), payload.timestamp
                )
                # Trigger mining as new transactions arrive
                if self.is_miner and self.network_established:
                    self._safely_register_mining_task()
            else:
                # Optionally update timestamp even if transaction exists
                peer_id_hex = peer.public_key.key_to_bin().hex()
                self.latest_tx_timestamps[peer_id_hex] = max(
                    self.latest_tx_timestamps.get(
                        peer_id_hex, 0.0), payload.timestamp
                )
        else:
            # print(f"Received invalid transaction from {peer.address.port}")
            pass

    @lazy_wrapper(TransactionsRequest)
    def on_get_transactions_request(self, peer: Peer, payload: TransactionsRequest):
        MAX_TRANSACTIONS_PER_RESPONSE = 50
        latest_txs = self.tx_mempool.get_latest_transactions(
            payload.last_seen_timestamp)
        batch = [asdict(tx)
                 for tx in latest_txs[:MAX_TRANSACTIONS_PER_RESPONSE]]
        remaining = len(latest_txs) > MAX_TRANSACTIONS_PER_RESPONSE
        self.ez_send(peer, TransactionsResponse(
            transactions=json.dumps(batch),
            has_more=remaining
        ))

    @lazy_wrapper(TransactionsResponse)
    def on_transactions_response(self, peer: Peer, payload: TransactionsResponse):
        try:
            transactions_data = json.loads(payload.transactions)
            for tx_data in transactions_data:
                tx = BetPayload(**tx_data)
                txid = tx._generate_txid()
                if not self.tx_mempool.get_transaction(txid):
                    self.tx_mempool.add_transaction(tx._generate_txid(), tx)
                    peer_id_hex = peer.public_key.key_to_bin().hex()
                    self.latest_tx_timestamps[peer_id_hex] = max(
                        self.latest_tx_timestamps.get(peer_id_hex, 0.0), tx.timestamp)

                else:
                    peer_id_hex = peer.public_key.key_to_bin().hex()
                    self.latest_tx_timestamps[peer_id_hex] = max(
                        self.latest_tx_timestamps.get(peer_id_hex, 0.0), tx.timestamp)

            # Request more transactions if the response indicated there are more
            if payload.has_more:
                peer_id_hex = peer.public_key.key_to_bin().hex()
                last_seen = self.latest_tx_timestamps.get(peer_id_hex, 0.0)
                self.ez_send(peer, TransactionsRequest(
                    last_seen_timestamp=last_seen))

        except json.JSONDecodeError as e:
            pass

    async def broadcast_block(self, block: Block):
        for peer in self.get_peers():
            self.ez_send(peer, block)
        print(f"{self.my_peer.address.port}: Block {block.index} broadcasted.")

    @lazy_wrapper(Block)
    async def on_block(self, peer: Peer, payload: Block):
        print(
            f"{self.my_peer.address.port}: Received block {payload.index} from {peer.address.port}"
        )
        if self.chain.validate_block(payload):
            if self.chain._add_block(payload):
                print(
                    f"{self.my_peer.address.port}: Added block {payload.index} to the chain."
                )
                self.tx_mempool.remove_transactions(payload.transactions)

                # If the Chain Length is 12, Trigger Broadcast Lottery
                if (self.chain._get_length() % BLOCKS_PER_ROUND == 0) and (self.chain._get_length() > 0):

                    self.broadcast_lottery()

            else:
                print(
                    f"{self.my_peer.address.port}: Block {payload.index} already in chain."
                )
        else:
            print(
                f"{self.my_peer.address.port}: Invalid block {payload.index} received."
            )

    # Lottery

    def broadcast_lottery(self):
        if self.is_lottery_broadcaster:
            print(
                f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! CHAIN LENGTH IS NOW {self.chain._get_length()}, BROADCASTING LOTTERY !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            lottery_result, total_amount, winner_list = self.chain.get_winning_result()

            print(
                f"Received lottery result for round {self.chain._get_round_number()}. Winning number is {lottery_result}. Total Amount is {total_amount}")

            print("Winner:", json.dumps(winner_list, indent=4))
            if lottery_result is not None:
                for peer in self.get_peers():
                    self.ez_send(peer, LotteryResult(
                        round=self.chain._get_round_number(),
                        winning_number=lottery_result,
                        total_amount=total_amount,
                        winner_list=json.dumps(winner_list)
                    ))

    async def select_lottery_broadcaster(self):
        all_peers = list(self.get_peers()) + [self.my_peer]
        if all_peers:
            sorted_peers = sorted(
                all_peers, key=lambda p: p.public_key.key_to_bin().hex()
            )
            broadcaster = sorted_peers[0]
            if broadcaster == self.my_peer:
                self.is_lottery_broadcaster = True
                print(
                    f"{broadcaster.address.port} is the lottery broadcaster (lowest peer ID)."
                )
        else:
            print("No peers available to select a lottery broadcaster.")
            self.is_lottery_broadcaster = False

    @lazy_wrapper(LotteryResult)
    def on_lottery_result(self, peer: Peer, payload: LotteryResult):

        try:
            winner_list = json.loads(payload.winner_list)
            my_public_key_hex = self.crypto.key_to_bin(
                self.my_peer.public_key).hex()
            if my_public_key_hex in winner_list:
                winnings = winner_list[my_public_key_hex]
                print(
                    f"Congratulations! This node ({self.my_peer.address.port}) won {winnings} in the lottery (Round {payload.round}).")

        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            pass

    async def _mine_and_broadcast(self):

        while True:
            await asyncio.sleep(5)  # Check every 5 seconds (adjust as needed)
            if self.is_miner and self.network_established and self.tx_mempool.get_all_transactions():
                print(f"{self.my_peer.address.port}: Mining a new block...")
                transactions_to_mine = self.tx_mempool.get_all_transactions()
                if transactions_to_mine:
                    new_block = self.chain.create_block()
                    if new_block:

                        await self.broadcast_block(new_block)

                        self.tx_mempool.clear_mempool()  # Clear mempool after successful mining
                        print(
                            f"{self.my_peer.address.port}: Successfully mined and broadcasted block {new_block.index}.")
                    else:
                        print(
                            f"{self.my_peer.address.port}: Failed to create a new block.")
                else:
                    print(
                        f"{self.my_peer.address.port}: No transactions in mempool to mine.")

    def started(self) -> None:
        self.network.add_peer_observer(self)

        # Do not register generate_transaction here initially
        pass
