import matplotlib.pyplot as plt
import networkx as nx
import os
from datetime import datetime


class LotteryVisualizer:
    def __init__(self, output_dir='visualizations'):
        self.output_dir = output_dir
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def plot_lottery_results(self, blockchain, winners):
        """Plot lottery results over time"""
        # Skip genesis block
        blocks = blockchain[1:]
        
        if not blocks:
            print("No blocks to visualize yet")
            return
        
        # Extract data
        block_indices = [block.index for block in blocks]
        winning_numbers = [block.winning_number for block in blocks]
        timestamps = [datetime.fromtimestamp(block.timestamp).strftime('%H:%M:%S') for block in blocks]
        
        # Count winners per block
        winner_counts = []
        prize_pools = []
        for block in blocks:
            block_winners = winners.get(block.index, {})
            winner_list = block_winners.get('winners', [])
            winner_counts.append(len(winner_list))
            prize_pools.append(block_winners.get('prize_pool', 0))
        
        # Create figure with multiple subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))
        
        # Plot winning numbers
        ax1.plot(block_indices, winning_numbers, 'o-', color='blue')
        ax1.set_title('Winning Numbers Over Time')
        ax1.set_xlabel('Block Number')
        ax1.set_ylabel('Winning Number')
        ax1.grid(True)
        
        # Plot winner counts
        ax2.bar(block_indices, winner_counts, color='green')
        ax2.set_title('Number of Winners Per Block')
        ax2.set_xlabel('Block Number')
        ax2.set_ylabel('Number of Winners')
        ax2.grid(True)
        
        # Plot prize pools
        ax3.bar(block_indices, prize_pools, color='orange')
        ax3.set_title('Prize Pool Per Block')
        ax3.set_xlabel('Block Number')
        ax3.set_ylabel('Prize Pool (tokens)')
        ax3.grid(True)
        
        plt.tight_layout()
        
        # Save the figure
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.output_dir}/lottery_results_{timestamp}.png"
        plt.savefig(filename)
        plt.close()
        
        print(f"Lottery results visualization saved to {filename}")
    
    def plot_network_topology(self, peers, connections):
        """Plot the network topology of peers"""
        G = nx.Graph()
        
        # Add nodes (peers)
        for peer_id in peers:
            G.add_node(peer_id)
        
        # Add edges (connections)
        for source, targets in connections.items():
            for target in targets:
                G.add_edge(source, target)
        
        # Create the plot
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(G)  # Position nodes using spring layout
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color='lightblue')
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
        
        plt.title('Lottery Network Topology')
        plt.axis('off')  # Turn off axis
        
        # Save the figure
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.output_dir}/network_topology_{timestamp}.png"
        plt.savefig(filename)
        plt.close()
        
        print(f"Network topology visualization saved to {filename}")
    
    def plot_bet_distribution(self, bets):
        """Plot distribution of bet numbers and amounts"""
        if not bets:
            print("No bets to visualize yet")
            return
        
        # Extract data
        bet_numbers = [bet['bet_number'] for bet in bets]
        bet_amounts = [bet['bet_amount'] for bet in bets]
        
        # Create figure with multiple subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
        
        # Plot bet number distribution
        ax1.hist(bet_numbers, bins=range(1, 101), color='blue', alpha=0.7)
        ax1.set_title('Distribution of Bet Numbers')
        ax1.set_xlabel('Bet Number')
        ax1.set_ylabel('Frequency')
        ax1.set_xlim(1, 99)
        ax1.grid(True)
        
        # Plot bet amount distribution
        ax2.hist(bet_amounts, bins=range(1, 101), color='green', alpha=0.7)
        ax2.set_title('Distribution of Bet Amounts')
        ax2.set_xlabel('Bet Amount (tokens)')
        ax2.set_ylabel('Frequency')
        ax2.set_xlim(1, 99)
        ax2.grid(True)
        
        plt.tight_layout()
        
        # Save the figure
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.output_dir}/bet_distribution_{timestamp}.png"
        plt.savefig(filename)
        plt.close()
        
        print(f"Bet distribution visualization saved to {filename}")