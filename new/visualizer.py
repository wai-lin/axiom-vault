import json
import time
import os
from typing import Dict, List, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser

from blockchain import LotteryBlockchain, Block

class LotteryVisualizer:
    def __init__(self, blockchain: LotteryBlockchain, port: int = 8080):
        self.blockchain = blockchain
        self.port = port
        self.server = None
        self.server_thread = None
        
    def start(self):
        """Start the visualization server"""
        # Create and start the HTTP server
        self.server = HTTPServer(('localhost', self.port), VisualizerRequestHandler)
        self.server.blockchain = self.blockchain
        
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"Visualization server started at http://localhost:{self.port}")
        
        # Open the browser
        webbrowser.open(f"http://localhost:{self.port}")
    
    def stop(self):
        """Stop the visualization server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("Visualization server stopped")

class VisualizerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_index_html().encode())
        elif self.path == '/blockchain':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.get_blockchain_data()).encode())
        elif self.path == '/style.css':
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            self.wfile.write(self.get_css().encode())
        elif self.path == '/script.js':
            self.send_response(200)
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            self.wfile.write(self.get_js().encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_blockchain_data(self):
        """Get blockchain data for visualization"""
        blockchain = self.server.blockchain
        
        # Format blocks for visualization
        blocks = []
        for block in blockchain.chain:
            # Calculate lottery results for this block
            results = blockchain.calculate_lottery_results(block)
            
            # Format block data
            block_data = {
                "index": block.index,
                "timestamp": block.timestamp,
                "hash": block.hash[:10] + "...",
                "previous_hash": block.previous_hash[:10] + "...",
                "validator": block.validator[:10] + "..." if block.validator else "Genesis",
                "transactions": len(block.transactions),
                "winning_number": block.winning_number,
                "winners": len(results["winners"]) if "winners" in results else 0,
                "total_pot": results.get("total_pot", 0)
            }
            blocks.append(block_data)
        
        # Get mempool transactions
        mempool = []
        for tx in blockchain.mempool:
            tx_data = {
                "sender": tx["sender"][:10] + "...",
                "bet_number": tx["bet_number"],
                "amount": tx["amount"],
                "timestamp": tx["timestamp"]
            }
            mempool.append(tx_data)
        
        return {
            "blocks": blocks,
            "mempool": mempool,
            "validators": [
                {"id": validator_id[:10] + "...", "stake": stake}
                for validator_id, stake in blockchain.validators.items()
            ]
        }
    
    def get_index_html(self):
        """Get the HTML for the visualization page"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2-Digit Lottery Blockchain</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <header>
        <h1>2-Digit Lottery Blockchain</h1>
    </header>
    
    <main>
        <section class="dashboard">
            <div class="card">
                <h2>Blockchain Stats</h2>
                <div id="blockchain-stats">
                    <p>Loading...</p>
                </div>
            </div>
            
            <div class="card">
                <h2>Latest Lottery Results</h2>
                <div id="lottery-results">
                    <p>Loading...</p>
                </div>
            </div>
        </section>
        
        <section class="blockchain-view">
            <h2>Blockchain</h2>
            <div id="blockchain-container">
                <p>Loading blockchain...</p>
            </div>
        </section>
        
        <section class="mempool-view">
            <h2>Mempool (Pending Bets)</h2>
            <div id="mempool-container">
                <p>Loading mempool...</p>
            </div>
        </section>
        
        <section class="validators-view">
            <h2>Validators</h2>
            <div id="validators-container">
                <p>Loading validators...</p>
            </div>
        </section>
    </main>
    
    <footer>
        <p>2-Digit Lottery Blockchain System</p>
    </footer>
    
    <script src="/script.js"></script>
</body>
</html>
"""
    
    def get_css(self):
        """Get the CSS for the visualization page"""
        return """
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f7fa;
}

header {
    background-color: #2c3e50;
    color: white;
    text-align: center;
    padding: 1rem;
}

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}

.dashboard {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.card {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
}

h2 {
    color: #2c3e50;
    margin-bottom: 1rem;
    border-bottom: 2px solid #ecf0f1;
    padding-bottom: 0.5rem;
}

.blockchain-view, .mempool-view, .validators-view {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
    margin-bottom: 2rem;
}

.block {
    background-color: #ecf0f1;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    border-left: 4px solid #3498db;
}

.block-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
}

.block-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.5rem;
}

.block-item {
    background-color: white;
    padding: 0.5rem;
    border-radius: 4px;
}

.transaction, .validator {
    background-color: #ecf0f1;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
}

.winning-number {
    font-size: 1.5rem;
    font-weight: bold;
    color: #e74c3c;
}

footer {
    text-align: center;
    padding: 1rem;
    background-color: #2c3e50;
    color: white;
}

@media (max-width: 768px) {
    .dashboard {
        grid-template-columns: 1fr;
    }
    
    .block-content {
        grid-template-columns: 1fr;
    }
}
"""
    
    def get_js(self):
        """Get the JavaScript for the visualization page"""
        return """
