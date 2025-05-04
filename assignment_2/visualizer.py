import networkx as nx
import matplotlib.pyplot as plt
from db import Database

"""
Recommended layouts for good visualization:
- circular
- shell
"""
layouts = ["spring", "circular", "shell", "kamada"]

class TopologyPlotter:
    def __init__(self):
        self.db = Database()
        self.edges = self.db.get_edges()
        self.G = nx.DiGraph()
        self.G.add_edges_from(self.edges)

    def plot(self, layout: str = "shell"):
        layout_func = self._get_layout_func(layout)
        pos = layout_func(self.G)

        plt.figure(figsize=(8, 6))
        nx.draw(
            self.G, pos,
            with_labels=True,
            node_color='lightgreen',
            node_size=2000,
            arrows=True,
            arrowsize=20,
            font_size=12,
            font_weight='bold',
            edge_color='gray'
        )

        plt.title(f"Gossip pull-based topology ({layout})", fontsize=14)
        filename = f"topology_{layout}.png"
        plt.savefig(filename, dpi=300)
        plt.close()

    def _get_layout_func(self, layout: str):
        layout = layout.lower()
        if layout == "spring":
            return lambda G: nx.spring_layout(G, seed=42)
        elif layout == "shell":
            return nx.shell_layout
        elif layout == "circular":
            return nx.circular_layout
        elif layout == "kamada":
            return nx.kamada_kawai_layout
        elif layout == "spectral":
            return nx.spectral_layout
        else:
            raise ValueError(f"Unsupported layout: {layout}")


# if __name__ == '__main__':
#     plotter = TopologyPlotter()
#     for layout in ["spring", "shell", "circular", "kamada"]:
#         plotter.plot(layout)