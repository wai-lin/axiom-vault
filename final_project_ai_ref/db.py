import json
import os
import time


class Database:
    def __init__(self, filename='lottery_blockchain.json'):
        self.filename = filename
        self.data = self.load_data()
        
        # Initialize database structure if it doesn't exist
        if 'blockchain' not in self.data:
            self.data['blockchain'] = []
        if 'mempool' not in self.data:
            self.data['mempool'] = {}
        if 'winners' not in self.data:
            self.data['winners'] = {}
        if 'peers' not in self.data:
            self.data['peers'] = {}

    def load_data(self):
        if os.path.exists(self.filename) and os.path.getsize(self.filename) > 0:
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {self.filename}: {e}")
                print("Initializing database with empty data.")
                return {}
        else:
            print(
                f"Database file {self.filename} does not exist or is empty. Initializing with empty data.")
            return {}

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    # Blockchain operations
    def save_block(self, block):
        """Save a block to the blockchain"""
        # Convert block object to dictionary
        block_dict = {
            "index": block.index,
            "timestamp": block.timestamp,
            "bets": block.bets,
            "previous_hash": block.previous_hash,
            "hash": block.hash,
            "winning_number": block.winning_number,
            "commit_reveals": block.commit_reveals
        }
        
        # Add to blockchain
        self.data['blockchain'].append(block_dict)
        self.save_data()
        return block_dict
    
    def get_blockchain(self):
        """Get the entire blockchain"""
        return self.data['blockchain']
    
    def get_latest_block(self):
        """Get the latest block in the blockchain"""
        if not self.data['blockchain']:
            return None
        return self.data['blockchain'][-1]
    
    # Mempool operations
    def add_transaction(self, tx_hash, transaction):
        """Add a transaction to the mempool"""
        self.data['mempool'][tx_hash] = transaction
        self.save_data()
        
    def get_mempool_transactions(self):
        """Get all transactions in the mempool"""
        return self.data['mempool']
    
    def clear_transactions(self, tx_hashes):
        """Remove transactions from the mempool"""
        for tx_hash in tx_hashes:
            if tx_hash in self.data['mempool']:
                del self.data['mempool'][tx_hash]
        self.save_data()
    
    # Winner operations
    def save_winners(self, block_index, winners_data):
        """Save winners for a block"""
        self.data['winners'][str(block_index)] = winners_data
        self.save_data()
    
    def get_winners(self, block_index=None):
        """Get winners for a specific block or all winners"""
        if block_index is not None:
            return self.data['winners'].get(str(block_index))
        return self.data['winners']
    
    # Peer operations
    def update_peer(self, peer_id, data):
        """Update peer data"""
        if peer_id not in self.data['peers']:
            self.data['peers'][peer_id] = {}
        
        # Update peer data
        self.data['peers'][peer_id].update(data)
        self.data['peers'][peer_id]['last_seen'] = time.time()
        self.save_data()
    
    def get_peers(self):
        """Get all peers"""
        return self.data['peers']
    
    def get_peer(self, peer_id):
        """Get a specific peer"""
        return self.data['peers'].get(peer_id)