document.addEventListener('DOMContentLoaded', function() {
    // Initial data load
    fetchBlockchainData();
    
    // Set up periodic refresh
    setInterval(fetchBlockchainData, 5000);
});

function fetchBlockchainData() {
    fetch('/blockchain')
        .then(response => response.json())
        .then(data => {
            updateBlockchainStats(data);
            updateLotteryResults(data);
            updateBlockchain(data.blocks);
            updateMempool(data.mempool);
            updateValidators(data.validators);
        })
        .catch(error => console.error('Error fetching blockchain data:', error));
}

function updateBlockchainStats(data) {
    const statsContainer = document.getElementById('blockchain-stats');
    const blocks = data.blocks;
    const mempool = data.mempool;
    
    statsContainer.innerHTML = `
        <p><strong>Blocks:</strong> ${blocks.length}</p>
        <p><strong>Pending Bets:</strong> ${mempool.length}</p>
        <p><strong>Validators:</strong> ${data.validators.length}</p>
    `;
}

function updateLotteryResults(data) {
    const resultsContainer = document.getElementById('lottery-results');
    const blocks = data.blocks;
    
    if (blocks.length <= 1) {
        resultsContainer.innerHTML = '<p>No lottery results yet</p>';
        return;
    }
    
    // Get the latest non-genesis block
    const latestBlock = blocks[blocks.length - 1];
    
    resultsContainer.innerHTML = `
        <p><strong>Latest Draw (Block #${latestBlock.index}):</strong></p>
        <p class="winning-number">${latestBlock.winning_number || 'No draw'}</p>
        <p><strong>Winners:</strong> ${latestBlock.winners}</p>
        <p><strong>Total Pot:</strong> ${latestBlock.total_pot} tokens</p>
    `;
}

function updateBlockchain(blocks) {
    const blockchainContainer = document.getElementById('blockchain-container');
    
    if (blocks.length === 0) {
        blockchainContainer.innerHTML = '<p>No blocks in the blockchain</p>';
        return;
    }
    
    let blocksHTML = '';
    
    // Reverse to show newest blocks first
    blocks.slice().reverse().forEach(block => {
        blocksHTML += `
            <div class="block">
                <div class="block-header">
                    <span><strong>Block #${block.index}</strong></span>
                    <span>${new Date(block.timestamp * 1000).toLocaleString()}</span>
                </div>
                <div class="block-content">
                    <div class="block-item">
                        <p><strong>Hash:</strong> ${block.hash}</p>
                        <p><strong>Previous Hash:</strong> ${block.previous_hash}</p>
                    </div>
                    <div class="block-item">
                        <p><strong>Validator:</strong> ${block.validator}</p>
                        <p><strong>Transactions:</strong> ${block.transactions}</p>
                    </div>
                    <div class="block-item">
                        <p><strong>Winning Number:</strong> ${block.winning_number || 'N/A'}</p>
                        <p><strong>Winners:</strong> ${block.winners}</p>
                        <p><strong>Total Pot:</strong> ${block.total_pot} tokens</p>
                    </div>
                </div>
            </div>
        `;
    });
    
    blockchainContainer.innerHTML = blocksHTML;
}

function updateMempool(mempool) {
    const mempoolContainer = document.getElementById('mempool-container');
    
    if (mempool.length === 0) {
        mempoolContainer.innerHTML = '<p>No pending bets in the mempool</p>';
        return;
    }
    
    let mempoolHTML = '';
    
    // Sort by timestamp (newest first)
    mempool.sort((a, b) => b.timestamp - a.timestamp);
    
    mempool.forEach(tx => {
        mempoolHTML += `
            <div class="transaction">
                <div>
                    <p><strong>Sender:</strong> ${tx.sender}</p>
                    <p><strong>Time:</strong> ${new Date(tx.timestamp * 1000).toLocaleString()}</p>
                </div>
                <div>
                    <p><strong>Bet Number:</strong> ${tx.bet_number}</p>
                    <p><strong>Amount:</strong> ${tx.amount} tokens</p>
                </div>
            </div>
        `;
    });
    
    mempoolContainer.innerHTML = mempoolHTML;
}

function updateValidators(validators) {
    const validatorsContainer = document.getElementById('validators-container');
    
    if (validators.length === 0) {
        validatorsContainer.innerHTML = '<p>No validators registered</p>';
        return;
    }
    
    let validatorsHTML = '';
    
    // Sort by stake (highest first)
    validators.sort((a, b) => b.stake - a.stake);
    
    validators.forEach(validator => {
        validatorsHTML += `
            <div class="validator">
                <div>
                    <p><strong>Validator:</strong> ${validator.id}</p>
                </div>
                <div>
                    <p><strong>Stake:</strong> ${validator.stake} tokens</p>
                </div>
            </div>
        `;
    });
    
    validatorsContainer.innerHTML = validatorsHTML;
}
"""
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        return