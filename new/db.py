import json
import plyvel
import os
from typing import Dict, List, Any, Optional
from bloomfilter import BloomFilter

class DatabaseManager:
    def __init__(self, db_path: str = "./lottery_db"):
        # Ensure directory exists
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize databases
        self.blockchain_db = plyvel.DB(os.path.join(db_path, 'blockchain'), create_if_missing=True)
        self.mempool_db = plyvel.DB(os.path.join(db_path, 'mempool'), create_if_missing=True)
        self.peer_db = plyvel.DB(os.path.join(db_path, 'peers'), create_if_missing=True)
        
        # Initialize bloom filter for transaction lookup optimization
        self.tx_bloom = BloomFilter(capacity=10000, error_rate=0.001)
        self._load_tx_bloom()
    
    def _load_tx_bloom(self) -> None:
        """Load transaction IDs into bloom filter"""
        with self.mempool_db.iterator() as it:
            for key, _ in it:
                self.tx_bloom.add(key)
    
    def save_block(self, block: Dict) -> None:
        """Save a block to the blockchain database"""
        block_key = f"block_{block['index']}".encode()
        self.blockchain_db.put(block_key, json.dumps(block).encode())
    
    def get_block(self, index: int) -> Optional[Dict]:
        """Get a block by index"""
        block_key = f"block_{index}".encode()
        block_data = self.blockchain_db.get(block_key)
        if block_data:
            return json.loads(block_data.decode())
        return None
    
    def get_latest_block_index(self) -> int:
        """Get the index of the latest block"""
        latest_index = -1
        with self.blockchain_db.iterator(reverse=True) as it:
            for key, _ in it:
                key_str = key.decode()
                if key_str.startswith("block_"):
                    try:
                        index = int(key_str.split("_")[1])
                        latest_index = max(latest_index, index)
                    except (ValueError, IndexError):
                        pass
                    break
        return latest_index if latest_index >= 0 else 0
    
    def get_all_blocks(self) -> List[Dict]:
        """Get all blocks in the blockchain"""
        blocks = []
        with self.blockchain_db.iterator() as it:
            for key, value in it:
                if key.decode().startswith("block_"):
                    blocks.append(json.loads(value.decode()))
        
        # Sort blocks by index
        blocks.sort(key=lambda x: x['index'])
        return blocks
    
    def save_transaction(self, transaction: Dict) -> None:
        """Save a transaction to the mempool database"""
        tx_id = transaction.get("id", str(transaction["timestamp"]) + transaction["sender"])
        tx_key = tx_id.encode()
        self.mempool_db.put(tx_key, json.dumps(transaction).encode())
        self.tx_bloom.add(tx_key)
    
    def get_transaction(self, tx_id: str) -> Optional[Dict]:
        """Get a transaction by ID"""
        tx_key = tx_id.encode()
        # Use bloom filter for quick negative lookups
        if tx_key not in self.tx_bloom:
            return None
        
        tx_data = self.mempool_db.get(tx_key)
        if tx_data:
            return json.loads(tx_data.decode())
        return None
    
    def get_all_mempool_transactions(self) -> List[Dict]:
        """Get all transactions in the mempool"""
        transactions = []
        with self.mempool_db.iterator() as it:
            for _, value in it:
                transactions.append(json.loads(value.decode()))
        return transactions
    
    def clear_mempool_transactions(self, tx_ids: List[str]) -> None:
        """Remove transactions from mempool after they're included in a block"""
        for tx_id in tx_ids:
            tx_key = tx_id.encode()
            self.mempool_db.delete(tx_key)
    
    def save_peer_info(self, peer_id: str, peer_info: Dict) -> None:
        """Save peer information"""
        self.peer_db.put(peer_id.encode(), json.dumps(peer_info).encode())
    
    def get_peer_info(self, peer_id: str) -> Optional[Dict]:
        """Get peer information"""
        peer_data = self.peer_db.get(peer_id.encode())
        if peer_data:
            return json.loads(peer_data.decode())
        return None
    
    def get_all_peers(self) -> Dict[str, Dict]:
        """Get all known peers"""
        peers = {}
        with self.peer_db.iterator() as it:
            for key, value in it:
                peer_id = key.decode()
                peers[peer_id] = json.loads(value.decode())
        return peers
    
    def create_tx_bloom_filter(self) -> BloomFilter:
        """Create a bloom filter of current mempool transactions for gossip protocol"""
        bloom = BloomFilter(capacity=10000, error_rate=0.001)
        with self.mempool_db.iterator() as it:
            for key, _ in it:
                bloom.add(key)
        return bloom
    
    def close(self) -> None:
        """Close all database connections"""
        self.blockchain_db.close()
        self.mempool_db.close()
        self.peer_db.close()