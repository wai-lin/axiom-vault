import os
import sys
import time
import random
import argparse
from typing import List

from ipv8.configuration import ConfigBuilder
from ipv8_service import IPv8
from ipv8.peerdiscovery.discovery import RandomWalk

from community import LotteryCommunity
from visualizer import LotteryVisualizer

# Number of peers in the network
NUM_PEERS = 10


def start_lottery_network(peer_id: int = 0, total_peers: int = NUM_PEERS):
    """Start a lottery network peer"""
    # Create a configuration for IPv8
    builder = ConfigBuilder().clear_keys().clear_overlays()

    # Generate a new key for this peer
    builder.add_key("my peer", "medium", f"peer_{peer_id}")

    # Setup the lottery network overlay
    builder.add_overlay(
        "LotteryNetwork",
        "my peer",
        [RandomWalk],
        {},
        [("started", lambda: None)],
        LotteryCommunity,
    )

    # Create custom data directory for this peer
    data_dir = f"./peer_{peer_id}_data"
    os.makedirs(data_dir, exist_ok=True)

    # Create the IPv8 service
    ipv8 = IPv8(
        builder.finalize(), extra_communities={"LotteryNetwork": LotteryCommunity}
    )
    ipv8.start()

    # Get the lottery community instance
    lottery_community = None
    for overlay in ipv8.overlays:
        if isinstance(overlay, LotteryCommunity):
            lottery_community = overlay
            break

    if not lottery_community:
        print("Failed to start lottery community")
        ipv8.stop()
        return

    # Set the database path for this peer
    lottery_community.db_manager = lottery_community.db_manager.__class__(
        f"{data_dir}/lottery_db"
    )

    print(f"Started peer {peer_id} with mid: {lottery_community.my_peer.mid.hex()[:8]}")

    return ipv8, lottery_community


def start_multiple_peers(num_peers: int = NUM_PEERS):
    """Start multiple peers in the same process"""
    instances = []

    for i in range(num_peers):
        instance = start_lottery_network(i, num_peers)
        if instance:
            instances.append(instance)

    return instances


def main():
    parser = argparse.ArgumentParser(description="Start a lottery blockchain network")
    parser.add_argument(
        "--peers", type=int, default=NUM_PEERS, help="Number of peers to start"
    )
    parser.add_argument(
        "--single", type=int, default=None, help="Start a single peer with the given ID"
    )
    parser.add_argument(
        "--visualize", action="store_true", help="Start with visualization"
    )

    args = parser.parse_args()

    if args.single is not None:
        # Start a single peer
        instance = start_lottery_network(args.single, args.peers)
        if not instance:
            return

        ipv8, lottery_community = instance

        # Start visualizer if requested
        visualizer = None
        if args.visualize:
            visualizer = LotteryVisualizer(lottery_community.blockchain)
            visualizer.start()

        # Keep the process running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            if visualizer:
                visualizer.stop()
            ipv8.stop()
    else:
        # Start multiple peers
        instances = start_multiple_peers(args.peers)

        if not instances:
            return

        # Start visualizer for the first peer if requested
        visualizer = None
        if args.visualize and instances:
            ipv8, lottery_community = instances[0]
            visualizer = LotteryVisualizer(lottery_community.blockchain)
            visualizer.start()

        # Keep the process running
        try:
            print(f"Started {len(instances)} peers. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping all peers...")
        finally:
            if visualizer:
                visualizer.stop()
            for ipv8, _ in instances:
                ipv8.stop()


if __name__ == "__main__":
    main()
