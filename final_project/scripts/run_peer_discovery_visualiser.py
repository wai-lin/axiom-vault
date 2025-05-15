"""
Live peer graph merger and visualizer.

• Watches `data/*/peer_discovery.json` and merges discovered peers
• Generates a graph frame every second using matplotlib
• Outputs:
    - combined_peer_graph.json
    - peer_discovery.gif
"""

import json
import pathlib
import time
from typing import Dict, Set
from io import BytesIO

import networkx as nx
import matplotlib.pyplot as plt
import imageio.v2 as imageio

DATA_DIR = pathlib.Path("data")
OUTPUT_FILE = pathlib.Path("combined_peer_graph.json")
GIF_PATH = "peer_discovery.gif"
POLL_INTERVAL = 1.0  # seconds
FRAME_DURATION = 0.4  # seconds
NODE_LABELS: Dict[str, str] = {}


mtime_cache: Dict[pathlib.Path, float] = {}
graph: Dict[str, Set[str]] = {}
layout_cache = {}
gif_frames: list[BytesIO] = []


def log(msg: str):
    print(f"[INFO] {msg}")


def warn(msg: str):
    print(f"[WARN] {msg}")


def error(msg: str):
    print(f"[ERROR] {msg}")


def safe_load_json(path: pathlib.Path):
    try:
        with path.open() as f:
            return json.load(f)
    except json.JSONDecodeError:
        error(f"JSON decoding failed: {path}")
        return None


def process_file(node_dir: pathlib.Path):
    peer_file = node_dir / "peer_discovery.json"
    if not peer_file.exists():
        return

    mtime = peer_file.stat().st_mtime
    if mtime_cache.get(peer_file) == mtime:
        return

    mtime_cache[peer_file] = mtime
    records = safe_load_json(peer_file)
    if not isinstance(records, dict):
        warn(f"Skipping malformed file: {peer_file}")
        return

    for src, peers in records.items():
        bucket = graph.setdefault(src, set())
        bucket.update(peers)
        # Assign label once
        if src not in NODE_LABELS:
            NODE_LABELS[src] = node_dir.name


def write_output_json():
    with OUTPUT_FILE.open("w") as f:
        json.dump({k: sorted(v) for k, v in graph.items()}, f, indent=2)


def render_graph_to_buffer(graph_data: Dict[str, list]) -> BytesIO:
    G = nx.DiGraph()
    for src, targets in graph_data.items():
        for dst in targets:
            G.add_edge(src, dst)

    global layout_cache
    if set(G.nodes) != set(layout_cache.keys()):
        layout_cache = nx.circular_layout(G)

    fig, ax = plt.subplots(figsize=(10, 8))
    labels = {n: NODE_LABELS.get(n, n) for n in G.nodes}
    nx.draw_networkx_labels(
        G, pos=layout_cache, labels=labels, font_size=8, font_color="black", ax=ax
    )
    nx.draw(
        G,
        pos=layout_cache,
        node_size=300,
        node_color="skyblue",
        edge_color="gray",
        with_labels=False,
        arrows=True,
        ax=ax,
    )
    ax.set_title("Peer Discovery")

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def update_gif():
    if not gif_frames:
        warn("No frames to render GIF.")
        return
    imageio.mimsave(GIF_PATH, gif_frames)
    log(f"GIF updated with {len(gif_frames)} frames → {GIF_PATH}")


def main():
    graph.clear()
    layout_cache.clear()
    gif_frames.clear()

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    step = 0
    while True:
        for node_dir in DATA_DIR.iterdir():
            if node_dir.is_dir():
                process_file(node_dir)

        write_output_json()

        with OUTPUT_FILE.open() as f:
            graph_data = json.load(f)

        frame_buf = render_graph_to_buffer(graph_data)
        gif_frames.append(imageio.imread(frame_buf))
        log(f"Captured in-memory frame {step}")

        # batch render every 5 frames
        if step % 5 == 0:
            update_gif()

        step += 1
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
